# Google Calendar Credentials Setup Guide

This guide walks you through setting up Google Calendar authentication for both local development and cloud deployment.

## Prerequisites

- Python 3.7 or higher
- pip package manager
- A Google account
- Access to Google Cloud Console

## Step 1: Set Up Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com)

2. Create a new project (or select an existing one)

3. Enable the Google Calendar API:
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"

4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop app" as the application type
   - Give it a name (e.g., "Suggest Some Time Local")
   - Click "Create"

5. Download the credentials:
   - Click the download button (⬇️) next to your new OAuth client
   - Save the file as `credentials.json` in your project directory

## Step 2: Local Development Setup

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Authenticate with Google

```bash
python app.py
```

This will:
1. Open your browser automatically
2. Ask you to sign in to your Google account
3. Request permission to access your Google Calendar (read-only)
4. Save the authentication token to `token.pickle`

**Important:** Keep `token.pickle` secure and never commit it to version control!

### Verify Local Setup

```bash
python test_credentials.py
```

All tests should pass:
- ✓ Environment Variables (may skip if using local files)
- ✓ Credential Parsing
- ✓ Credential Loading & Refresh
- ✓ Calendar API Access

## Step 3: Cloud Deployment Setup (Render, Heroku, etc.)

### Generate Cloud Credentials

After successfully authenticating locally (Step 2), run:

```bash
python generate_cloud_credentials.py
```

This will output a base64-encoded string that looks like:
```
eyJ0b2tlbiI6ICJ5YTI5LmEwQVdZN0NrLi4uIn0=
```

**Copy this entire string** - you'll need it for the next step.

### Set Environment Variable

#### On Render:

1. Go to your Render dashboard
2. Select your web service
3. Click on "Environment" in the left sidebar
4. Add a new environment variable:
   - **Key:** `GOOGLE_CREDENTIALS`
   - **Value:** [paste the base64 string from above]
5. Click "Save Changes"
6. Your service will automatically redeploy

#### On Heroku:

```bash
heroku config:set GOOGLE_CREDENTIALS="[paste the base64 string]"
```

#### On other platforms:

Set an environment variable named `GOOGLE_CREDENTIALS` with the base64-encoded value.

### Verify Cloud Setup

After deployment, check the debug endpoint:

```bash
curl https://your-app.onrender.com/debug/credentials
```

Look for:
```json
{
  "credential_parsing": {
    "parse_success": true,
    "has_refresh_token": true,
    "has_client_id": true,
    "has_client_secret": true,
    "missing_fields": []
  },
  "service_status": {
    "service_created": true,
    "api_call_success": true
  }
}
```

## Step 4: Testing the Application

### Test the Calendar Status Endpoint

```bash
# Local
curl http://localhost:5050/calendar/status

# Production
curl https://your-app.onrender.com/calendar/status
```

Expected response:
```json
{
  "connected": true,
  "calendar": [...]
}
```

### Test Generating a Reply

Use the web interface or API:

```bash
curl -X POST http://localhost:5050/generate \
  -H "Content-Type: application/json" \
  -d '{
    "email_text": "Hi! Can we meet next week?",
    "timezone": "ET",
    "duration": 30,
    "date_range": "next_week"
  }'
```

## Troubleshooting

If you encounter any issues, refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed diagnostic steps.

### Quick Fixes

**Issue:** "GOOGLE_CREDENTIALS is set but could not be loaded"
```bash
# Re-generate credentials
rm token.pickle
python app.py
python generate_cloud_credentials.py
# Update your environment variable with the new value
```

**Issue:** "Token refresh failed"
```bash
# Re-authenticate from scratch
rm token.pickle
python app.py
python generate_cloud_credentials.py
```

**Issue:** Test script shows missing fields
```bash
# Verify your credentials.json is correct
cat credentials.json | jq .
# Should contain "client_id", "client_secret", etc.
```

## Security Best Practices

1. **Never commit** `credentials.json` or `token.pickle` to version control
2. **Keep GOOGLE_CREDENTIALS secret** - it has full access to your calendar
3. **Use read-only scopes** - the app only needs `calendar.readonly`
4. **Regenerate tokens** if they are ever exposed
5. **Review OAuth consent screen** settings in Google Cloud Console
6. **Monitor API usage** in Google Cloud Console

## File Checklist

After setup, you should have:

- ✓ `credentials.json` - OAuth client credentials (local only, in .gitignore)
- ✓ `token.pickle` - Authenticated token (local only, in .gitignore)
- ✓ `env` file with `GOOGLE_CREDENTIALS` (local only, in .gitignore)
- ✓ Environment variable `GOOGLE_CREDENTIALS` set in production

## Maintenance

### Refresh Credentials (if expired)

If your credentials expire after months of inactivity:

```bash
# Local
rm token.pickle
python app.py

# Cloud - regenerate and update environment variable
python generate_cloud_credentials.py
# Update GOOGLE_CREDENTIALS in your cloud platform
```

### Check Credential Status

Run diagnostics periodically:

```bash
python test_credentials.py
```

Or check the debug endpoint:

```bash
curl https://your-app.onrender.com/debug/credentials | jq .
```

## Additional Resources

- [Google Calendar API Documentation](https://developers.google.com/calendar)
- [OAuth 2.0 for Desktop Apps](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Google Cloud Console](https://console.cloud.google.com)

## Support

If you need help:

1. Run `python test_credentials.py` and save the output
2. Check server logs for `[ERROR]` or `[DEBUG]` messages
3. Visit `/debug/credentials` endpoint
4. Review [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
