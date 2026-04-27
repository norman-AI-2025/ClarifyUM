import os
import json
import io
import glob
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.5-flash" 

app = FastAPI(title="ClarifyUM Backend")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
COURSES_DIR = os.path.join(BASE_DIR, "courses")

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(COURSES_DIR, exist_ok=True)

def get_data_path(filename):
    return os.path.join(DATA_DIR, filename)

from run_pipeline import run_full_sync
from query_ai import run_ai_query
from time_manager import get_up_next

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/sync")
def trigger_sync():
    try:
        run_full_sync()
        return {"status": "success", "message": "SPeCTRUM data synced."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/data/status")
def get_system_status():
    course_files = glob.glob(os.path.join(COURSES_DIR, "*.json"))
    return {
        "timetable_exists": os.path.exists(get_data_path("timetable.json")),
        "courses_synced": len(course_files) > 0
    }

@app.post("/timetable/upload")
async def handle_timetable_image(file: UploadFile = File(...)):
    try:
        image_bytes = await file.read()
        prompt = "ACT AS AN OCR ENGINE. Extract classes into JSON: {'classes': [{'course_name': '...', 'day': '...', 'time_start': 'HH:MM', 'time_end': 'HH:MM', 'location': '...'}]}. 24h format."
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=[prompt, types.Part.from_bytes(data=image_bytes, mime_type=file.content_type)],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        raw_text = response.text.replace("```json", "").replace("```", "").strip()
        extracted_data = json.loads(raw_text)
        with open(get_data_path("timetable.json"), "w", encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4)
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/data/dashboard")
def get_dashboard_data():
    courses_list = []
    if os.path.exists(COURSES_DIR):
        for file_path in glob.glob(os.path.join(COURSES_DIR, "*.json")):
            try:
                with open(file_path, "r", encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        courses_list.append({
                            "course_id": data.get("course_id", data.get("id", "Unknown")),
                            "course_name": data.get("course_name", data.get("name", "Unnamed Course"))
                        })
            except Exception as e:
                pass
    return {"courses": courses_list}

@app.get("/data/up-next")
def get_live_schedule():
    return get_up_next()

@app.get("/data/timetable")
def get_timetable_data():
    path = get_data_path("timetable.json")
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    return {"classes": []}

# --- NEW: Get Tasks Route ---
@app.get("/data/tasks")
def get_upcoming_tasks():
    path = os.path.join(BASE_DIR, "upcoming_tasks.json")
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    return []

# --- NEW: Get Specific Course Markdown Route ---
@app.get("/data/course/{course_id}")
def get_course_summary(course_id: str):
    # Find the markdown file that contains this course ID
    md_files = glob.glob(os.path.join(COURSES_DIR, f"*{course_id}*_summary.md"))
    if md_files:
        with open(md_files[0], "r", encoding='utf-8') as f:
            return {"status": "success", "markdown": f.read()}
    return {"status": "error", "message": "Summary file not found for this course."}

@app.post("/ai/query")
async def chat_with_gemini(request: Request):
    payload = await request.json()
    return run_ai_query(payload.get("prompt", ""))

# ... (Keep all your existing routes) ...

@app.get("/data/course_raw/{course_id}")
def get_course_raw(course_id: str):
    """Fetches the raw scraped JSON for a specific course to build the details dashboard."""
    # Find the JSON file that contains this course ID
    json_files = glob.glob(os.path.join(COURSES_DIR, f"*{course_id}*.json"))
    
    # Exclude dashboard.json just in case
    json_files = [f for f in json_files if "dashboard" not in f]
    
    if json_files:
        with open(json_files[0], "r", encoding='utf-8') as f:
            return {"status": "success", "data": json.load(f)}
    return {"status": "error", "message": "Course data not found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

