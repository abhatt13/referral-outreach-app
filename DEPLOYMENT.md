# Local Deployment Guide

This guide will help you deploy the Referral Outreach App on your Mac for continuous operation.

## Quick Start

### Option 1: Manual Start (Recommended for First Time)

Simply run:
```bash
cd ~/referral-outreach-app
./start.sh
```

The app will:
- Create a virtual environment (if needed)
- Install dependencies
- Start the Streamlit app at http://localhost:8501

Press `Ctrl+C` to stop the app.

---

## Setup Instructions

### 1. Initial Setup

Before deploying, make sure you've completed the setup from README.md:

1. **Install dependencies:**
   ```bash
   cd ~/referral-outreach-app
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure Apollo.io API Key:**
   - Sign up at https://www.apollo.io/
   - Get your API key from Settings → API
   - Edit `.env` file and add:
     ```
     APOLLO_API_KEY=your_actual_api_key_here
     ```

3. **Set up Gmail OAuth:**
   - Go to https://console.cloud.google.com/
   - Create a new project (or select existing)
   - Enable Gmail API
   - Create OAuth 2.0 Credentials (Application type: Desktop app)
   - Download credentials and save as `credentials.json` in project root
   - Run the app once manually to complete OAuth authentication:
     ```bash
     ./start.sh
     ```
   - A browser will open for you to authenticate
   - After authentication, `token.pickle` will be created

### 2. Running the App

**Simple Method:**
```bash
cd ~/referral-outreach-app
./start.sh
```

The app will open in your browser at http://localhost:8501

---

## Option 2: Auto-Start on Login (macOS)

To have the app start automatically when you log in to your Mac:

### Step 1: Set Up Virtual Environment

```bash
cd ~/referral-outreach-app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

### Step 2: Install as Login Item

```bash
# Copy the plist file to LaunchAgents
cp ~/referral-outreach-app/referral-outreach.plist ~/Library/LaunchAgents/

# Load the service
launchctl load ~/Library/LaunchAgents/referral-outreach.plist

# Start the service
launchctl start com.user.referral-outreach
```

The app will now:
- Start automatically when you log in
- Restart automatically if it crashes
- Run in the background
- Be accessible at http://localhost:8501

### Managing the Service

**Check status:**
```bash
launchctl list | grep referral-outreach
```

**Stop the service:**
```bash
launchctl stop com.user.referral-outreach
```

**Start the service:**
```bash
launchctl start com.user.referral-outreach
```

**Uninstall the service:**
```bash
launchctl unload ~/Library/LaunchAgents/referral-outreach.plist
rm ~/Library/LaunchAgents/referral-outreach.plist
```

**View logs:**
```bash
tail -f ~/referral-outreach-app/logs/stdout.log
tail -f ~/referral-outreach-app/logs/stderr.log
```

---

## Accessing the App

Once running, open your browser and go to:
```
http://localhost:8501
```

You can access it from:
- The same computer
- Other devices on your local network (use your Mac's IP address):
  ```
  http://YOUR_MAC_IP:8501
  ```

To find your Mac's IP address:
```bash
ipconfig getifaddr en0
```

---

## Troubleshooting

### App Won't Start

1. **Check virtual environment:**
   ```bash
   cd ~/referral-outreach-app
   ls venv/
   ```
   If `venv/` doesn't exist, run `./start.sh`

2. **Check dependencies:**
   ```bash
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Check logs (if using launchctl):**
   ```bash
   cat ~/referral-outreach-app/logs/stderr.log
   ```

### Gmail Authentication Issues

1. **Missing credentials.json:**
   - Download from Google Cloud Console
   - Save as `credentials.json` in project root

2. **Token expired:**
   ```bash
   rm token.pickle
   ./start.sh
   ```
   Re-authenticate when browser opens

3. **OAuth consent screen error:**
   - Make sure your Google Cloud project has correct OAuth consent screen configuration
   - Add your Gmail address as a test user

### Apollo.io Not Working

1. **Check API key:**
   ```bash
   cat .env
   ```
   Make sure `APOLLO_API_KEY` is set

2. **Verify credits:**
   - Log in to Apollo.io
   - Check remaining credits in your account

### Port Already in Use

If port 8501 is already in use:

1. **Find what's using it:**
   ```bash
   lsof -i :8501
   ```

2. **Kill the process:**
   ```bash
   kill -9 <PID>
   ```

Or change the port in `start.sh`:
```bash
streamlit run app.py --server.port 8502
```

---

## Security Notes

- **Never commit** `credentials.json`, `token.pickle`, or `.env` to git
- These files contain sensitive authentication data
- The `.gitignore` is already configured to exclude them
- Keep your Apollo.io API key private

---

## Updating the App

To update code or dependencies:

1. **If using launchctl, stop the service:**
   ```bash
   launchctl stop com.user.referral-outreach
   ```

2. **Update code and dependencies:**
   ```bash
   cd ~/referral-outreach-app
   source venv/bin/activate
   pip install --upgrade -r requirements.txt
   ```

3. **Restart:**
   ```bash
   launchctl start com.user.referral-outreach
   # or
   ./start.sh
   ```

---

## Performance Tips

- **Scheduler**: Keep the follow-up scheduler running in the sidebar for automatic follow-ups
- **Email Limits**: Gmail has a ~500 emails/day limit for personal accounts
- **Apollo Credits**: Monitor your Apollo.io credit usage
- **Database**: The SQLite database grows over time; you can delete `data/outreach.db` to reset (you'll lose history)

---

## Next Steps

After deployment:

1. Open http://localhost:8501 in your browser
2. Configure your information in the sidebar
3. Create your first campaign!
4. Enable the follow-up scheduler in the sidebar

Enjoy your automated referral outreach! 🚀
