from google.cloud import firestore
import json
from datetime import datetime

db = firestore.Client(
    project="second-brain-ai-2026",
    database="second-brain-db-26"
)

def store_memory(collection: str, doc_id: str, data: dict):
    data["stored_at"] = datetime.now().isoformat()
    db.collection(collection).document(doc_id).set(data)
    print(f"✅ Stored {doc_id} in {collection}")

def get_memory(collection: str, doc_id: str):
    doc = db.collection(collection).document(doc_id).get()
    if doc.exists:
        return doc.to_dict()
    return None

def get_all_memories(collection: str):
    docs = db.collection(collection).stream()
    return [doc.to_dict() for doc in docs]

def search_memories(collection: str, field: str, value: str):
    docs = db.collection(collection).where(field, "==", value).stream()
    return [doc.to_dict() for doc in docs]

def load_sample_data():
    with open("data/sample_data.json", "r") as f:
        data = json.load(f)
    for email in data["emails"]:
        store_memory("emails", email["id"], email)
    for event in data["calendar"]:
        store_memory("calendar", event["id"], event)
    for note in data["notes"]:
        store_memory("notes", note["id"], note)
    for mood in data["mood_entries"]:
        store_memory("mood_entries", mood["id"], mood)
    print("\n✅ All sample data loaded!")

if __name__ == "__main__":
    load_sample_data()