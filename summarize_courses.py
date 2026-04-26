import os
import json
import glob
import google.generativeai as genai
from dotenv import load_dotenv

# 1. Load environment variables and configure Gemini
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("[!] GEMINI_API_KEY not found in .env file. Please add it.")

# Configure the API
genai.configure(api_key=GEMINI_API_KEY)

# Using gemini-1.5-flash: It is blazing fast and has a massive 1-million token 
# context window, which is perfect for dumping entire JSON structures into.
model = genai.GenerativeModel('gemini-2.5-flash')

def summarize_course(filepath):
    print(f"[*] Analyzing {filepath}...")
    
    # Read the scraped JSON data
    with open(filepath, 'r', encoding='utf-8') as f:
        course_data = json.load(f)

    course_name = course_data.get('course_name', 'Unknown Course')
    content = course_data.get('content', [])

    if not content:
        print(f"  [~] No content found in {course_name}. Skipping.")
        return

    # 2. Craft the Prompt for Gemini
    # We instruct Gemini to act as an academic assistant and parse the JSON.
    prompt = f"""
    You are a highly organized academic assistant. I am providing you with the raw JSON 
    data scraped from a university course on Moodle (SPeCTRUM). 

    Course Name: {course_name}
    
    Here is the JSON data representing the course structure:
    {json.dumps(content, indent=2)}

    Please analyze this data and generate a clean, highly readable Markdown report. 
    Format your response with the following sections:

    # 📢 Announcements
    List any items labeled as announcements or news forums.

    # 📝 Assignments & Quizzes
    Identify any assignments, quizzes, or submissions. Look for types like 'assign', 'quiz', 
    or keywords in the title. If a date is mentioned in the title, highlight it. Include the 
    URL so I can easily click it.

    # 📚 Course Materials (Week by Week)
    Provide a summary of the study materials (PDFs, slides, links, videos) grouped by 
    their section (which usually represents the week or topic). Go from the first section 
    up to the most recent. Keep it concise but ensure I know exactly what materials are available.
    """

    try:
        # 3. Call the Gemini API
        response = model.generate_content(prompt)
        
        # 4. Save the generated Markdown report
        output_filename = filepath.replace('.json', '_summary.md')
        with open(output_filename, 'w', encoding='utf-8') as f:
            f.write(f"# Course Summary: {course_name}\n\n")
            f.write(response.text)
            
        print(f"  [+] Saved summary -> {output_filename}")

    except Exception as e:
        print(f"  [!] Failed to summarize {course_name}: {e}")


def main():
    # Find all JSON files in the 'courses' directory
    course_files = glob.glob('courses/*.json')
    
    if not course_files:
        print("[!] No JSON files found in the 'courses/' directory. Run your scraper first!")
        return

    print(f"[*] Found {len(course_files)} course files. Booting up Gemini...")
    
    # Process each file
    for file in course_files:
        summarize_course(file)
        
    print("\n[+] All courses summarized successfully!")

if __name__ == "__main__":
    main()