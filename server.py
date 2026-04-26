import os
import json
import io
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Setup Environment and GenAI Client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.5-flash" 

# 2. Initialize FastAPI and Folder Paths
app = FastAPI(title="ClarifyUM Backend")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

def get_data_path(filename):
    return os.path.join(DATA_DIR, filename)

# Import local modules
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

# --- ROUTES ---

@app.get("/data/status")
def get_system_status():
    """Checks for file existence in the isolated data folder."""
    return {
        "timetable_exists": os.path.exists(get_data_path("timetable.json")),
        "courses_synced": os.path.exists(get_data_path("dashboard.json"))
    }

@app.post("/timetable/upload")
async def handle_timetable_image(file: UploadFile = File(...)):
    """Processes screenshot and refreshes live status."""
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

        # Save to the isolated data folder
        with open(get_data_path("timetable.json"), "w", encoding='utf-8') as f:
            json.dump(extracted_data, f, indent=4)

        # TRIGGER LIVE STATUS REFRESH IMMEDIATELY
        get_up_next()

        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/data/dashboard")
def get_dashboard_data():
    path = get_data_path("dashboard.json")
    if os.path.exists(path):
        with open(path, "r", encoding='utf-8') as f:
            return json.load(f)
    return {"courses": []}

@app.get("/data/up-next")
def get_live_schedule():
    """Returns the current/next class countdown."""
    return get_up_next()

@app.post("/ai/query")
async def chat_with_gemini(request: Request):
    payload = await request.json()
    return run_ai_query(payload.get("prompt", ""))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)