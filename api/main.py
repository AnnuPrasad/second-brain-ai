from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from agents.coordinator import ask
from agents.mindmate.mood_agent import analyze_mood_pattern, log_mood
from agents.mindmate.signal_agent import run_full_signal_scan, analyze_email_signals, analyze_calendar_signals
from agents.mindmate.persona_agent import build_persona, get_user_persona, get_persona_questions
from agents.mindmate.therapy_agent import chat_with_task_detection, start_session
from agents.task_agent import process_task_with_google
from database.firestore_db import load_sample_data, get_all_memories
from sources.gmail_source import fetch_emails
from sources.calendar_source import fetch_calendar_events
from sources.tasks_source import fetch_tasks, create_google_task, complete_task

app = FastAPI(title="Second Brain AI", version="1.0")

# ── Models ──
class Question(BaseModel):
    question: str

class MoodEntry(BaseModel):
    mood: str
    score: int
    note: str

class PersonaAnswers(BaseModel):
    q1: str
    q2: str
    q3: str
    q4: str
    q5: str

class ChatMessage(BaseModel):
    message: str
    session_id: str = "default"

class TaskMessage(BaseModel):
    message: str

class GoogleTask(BaseModel):
    title: str
    due_date: str = None
    notes: str = ""

# ── Core ──
@app.get("/")
def home():
    return RedirectResponse(url="/login")

@app.post("/ask")
def ask_question(q: Question):
    answer = ask(q.question)
    return {"question": q.question, "answer": answer}

@app.get("/memories/{collection}")
def get_memories(collection: str):
    memories = get_all_memories(collection)
    return {"collection": collection, "data": memories}

@app.post("/load-sample-data")
def load_data():
    load_sample_data()
    return {"message": "Sample data loaded successfully"}

# ── Mood ──
@app.get("/mood/analysis")
def mood_analysis():
    return analyze_mood_pattern()

@app.post("/mood/log")
def log_mood_entry(entry: MoodEntry):
    result = log_mood(entry.mood, entry.score, entry.note)
    return {"message": "Mood logged successfully", "entry": result}

# ── Signals ──
@app.get("/signals/scan")
def full_signal_scan():
    return run_full_signal_scan()

@app.get("/signals/emails")
def email_signals():
    return analyze_email_signals()

@app.get("/signals/calendar")
def calendar_signals():
    return analyze_calendar_signals()

# ── Persona ──
@app.get("/persona/questions")
def persona_questions():
    return {"questions": get_persona_questions()}

@app.post("/persona/build")
def create_persona(answers: PersonaAnswers):
    persona = build_persona(answers.dict())
    return {"message": "Persona created!", "persona": persona}

@app.get("/persona/me")
def my_persona():
    return {"persona": get_user_persona()}

# ── Therapy ──
@app.get("/therapy/start")
def therapy_start():
    return start_session()

@app.post("/therapy/chat")
def therapy_chat(msg: ChatMessage):
    return chat_with_task_detection(msg.message, msg.session_id)

@app.get("/therapy/history")
def therapy_history():
    return {"sessions": get_all_memories("therapy_sessions")}

# ── Sync ──
@app.post("/sync/gmail")
def sync_gmail():
    emails = fetch_emails(max_results=10)
    return {"message": f"Synced {len(emails)} emails", "count": len(emails)}

@app.post("/sync/calendar")
def sync_calendar():
    events = fetch_calendar_events(days_ahead=30)
    return {"message": f"Synced {len(events)} events", "count": len(events)}

@app.post("/sync/tasks")
def sync_google_tasks():
    tasks = fetch_tasks()
    return {"message": f"Synced {len(tasks)} tasks", "count": len(tasks)}

# ── Tasks ──
@app.post("/task/create")
def create_task(msg: TaskMessage):
    result = process_task_with_google(msg.message)
    if result:
        return result
    return {"success": False, "message": "No task detected"}

@app.get("/task/list")
def list_tasks():
    tasks = get_all_memories("tasks")
    tasks = sorted(tasks, key=lambda x: x.get("date", ""))
    return {"tasks": tasks}

@app.post("/tasks/create")
def create_gtask(task: GoogleTask):
    result = create_google_task(task.title, task.due_date, task.notes)
    return {"message": "Task created", "task": result}

@app.post("/tasks/complete/{task_id}")
def complete_gtask(task_id: str):
    result = complete_task(task_id)
    return {"message": "Task completed", "task": result}

@app.get("/tasks/google")
def get_google_tasks():
    return {"tasks": get_all_memories("google_tasks")}

# ── Frontend ──
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/ui")
def serve_ui():
    return FileResponse("frontend/index.html")

@app.get("/login")
def serve_login():
    return FileResponse("frontend/login.html")
    
from fastapi.responses import RedirectResponse

@app.get("/home")
def home_redirect():
    return RedirectResponse(url="/login")
