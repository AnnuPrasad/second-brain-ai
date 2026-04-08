import sys
sys.path.insert(0, "/app")
from agents.gemini_client import generate
from database.firestore_db import store_memory, get_memory
import json

PERSONA_QUESTIONS = [
    {"id": "q1", "question": "When you're stressed, what kind of support helps most?",
     "options": ["A) Someone who listens without judging","B) Someone who gives practical solutions","C) Someone who makes me laugh","D) Someone who just sits with me quietly"]},
    {"id": "q2", "question": "How do you prefer someone to talk to you?",
     "options": ["A) Warm and emotional like a close friend","B) Calm and logical like a mentor","C) Casual and chill like a peer","D) Direct and honest even if it stings"]},
    {"id": "q3", "question": "When you share a problem, what do you want first?",
     "options": ["A) To be heard and validated","B) Immediate solutions","C) Someone to share the burden","D) Honest feedback"]},
    {"id": "q4", "question": "What kind of person do you open up to most easily?",
     "options": ["A) A nurturing older figure","B) A wise mentor","C) A fun peer your age","D) A no-nonsense straight talker"]},
    {"id": "q5", "question": "When things get hard, what message helps you most?",
     "options": ["A) You are not alone in this","B) Here is exactly what you should do","C) Let us figure this out together","D) You are stronger than you think"]}
]

def build_persona(answers: dict):
    answers_text = "\n".join([
        f"Q: {PERSONA_QUESTIONS[i]['question']}\nA: {answers.get(f'q{i+1}', 'not answered')}"
        for i in range(len(PERSONA_QUESTIONS))
    ])

    prompt = f"""
    Based on these answers build a comfort persona profile:
    {answers_text}

    Return ONLY valid JSON:
    {{
        "persona_name": "warm name like Maya Arjun Alex",
        "persona_type": "nurturer/mentor/peer/straight_talker",
        "communication_style": "detailed description",
        "tone": "warm/calm/casual/direct",
        "opening_style": "how this persona starts conversations",
        "empathy_style": "how this persona shows empathy",
        "advice_style": "how this persona gives advice",
        "example_response": "example response to I am feeling overwhelmed today",
        "avoid": "what this persona never does"
    }}
    """

    text = generate(prompt).strip().replace("```json","").replace("```","").strip()
    try:
        persona = json.loads(text)
    except:
        persona = {"raw": text}

    store_memory("personas", "user_persona", persona)
    return persona

def get_user_persona():
    persona = get_memory("personas", "user_persona")
    if persona:
        return persona
    return {
        "persona_name": "Anya",
        "persona_type": "nurturer",
        "tone": "warm",
        "communication_style": "Warm empathetic non-judgmental friend who listens first",
        "example_response": "I hear you. That sounds really tough. Want to tell me more?"
    }

def get_persona_questions():
    return PERSONA_QUESTIONS

if __name__ == "__main__":
    sample_answers = {"q1": "A","q2": "A","q3": "A","q4": "A","q5": "A"}
    persona = build_persona(sample_answers)
    print(f"🎭 Persona: {persona.get('persona_name')}")
    print(f"💬 Example: {persona.get('example_response')}")