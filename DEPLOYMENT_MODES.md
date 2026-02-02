# Deployment Modes: Single-User vs Multi-User

This app supports two different deployment configurations depending on your use case.

## 🎯 Quick Comparison

| Feature | Single-User Mode | Multi-User Mode |
|---------|------------------|-----------------|
| **Use Case** | Personal app, only you use it | Public app, many users |
| **Authentication** | Pre-authenticated (your calendar) | OAuth per user (their calendar) |
| **Setup Complexity** | Simple | Moderate |
| **Credential Type** | `GOOGLE_CREDENTIALS` env var | `CLIENT_ID` + `CLIENT_SECRET` |
| **Token Storage** | Environment variable | Session/Database per user |
| **Calendar Access** | Always YOUR calendar | Each user's own calendar |
| **Setup Guide** | [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md) | [OAUTH_SETUP_RENDER.md](OAUTH_SETUP_RENDER.md) |

---

## 📌 Single-User Mode (Legacy)

### When to Use
- You're the only person using the app
- Personal productivity tool
- Checking your own calendar availability
- Simpler setup, fewer moving parts

### How It Works
```
┌─────────────┐
│   You       │
│ (Developer) │
└──────┬──────┘
       │
       │ 1. Authenticate locally
       │    (python app.py)
       ▼
┌─────────────┐
│ token.pickle│
└──────┬──────┘
       │
       │ 2. Generate cloud credentials
       │    (generate_cloud_credentials.py)
       ▼
┌─────────────────────────────┐
│ GOOGLE_CREDENTIALS (base64) │
└──────────┬──────────────────┘
           │
           │ 3. Set on Render
           ▼
    ┌─────────────┐
    │   Render    │
    │  (Production)│
    └──────┬──────┘
           │
           │ Always uses YOUR calendar
           ▼
    ┌─────────────┐
    │ Your Google │
    │  Calendar   │
    └─────────────┘
```

### Environment Variables (Render)
```bash
GOOGLE_CREDENTIALS=eyJ0b2tlbiI6ICJ5YTI5LmEwQVdZN0NrLi4uIn0=
OPENAI_API_KEY=sk-your-openai-key
```

### Pros
- ✅ Simple setup
- ✅ One-time authentication
- ✅ No database needed
- ✅ Perfect for personal use

### Cons
- ❌ Only checks YOUR calendar
- ❌ Can't be used by multiple people
- ❌ Tokens embedded in environment
- ❌ All users see your availability

---

## 🌐 Multi-User Mode (OAuth Web Flow)

### When to Use
- Multiple people will use the app
- Each user has their own Google account
- Public-facing application
- SaaS product

### How It Works
```
┌─────────────┐
│   User 1    │
└──────┬──────┘
       │
       │ 1. Clicks "Connect Calendar"
       │    → /auth/connect
       ▼
┌─────────────────────┐
│  Google OAuth       │
│  Consent Screen     │
└──────┬──────────────┘
       │
       │ 2. User approves
       │    → /auth/callback?code=xyz
       ▼
┌─────────────────────┐
│   Your App          │
│   Exchange code     │
│   for tokens        │
└──────┬──────────────┘
       │
       │ 3. Store in session/DB
       ▼
┌─────────────────────┐
│  User 1's tokens    │
│  (in session)       │
└──────┬──────────────┘
       │
       │ 4. Access User 1's calendar
       ▼
┌─────────────────────┐
│  User 1's Google    │
│  Calendar           │
└─────────────────────┘

┌─────────────┐
│   User 2    │ → Same flow → User 2's tokens → User 2's calendar
└─────────────┘
```

### Environment Variables (Render)
```bash
GOOGLE_OAUTH_CLIENT_ID=123456789-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-YourClientSecret
SECRET_KEY=your-random-secret-key
OPENAI_API_KEY=sk-your-openai-key
```

### Pros
- ✅ Each user connects their own calendar
- ✅ Proper multi-tenant architecture
- ✅ Can be public-facing
- ✅ Scalable to many users

### Cons
- ❌ More complex setup
- ❌ Requires Google Cloud Console configuration
- ❌ Need user sessions or database
- ❌ Must handle token refresh per user

---

## 🔄 Migration Guide

### From Single-User to Multi-User

If you're currently using single-user mode and want to upgrade:

1. **Set up OAuth Client** (see [OAUTH_SETUP_RENDER.md](OAUTH_SETUP_RENDER.md))
   - Create OAuth 2.0 Client ID in Google Cloud Console
   - Configure redirect URIs

2. **Update Environment Variables on Render:**
   - Remove: `GOOGLE_CREDENTIALS`
   - Add: `GOOGLE_OAUTH_CLIENT_ID`
   - Add: `GOOGLE_OAUTH_CLIENT_SECRET`
   - Add: `SECRET_KEY` (if not already set)

3. **Deploy Updated Code:**
   - The app automatically detects which mode to use
   - If `GOOGLE_OAUTH_CLIENT_ID` is set → Multi-user mode
   - If `GOOGLE_CREDENTIALS` is set → Single-user mode

4. **Update Frontend:**
   - Add "Connect Calendar" button
   - Handle OAuth flow
   - Show connection status

### From Multi-User to Single-User

If you want to simplify to single-user:

1. **Authenticate Locally:**
   ```bash
   python app.py
   # Complete OAuth flow in browser
   ```

2. **Generate Credentials:**
   ```bash
   python generate_cloud_credentials.py
   # Copy the base64 output
   ```

3. **Update Render Environment:**
   - Add: `GOOGLE_CREDENTIALS=<base64-string>`
   - Remove: `GOOGLE_OAUTH_CLIENT_ID` (optional)
   - Remove: `GOOGLE_OAUTH_CLIENT_SECRET` (optional)

4. **Redeploy**

---

## 🔍 How the App Detects Mode

The app automatically chooses the mode based on available credentials:

### Priority Order (in `get_calendar_service()`):

1. **Multi-user session** - Check if user has connected via OAuth
   ```python
   if session.get('google_credentials'):
       # Use user's credentials from session
   ```

2. **Single-user environment** - Check for GOOGLE_CREDENTIALS
   ```python
   elif os.environ.get('GOOGLE_CREDENTIALS'):
       # Use admin's pre-authenticated credentials
   ```

3. **Local development** - Check for token.pickle file
   ```python
   elif os.path.exists('token.pickle'):
       # Use local file-based credentials
   ```

### What This Means:

- **Multi-user mode takes precedence** if user is authenticated
- **Single-user mode is fallback** for admin or unauthenticated users
- **Both modes can coexist** on the same deployment
- **Local development mode** for testing

---

## 🛠️ Configuration Quick Reference

### Environment Variables by Mode

#### Single-User Only:
```bash
GOOGLE_CREDENTIALS=eyJ0b2tlbiI6...  # Your pre-authenticated tokens (base64)
OPENAI_API_KEY=sk-...
SECRET_KEY=random-string  # For sessions
```

#### Multi-User Only:
```bash
GOOGLE_OAUTH_CLIENT_ID=123-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xyz
OPENAI_API_KEY=sk-...
SECRET_KEY=random-string  # For sessions (REQUIRED!)
```

#### Hybrid (Both modes):
```bash
# Multi-user (preferred for authenticated users)
GOOGLE_OAUTH_CLIENT_ID=123-abc.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=GOCSPX-xyz

# Single-user (fallback for admin/testing)
GOOGLE_CREDENTIALS=eyJ0b2tlbiI6...

# Common
OPENAI_API_KEY=sk-...
SECRET_KEY=random-string
```

---

## 📊 Feature Comparison

| Feature | Single-User | Multi-User |
|---------|-------------|------------|
| OAuth Flow | No | Yes |
| User Sessions | Not needed | Required |
| Database | Not needed | Recommended |
| Token Storage | Environment | Session/DB |
| Session Secret | Optional | **Required** |
| Google Setup | Desktop app | Web application |
| Redirect URI | Not needed | **Required** |
| Consent Screen | Once (local) | Per user |
| Token Refresh | Automatic | Per user |
| Scalability | 1 user | Unlimited |
| Setup Time | 10 minutes | 30 minutes |

---

## 🎓 Which Mode Should You Choose?

### Choose Single-User If:
- ✅ You're the only user
- ✅ It's a personal productivity tool
- ✅ You want simple setup
- ✅ You're OK with everyone seeing your availability
- ✅ You don't need user accounts

### Choose Multi-User If:
- ✅ Multiple people will use it
- ✅ Each user should see their own calendar
- ✅ You're building a product/service
- ✅ You want proper user separation
- ✅ You plan to add user accounts later

### Choose Hybrid (Both) If:
- ✅ You want to use it yourself (single-user)
- ✅ But also allow others to connect their calendars (multi-user)
- ✅ You want admin features using GOOGLE_CREDENTIALS
- ✅ You want flexibility for future expansion

---

## 🔐 Security Considerations

### Single-User Mode Security:
- `GOOGLE_CREDENTIALS` contains refresh token → Keep secret!
- Anyone with access to Render environment can access tokens
- Rotate tokens if exposed
- Use Render's environment variable encryption

### Multi-User Mode Security:
- `CLIENT_SECRET` must be kept secret (never expose to frontend)
- `CLIENT_ID` can be public but keep it private
- Use `SECRET_KEY` for session encryption
- Store user tokens in encrypted database (production)
- Implement session timeout
- Use HTTPS (Render provides this automatically)
- Validate state parameter (already implemented)

---

## 📖 Related Documentation

- **Single-User Setup**: [SETUP_CREDENTIALS.md](SETUP_CREDENTIALS.md)
- **Multi-User Setup**: [OAUTH_SETUP_RENDER.md](OAUTH_SETUP_RENDER.md)
- **Troubleshooting**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Testing**: Run `python test_credentials.py` (single-user mode only)
- **Debug Endpoint**: `/debug/credentials` (both modes)

---

## 💡 Tips

### For Development:
- Use **single-user mode** locally (simplest)
- Test OAuth flow with `http://localhost:5050/auth/callback`
- Use Render preview deployments to test multi-user

### For Production:
- Use **multi-user mode** for public apps
- Use **single-user mode** for personal/internal apps
- Consider database for production multi-user
- Implement proper error handling
- Add user authentication/accounts

### For Hybrid Deployment:
- Set both `GOOGLE_CREDENTIALS` and `GOOGLE_OAUTH_CLIENT_ID`
- Multi-user takes precedence when user is authenticated
- Single-user is fallback for admin access
- Useful for gradual migration
