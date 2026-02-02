# ☕ Coffee Chat Email Assistant

A smart web app that helps you schedule meetings by automatically checking your Google Calendar and generating natural, contextual email replies.

![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0+-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## Features

### 📧 Reply to Emails
- Paste an incoming meeting request email
- AI automatically detects: sender name, meeting duration, timezone, and date preferences
- Prompts for clarification only when info can't be determined
- Generates warm, contextual replies that match the tone of the original email

### ✍️ Compose New Emails
- Draft outbound meeting request emails
- Specify recipient, timezone, duration, date range, and meeting purpose
- AI writes natural, personalized emails with your availability

### 🗓️ Smart Calendar Integration
- Connects to your Google Calendar
- Finds available time slots automatically
- Respects working hours (10am-6pm ET)
- Adds 30-minute buffers around existing events
- Combines consecutive slots into clean time ranges

### 🎨 Modern UI
- Clean, responsive design
- Real-time AI detection feedback
- Copy-to-clipboard functionality
- Refine emails with AI feedback

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/candicesxc/suggest-some-time.git
cd suggest-some-time
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up Google Calendar API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Google Calendar API**:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click "Enable"
4. Create OAuth 2.0 credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the JSON file
5. Rename the downloaded file to `credentials.json` and place it in the project root

### 4. Set Up OpenAI API

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Create an `env` file in the project root:

```bash
cp env.example env
```

3. Edit `env` and add your OpenAI API key:

```
OPENAI_API_KEY=your-actual-api-key-here
```

### 5. Run the App

```bash
python app.py
```

On first run, a browser window will open asking you to authorize Google Calendar access. After authorizing, a `token.pickle` file will be created to store your authentication.

### 6. Open in Browser

Navigate to [http://localhost:5050](http://localhost:5050)

## Usage

### Replying to Emails

1. Select the **"Reply to Email"** tab
2. Paste the email you received
3. Click **"Generate Reply"**
4. If any info is missing (duration, timezone, dates), you'll be prompted to provide it
5. Review and edit the generated reply
6. Use **"Refine with AI"** to adjust the tone or content
7. Click **"Copy to Clipboard"**

### Composing New Emails

1. Select the **"Compose New"** tab
2. Fill in:
   - Recipient's name
   - Their timezone
   - Meeting duration
   - When to meet (this week, next week, within 2 weeks)
   - What the meeting is about
3. Click **"Generate Email"**
4. Review, refine, and copy!

## File Structure

```
suggest-some-time/
├── app.py              # Flask backend
├── templates/
│   └── index.html      # Frontend UI
├── requirements.txt    # Python dependencies
├── credentials.json    # Google OAuth credentials (not in repo)
├── token.pickle        # Google auth token (not in repo)
├── env                 # Environment variables (not in repo)
├── env.example         # Example env file
└── README.md
```

## Security Notes

⚠️ **Never commit these files to version control:**
- `credentials.json` - Your Google OAuth client credentials
- `token.pickle` - Your authenticated session token
- `env` - Contains your OpenAI API key

These are already in `.gitignore`.

## Customization

To change the default signature name from "Candice", search for "Candice" in `app.py` and replace with your name.

## Cloud Deployment

This app supports two deployment modes depending on your use case:

### 🔵 Single-User Mode (Recommended for Personal Use)

**Use case**: You're the only person using the app, checks YOUR calendar

**Quick Setup**:
1. Authenticate locally: `python app.py`
2. Generate credentials: `python generate_cloud_credentials.py`
3. Deploy to Render and set `GOOGLE_CREDENTIALS` environment variable

📖 **Complete Guide**: [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md)

### 🌐 Multi-User Mode (OAuth Web Flow)

**Use case**: Multiple users, each connects their own calendar

**Quick Setup**:
1. Create OAuth 2.0 Client in [Google Cloud Console](https://console.cloud.google.com)
2. Deploy to Render
3. Set `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` environment variables
4. Users click "Connect Calendar" to authenticate with their Google account

📖 **Complete Guide**: [OAUTH_SETUP_RENDER.md](OAUTH_SETUP_RENDER.md)

### 🔄 Mode Comparison

| Feature | Single-User | Multi-User |
|---------|-------------|------------|
| **Setup Time** | 10 minutes | 30 minutes |
| **Calendar Access** | Always yours | Each user's own |
| **Best For** | Personal tool | Public app |
| **User Accounts** | Not needed | Recommended |
| **Complexity** | Simple | Moderate |

📊 **Detailed Comparison**: [DEPLOYMENT_MODES.md](DEPLOYMENT_MODES.md)

### General Render Setup

1. Go to [Render Dashboard](https://dashboard.render.com/)
2. Click "New" > "Web Service"
3. Connect your GitHub repository
4. Configure:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
5. Add Environment Variables based on your chosen mode (see guides above)
6. Click "Create Web Service"

Your app will be live at `https://suggest-some-time.onrender.com` (or similar).

**Note**: Free tier on Render may spin down after inactivity (first request takes ~30 seconds)

## Troubleshooting

### Authentication Issues

If you're experiencing Google Calendar authentication problems, we have comprehensive diagnostic tools:

#### 1. Run the Test Script

```bash
python test_credentials.py
```

This will check your environment variables, credential parsing, token refresh, and API access.

#### 2. Use the Debug Endpoint

For deployed apps, visit the debug endpoint:

```bash
# Local
curl http://localhost:5050/debug/credentials

# Production
curl https://your-app.onrender.com/debug/credentials
```

#### 3. Common Issues

- **"Calendar not connected"**: Your GOOGLE_CREDENTIALS may be missing required fields or the refresh token is invalid
- **"Token refresh failed"**: Re-authenticate locally and regenerate cloud credentials
- **"Missing fields"**: Your credentials are incomplete - regenerate using `python generate_cloud_credentials.py`

### Complete Documentation

For detailed setup and troubleshooting:

- 📖 [**Setup Guide**](SETUP_CREDENTIALS.md) - Step-by-step credential configuration
- 🔧 [**Troubleshooting Guide**](TROUBLESHOOTING.md) - Common issues and solutions
- ✅ **Test Script** - Run `python test_credentials.py` to diagnose issues
- 🐛 **Debug Endpoint** - Visit `/debug/credentials` for detailed diagnostics

### Quick Fixes

```bash
# Re-authenticate and regenerate credentials
rm token.pickle
python app.py
python generate_cloud_credentials.py
# Update GOOGLE_CREDENTIALS in your cloud platform

# Test your credentials
python test_credentials.py

# Check credential status
curl http://localhost:5050/debug/credentials | jq .
```

## License

MIT License - feel free to use and modify!
