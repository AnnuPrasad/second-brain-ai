import sys
sys.path.insert(0, "/app")
import os
import base64
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from database.firestore_db import store_memory
from datetime import datetime

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]
TOKEN_FILE = 'token_gmail.json'
CREDENTIALS_FILE = 'oauth_credentials.json'

def authenticate():
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
    return creds

def fetch_emails(max_results=10):
    print("📧 Connecting to Gmail...")
    creds = authenticate()
    service = build('gmail', 'v1', credentials=creds)

    results = service.users().messages().list(
        userId='me', maxResults=max_results, labelIds=['INBOX']
    ).execute()

    messages = results.get('messages', [])
    emails = []

    for msg in messages:
        message = service.users().messages().get(
            userId='me', id=msg['id'], format='full'
        ).execute()

        headers = message['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), '')

        body = ""
        if 'parts' in message['payload']:
            for part in message['payload']['parts']:
                if part['mimeType'] == 'text/plain':
                    try:
                        body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
                    except:
                        pass
        elif 'body' in message['payload']:
            try:
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')
            except:
                body = ""

        email = {
            "id": f"gmail_{msg['id']}",
            "from": sender,
            "subject": subject,
            "body": body[:500],
            "date": date,
            "source": "gmail_real",
            "tags": []
        }

        emails.append(email)
        store_memory("emails", email["id"], email)
        print(f"✅ Stored: {subject[:50]}")

    print(f"\n✅ Fetched {len(emails)} emails")
    return emails

if __name__ == "__main__":
    emails = fetch_emails(max_results=10)