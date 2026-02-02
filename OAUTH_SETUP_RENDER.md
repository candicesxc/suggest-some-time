# Multi-User OAuth Setup Guide for Render

This guide shows you how to set up Google Calendar OAuth authentication for a **multi-user web application** where each user connects their own calendar.

## 🎯 Overview

There are two deployment modes:

### Mode 1: Single-User (Legacy)
- **Use case**: Only you use the app
- **Setup**: Authenticate locally, generate GOOGLE_CREDENTIALS
- **Storage**: Environment variable with your tokens
- **See**: SETUP_CREDENTIALS.md for this approach

### Mode 2: Multi-User (OAuth Web Flow) ⭐ **YOU'RE HERE**
- **Use case**: Multiple users, each with their own calendar
- **Setup**: Configure OAuth client in Google Cloud Console
- **Storage**: Each user's tokens stored in session/database
- **Flow**: Users click "Connect Calendar" → Google OAuth → tokens stored per user

---

## 📋 Prerequisites

- Google Cloud Console account
- Render.com account
- Your app deployed to Render

---

## Step 1: Create OAuth 2.0 Credentials in Google Cloud Console

### 1.1 Go to Google Cloud Console

Visit [Google Cloud Console](https://console.cloud.google.com)

### 1.2 Create or Select a Project

- Click on the project dropdown at the top
- Create a new project or select an existing one
- Name it something like "Suggest Some Time" or "Calendar App"

### 1.3 Enable Google Calendar API

1. In the left sidebar, go to **"APIs & Services"** → **"Library"**
2. Search for **"Google Calendar API"**
3. Click on it and press **"Enable"**

### 1.4 Configure OAuth Consent Screen

1. Go to **"APIs & Services"** → **"OAuth consent screen"**
2. Choose **"External"** (unless you have a Google Workspace)
3. Click **"Create"**

4. **Fill in the App Information:**
   - **App name**: `Suggest Some Time` (or your app name)
   - **User support email**: Your email
   - **App logo**: (optional)
   - **Application home page**: `https://your-app-name.onrender.com`
   - **Authorized domains**: `onrender.com` (and your custom domain if you have one)
   - **Developer contact information**: Your email

5. Click **"Save and Continue"**

6. **Add Scopes:**
   - Click **"Add or Remove Scopes"**
   - Search for `Google Calendar API`
   - Check: `https://www.googleapis.com/auth/calendar.readonly` or `.../calendar.events`
   - Click **"Update"**
   - Click **"Save and Continue"**

7. **Test Users** (if in Testing mode):
   - Add email addresses of users who can test the app
   - Click **"Save and Continue"**

8. Click **"Back to Dashboard"**

### 1.5 Create OAuth 2.0 Client ID

1. Go to **"APIs & Services"** → **"Credentials"**
2. Click **"Create Credentials"** → **"OAuth client ID"**

3. **Application type**: Select **"Web application"**

4. **Fill in the details:**
   - **Name**: `Suggest Some Time Web Client`

   - **Authorized JavaScript origins**: Add these URLs:
     ```
     https://your-app-name.onrender.com
     http://localhost:5050
     ```
     Replace `your-app-name` with your actual Render app name

   - **Authorized redirect URIs**: Add these URLs:
     ```
     https://your-app-name.onrender.com/auth/callback
     http://localhost:5050/auth/callback
     ```

5. Click **"Create"**

6. **Copy your credentials:**
   - You'll see a popup with your **Client ID** and **Client Secret**
   - **IMPORTANT**: Copy both of these - you'll need them for Render

   Example:
   ```
   Client ID: 123456789-abcdefg.apps.googleusercontent.com
   Client Secret: GOCSPX-AbCdEfGhIjKlMnOpQrStUvWx
   ```

---

## Step 2: Configure Environment Variables on Render

### 2.1 Go to Your Render Dashboard

1. Visit [Render Dashboard](https://dashboard.render.com)
2. Select your **web service** (suggest-some-time)

### 2.2 Add Environment Variables

1. Click on **"Environment"** in the left sidebar
2. Add these environment variables:

#### Required Variables:

| Key | Value | Description |
|-----|-------|-------------|
| `GOOGLE_OAUTH_CLIENT_ID` | `123456789-abcdefg.apps.googleusercontent.com` | Your OAuth Client ID from Step 1.5 |
| `GOOGLE_OAUTH_CLIENT_SECRET` | `GOCSPX-AbCdEfGhIjKlMnOpQrStUvWx` | Your OAuth Client Secret from Step 1.5 |
| `OPENAI_API_KEY` | `sk-...` | Your OpenAI API key |
| `SECRET_KEY` | `your-random-secret-key-here` | Flask session secret (generate a random string) |

#### Optional Variables:

| Key | Value | Description |
|-----|-------|-------------|
| `GOOGLE_OAUTH_REDIRECT_URI` | (leave empty) | Auto-detected based on your domain. Only set if auto-detection fails |

### 2.3 Generate a Secret Key

For the `SECRET_KEY`, generate a random string. You can use:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

This generates something like: `a3f9d8e7c2b1a0987654321fedcba9876543210fedcba9876543210fedcba98`

### 2.4 Save and Deploy

1. Click **"Save Changes"**
2. Render will automatically redeploy your app with the new environment variables

---

## Step 3: Update Authorized Redirect URIs (If Needed)

After your first deployment, Render assigns a URL like:
```
https://suggest-some-time-abc123.onrender.com
```

If the URL is different from what you set in Step 1.5:

1. Go back to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to **"APIs & Services"** → **"Credentials"**
3. Click on your **OAuth 2.0 Client ID**
4. Update **Authorized redirect URIs** to include:
   ```
   https://suggest-some-time-abc123.onrender.com/auth/callback
   ```
5. Click **"Save"**

---

## Step 4: Test the OAuth Flow

### 4.1 Visit Your App

Go to: `https://your-app-name.onrender.com`

### 4.2 Check Calendar Status

Open browser console and test the status endpoint:

```javascript
fetch('/calendar/status')
  .then(r => r.json())
  .then(console.log)
```

Expected response:
```json
{
  "connected": false,
  "auth_mode": null,
  "requires_auth": true
}
```

### 4.3 Initiate OAuth Flow

Test the connect endpoint:

```javascript
fetch('/auth/connect')
  .then(r => r.json())
  .then(data => {
    console.log(data);
    window.open(data.authorization_url, '_blank');
  })
```

This should:
1. Open a popup/tab with Google sign-in
2. Ask you to choose a Google account
3. Show the OAuth consent screen
4. Redirect back to your app at `/auth/callback`
5. Show "✅ Calendar Connected!" message

### 4.4 Verify Connection

After connecting, check status again:

```javascript
fetch('/calendar/status')
  .then(r => r.json())
  .then(console.log)
```

Expected response:
```json
{
  "connected": true,
  "auth_mode": "multi-user",
  "calendar_count": 1,
  "primary_calendar": "your-email@gmail.com"
}
```

---

## Step 5: Update Frontend UI (Optional)

You can add a "Connect Calendar" button to your frontend. Here's a simple example:

```html
<button id="connectCalendar">Connect Google Calendar</button>
<div id="calendarStatus"></div>

<script>
// Check connection status on page load
fetch('/calendar/status')
  .then(r => r.json())
  .then(data => {
    if (data.connected) {
      document.getElementById('calendarStatus').innerHTML =
        `✅ Connected: ${data.primary_calendar}`;
      document.getElementById('connectCalendar').style.display = 'none';
    } else {
      document.getElementById('calendarStatus').innerHTML =
        '❌ Calendar not connected';
    }
  });

// Connect calendar button
document.getElementById('connectCalendar').addEventListener('click', () => {
  fetch('/auth/connect')
    .then(r => r.json())
    .then(data => {
      // Open OAuth in popup
      const popup = window.open(
        data.authorization_url,
        'Connect Calendar',
        'width=600,height=700'
      );

      // Listen for success message
      window.addEventListener('message', (event) => {
        if (event.data.type === 'calendar_connected') {
          popup.close();
          location.reload(); // Refresh to show connected status
        }
      });
    });
});
</script>
```

---

## 🔍 Troubleshooting

### Issue: "redirect_uri_mismatch" Error

**Problem**: Google shows an error about redirect URI not matching.

**Solution**:
1. Check the exact error message - it shows what URI Google received
2. Go to Google Cloud Console → Credentials
3. Make sure the **exact** URI is listed in "Authorized redirect URIs"
4. Include both `http://` (local) and `https://` (production)
5. No trailing slashes!

Example URIs:
```
✅ https://suggest-some-time.onrender.com/auth/callback
❌ https://suggest-some-time.onrender.com/auth/callback/
❌ https://suggest-some-time.onrender.com
```

### Issue: "OAuth not configured" Error

**Problem**: App returns error about missing OAuth configuration.

**Solution**:
1. Go to Render Dashboard → Environment
2. Verify `GOOGLE_OAUTH_CLIENT_ID` is set
3. Verify `GOOGLE_OAUTH_CLIENT_SECRET` is set
4. Make sure there are no extra spaces in the values
5. Click "Save Changes" and redeploy

### Issue: "Access blocked: This app's request is invalid"

**Problem**: OAuth consent screen not configured properly.

**Solution**:
1. Go to Google Cloud Console → OAuth consent screen
2. Make sure the app is **Published** (or you're a test user)
3. Verify the scopes include Calendar API
4. Check that authorized domains include `onrender.com`

### Issue: Can't get refresh token

**Problem**: OAuth flow succeeds but can't access calendar later.

**Solution**:
Make sure your OAuth flow includes:
```python
authorization_url, state = flow.authorization_url(
    access_type='offline',  # ← This is crucial!
    prompt='consent'        # ← This too!
)
```

Both parameters are already set in the updated code.

### Issue: Session lost after restart

**Problem**: Users have to reconnect calendar after server restarts.

**Solution**:
This is expected with session storage. For production, you should:
1. Use a database (PostgreSQL, MongoDB) to store user tokens
2. Implement user accounts/authentication
3. Store credentials per user ID in the database

The current implementation uses Flask sessions which are cookie-based and temporary.

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets

Never commit to Git:
- ❌ Client ID (can be in frontend, but keep private)
- ❌ Client Secret (NEVER expose to frontend)
- ❌ User tokens
- ❌ Refresh tokens

### 2. Use HTTPS in Production

Render automatically provides HTTPS. Make sure:
- All redirect URIs use `https://`
- Set secure cookies: `app.config['SESSION_COOKIE_SECURE'] = True` in production

### 3. Validate State Parameter

The code already does this to prevent CSRF attacks:
```python
if state != stored_state:
    return jsonify({'error': 'Invalid state'}), 400
```

### 4. Store Tokens Securely

For production:
- ✅ Use database with encryption
- ✅ Never log tokens
- ✅ Implement token rotation
- ❌ Don't store in localStorage (frontend)
- ❌ Don't use file storage in cloud (ephemeral)

### 5. Limit Scopes

Only request the minimum scopes needed:
```python
# Good - read-only
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Or if you need to create events
SCOPES = ['https://www.googleapis.com/auth/calendar.events']
```

---

## 📊 Monitoring

### Check Debug Endpoint

```bash
curl https://your-app.onrender.com/debug/credentials | jq .
```

Look for:
```json
{
  "session": {
    "has_credentials": true,
    "has_refresh_token": true
  },
  "environment_variables": {
    "GOOGLE_OAUTH_CLIENT_ID_set": true,
    "GOOGLE_OAUTH_CLIENT_SECRET_set": true
  },
  "service_status": {
    "service_created": true,
    "api_call_success": true
  }
}
```

### Check Render Logs

1. Go to Render Dashboard
2. Select your service
3. Click "Logs" tab
4. Look for `[DEBUG]` messages showing OAuth flow:
   ```
   [DEBUG] OAuth redirect URI: https://...
   [DEBUG] Generated auth URL, state: xyz...
   [DEBUG] OAuth callback received
   [DEBUG] Exchanging code for tokens...
   [DEBUG] Successfully obtained tokens
   [DEBUG] Has refresh token: True
   [DEBUG] Credentials validated successfully!
   ```

---

## 🚀 Production Recommendations

For a production multi-user app, you should:

### 1. Add User Authentication
- Implement login system (email/password, social login, etc.)
- Associate calendar credentials with user accounts

### 2. Use Database Storage
- Store tokens in PostgreSQL or MongoDB
- Encrypt refresh tokens at rest
- Add Render PostgreSQL add-on

### 3. Handle Token Expiration
- Automatically refresh tokens before they expire
- Handle refresh token expiration gracefully
- Allow users to reconnect if tokens are revoked

### 4. Add User Management
- Allow users to disconnect calendar
- Show connection status on profile page
- Let users revoke access from Google settings

### 5. Error Handling
- Show user-friendly error messages
- Implement retry logic for temporary failures
- Log errors for debugging (without exposing tokens)

---

## 📚 Summary

**Environment Variables on Render:**
```
GOOGLE_OAUTH_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-YourClientSecret
SECRET_KEY=your-random-secret-key
OPENAI_API_KEY=sk-your-openai-key
```

**OAuth Flow:**
1. User clicks "Connect Calendar"
2. App redirects to `/auth/connect`
3. Google shows OAuth consent
4. User approves
5. Google redirects to `/auth/callback?code=...`
6. App exchanges code for tokens
7. Tokens stored in session
8. User can now use calendar features

**Key Files:**
- No `credentials.json` needed on Render
- No `token.pickle` needed
- Everything configured via environment variables
- Each user's tokens stored in their session

---

## 🆘 Need Help?

- **Debug endpoint**: `https://your-app.onrender.com/debug/credentials`
- **Test script**: `python test_credentials.py` (local only)
- **Render logs**: Dashboard → Your Service → Logs
- **Google API Console**: [console.cloud.google.com](https://console.cloud.google.com)

---

## ✅ Verification Checklist

Before going live, check:

- [ ] Google Calendar API is enabled
- [ ] OAuth consent screen is configured
- [ ] OAuth Client ID is created (type: Web application)
- [ ] Authorized redirect URIs include your Render URL + `/auth/callback`
- [ ] `GOOGLE_OAUTH_CLIENT_ID` set on Render
- [ ] `GOOGLE_OAUTH_CLIENT_SECRET` set on Render
- [ ] `SECRET_KEY` set on Render (random, secure)
- [ ] App deploys successfully
- [ ] `/auth/connect` returns authorization URL
- [ ] OAuth flow completes and shows "Calendar Connected"
- [ ] `/calendar/status` shows `"connected": true`
- [ ] Can generate meeting replies with calendar data
