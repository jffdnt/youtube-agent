# Local Setup Guide (Windows Task Scheduler)

## Why run locally instead of the cloud?
While cloud environments like GitHub Actions are extremely convenient for automations, YouTube employs highly aggressive anti-bot protections. Because cloud execution environments run on massive public datacenters (like Microsoft Azure or AWS), YouTube instantly flags their IP ranges as bots and completely blocks them from fetching video transcripts—even if you authenticate with your personal cookies!

Running this script locally on your own computer or enterprise workstation perfectly bypasses this block. Since you are executing the script from a normal residential or corporate network, YouTube sees the connection as a standard human user browsing the web. 

## How to Automate with Windows Task Scheduler

To get this agent running completely hands-free every day, follow these steps to hook it into Windows Task Scheduler:

### 1. Set the Gemini API Key
Task Scheduler runs completely silently in the background, meaning it doesn't automatically inherit the variables you set in a normal terminal window. You must set your API key as a persistent System environment variable.

1. Click your Windows Start button, type **Environment Variables**, and select **Edit the system environment variables**.
2. Click the **Environment Variables...** button near the bottom right.
3. In the top half of the window (User variables), click **New...**
4. For the **Variable name**, type exactly: `GEMINI_API_KEY`
5. For the **Variable value**, paste your Gemini API key.
6. Click **OK** on all the windows to save it.

### 2. Create the Task Scheduler Job
1. Click your Windows Start button, type **Task Scheduler**, and open it.
2. In the right-hand panel under "Actions", click **Create Basic Task**.
3. **Name:** Type "YouTube Agent" and click Next.
4. **Trigger:** Set the trigger to **Daily** and pick a consistent time (e.g., 8:00 AM). Click Next.
5. **Action:** Select **Start a program** and click Next.
6. **Program/script:** Enter the absolute path to your Python executable. If you are using the virtual environment inside this repository, enter: `C:\dev\10_YouTubeAgent\venv\Scripts\python.exe`
7. **Add arguments:** Type `youtube_agent.py`
8. **Start in:** Type the absolute path to the directory where this repository lives (e.g., `C:\dev\10_YouTubeAgent\`).
9. Click **Finish**.

### 3. Verify it Works
To manually trigger the task and ensure Windows is correctly launching it:
1. In the left-hand panel of Task Scheduler, click exactly on the **Task Scheduler Library** folder icon.
2. Find the "YouTube Agent" task in the middle panel.
3. Right-click the task and select **Run**.
4. Right-click again and hit **Refresh** (or use the Refresh button on the right). The "Last Run Result" column should report `(0x0)`, meaning it was successful.
5. Check the `youtube_agent.log` file in the folder to see a live output of the agent checking the channels!
