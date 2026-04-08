import sys
sys.path.insert(0, "/app")
from agents.gemini_client import generate
from database.firestore_db import get_all_memories, store_memory
from datetime import datetime
import json

def analyze_email_signals():
    emails = get_all_memories("emails")
    if not emails:
        return {"stress_score": 0, "stress_level": "low", "signals_found": [], "summary": "No emails found"}

    email_text = "\n".join([
        f"From: {e['from']} | Subject: {e['subject']} | Body: {e['body']}"
        for e in emails
    ])

    prompt = f"""
    Analyze these emails and detect stress signals:
    {email_text}

    Return ONLY valid JSON:
    {{
        "stress_level": "low/medium/high",
        "stress_score": 1-10,
        "signals_found": ["list of signals"],
        "most_stressful_email": "subject",
        "summary": "2 sentence summary"
    }}
    """

    text = generate(prompt).strip().replace("```json","").replace("```","").strip()
    try:
        return json.loads(text)
    except:
        return {"stress_score": 0, "stress_level": "low", "signals_found": [], "summary": text}

def analyze_calendar_signals():
    events = get_all_memories("calendar")
    if not events:
        return {"overload_score": 0, "overload_level": "low", "signals_found": [], "summary": "No events found"}

    calendar_text = "\n".join([
        f"Event: {e['title']} | Date: {e['date']} | Time: {e['time']}"
        for e in events
    ])

    prompt = f"""
    Analyze this calendar and detect overload signals:
    {calendar_text}

    Return ONLY valid JSON:
    {{
        "overload_level": "low/medium/high",
        "overload_score": 1-10,
        "signals_found": ["list of signals"],
        "busiest_day": "date",
        "summary": "2 sentence summary"
    }}
    """

    text = generate(prompt).strip().replace("```json","").replace("```","").strip()
    try:
        return json.loads(text)
    except:
        return {"overload_score": 0, "overload_level": "low", "signals_found": [], "summary": text}

def run_full_signal_scan():
    print("📡 Scanning signals...\n")
    email_signals = analyze_email_signals()
    calendar_signals = analyze_calendar_signals()

    email_score = float(email_signals.get("stress_score", 0))
    calendar_score = float(calendar_signals.get("overload_score", 0))
    combined_score = (email_score + calendar_score) / 2

    if combined_score >= 7:
        overall = "high"
        message = "You seem under significant pressure. Let's talk about it."
    elif combined_score >= 4:
        overall = "medium"
        message = "Things seem busy lately. Make sure you're taking breaks."
    else:
        overall = "low"
        message = "You seem to be managing well. Keep it up!"

    result = {
        "date": datetime.now().isoformat(),
        "email_signals": email_signals,
        "calendar_signals": calendar_signals,
        "combined_score": combined_score,
        "overall_status": overall,
        "message": message
    }

    store_memory("signal_scans", f"scan_{datetime.now().strftime('%Y%m%d%H%M%S')}", result)
    return result

if __name__ == "__main__":
    result = run_full_signal_scan()
    print(f"📊 Status: {result['overall_status']}")
    print(f"💬 Message: {result['message']}")