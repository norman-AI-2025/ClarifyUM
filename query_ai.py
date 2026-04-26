import os
import json
import glob
from google import genai
from google.genai import types
from dotenv import load_dotenv

# 1. Setup Environment and Client
load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_ID = "gemini-2.5-flash"

# Inside query_ai.py, update load_all_course_data()

def load_all_course_data():
    """Reads course and timetable data into a single knowledge base."""
    course_files = glob.glob('courses/*.json')
    knowledge_base = []
    
    for f in course_files:
        try:
            with open(f, 'r', encoding='utf-8') as file:
                knowledge_base.append(json.load(file))
        except Exception as e:
            print(f"  [!] Skipping {f}: {e}")
            
    # FIXED: Continue to load timetable before returning
    timetable_data = {}
    timetable_path = os.path.join("backend", "data", "timetable.json") 
    if os.path.exists(timetable_path):
        with open(timetable_path, 'r') as f:
            timetable_data = json.load(f)
            
    return {
        "course_content": knowledge_base,
        "my_schedule": timetable_data
    }
def run_ai_query(user_prompt):
    """Sends the prompt and course data to Gemini and saves the result to a JSON file."""
    
    data = load_all_course_data()
    
    if not data:
        print("[!] No course data found. Please run main.py to scrape SPeCTRUM first.")
        return

    # 2. Configure AI for strict JSON output
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are a student assistant for Universiti Malaya. Use the provided SPeCTRUM data "
            "to answer queries. You MUST respond in valid JSON format only."
        ),
        response_mime_type="application/json"
    )

    # 3. Create the contextual prompt
    prompt = f"""
    Context (My Scraped Course Data):
    {json.dumps(data)}

    Question: {user_prompt}

    Output Requirement:
    - If asking about assignments: Return a list of objects with 'course', 'title', 'due_date', and 'url'.
    - If asking a general summary: Return a single object with a 'summary' key.
    - Do not include conversational text, only the JSON.
    """

    try:
        response = client.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=config
        )
        
        # 4. Save response to the output file
        result = json.loads(response.text)
        with open("ai_query_output.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=4)
            
        print("\n[+] AI response written to ai_query_output.json")
        return result

    except Exception as e:
        print(f"[!] Error contacting Gemini: {e}")
        return None

# 5. The Independent Interactive Loop
if __name__ == "__main__":
    print("--- ClarifyUM AI Query Engine ---")
    print("Ask about your UM courses (e.g., 'What assignments are due?')")
    print("Type 'exit' to quit.\n")

    while True:
        query = input("Enter Query > ").strip()
        
        if query.lower() in ['exit', 'quit', 'q']:
            print("Closing Query Engine.")
            break
            
        if not query:
            continue
            
        print("[*] Consulting Gemini...")
        run_ai_query(query)
        print("-" * 35)