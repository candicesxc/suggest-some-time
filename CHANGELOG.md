# Changelog

## [Unreleased] - 2026-02-02

### Fixed - Google Calendar Authentication

#### Problem
Users experienced "Calendar not connected. GOOGLE_CREDENTIALS is set but could not be loaded" error with insufficient debugging information to diagnose the root cause.

#### Solution
Implemented comprehensive authentication improvements:

1. **Enhanced Error Logging** (app.py:143-168)
   - Added detailed debug logging throughout credential loading process
   - Shows credential parsing status, token refresh attempts, and API validation
   - Provides specific error messages for different failure modes
   - All debug messages prefixed with `[DEBUG]` or `[ERROR]` for easy filtering

2. **Improved Token Refresh Logic** (app.py:160-168)
   - Changed from conditional refresh (only when `creds.expired`) to proactive refresh
   - Always attempts to refresh token when refresh_token is available
   - Provides specific error messages when refresh fails
   - Validates credentials immediately after refresh with test API call

3. **Added Diagnostic Endpoint** (app.py:1139-1213)
   - New `/debug/credentials` endpoint for troubleshooting
   - Returns comprehensive JSON with:
     - Environment variable status
     - File existence checks
     - Credential parsing results
     - Missing field detection
     - Service creation and API call status
   - Safe for production (doesn't expose secrets, only status)

4. **Created Test Script** (test_credentials.py)
   - Standalone diagnostic tool: `python test_credentials.py`
   - Tests 4 key areas:
     1. Environment variable configuration
     2. Credential parsing (base64/JSON)
     3. Token refresh capability
     4. Calendar API access
   - Provides clear pass/fail results with troubleshooting suggestions
   - Can be run without starting the web server

5. **Comprehensive Documentation**
   - **SETUP_CREDENTIALS.md**: Step-by-step guide for both local and cloud setup
   - **TROUBLESHOOTING.md**: Detailed solutions for common authentication issues
   - **README.md**: Added troubleshooting section with quick fixes
   - All guides include command examples and expected outputs

### Added

- `/debug/credentials` endpoint for diagnostics
- `test_credentials.py` - Automated credential testing script
- `SETUP_CREDENTIALS.md` - Complete setup guide
- `TROUBLESHOOTING.md` - Problem-solving reference
- Enhanced debug logging throughout authentication flow

### Changed

- Token refresh now always attempts when refresh_token is available (more reliable)
- `get_calendar_service()` now validates credentials with test API call
- Error messages are more specific and actionable
- Added API call validation after service creation

### Technical Details

#### Modified Functions

**`_credentials_from_env()`**:
- Added debug logging for credential creation
- Changed token refresh strategy to proactive (always refresh)
- Improved error handling with specific exception messages

**`get_calendar_service()`**:
- Added comprehensive debug logging at each step
- Added credential validation via test API call
- Better error handling with specific ValueError catching
- More detailed error messages in console

#### New Features

**Debug Endpoint Response Structure**:
```json
{
  "timestamp": "2026-02-02T10:30:00-05:00",
  "environment_variables": {
    "GOOGLE_CREDENTIALS_set": true,
    "GOOGLE_CREDENTIALS_length": 450
  },
  "credential_parsing": {
    "parse_success": true,
    "has_refresh_token": true,
    "has_client_id": true,
    "has_client_secret": true,
    "missing_fields": []
  },
  "service_status": {
    "service_created": true,
    "api_call_success": true,
    "calendar_count": 1
  }
}
```

#### Testing

The test script validates:
1. ✓ Environment variables are set correctly
2. ✓ Credentials can be parsed (base64 or JSON)
3. ✓ All required fields are present
4. ✓ Token refresh succeeds
5. ✓ Calendar API is accessible

### Migration Notes

No breaking changes. All improvements are backward compatible.

### For Developers

To test the changes:

```bash
# Run the diagnostic test
python test_credentials.py

# Check debug endpoint (with server running)
curl http://localhost:5050/debug/credentials | jq .

# View enhanced logs
python app.py
# Look for [DEBUG] and [ERROR] prefixed messages
```

### Common Issues Resolved

1. **Expired tokens**: Now automatically refreshed on every service creation
2. **Missing fields**: Clear error messages indicate exactly what's missing
3. **Silent failures**: Debug logging shows exactly where authentication fails
4. **Difficult debugging**: Multiple diagnostic tools now available

### Security

- Debug endpoint does not expose sensitive credential data
- Only shows status flags (true/false) and prefixes of IDs
- All sensitive values remain in environment variables
- Test script only outputs success/failure status

---

## Future Improvements (Not in this release)

Potential enhancements for future versions:
- Automatic credential refresh monitoring
- Webhook for credential expiration warnings
- Support for multiple calendar accounts
- Enhanced OAuth flow for web-based apps
