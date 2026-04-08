import sys
sys.path.insert(0, "/app")
from agents.gemini_client import generate
from database.firestore_db import store_memory
from datetime import datetime
import json

def extract_task_details(user_message: str, conversation_history: list = []):
    now = datetime.now()
    today = now.strftime("%Y-%m-%d")
    current_day = now.strftime("%A")
    current_year = now.year
    current_time = now.strftime("%H:%M")

    context = ""
    if conversation_history:
        context = "\n".join([
            f"User: {h['user']}\nAnya: {h['assistant']}"
            for h in conversation_history[-3:]
        ])

    prompt = f"""
    Today's date is {today} ({current_day}), Year: {current_year}, Time: {current_time}.
    IMPORTANT: Use {current_year} as the year for ALL dates. Never use past years.

    Recent conversation context:
    {context}

    Current user message: "{user_message}"

    Detect if user wants to save/create a calendar event or task.

    This includes:
    - Direct tasks: "call mom Sunday 5pm"
    - Hinglish commands: "isko calendar me save kr do", "calendar me daal do"
    - References using "isko", "this", "usko" — extract from context

    Return ONLY valid JSON:
    {{
        "is_task": true/false,
        "title": "clear task title in English",
        "date": "YYYY-MM-DD or null",
        "time": "HH:MM or null",
        "description": "any extra details"
    }}

    Return ONLY JSON. No extra text.
    """

    text = generate(prompt).strip().replace("```json","").replace("```","").strip()
    try:
        return json.loads(text)
    except:
        return {"is_task": False}

def process_task(user_message: str, conversation_history: list = []):
    details = extract_task_details(user_message, conversation_history)

    if not details.get("is_task"):
        return None

    title = details.get("title", user_message)
    date = details.get("date") or datetime.now().strftime("%Y-%m-%d")
    time = details.get("time") or ""
    description = details.get("description", "")

    try:
        from sources.calendar_source import create_calendar_event
        create_calendar_event(title, date, time, description)

        store_memory("tasks", f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}", {
            "title": title,
            "date": date,
            "time": time,
            "description": description,
            "original_message": user_message,
            "created_at": datetime.now().isoformat()
        })

        return {
            "success": True,
            "title": title,
            "date": date,
            "time": time,
            "message": f"Added to calendar: {title} on {date}" + (f" at {time}" if time else "")
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Couldn't create event: {str(e)}"
        }

def process_task_with_google(user_message: str, conversation_history: list = []):
    """Process task — create BOTH calendar event AND Google Task"""
    details = extract_task_details(user_message, conversation_history)

    if not details.get("is_task"):
        return None

    title = details.get("title", user_message)
    date = details.get("date") or datetime.now().strftime("%Y-%m-%d")
    time = details.get("time") or ""
    description = details.get("description", "")

    results = {"title": title, "date": date, "time": time}

    # Create Calendar Event
    try:
        from sources.calendar_source import create_calendar_event
        create_calendar_event(title, date, time, description)
        results["calendar"] = True
    except Exception as e:
        results["calendar"] = False
        print(f"❌ Calendar failed: {e}")

    # Create Google Task
    try:
        from sources.tasks_source import create_google_task
        create_google_task(title, date, description)
        results["google_task"] = True
    except Exception as e:
        results["google_task"] = False
        print(f"❌ Google task failed: {e}")

    store_memory("tasks", f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}", {
        "title": title,
        "date": date,
        "time": time,
        "description": description,
        "original_message": user_message,
        "calendar_created": results.get("calendar"),
        "google_task_created": results.get("google_task"),
        "created_at": datetime.now().isoformat()
    })

    results["success"] = True
    results["message"] = f"Added to calendar and tasks: {title} on {date}"
    return results