#!/usr/bin/env python3
"""
Coffee Chat Email Reply Assistant
Web interface for generating meeting availability responses
"""

from flask import Flask, render_template, request, jsonify, session
from flask_cors import CORS
import datetime
import pytz
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import os.path
import os
import re
import json
import base64
from typing import Any, Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from env file (local) or environment (cloud)
load_dotenv('env')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'coffee-chat-secret-key-2024')

# Enable CORS for GitHub Pages frontend
CORS(app, origins=[
    'https://candicesxc.github.io',
    'https://candiceshen.com',
    'http://localhost:5050',
    'http://127.0.0.1:5050'
])

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
TOKEN_PATH = os.getenv('GOOGLE_TOKEN_PATH', 'token.pickle')
CLIENT_SECRETS_PATH = os.getenv('GOOGLE_CLIENT_SECRETS_PATH', 'credentials.json')

# Timezone definitions
ET = pytz.timezone('America/New_York')
CST = pytz.timezone('America/Chicago')
PST = pytz.timezone('America/Los_Angeles')

# Working hours constraints
ET_START = 10  # 10am ET
ET_END = 18    # 6pm ET
LOCAL_START = 9  # 9am local time (CST/PST)
LOCAL_END = 17   # 5pm local time (CST/PST)

BUFFER_MINUTES = 30
SLOT_INCREMENT = 30


def _parse_google_credentials(value: str) -> Dict[str, Any]:
    raw_value = value.strip()
    if not raw_value:
        raise ValueError('GOOGLE_CREDENTIALS is empty after trimming.')

    try:
        decoded = base64.b64decode(raw_value).decode('utf-8')
        return json.loads(decoded)
    except (ValueError, json.JSONDecodeError):
        return json.loads(raw_value)


def _credentials_from_env() -> Optional[Credentials]:
    creds_value = os.environ.get('GOOGLE_CREDENTIALS')
    if not creds_value:
        return None

    creds_data = _parse_google_credentials(creds_value)
    required_fields = ['refresh_token', 'client_id', 'client_secret']
    missing = [field for field in required_fields if not creds_data.get(field)]
    if missing:
        raise ValueError(f"GOOGLE_CREDENTIALS missing required fields: {missing}")

    creds = Credentials(
        token=creds_data.get('token'),
        refresh_token=creds_data.get('refresh_token'),
        token_uri=creds_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
        client_id=creds_data.get('client_id'),
        client_secret=creds_data.get('client_secret'),
        scopes=SCOPES
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())

    return creds


def _credentials_from_local_token() -> Optional[Credentials]:
    if not os.path.exists(TOKEN_PATH):
        return None

    with open(TOKEN_PATH, 'rb') as token:
        creds = pickle.load(token)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'wb') as token_file:
            pickle.dump(creds, token_file)

    return creds


def _credentials_from_local_flow() -> Optional[Credentials]:
    if not os.path.exists(CLIENT_SECRETS_PATH):
        return None

    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_PATH, SCOPES)
    creds = flow.run_local_server(port=0)

    with open(TOKEN_PATH, 'wb') as token:
        pickle.dump(creds, token)

    return creds


def get_calendar_service():
    """Authenticate and return Google Calendar service.

    Supports two modes:
    1. Local development: Uses credentials.json and token.pickle files
    2. Cloud deployment: Uses GOOGLE_CREDENTIALS environment variable (base64 encoded token)
    """
    creds = None

    # Check for cloud deployment credentials first
    google_creds_env = os.environ.get('GOOGLE_CREDENTIALS')
    if google_creds_env:
        try:
            creds = _credentials_from_env()
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            print(f"Error loading cloud credentials: {e}")
            import traceback
            traceback.print_exc()
            return None

    # Local development: use file-based credentials
    creds = _credentials_from_local_token()

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = _credentials_from_local_flow()

        if creds:
            with open(TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)

    if not creds:
        return None

    return build('calendar', 'v3', credentials=creds)


def get_busy_times(service, start_date, end_date):
    """Get all busy times from calendar"""
    time_min = start_date.isoformat()
    time_max = end_date.isoformat()

    events_result = service.events().list(
        calendarId='primary',
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    busy_times = []
    for event in events:
        if 'date' in event['start']:
            continue

        start = datetime.datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
        end = datetime.datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00'))

        start_et = start.astimezone(ET)
        end_et = end.astimezone(ET)

        start_with_buffer = start_et - datetime.timedelta(minutes=BUFFER_MINUTES)
        end_with_buffer = end_et + datetime.timedelta(minutes=BUFFER_MINUTES)

        busy_times.append((start_with_buffer, end_with_buffer))

    return busy_times


def is_time_available(check_time, busy_times):
    """Check if a given time slot is available"""
    for busy_start, busy_end in busy_times:
        if check_time >= busy_start and check_time < busy_end:
            return False
    return True


def is_valid_for_timezone(time_et, target_tz):
    """Check if the ET time falls within working hours for target timezone"""
    if target_tz == 'ET':
        return True

    tz = CST if target_tz == 'CST' else PST
    local_time = time_et.astimezone(tz)

    hour = local_time.hour
    return LOCAL_START <= hour < LOCAL_END


def find_available_meeting_slots(service, start_date, end_date, target_timezone='ET', meeting_duration=30):
    """Find all possible meeting start times.

    Returns a list of start times where a meeting of meeting_duration can fit,
    with at least BUFFER_MINUTES before the next event.
    """
    now = datetime.datetime.now(ET)
    required_duration = meeting_duration + BUFFER_MINUTES
    busy_times = get_busy_times(service, start_date, end_date)

    # First, find all available 30-min slots
    all_available_slots = []
    current_date = start_date

    while current_date < end_date:
        if current_date.weekday() >= 5:
            current_date += datetime.timedelta(days=1)
            continue

        for hour in range(ET_START, ET_END):
            for minute in [0, 30]:
                check_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

                if check_time <= now:
                    continue

                if not is_time_available(check_time, busy_times):
                    continue

                if not is_valid_for_timezone(check_time, target_timezone):
                    continue

                all_available_slots.append(check_time)

        current_date += datetime.timedelta(days=1)

    if not all_available_slots:
        return []

    # Convert to a set for O(1) lookup
    available_set = set(all_available_slots)

    # Find all valid meeting start times
    # A start time is valid if all required slots (for meeting + buffer) are available
    valid_start_times = []
    slots_needed = int(required_duration / SLOT_INCREMENT)

    for slot in all_available_slots:
        # Check if all required consecutive slots are available
        all_slots_available = True
        for i in range(slots_needed):
            check_slot = slot + datetime.timedelta(minutes=i * SLOT_INCREMENT)
            if check_slot not in available_set:
                all_slots_available = False
                break

        if all_slots_available:
            valid_start_times.append(slot)

    return valid_start_times


def format_slot_for_timezone(start_et, target_tz, meeting_duration):
    """Format a meeting slot for display in target timezone."""
    meeting_end_et = start_et + datetime.timedelta(minutes=meeting_duration)

    if target_tz == 'ET':
        start_local = start_et
        meeting_end_local = meeting_end_et
        tz_abbr = 'EST'
    else:
        tz = CST if target_tz == 'CST' else PST
        start_local = start_et.astimezone(tz)
        meeting_end_local = meeting_end_et.astimezone(tz)
        tz_abbr = target_tz

    date_str = start_local.strftime('%A, %B %d')
    start_time = start_local.strftime('%I:%M %p').lstrip('0')
    end_time = meeting_end_local.strftime('%I:%M %p').lstrip('0')

    formatted = f"{date_str} from {start_time} to {end_time} {tz_abbr}"

    # Also get EST times for verification
    est_start_time = start_et.strftime('%I:%M %p').lstrip('0')
    est_end_time = meeting_end_et.strftime('%I:%M %p').lstrip('0')
    est_str = f"{est_start_time} to {est_end_time} EST"

    return formatted, est_str


def extract_sender_name_from_email(email_text):
    """Extract the sender's name from the email signature.

    The sender is the person who wrote the email (signs at the bottom),
    NOT the person being addressed (Hi [Name]).
    """
    # Look for signature patterns - the sender's name
    # Common patterns: "Thank you,\nName", "Best,\nName", "Regards,\nName", etc.
    signature_patterns = [
        r'(?:Thank you|Thanks|Best|Regards|Cheers|Sincerely|Best regards|Kind regards|Warm regards)[,.]?\s*\n+\s*([A-Z][a-z]+)',
        r'\n([A-Z][a-z]+)\s*$',  # Last line with a capitalized name
    ]

    for pattern in signature_patterns:
        match = re.search(pattern, email_text, re.IGNORECASE | re.MULTILINE)
        if match:
            return match.group(1)

    return None


def parse_email_with_ai(email_text):
    """Use OpenAI to parse the email and extract meeting details."""
    try:
        client = OpenAI()

        today = datetime.datetime.now(ET)
        today_str = today.strftime('%A, %B %d, %Y')

        # Calculate next week's Monday for reference
        days_until_monday = (7 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + datetime.timedelta(days=days_until_monday)
        next_monday_str = next_monday.strftime('%Y-%m-%d')
        next_friday = next_monday + datetime.timedelta(days=4)
        next_friday_str = next_friday.strftime('%Y-%m-%d')

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Today is {today_str}. Next week runs from Monday {next_monday_str} to Friday {next_friday_str}.

Analyze this email and extract meeting scheduling information. Return ONLY a JSON object with these fields:

1. "sender_name": The first name of the person who WROTE/SENT the email (look at the signature at the bottom, NOT the greeting "Hi [Name]")

2. "duration": Meeting duration in minutes. ONLY set this if explicitly mentioned (e.g., "30-minute call", "1 hour meeting", "45 min chat").
   - If duration is explicitly stated, extract it (e.g., "30-minute" = 30, "1 hour" = 60)
   - If NOT explicitly mentioned, set to null

3. "timezone": Infer from location/company mentions:
   - NYC, New York, East Coast, Eastern = "ET"
   - Chicago, Central = "CST"
   - LA, San Francisco, Seattle, Pacific, West Coast = "PST"
   - If no location clues, set to null

4. "start_date": The FIRST day they want to meet (YYYY-MM-DD format)
   - "next week" = {next_monday_str} (Monday of next week)
   - "next Wednesday-Friday" = calculate next Wednesday's date
   - "this week" = tomorrow's date
   - If no date mentioned, set to null

5. "end_date": The day AFTER the last day they want to meet (YYYY-MM-DD format, exclusive)
   - "next week" = the Saturday after next Friday ({(next_friday + datetime.timedelta(days=1)).strftime('%Y-%m-%d')})
   - "next Wednesday-Friday" = the Saturday after that Friday
   - If no date mentioned, set to null

IMPORTANT:
- Only extract what is EXPLICITLY stated or can be CLEARLY inferred
- Use null for any field that cannot be determined from the email
- "next week" means the ENTIRE week (Mon-Fri), not a subset

Email:
{email_text}

Return ONLY valid JSON, no explanation."""
                }
            ]
        )

        result_text = response.choices[0].message.content
        # Clean up potential markdown formatting
        if result_text.startswith('```'):
            result_text = result_text.split('```')[1]
            if result_text.startswith('json'):
                result_text = result_text[4:]
        result_text = result_text.strip()

        result = json.loads(result_text)
        return result
    except Exception as e:
        print(f"AI parsing error: {e}")
        return None


def generate_contextual_reply(original_email, sender_name, time_slots_text):
    """Generate a natural, contextual email reply using AI."""
    try:
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Write a friendly, natural email reply to schedule a meeting.

ORIGINAL EMAIL FROM {sender_name}:
{original_email}

MY AVAILABLE TIME SLOTS:
{time_slots_text}

INSTRUCTIONS:
- Start with "Hi {sender_name},"
- Be warm and human - match the tone of their email
- If they apologized or mentioned inconvenience, acknowledge it naturally (e.g., "No worries at all!", "Totally understand!")
- If they expressed excitement, mirror that energy
- If it's a job/recruiting email, be professionally enthusiastic
- Keep it concise - 2-3 short paragraphs max
- Include the time slots as a bulleted list
- End with something like "Let me know what works!" and sign off as "Candice"
- Don't be overly formal or stiff - write like a real person

Return ONLY the email text, no explanation."""
                }
            ]
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI reply generation error: {e}")
        # Fallback to simple template
        return f"""Hi {sender_name},

Thanks for reaching out! I'd be happy to chat.

Here are some times that work for me:

{time_slots_text}

Let me know what works best for you!

Best,
Candice"""


def parse_date_range(range_type, custom_start=None, custom_end=None):
    """Parse date range from selection or custom dates"""
    now = datetime.datetime.now(ET)
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # If custom dates are provided, use them
    if custom_start and custom_end:
        try:
            start = datetime.datetime.strptime(custom_start, '%Y-%m-%d')
            start = ET.localize(start)
            end = datetime.datetime.strptime(custom_end, '%Y-%m-%d')
            end = ET.localize(end)
            return start, end
        except:
            pass

    days_until_monday = (7 - today.weekday()) % 7
    if days_until_monday == 0:
        days_until_monday = 7
    next_monday = today + datetime.timedelta(days=days_until_monday)

    if range_type == 'this_week':
        start = today + datetime.timedelta(days=1)
        days_until_sunday = (6 - today.weekday()) % 7
        end = today + datetime.timedelta(days=days_until_sunday + 1)
        return start, end
    elif range_type == 'next_week':
        return next_monday, next_monday + datetime.timedelta(days=7)
    elif range_type == 'two_weeks':
        start = today + datetime.timedelta(days=1)
        end = today + datetime.timedelta(days=15)
        return start, end
    else:
        # Default to two weeks
        start = today + datetime.timedelta(days=1)
        end = today + datetime.timedelta(days=15)
        return start, end


def select_best_days(day_blocks, max_days=4):
    """Select the best days to suggest when there are more than max_days available.

    Prioritizes:
    1. Days with more available time
    2. Spread across the date range (not all bunched together)
    """
    if len(day_blocks) <= max_days:
        return day_blocks

    # Calculate total available time per day
    day_scores = []
    for day_date, blocks in day_blocks.items():
        total_minutes = 0
        for block in blocks:
            duration = (block['end_local'] - block['start_local']).total_seconds() / 60
            total_minutes += duration
        day_scores.append((day_date, total_minutes, blocks))

    # Sort by total available time (most available first)
    day_scores.sort(key=lambda x: x[1], reverse=True)

    # Take top days but try to spread them out
    selected = []
    selected_dates = []

    for day_date, score, blocks in day_scores:
        if len(selected) >= max_days:
            break
        selected.append((day_date, blocks))
        selected_dates.append(day_date)

    # Sort selected days chronologically
    selected.sort(key=lambda x: x[0])

    return {day: blocks for day, blocks in selected}


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/generate', methods=['POST'])
def generate_reply():
    data = request.json

    email_text = data.get('email_text', '')

    # Try to parse email with AI first
    ai_parsed = None
    if email_text.strip():
        ai_parsed = parse_email_with_ai(email_text)

    # Track what fields are missing and need clarification
    missing_fields = []

    # Use AI-parsed values, user-provided clarification, or mark as missing
    if ai_parsed:
        # Timezone - AI returns null if not determinable, require clarification
        ai_timezone = ai_parsed.get('timezone')
        if ai_timezone and ai_timezone != 'null':
            timezone = ai_timezone
        elif data.get('timezone'):
            timezone = data.get('timezone')
        else:
            missing_fields.append('timezone')
            timezone = None

        # Duration - AI returns null if not explicitly mentioned
        ai_duration = ai_parsed.get('duration')
        if ai_duration and ai_duration != 'null' and str(ai_duration) != 'null':
            duration = int(ai_duration)
        elif data.get('duration'):
            duration = int(data.get('duration'))
        else:
            missing_fields.append('duration')
            duration = None

        # Sender name
        sender_name = ai_parsed.get('sender_name') or extract_sender_name_from_email(email_text) or 'there'

        # Date range - AI returns null if not mentioned
        custom_start = ai_parsed.get('start_date')
        custom_end = ai_parsed.get('end_date')

        # Check if AI returned null values (as string or None)
        if not custom_start or custom_start == 'null' or not custom_end or custom_end == 'null':
            custom_start = None
            custom_end = None
            if data.get('date_range'):
                # User provided clarification via dropdown
                pass
            else:
                missing_fields.append('date_range')
    else:
        # No AI parsing available, check for user-provided values
        if data.get('timezone'):
            timezone = data.get('timezone')
        else:
            missing_fields.append('timezone')
            timezone = None

        if data.get('duration'):
            duration = int(data.get('duration'))
        else:
            missing_fields.append('duration')
            duration = None

        sender_name = extract_sender_name_from_email(email_text) or 'there'
        custom_start = None
        custom_end = None

        if not data.get('date_range'):
            missing_fields.append('date_range')

    # If there are missing required fields, return for clarification
    if missing_fields:
        return jsonify({
            'needs_clarification': True,
            'missing_fields': missing_fields,
            'ai_parsed': ai_parsed
        })

    date_range = data.get('date_range', 'two_weeks')

    # Get calendar service
    service = get_calendar_service()
    if not service:
        return jsonify({
            'error': 'Calendar not connected. Check that GOOGLE_CREDENTIALS is set correctly in environment variables, or run locally to authenticate.'
        }), 400

    # Get date range
    start_date, end_date = parse_date_range(date_range, custom_start, custom_end)

    # Find all available meeting start times
    slots = find_available_meeting_slots(service, start_date, end_date,
                                          target_timezone=timezone,
                                          meeting_duration=duration)

    if not slots:
        return jsonify({
            'error': f'No available slots found for {duration}-minute meetings with 30-min buffer.'
        }), 400

    # Format slots for display
    formatted_blocks = []
    for start in slots:
        local_format, est_format = format_slot_for_timezone(start, timezone, duration)
        formatted_blocks.append({
            'local': local_format,
            'est': est_format,
            'start_iso': start.isoformat(),
            'start_et': start
        })

    # Combine consecutive/overlapping slots on the same day into continuous availability windows
    # Each slot is a potential meeting START time. Two slots are consecutive if the second
    # starts within SLOT_INCREMENT (30 min) of the first.
    combined_blocks = []
    for block in formatted_blocks:
        start_et = block['start_et']
        # The meeting would end at start + duration
        meeting_end_et = start_et + datetime.timedelta(minutes=duration)

        # Convert to target timezone for grouping
        if timezone == 'ET':
            start_local = start_et
            end_local = meeting_end_et
            tz_abbr = 'EST'
        else:
            tz = CST if timezone == 'CST' else PST
            start_local = start_et.astimezone(tz)
            end_local = meeting_end_et.astimezone(tz)
            tz_abbr = timezone

        # Check if this slot can be merged with the previous one
        # Slots are consecutive if on the same day and the new start is within SLOT_INCREMENT of previous end
        # (meaning they overlap or touch since meetings are longer than the increment)
        if combined_blocks:
            prev = combined_blocks[-1]
            time_gap = (start_local - prev['end_local']).total_seconds() / 60

            # Same day and slots are within SLOT_INCREMENT minutes (consecutive availability)
            if (prev['end_local'].date() == start_local.date() and
                time_gap <= SLOT_INCREMENT and time_gap >= -duration):
                # Merge: extend the end time if this slot ends later
                if end_local > prev['end_local']:
                    combined_blocks[-1]['end_local'] = end_local
                    combined_blocks[-1]['end_et'] = meeting_end_et
                continue

        combined_blocks.append({
            'start_local': start_local,
            'end_local': end_local,
            'start_et': start_et,
            'end_et': meeting_end_et,
            'tz_abbr': tz_abbr
        })

    # Group blocks by day
    day_blocks = {}
    for cb in combined_blocks:
        day_date = cb['start_local'].date()
        if day_date not in day_blocks:
            day_blocks[day_date] = []
        day_blocks[day_date].append(cb)

    # Select best 4 days if more than 4 available
    if len(day_blocks) > 4:
        day_blocks = select_best_days(day_blocks, max_days=4)

    # Flatten back and format - combine multiple time ranges on same day
    final_blocks = []
    for day_date in sorted(day_blocks.keys()):
        blocks = day_blocks[day_date]

        # Format the day string once
        date_str = blocks[0]['start_local'].strftime('%A, %B %d')
        tz_abbr = blocks[0]['tz_abbr']

        # Collect all time ranges for this day
        time_ranges = []
        est_ranges = []
        for cb in blocks:
            start_time = cb['start_local'].strftime('%I:%M %p').lstrip('0')
            end_time = cb['end_local'].strftime('%I:%M %p').lstrip('0')
            time_ranges.append(f"{start_time} to {end_time}")

            est_start = cb['start_et'].strftime('%I:%M %p').lstrip('0')
            est_end = cb['end_et'].strftime('%I:%M %p').lstrip('0')
            est_ranges.append(f"{est_start} to {est_end}")

        # Combine into single line: "Friday, February 13 from 10:00 AM to 10:30 AM, 3:00 PM to 5:30 PM EST"
        time_str = ", ".join(time_ranges)
        local_format = f"{date_str} from {time_str} {tz_abbr}"

        est_str = ", ".join(est_ranges)
        est_format = f"{est_str} EST"

        final_blocks.append({
            'local': local_format,
            'est': est_format,
            'start_iso': blocks[0]['start_et'].isoformat()
        })

    # Generate email reply using AI for natural, contextual tone
    time_slots_text = "\n".join([f"• {b['local']}" for b in final_blocks])

    reply = generate_contextual_reply(email_text, sender_name, time_slots_text)

    return jsonify({
        'reply': reply,
        'blocks': final_blocks,
        'timezone': timezone,
        'duration': duration,
        'ai_parsed': ai_parsed  # Include parsed info for debugging
    })


def generate_compose_email(recipient_name, context, time_slots_text):
    """Generate a natural outbound email requesting a meeting using AI."""
    try:
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=500,
            messages=[
                {
                    "role": "user",
                    "content": f"""Write a friendly, natural email to request a meeting.

RECIPIENT: {recipient_name}
PURPOSE/CONTEXT: {context}

MY AVAILABLE TIME SLOTS:
{time_slots_text}

INSTRUCTIONS:
- Start with "Hi {recipient_name},"
- Be warm and natural - write like a real person, not a corporate robot
- Briefly explain why you want to meet (based on the context provided)
- Include the time slots as a bulleted list
- Ask them to let you know what works or suggest alternatives
- Keep it concise - 2-3 short paragraphs max
- Sign off as "Candice"
- Don't be overly formal or stiff

Return ONLY the email text, no explanation."""
                }
            ]
        )

        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"AI compose generation error: {e}")
        # Fallback to simple template
        return f"""Hi {recipient_name},

I hope you're doing well! {context}

I'd love to find a time to chat. Here are some slots that work for me:

{time_slots_text}

Let me know what works for you, or feel free to suggest another time!

Best,
Candice"""


@app.route('/compose', methods=['POST'])
def compose_email():
    """Generate an outbound meeting request email."""
    data = request.json

    recipient_name = data.get('recipient_name', 'there')
    timezone = data.get('timezone', 'ET')
    duration = int(data.get('duration', 30))
    date_range = data.get('date_range', 'two_weeks')
    context = data.get('context', '')

    # Get calendar service
    service = get_calendar_service()
    if not service:
        return jsonify({
            'error': 'Calendar not connected. Check that GOOGLE_CREDENTIALS is set correctly in environment variables, or run locally to authenticate.'
        }), 400

    # Get date range
    start_date, end_date = parse_date_range(date_range)

    # Find all available meeting start times
    slots = find_available_meeting_slots(service, start_date, end_date,
                                          target_timezone=timezone,
                                          meeting_duration=duration)

    if not slots:
        return jsonify({
            'error': f'No available slots found for {duration}-minute meetings with 30-min buffer.'
        }), 400

    # Format slots for display (reuse the same logic as generate_reply)
    formatted_blocks = []
    for start in slots:
        local_format, est_format = format_slot_for_timezone(start, timezone, duration)
        formatted_blocks.append({
            'local': local_format,
            'est': est_format,
            'start_iso': start.isoformat(),
            'start_et': start
        })

    # Combine consecutive/overlapping slots
    combined_blocks = []
    for block in formatted_blocks:
        start_et = block['start_et']
        meeting_end_et = start_et + datetime.timedelta(minutes=duration)

        if timezone == 'ET':
            start_local = start_et
            end_local = meeting_end_et
            tz_abbr = 'EST'
        else:
            tz = CST if timezone == 'CST' else PST
            start_local = start_et.astimezone(tz)
            end_local = meeting_end_et.astimezone(tz)
            tz_abbr = timezone

        if combined_blocks:
            prev = combined_blocks[-1]
            time_gap = (start_local - prev['end_local']).total_seconds() / 60

            if (prev['end_local'].date() == start_local.date() and
                time_gap <= SLOT_INCREMENT and time_gap >= -duration):
                if end_local > prev['end_local']:
                    combined_blocks[-1]['end_local'] = end_local
                    combined_blocks[-1]['end_et'] = meeting_end_et
                continue

        combined_blocks.append({
            'start_local': start_local,
            'end_local': end_local,
            'start_et': start_et,
            'end_et': meeting_end_et,
            'tz_abbr': tz_abbr
        })

    # Group blocks by day
    day_blocks = {}
    for cb in combined_blocks:
        day_date = cb['start_local'].date()
        if day_date not in day_blocks:
            day_blocks[day_date] = []
        day_blocks[day_date].append(cb)

    # Select best 4 days if more than 4 available
    if len(day_blocks) > 4:
        day_blocks = select_best_days(day_blocks, max_days=4)

    # Flatten back and format
    final_blocks = []
    for day_date in sorted(day_blocks.keys()):
        blocks = day_blocks[day_date]

        date_str = blocks[0]['start_local'].strftime('%A, %B %d')
        tz_abbr = blocks[0]['tz_abbr']

        time_ranges = []
        est_ranges = []
        for cb in blocks:
            start_time = cb['start_local'].strftime('%I:%M %p').lstrip('0')
            end_time = cb['end_local'].strftime('%I:%M %p').lstrip('0')
            time_ranges.append(f"{start_time} to {end_time}")

            est_start = cb['start_et'].strftime('%I:%M %p').lstrip('0')
            est_end = cb['end_et'].strftime('%I:%M %p').lstrip('0')
            est_ranges.append(f"{est_start} to {est_end}")

        time_str = ", ".join(time_ranges)
        local_format = f"{date_str} from {time_str} {tz_abbr}"

        est_str = ", ".join(est_ranges)
        est_format = f"{est_str} EST"

        final_blocks.append({
            'local': local_format,
            'est': est_format,
            'start_iso': blocks[0]['start_et'].isoformat()
        })

    # Generate compose email using AI
    time_slots_text = "\n".join([f"• {b['local']}" for b in final_blocks])
    reply = generate_compose_email(recipient_name, context, time_slots_text)

    return jsonify({
        'reply': reply,
        'blocks': final_blocks,
        'timezone': timezone,
        'duration': duration
    })


@app.route('/refine', methods=['POST'])
def refine_reply():
    """Use AI to refine the email based on user feedback."""
    data = request.json

    current_reply = data.get('current_reply', '')
    feedback = data.get('feedback', '')

    if not feedback.strip():
        return jsonify({'error': 'Please provide feedback'}), 400

    try:
        client = OpenAI()

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": f"""Here is an email reply I'm drafting:

{current_reply}

Please modify this email based on the following feedback:
{feedback}

Return ONLY the modified email text, nothing else. Keep the same general structure and time slots unless the feedback specifically asks to change them."""
                }
            ]
        )

        refined_reply = response.choices[0].message.content.strip()
        return jsonify({'reply': refined_reply})
    except Exception as e:
        return jsonify({'error': f'AI refinement failed: {str(e)}'}), 500


@app.route('/calendar/status')
def calendar_status():
    try:
        service = get_calendar_service()
        if not service:
            return jsonify({'connected': False}), 500
        calendar = service.calendarList().list(maxResults=1).execute()
        return jsonify({'connected': True, 'calendar': calendar.get('items', [])})
    except Exception as exc:
        return jsonify({'connected': False, 'error': str(exc)}), 500


if __name__ == '__main__':
    # Change to the script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    app.run(debug=True, port=5050)
