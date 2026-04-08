import sys
sys.path.append('/home/annuprasad2003/second-brain-ai')
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from database.firestore_db import store_memory, get_all_memories
from datetime import datetime

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks'
]
TOKEN_FILE = 'token_gmail.json'
CREDENTIALS_FILE = 'oauth_credentials.json'

def authenticate_tasks():
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
    return build('tasks', 'v1', credentials=creds)

def fetch_tasks():
    print("✅ Connecting to Google Tasks...")
    service = authenticate_tasks()
    tasklists = service.tasklists().list().execute()
    all_tasks = []

    for tasklist in tasklists.get('items', []):
        tasks = service.tasks().list(
            tasklist=tasklist['id'],
            showCompleted=False
        ).execute()

        for task in tasks.get('items', []):
            task_data = {
                "id": f"gtask_{task['id']}",
                "title": task.get('title', ''),
                "status": task.get('status', 'needsAction'),
                "due": task.get('due', '')[:10] if task.get('due') else '',
                "notes": task.get('notes', ''),
                "tasklist": tasklist['title'],
                "source": "google_tasks",
                "created_at": datetime.now().isoformat()
            }
            all_tasks.append(task_data)
            store_memory("google_tasks", task_data["id"], task_data)
            print(f"✅ Stored task: {task_data['title'][:50]}")

    print(f"\n✅ Fetched {len(all_tasks)} tasks")
    return all_tasks

def create_google_task(title: str, due_date: str = None, notes: str = ""):
    print(f"📝 Creating Google Task: {title}")
    service = authenticate_tasks()

    tasklists = service.tasklists().list().execute()
    default_list = tasklists['items'][0]['id']

    task_body = {
        'title': title,
        'notes': notes,
        'status': 'needsAction'
    }

    if due_date:
        task_body['due'] = f"{due_date}T00:00:00.000Z"

    task = service.tasks().insert(tasklist=default_list, body=task_body).execute()

    task_data = {
        "id": f"gtask_{task['id']}",
        "title": title,
        "due": due_date or '',
        "notes": notes,
        "source": "second_brain_created",
        "created_at": datetime.now().isoformat()
    }
    store_memory("google_tasks", task_data["id"], task_data)

    print(f"✅ Task created: {title}")
    return task

def complete_task(task_id: str):
    service = authenticate_tasks()
    tasklists = service.tasklists().list().execute()
    default_list = tasklists['items'][0]['id']
    real_id = task_id.replace("gtask_", "")

    task = service.tasks().patch(
        tasklist=default_list,
        task=real_id,
        body={'status': 'completed'}
    ).execute()
    return task

if __name__ == "__main__":
    tasks = fetch_tasks()
    print(f"\nFound {len(tasks)} tasks")