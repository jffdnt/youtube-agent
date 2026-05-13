# YouTube AI Agent

An automated workflow that monitors specific YouTube channels and extracts actionable insights from their latest videos using Google's Gemini AI. 

## How it Works
1. **Daily Execution:** A GitHub Actions workflow runs the script (`youtube_agent.py`) every day.
2. **Channel Monitoring:** It checks the RSS feeds of configured YouTube channels (e.g., `@MSFTMechanics`, `@NateBJones`, `@MicrosoftCommunityLearning`) for new uploads.
3. **Transcript Fetching:** It securely downloads the closed captions/transcript of any new video using `youtube-transcript-api`.
4. **AI Summarization:** It passes the raw transcript to the `gemini-1.5-flash` model, requesting a concise, highly actionable Markdown summary of workflow improvements, tools, and tips.
5. **Auto-Commit:** The resulting `.md` files are committed directly to the `insights/` folder in this repository.

## Local Development
To run this locally:
1. Create a virtual environment and `pip install -r requirements.txt`.
2. Set your `GEMINI_API_KEY` as an environment variable.
3. Run `python youtube_agent.py`.
