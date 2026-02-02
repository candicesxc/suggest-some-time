# Google Calendar Authentication Troubleshooting Guide

This guide helps you diagnose and fix Google Calendar authentication issues.

## Common Error Messages

### Error: "Calendar not connected. GOOGLE_CREDENTIALS is set but could not be loaded"

This error means the `GOOGLE_CREDENTIALS` environment variable exists but something is wrong with its content or the credentials themselves.

## Diagnostic Steps

### Step 1: Run the Test Script

```bash
python test_credentials.py
```

This script will check:
- ✓ Environment variable configuration
- ✓ Credential parsing (base64/JSON)
- ✓ Token refresh capability
- ✓ Calendar API access

### Step 2: Use the Debug Endpoint

If you have the server running, access the debug endpoint:

```bash
# Local development
curl http://localhost:5050/debug/credentials

# Production (Render)
curl https://your-app.onrender.com/debug/credentials
```

This will show you detailed diagnostic information including:
- Environment variable status
- Credential parsing results
- Missing fields
- API connection status

### Step 3: Check Server Logs

The improved error logging will now show detailed debug messages:

```
[DEBUG] Loading credentials from GOOGLE_CREDENTIALS environment variable...
[DEBUG] Creating credentials with client_id: 1234567890...
[DEBUG] Token URI: https://oauth2.googleapis.com/token
[DEBUG] Has refresh_token: True
[DEBUG] Has token: True
[DEBUG] Attempting to refresh token...
[DEBUG] Token refreshed successfully
[DEBUG] Building Calendar API service...
[DEBUG] Validating credentials with test API call...
[DEBUG] Credentials validated successfully!
```

If you see errors, they will clearly indicate the problem:
- `[ERROR] GOOGLE_CREDENTIALS missing required fields: ['refresh_token']`
- `[ERROR] Token refresh failed: invalid_grant`
- `[ERROR] Credential validation error: ...`

## Common Issues and Solutions

### Issue 1: Missing Required Fields

**Error:**
```
GOOGLE_CREDENTIALS missing required fields: ['refresh_token', 'client_id', 'client_secret']
```

**Solution:**
Your GOOGLE_CREDENTIALS is missing one or more required fields. You need to regenerate it:

1. Authenticate locally first:
   ```bash
   python app.py
   # This will open a browser for OAuth authentication
   ```

2. After authentication, generate cloud credentials:
   ```bash
   python generate_cloud_credentials.py
   ```

3. Copy the output and set it as your GOOGLE_CREDENTIALS environment variable.

### Issue 2: Invalid or Expired Refresh Token

**Error:**
```
[ERROR] Token refresh failed: invalid_grant
```

**Possible Causes:**
- The refresh token has been revoked
- The OAuth consent screen settings changed
- The credentials were regenerated in Google Cloud Console
- Too much time has passed (refresh tokens can expire after 6 months of inactivity)

**Solution:**
1. Delete your local `token.pickle` file
2. Re-authenticate:
   ```bash
   rm token.pickle
   python app.py
   # Complete the OAuth flow in the browser
   ```
3. Regenerate cloud credentials:
   ```bash
   python generate_cloud_credentials.py
   ```
4. Update your GOOGLE_CREDENTIALS environment variable

### Issue 3: Malformed GOOGLE_CREDENTIALS

**Error:**
```
GOOGLE_CREDENTIALS parse error: Invalid base64-encoded string
```

**Solution:**
The GOOGLE_CREDENTIALS value is corrupted or incorrectly formatted.

1. Ensure the entire base64 string was copied (no truncation)
2. Remove any extra whitespace or newlines
3. Regenerate using `python generate_cloud_credentials.py`

### Issue 4: Wrong Client ID or Secret

**Error:**
```
[ERROR] Token refresh failed: unauthorized_client
```

**Solution:**
The client_id or client_secret in your credentials don't match.

1. Download fresh OAuth credentials from Google Cloud Console:
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Navigate to "APIs & Services" > "Credentials"
   - Download your OAuth 2.0 Client ID as `credentials.json`

2. Re-authenticate and regenerate:
   ```bash
   rm token.pickle
   python app.py
   python generate_cloud_credentials.py
   ```

### Issue 5: Network or API Issues

**Error:**
```
[ERROR] Error loading cloud credentials: HTTPSConnectionPool...
```

**Solution:**
This is typically a network connectivity issue or Google API outage.

1. Check your internet connection
2. Verify Google Calendar API is enabled in Google Cloud Console
3. Check [Google Cloud Status Dashboard](https://status.cloud.google.com/)
4. Try again in a few minutes

## Manual Verification

### Verify GOOGLE_CREDENTIALS Format

Your GOOGLE_CREDENTIALS should be a base64-encoded JSON with these fields:

```json
{
  "token": "ya29.a0...",
  "refresh_token": "1//0g...",
  "token_uri": "https://oauth2.googleapis.com/token",
  "client_id": "1234567890-abc...apps.googleusercontent.com",
  "client_secret": "GOCSPX-..."
}
```

To decode and inspect (for debugging only - keep this secret!):

```bash
echo "$GOOGLE_CREDENTIALS" | base64 -d | jq .
```

### Check Required Fields

```bash
echo "$GOOGLE_CREDENTIALS" | base64 -d | jq 'has("refresh_token"), has("client_id"), has("client_secret")'
```

Should output:
```
true
true
true
```

## Getting Help

If you're still having issues:

1. Run the full diagnostic:
   ```bash
   python test_credentials.py > diagnostic_report.txt 2>&1
   ```

2. Check server logs for the detailed error messages starting with `[ERROR]` or `[DEBUG]`

3. Visit the `/debug/credentials` endpoint and save the JSON output

4. Review the error messages and error types to identify the specific issue

## Prevention

### Best Practices

1. **Always test locally first** before deploying to production
2. **Use the test script** after any credential changes
3. **Keep credentials.json** in a safe place (it's needed to regenerate tokens)
4. **Don't share** GOOGLE_CREDENTIALS (it contains sensitive data)
5. **Set up monitoring** to alert when authentication fails
6. **Refresh credentials** if you haven't used the app in months

### Regular Maintenance

- Test your credentials monthly: `python test_credentials.py`
- Re-authenticate if you see any warnings
- Keep backups of your `credentials.json` file

## Quick Reference

| Issue | Command | Description |
|-------|---------|-------------|
| Test credentials | `python test_credentials.py` | Run full diagnostic test |
| Debug endpoint | `curl /debug/credentials` | Get detailed credential status |
| Re-authenticate | `rm token.pickle && python app.py` | Start fresh OAuth flow |
| Regenerate | `python generate_cloud_credentials.py` | Create new GOOGLE_CREDENTIALS |
| Decode credentials | `echo $GOOGLE_CREDENTIALS \| base64 -d \| jq .` | Inspect credential content |
