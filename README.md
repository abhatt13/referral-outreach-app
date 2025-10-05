# Referral Outreach Automation App

![CI](https://github.com/abhatt13/referral-outreach-app/actions/workflows/ci.yml/badge.svg)

Automate your job referral requests by finding employees at target companies and sending personalized cold emails with automatic follow-ups.

## Features

- 🔍 **People Search**: Automatically find employees at companies using Apollo.io
- 📧 **Email Automation**: Send personalized cold emails via Gmail
- ⏰ **Auto Follow-ups**: Automatically send follow-up emails after 1 day
- 📊 **Campaign Tracking**: Track email campaigns and their success rates
- 🎨 **Customizable Templates**: Edit email templates to match your style
- 💾 **Email History**: Keep track of all sent emails and their status

## Setup Instructions

### 1. Install Dependencies

```bash
cd ~/referral-outreach-app
pip install -r requirements.txt
```

### 2. Configure Apollo.io API

1. Sign up for [Apollo.io](https://www.apollo.io/)
2. Get your API key from Settings > API
3. Add it to `.env` file:
   ```
   APOLLO_API_KEY=your_api_key_here
   ```

### 3. Configure Gmail API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Gmail API
4. Create OAuth 2.0 credentials:
   - Application type: Desktop app
   - Download the credentials
5. Save the downloaded file as `credentials.json` in the project root
6. First time you run the app, it will open a browser for OAuth authentication

### 4. Customize Your Information

In the app sidebar, configure:
- Your name
- Your email
- Your LinkedIn URL
- Your 3 key skills/experiences

### 5. Customize Email Templates (Optional)

Edit the templates in the `templates/` folder:
- `initial_email.txt` - First outreach email
- `followup_email.txt` - Follow-up email sent after 1 day

## Usage

### Run the App

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

### Creating a Campaign

1. Go to the "New Campaign" tab
2. Either paste a job description or manually enter company name and job title
3. Click "Find People & Preview Emails"
4. Review the contacts and email previews
5. Click "Send All Emails" to start the campaign
6. Follow-up emails will be sent automatically after 1 day

### Managing Follow-ups

- The scheduler runs in the background and checks for follow-ups every hour
- Start/stop the scheduler from the sidebar
- Follow-ups are sent exactly 1 day after the initial email

## Project Structure

```
referral-outreach-app/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables (API keys)
├── credentials.json            # Gmail OAuth credentials (you provide)
├── token.pickle               # Gmail auth token (auto-generated)
├── src/
│   ├── apollo_client.py       # Apollo.io API integration
│   ├── gmail_client.py        # Gmail API integration
│   ├── database.py            # Database models and utilities
│   ├── email_templates.py     # Email template management
│   ├── job_parser.py          # Job description parser
│   └── scheduler.py           # Follow-up scheduler
├── templates/
│   ├── initial_email.txt      # Initial email template
│   └── followup_email.txt     # Follow-up email template
└── data/
    └── outreach.db            # SQLite database (auto-generated)
```

## Important Notes

- **Rate Limiting**: Gmail has sending limits (~500 emails/day for standard accounts)
- **Apollo Credits**: Free tier has limited credits (~50 contacts/month)
- **Privacy**: Never commit `credentials.json`, `token.pickle`, or `.env` to version control
- **Email Templates**: Customize templates to match your personal style
- **Scheduler**: Keep it running for automatic follow-ups

## Troubleshooting

### Gmail Authentication Issues
- Make sure `credentials.json` is in the project root
- Delete `token.pickle` and re-authenticate if you get auth errors
- Check that Gmail API is enabled in Google Cloud Console

### Apollo.io Not Finding People
- Verify your API key is correct in `.env`
- Check that you have remaining credits in your Apollo account
- Try using the exact company name as it appears on LinkedIn

### Follow-ups Not Sending
- Make sure the scheduler is running (check sidebar)
- Verify that initial emails were sent successfully
- Check the Email History tab for any errors

## Support

For issues or questions, refer to:
- [Apollo.io API Documentation](https://apolloio.github.io/apollo-api-docs/)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Streamlit Documentation](https://docs.streamlit.io/)
