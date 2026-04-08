import sys
sys.path.insert(0, "/app")
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from database.firestore_db import store_memory
from datetime import datetime, timedelta

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]
TOKEN_FILE = 'token_gmail.json'
CREDENTIALS_FILE = 'oauth_credentials.json'

def authenticate_calendar():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            flow.redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
            auth_url, _ = flow.authorization_url(prompt="consent")
            print(f"\n🔗 Open this URL:\n{auth_url}")
            code = input("\n✏️ Paste code here: ")
            flow.fetch_token(code=code)
            creds = flow.credentials
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

def fetch_calendar_events(days_ahead=30):
    print("📅 Connecting to Google Calendar...")
    service = authenticate_calendar()

    now = datetime.utcnow().isoformat() + 'Z'
    future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=future,
        maxResults=20,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])
    calendar_events = []

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date', ''))
        attendees = []
        if 'attendees' in event:
            attendees = [a.get('email', '') for a in event['attendees']]

        calendar_event = {
            "id": f"cal_{event['id']}",
            "title": event.get('summary', 'No Title'),
            "date": start[:10] if start else '',
            "time": start[11:16] if 'T' in start else 'All day',
            "attendees": attendees,
            "location": event.get('location', ''),
            "description": event.get('description', '')[:200],
            "source": "google_calendar",
            "notes": event.get('description', '')[:100]
        }

        calendar_events.append(calendar_event)
        store_memory("calendar", calendar_event["id"], calendar_event)
        print(f"✅ Stored: {calendar_event['title'][:50]}")

    print(f"\n✅ Fetched {len(calendar_events)} events")
    return calendar_events

def create_calendar_event(title: str, date: str, time: str, description: str = ""):
    """Create a new calendar event"""
    print(f"📅 Creating event: {title}")
    service = authenticate_calendar()

    if time:
        start_datetime = f"{date}T{time}:00"
        hour = int(time[:2]) + 1
        end_time = f"{str(hour).zfill(2)}{time[2:]}"
        end_datetime = f"{date}T{end_time}:00"
        event_body = {
            'summary': title,
            'description': description,
            'start': {'dateTime': start_datetime, 'timeZone': 'Asia/Kolkata'},
            'end': {'dateTime': end_datetime, 'timeZone': 'Asia/Kolkata'}
        }
    else:
        event_body = {
            'summary': title,
            'description': description,
            'start': {'date': date},
            'end': {'date': date}
        }

    event = service.events().insert(calendarId='primary', body=event_body).execute()
    print(f"✅ Event created: {event.get('htmlLink')}")

    store_memory("calendar", f"cal_{event['id']}", {
        "id": f"cal_{event['id']}",
        "title": title,
        "date": date,
        "time": time,
        "description": description,
        "source": "user_created",
        "event_link": event.get('htmlLink', '')
    })

    return event

if __name__ == "__main__":
    events = fetch_calendar_events(days_ahead=30)