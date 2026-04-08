from google import genai
import time

client = genai.Client(
    vertexai=True,
    project="second-brain-ai-2026",
    location="us-central1"
)

def generate(prompt: str, retries: int = 3):
    for i in range(retries):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            if "429" in str(e) and i < retries - 1:
                wait = (i + 1) * 15
                print(f"⏳ Rate limit — waiting {wait}s...")
                time.sleep(wait)
            else:
                raise e

def generate_safe(prompt: str, retries: int = 3):
    return generate(prompt, retries)