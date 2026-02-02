#!/usr/bin/env python3
"""
Test script to validate Google Calendar credential loading.

This script checks:
1. Environment variable configuration
2. Credential parsing
3. Token refresh capability
4. Calendar API access

Usage:
    python test_credentials.py
"""

import os
import sys
import json
import base64
from dotenv import load_dotenv

# Load environment variables
load_dotenv('env')

def test_environment_variables():
    """Test that required environment variables are set."""
    print("=" * 60)
    print("1. Testing Environment Variables")
    print("=" * 60)

    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    if not google_creds:
        print("❌ GOOGLE_CREDENTIALS is not set")
        return False

    print("✓ GOOGLE_CREDENTIALS is set")
    print(f"  Length: {len(google_creds)} characters")
    print(f"  Preview: {google_creds[:50]}...")
    return True


def test_credential_parsing():
    """Test parsing of GOOGLE_CREDENTIALS."""
    print("\n" + "=" * 60)
    print("2. Testing Credential Parsing")
    print("=" * 60)

    google_creds = os.environ.get('GOOGLE_CREDENTIALS')
    if not google_creds:
        print("❌ Cannot test - GOOGLE_CREDENTIALS not set")
        return False

    # Try to parse as base64
    try:
        decoded = base64.b64decode(google_creds.strip()).decode('utf-8')
        creds_data = json.loads(decoded)
        print("✓ Successfully decoded from base64")
    except Exception as e:
        # Try as raw JSON
        try:
            creds_data = json.loads(google_creds.strip())
            print("✓ Successfully parsed as raw JSON")
        except Exception as e2:
            print(f"❌ Failed to parse credentials: {e}")
            print(f"   Also failed as raw JSON: {e2}")
            return False

    # Check required fields
    print("\nChecking required fields:")
    required_fields = ['refresh_token', 'client_id', 'client_secret']
    all_present = True

    for field in required_fields:
        if creds_data.get(field):
            print(f"  ✓ {field}: present")
            if field == 'client_id':
                print(f"    Preview: {creds_data[field][:20]}...")
        else:
            print(f"  ❌ {field}: MISSING")
            all_present = False

    # Check optional fields
    print("\nChecking optional fields:")
    if creds_data.get('token'):
        print("  ✓ token: present (current access token)")
    else:
        print("  ⚠ token: not present (will be generated from refresh_token)")

    if creds_data.get('token_uri'):
        print(f"  ✓ token_uri: {creds_data['token_uri']}")
    else:
        print("  ⚠ token_uri: not present (will use default)")

    return all_present


def test_credential_loading():
    """Test loading credentials and refreshing token."""
    print("\n" + "=" * 60)
    print("3. Testing Credential Loading & Token Refresh")
    print("=" * 60)

    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request
        from app import _parse_google_credentials

        google_creds = os.environ.get('GOOGLE_CREDENTIALS')
        if not google_creds:
            print("❌ Cannot test - GOOGLE_CREDENTIALS not set")
            return False

        # Parse credentials
        creds_data = _parse_google_credentials(google_creds)
        print("✓ Credentials parsed successfully")

        # Create Credentials object
        creds = Credentials(
            token=creds_data.get('token'),
            refresh_token=creds_data.get('refresh_token'),
            token_uri=creds_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=creds_data.get('client_id'),
            client_secret=creds_data.get('client_secret'),
            scopes=['https://www.googleapis.com/auth/calendar.readonly']
        )
        print("✓ Credentials object created")

        # Try to refresh token
        print("\nAttempting to refresh token...")
        try:
            creds.refresh(Request())
            print("✓ Token refreshed successfully!")
            print(f"  New token preview: {creds.token[:30]}...")
            return True
        except Exception as refresh_error:
            print(f"❌ Token refresh failed: {refresh_error}")
            print("\nPossible issues:")
            print("  1. refresh_token is invalid or expired")
            print("  2. client_id or client_secret is incorrect")
            print("  3. Network connectivity issues")
            print("  4. Token has been revoked")
            return False

    except ImportError as ie:
        print(f"❌ Import error: {ie}")
        print("   Make sure all dependencies are installed: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_calendar_api():
    """Test accessing the Calendar API."""
    print("\n" + "=" * 60)
    print("4. Testing Calendar API Access")
    print("=" * 60)

    try:
        from googleapiclient.discovery import build
        from app import get_calendar_service

        print("Attempting to get calendar service...")
        service = get_calendar_service()

        if not service:
            print("❌ Failed to get calendar service (returned None)")
            return False

        print("✓ Calendar service created")

        # Try to list calendars
        print("\nAttempting to list calendars...")
        calendar_list = service.calendarList().list(maxResults=5).execute()
        calendars = calendar_list.get('items', [])

        print(f"✓ Successfully accessed Calendar API!")
        print(f"  Found {len(calendars)} calendar(s):")
        for cal in calendars:
            print(f"    - {cal.get('summary', 'Unnamed')}")

        return True

    except Exception as e:
        print(f"❌ Calendar API access failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Google Calendar Credential Test Suite")
    print("=" * 60)
    print()

    results = []

    # Run tests
    results.append(("Environment Variables", test_environment_variables()))
    results.append(("Credential Parsing", test_credential_parsing()))
    results.append(("Credential Loading & Refresh", test_credential_loading()))
    results.append(("Calendar API Access", test_calendar_api()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 All tests passed! Credentials are configured correctly.")
        sys.exit(0)
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
        print("\nTroubleshooting steps:")
        print("1. Ensure GOOGLE_CREDENTIALS is set in your 'env' file or environment")
        print("2. Verify the credentials contain all required fields:")
        print("   - refresh_token")
        print("   - client_id")
        print("   - client_secret")
        print("3. Check that the credentials haven't been revoked in Google Cloud Console")
        print("4. Run the debug endpoint: curl http://localhost:5050/debug/credentials")
        sys.exit(1)


if __name__ == '__main__':
    main()
