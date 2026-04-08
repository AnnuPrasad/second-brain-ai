import sys
sys.path.insert(0, "/app")
from agents.gemini_client import generate
from database.firestore_db import get_all_memories, store_memory
from datetime import datetime

def analyze_mood_pattern():
    moods = get_all_memories("mood_entries")
    if not moods:
        return {"status": "no_data", "message": "No mood data found"}

    moods = sorted(moods, key=lambda x: x["date"])
    scores = [m["score"] for m in moods]
    avg_score = sum(scores) / len(scores)
    latest_score = scores[-1]
    trend = "declining" if latest_score < avg_score else "improving"

    mood_summary = "\n".join([
        f"- {m['date']}: {m['mood']} (score: {m['score']}) — {m['note']}"
        for m in moods
    ])

    prompt = f"""
    You are a compassionate mental health companion.
    Here is the user's mood history:
    {mood_summary}

    Average mood score: {avg_score:.1f}/10
    Latest mood score: {latest_score}/10
    Trend: {trend}

    Please:
    1. Summarize their emotional pattern in 2-3 sentences
    2. Identify what seems to be causing their mood
    3. Give one gentle practical suggestion
    4. End with a warm supportive message

    Be warm human and non-clinical. Talk like a caring friend.
    Max 3-4 sentences total.
    """

    analysis_text = generate(prompt)

    analysis = {
        "date": datetime.now().isoformat(),
        "avg_score": avg_score,
        "latest_score": latest_score,
        "trend": trend,
        "analysis": analysis_text,
        "total_entries": len(moods)
    }
    store_memory("mood_analysis", f"analysis_{datetime.now().strftime('%Y%m%d')}", analysis)
    return analysis

def check_crisis(mood_score: int):
    if mood_score <= 2:
        return {
            "crisis": True,
            "message": "I noticed you're having a really tough time. You're not alone. Would you like to talk?"
        }
    return {"crisis": False}

def log_mood(mood: str, score: int, note: str):
    entry = {
        "id": f"mood_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "mood": mood,
        "score": score,
        "note": note
    }
    store_memory("mood_entries", entry["id"], entry)
    crisis = check_crisis(score)
    if crisis["crisis"]:
        print(f"\n⚠️ Crisis detected: {crisis['message']}")
    return entry

if __name__ == "__main__":
    result = analyze_mood_pattern()
    print(f"Trend: {result['trend']}")
    print(f"\n💬 Analysis:\n{result['analysis']}")
    