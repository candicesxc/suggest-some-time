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

## License

MIT License - feel free to use and modify!
