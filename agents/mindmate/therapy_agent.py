import sys
sys.path.insert(0, "/app")
from agents.gemini_client import generate
from database.firestore_db import get_all_memories, get_memory, store_memory
from agents.mindmate.persona_agent import get_user_persona
from datetime import datetime

conversation_history = []

def get_user_context():
    moods = get_all_memories("mood_entries")
    notes = get_all_memories("notes")
    signal_scans = get_all_memories("signal_scans")

    mood_trend = "no data"
    if moods:
        recent_moods = sorted(moods, key=lambda x: x.get("date",""))[-3:]
        mood_trend = ", ".join([f"{m.get('mood')} ({m.get('score')})" for m in recent_moods])

    stress_level = "unknown"
    if signal_scans:
        latest = sorted(signal_scans, key=lambda x: x.get("date",""))[-1]
        stress_level = latest.get("overall_status","unknown")

    notes_summary = ""
    if notes:
        notes_summary = " | ".join([n.get("content","")[:100] for n in notes[-3:]])

    return {
        "mood_trend": mood_trend,
        "stress_level": stress_level,
        "notes_summary": notes_summary
    }

def detect_crisis(message: str):
    crisis_keywords = ["suicide","kill myself","end it all","hopeless","no point",
                      "cant go on","self harm","hurt myself","give up on life",
                      "jeena nahi","mar jaunga","khud ko hurt"]
    return any(k in message.lower() for k in crisis_keywords)

def detect_language(message: str):
    hindi_words = ["hai","hoon","mera","meri","kya","nahi","bahut","accha",
                  "theek","kal","aaj","yaar","bhai","dost","karo","karoo",
                  "hogaya","hua","thi","tha","raha","rahi","kyun","kaise",
                  "isko","usko","mujhe","tumhe","apna","apni","hum","tum"]
    words = message.lower().split()
    hindi_count = sum(1 for w in words if w in hindi_words)
    if hindi_count >= 1:
        return "hinglish"
    return "english"

def chat(user_message: str, session_id: str = "default"):
    global conversation_history

    if detect_crisis(user_message):
        crisis_response = """Yaar, main sun raha/rahi hoon. Tu akela/akeli nahi hai.
        Please abhi iCall India ko call kar: 9152987821
        Main yahan hoon tere liye. Bata mujhe kya ho raha hai?"""
        store_conversation(session_id, user_message, crisis_response, "crisis")
        return {"response": crisis_response, "flag": "crisis", "persona": "Anya"}

    persona = get_user_persona()
    user_context = get_user_context()
    language = detect_language(user_message)

    history_text = "\n".join([
        f"User: {h['user']}\n{persona.get('persona_name','Anya')}: {h['assistant']}"
        for h in conversation_history[-5:]
    ])

    if language == "hinglish":
        language_instruction = """
        LANGUAGE RULES — VERY IMPORTANT:
        - User is speaking Hinglish (Hindi + English mix)
        - YOU MUST reply in Hinglish too
        - Mix Hindi and English naturally like a friend
        - Example: "Arre yaar, that sounds really tough. Kya hua exactly?"
        - Use words like: yaar, arre, accha, theek hai, sach mein, bilkul, haan
        - Sound like a real desi friend, not a formal AI
        """
    else:
        language_instruction = """
        LANGUAGE RULES:
        - Reply in natural casual English
        - Like a real friend texting, not a formal AI
        """

    prompt = f"""
    Today is Wednesday, April 08, 2026. You are {persona.get('persona_name','Anya')}, a caring AI companion.

    PERSONALITY:
    - Type: {persona.get('persona_type','nurturer')}
    - Tone: {persona.get('tone','warm')}
    - Style: {persona.get('communication_style','')}

    USER CONTEXT:
    - Mood trend: {user_context.get('mood_trend')}
    - Stress level: {user_context.get('stress_level')}

    {language_instruction}

    RESPONSE RULES — CRITICAL:
    - MAX 2-3 sentences only
    - Sound like a real friend texting
    - NO long paragraphs
    - NO bullet points
    - NO formal language
    - Always end with ONE short question
    - Be warm but BRIEF

    CONVERSATION:
    {history_text}

    User: {user_message}
    {persona.get('persona_name','Anya')}:
    """

    reply = generate(prompt).strip()

    conversation_history.append({
        "user": user_message,
        "assistant": reply,
        "timestamp": datetime.now().isoformat()
    })

    store_conversation(session_id, user_message, reply, "normal")
    return {"persona": persona.get('persona_name'), "response": reply, "flag": "normal"}

def store_conversation(session_id, user_msg, assistant_msg, flag):
    store_memory("therapy_sessions", f"session_{datetime.now().strftime('%Y%m%d%H%M%S')}", {
        "session_id": session_id,
        "user_message": user_msg,
        "assistant_response": assistant_msg,
        "flag": flag,
        "timestamp": datetime.now().isoformat()
    })

def start_session():
    global conversation_history
    conversation_history = []
    persona = get_user_persona()
    user_context = get_user_context()

    prompt = f"""
    Today is Wednesday, April 08, 2026. You are {persona.get('persona_name','Anya')}, a warm AI companion.
    Tone: {persona.get('tone','warm')}

    User context:
    - Mood trend: {user_context.get('mood_trend')}
    - Stress level: {user_context.get('stress_level')}

    RULES:
    - Write ONE short greeting — max 2 sentences
    - Sound like a friend, not an AI
    - End with ONE simple question
    - If stress is medium/high — acknowledge it gently
    - Keep it super short and warm
    """

    return {
        "persona": persona.get('persona_name'),
        "opening_message": generate(prompt).strip()
    }

def chat_with_task_detection(user_message: str, session_id: str = "default"):
    from agents.task_agent import process_task_with_google
    task_result = process_task_with_google(user_message, conversation_history)

    if task_result and task_result.get("success"):
        persona = get_user_persona()
        language = detect_language(user_message)

        if language == "hinglish":
            prompt = f"""
            Today is Wednesday, April 08, 2026. You are {persona.get('persona_name','Anya')}.
            User ne kaha: "{user_message}"
            Tune calendar aur tasks mein add kar diya: {task_result['title']} on {task_result['date']} {task_result.get('time','')}
            Confirm kar Hinglish mein — max 1 sentence. Short aur warm rakh.
            """
        else:
            prompt = f"""
            Today is Wednesday, April 08, 2026. You are {persona.get('persona_name','Anya')}.
            User said: "{user_message}"
            You added to calendar and tasks: {task_result['title']} on {task_result['date']} {task_result.get('time','')}
            Confirm warmly — max 1 sentence. Keep it short.
            """

        reply = generate(prompt).strip()
        store_conversation(session_id, user_message, reply, "task_created")

        return {
            "persona": persona.get('persona_name'),
            "response": reply,
            "flag": "task_created",
            "task": task_result
        }

    return chat(user_message, session_id)

if __name__ == "__main__":
    opening = start_session()
    print(f"🎭 {opening['persona']}: {opening['opening_message']}\n")

    tests = [
        "I feel overwhelmed today",
        "yaar bahut stressed hoon aajkal",
        "kya karu samajh nahi aa raha"
    ]

    for msg in tests:
        print(f"👤 User: {msg}")
        result = chat(msg)
        print(f"🎭 {result['persona']}: {result['response']}\n")