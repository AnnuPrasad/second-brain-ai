import sys
sys.path.insert(0, "/app")
from agents.gemini_client import generate
from database.firestore_db import get_all_memories

def build_context():
    emails = get_all_memories("emails")
    calendar = get_all_memories("calendar")
    notes = get_all_memories("notes")
    moods = get_all_memories("mood_entries")

    return f"""
    Today is Wednesday, April 08, 2026. You are Second Brain AI — a personal AI that remembers everything about the user's life
    and also cares about their mental wellbeing.

    EMAILS: {emails}
    CALENDAR EVENTS: {calendar}
    NOTES: {notes}
    MOOD HISTORY: {moods}

    Answer the user's question with deep personalization.
    If you detect stress or anxiety patterns, acknowledge them with empathy.
    """

def ask(user_question: str):
    print(f"\n🧠 Processing: {user_question}")
    context = build_context()
    prompt = f"{context}\n\nUser asks: {user_question}"
    return generate(prompt)

if __name__ == "__main__":
    answer = ask("How am I feeling lately?")
    print(f"\n💬 Answer: {answer}")
