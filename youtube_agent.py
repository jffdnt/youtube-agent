import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter
import json
import os
import time
import logging
import schedule
import requests
import re
import google.generativeai as genai
import http.cookiejar
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("youtube_agent.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Configuration
# Replace these with the actual Channel IDs or @handles you want to track
# Note: If you provide a @handle or custom URL, the script will try to resolve it.
# It is safer and faster to provide the exact Channel ID (starts with UC...)
CHANNELS = [
    "UCJ9905MRHxwLZ2jeNQGIWxA", # @MSFTMechanics
    "UC0C-17n9iuUQPylguM1d-lQ", # @NateBJones
    "UC_mKdhw-V6CeCM7gTo_Iy7w", # @MicrosoftCommunityLearning
]

STATE_FILE = "state.json"
INSIGHTS_DIR = "insights"

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

def load_state():
    """Loads the state file to remember which videos were already processed."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            logging.error("Failed to parse state.json. Starting fresh.")
    return {}

def save_state(state):
    """Saves the state file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)

def resolve_channel_id(channel_identifier):
    """Attempts to resolve a YouTube handle/URL to a Channel ID."""
    if channel_identifier.startswith("UC") and len(channel_identifier) == 24:
        return channel_identifier # Already a channel ID
    
    # Try to resolve handle by scraping
    if channel_identifier.startswith("@"):
        url = f"https://www.youtube.com/{channel_identifier}"
    else:
        url = channel_identifier
        
    try:
        response = requests.get(url)
        if response.status_code == 200:
            # Look for channel ID in the page source
            match = re.search(r'"channelId":"(UC[\w-]{22})"', response.text)
            if match:
                return match.group(1)
    except Exception as e:
        logging.error(f"Error resolving channel ID for {channel_identifier}: {e}")
        
    logging.warning(f"Could not resolve channel ID for {channel_identifier}. Please use the exact Channel ID.")
    return None

def get_latest_videos(channel_id):
    """Fetches the latest videos for a given channel using its RSS feed."""
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    feed = feedparser.parse(url)
    return feed.entries

def get_transcript(video_id):
    """Retrieves and formats the transcript for a given video."""
    try:
        # Load cookies if they exist
        session = requests.Session()
        session.headers.update({"Accept-Language": "en-US"})
        if os.path.exists("cookies.txt"):
            cookie_jar = http.cookiejar.MozillaCookieJar("cookies.txt")
            cookie_jar.load(ignore_discard=True, ignore_expires=True)
            session.cookies.update(cookie_jar)
            
        transcript = YouTubeTranscriptApi(http_client=session).fetch(video_id)
        formatter = TextFormatter()
        transcript_text = formatter.format_transcript(transcript)
        return transcript_text
    except Exception as e:
        logging.error(f"Error fetching transcript for video {video_id} (It might not have captions enabled): {e}")
        return None

def extract_insights(transcript_text):
    """Passes the transcript to Gemini to extract actionable insights."""
    if not GEMINI_API_KEY:
        return "> **Note:** GEMINI_API_KEY environment variable not set. Saving raw transcript instead.\n\n" + transcript_text
        
    try:
        # Use gemini-1.5-flash as it's fast and highly capable for text summarization
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            "You are an expert tech analyst. Read the following transcript from a Microsoft technology/developer video. "
            "Extract a highly actionable, bulleted list of workflow improvements, tools, tips, and insights. "
            "Keep it concise, well-formatted in Markdown, and directly applicable to a developer or tech professional.\n\n"
            f"Transcript:\n{transcript_text}"
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logging.error(f"Error generating insights with Gemini: {e}")
        return f"> **Error generating insights:** {e}. Saving raw transcript instead.\n\n{transcript_text}"

def process_channels():
    """Main workflow to check channels and download new transcripts."""
    logging.info("Starting channel check workflow...")
    
    if not os.path.exists(INSIGHTS_DIR):
        os.makedirs(INSIGHTS_DIR)

    state = load_state()

    for channel in CHANNELS:
        logging.info(f"Processing target: {channel}")
        channel_id = resolve_channel_id(channel)
        
        if not channel_id:
            continue

        entries = get_latest_videos(channel_id)
        if not entries:
            logging.info(f"No videos found for {channel} (ID: {channel_id})")
            continue
            
        channel_state = state.get(channel_id, {"processed_videos": []})
        processed_videos = set(channel_state.get("processed_videos", []))
        
        new_videos_found = False
        
        for entry in entries:
            video_id = entry.yt_videoid
            title = entry.title
            
            if video_id in processed_videos:
                continue # Already processed this video
            
            logging.info(f"New video found: '{title}' ({video_id})")
            new_videos_found = True
            
            transcript = get_transcript(video_id)
            if transcript:
                logging.info(f"Extracting insights for '{title}'...")
                insights_md = extract_insights(transcript)
                
                safe_title = "".join([c for c in title if c.isalpha() or c.isdigit() or c==' ']).rstrip()
                filename = f"{safe_title}_{video_id}.md".replace(" ", "_")
                filepath = os.path.join(INSIGHTS_DIR, filename)
                
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(f"# {title}\n\n")
                    f.write(f"**Video URL:** https://www.youtube.com/watch?v={video_id}  \n")
                    f.write(f"**Channel ID:** {channel_id}  \n")
                    f.write("---\n\n")
                    f.write(insights_md)
                    
                logging.info(f"Successfully saved insights to {filepath}")
            else:
                logging.warning(f"Skipped transcript save for '{title}' due to missing captions.")
                
            # Add to processed list regardless of whether transcript succeeded, 
            # to avoid spamming failed transcript requests every time.
            processed_videos.add(video_id)
            
        if not new_videos_found:
            logging.info(f"No new videos for {channel}.")
            
        # Update state, keeping only the last 50 processed videos to prevent file from growing indefinitely
        state[channel_id] = {"processed_videos": list(processed_videos)[:50]}
        save_state(state)
        
    logging.info("Workflow complete.")

if __name__ == "__main__":
    # Run once immediately on start
    process_channels()
    
    # --- Uncomment the lines below to run continuously ---
    # logging.info("Scheduling daily runs...")
    # schedule.every().day.at("10:00").do(process_channels)
    # 
    # while True:
    #     schedule.run_pending()
    #     time.sleep(60)
