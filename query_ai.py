import os
import json
import glob
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Setup Environment and Client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.5-flash"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def load_all_course_data():
    """Reads course, timetable, and tasks data into a single knowledge base."""
    course_files = glob.glob(os.path.join(BASE_DIR, 'courses', '*.json'))
    knowledge_base = []
    
    for f in course_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                knowledge_base.append(json.load(file))
        except Exception:
            pass
            
    # Load Timetable
    timetable_data = {}
    timetable_path = os.path.join(BASE_DIR, "data", "timetable.json") 
    if os.path.exists(timetable_path):
        with open(timetable_path, 'r', encoding='utf-8') as f:
            timetable_data = json.load(f)

    # Load Upcoming Tasks
    tasks_data = []
    tasks_path = os.path.join(BASE_DIR, "upcoming_tasks.json") 
    if os.path.exists(tasks_path):
        with open(tasks_path, 'r', encoding='utf-8') as f:
            tasks_data = json.load(f)
            
    return {
        "course_content": knowledge_base,
        "my_schedule": timetable_data,
        "upcoming_tasks": tasks_data
    }

def run_ai_query(user_prompt):
    """Sends the prompt to Gemini and enforces a beautiful Markdown response."""
    data = load_all_course_data()
    
    # We removed response_mime_type="application/json" so Gemini can just speak naturally!
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are 'ClarifyAI', a helpful academic assistant for a student at Universiti Malaya. "
            "Use the provided scraped SPeCTRUM JSON data to answer the student's questions accurately. "
            "Always format your response cleanly using Markdown (use bold text, line breaks, and neat bullet points). "
            "If summarizing assignments or tasks, list the due dates clearly and embed the URL as a clickable Markdown link."
            "DO NOT wrap your response in JSON formatting. Just return the pure Markdown text."
        )
    )

    prompt = f"""
    Context Data:
    {json.dumps(data)}

    User Query: {user_prompt}
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=config
        )
        
        # We manually wrap the clean Markdown text into the summary dictionary
        return {"summary": response.text}

    except Exception as e:
        print(f"[!] Error contacting Gemini: {e}")
        return {"summary": "**System Error:** I encountered an issue connecting to the AI. Please check your terminal."}