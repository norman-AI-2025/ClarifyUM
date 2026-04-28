🎓 ClarifyUM

The Ultimate Academic Dashboard for Universiti Malaya Students.

ClarifyUM is a modern, unified academic portal that bridges the gap between Universiti Malaya's SPeCTRUM (Moodle) learning system and a clean, highly functional user interface. It automates course material retrieval, tracks upcoming tasks, and provides an integrated AI assistant powered by Gemini 2.5 Flash to help you navigate your curriculum seamlessly.

✨ Key Features

⚡ Automated SPeCTRUM Sync: A built-in Selenium web scraper securely logs into your SPeCTRUM account, fetches your enrolled modules, and downloads the latest course structures, assignments, and attendance links.

🧠 ClarifyAI Smart Search: Chat with your curriculum! Using the Gemini API, the AI reads your scraped course materials, syllabi, and upcoming tasks to answer specific questions (e.g., "What assignments are due next week?") in beautifully formatted Markdown.

📅 Live Timetable & "Up Next": Upload a screenshot of your schedule. The backend uses OCR to parse it into a live dashboard widget, calculating your current and next classes in real-time.

📝 Delta Sync & AI Summaries: To save API costs, the scraper uses Delta Sync to only summarize new content. Gemini automatically converts raw course JSON data into highly readable Markdown summaries.

🍏 Apple-Inspired Glass UI: A stunning frontend built with pure HTML, vanilla JavaScript, and Tailwind CSS, featuring a responsive macOS-style frosted glass aesthetic.

🛠️ Tech Stack

Frontend: HTML5, Vanilla JavaScript, Tailwind CSS

Backend: Python, FastAPI, Uvicorn

Automation: Selenium WebDriver

Artificial Intelligence: Google GenAI SDK (Gemini 2.5 Flash)

🚀 Installation & Setup

1. Clone the Repository

git clone [https://github.com/yourusername/clarifyum.git](https://github.com/yourusername/clarifyum.git)
cd clarifyum


2. Set Up the Virtual Environment

It is highly recommended to use a virtual environment to isolate project dependencies.

# Create the virtual environment
python3 -m venv venv

# Activate it (Mac/Linux)
source venv/bin/activate
# Activate it (Windows)
# .\venv\Scripts\activate


3. Install Dependencies

pip install fastapi uvicorn google-genai python-dotenv selenium


4. Configure Environment Variables

Create a .env file in the root directory. Do not push this file to GitHub!

SPECTRUM_USERNAME="your_matric_id@siswa.um.edu.my"
SPECTRUM_PASSWORD="your_actual_password"
GEMINI_API_KEY="your_gemini_api_key"


💻 Usage

Step 1: Start the FastAPI Backend

Ensure your virtual environment is active, then run:

python server.py


The backend will run on http://localhost:8000.

Step 2: Launch the Frontend

To prevent extensions like VS Code Live Server from aggressively refreshing the page when background Python scripts save data, use Python's built-in HTTP server.

Open a new terminal window in the project directory and run:

python3 -m http.server 5500


Navigate to http://localhost:5500/dashboard.html in your browser.

📁 Project Structure

ClarifyUM/
├── server.py                # FastAPI backend & endpoints
├── main.py / run_pipeline.py# Scraper pipeline execution
├── query_ai.py              # Gemini AI chat logic
├── time_manager.py          # Timetable calculations
├── summarize_courses.py     # Gemini JSON-to-Markdown generator
├── scraper/                 # Selenium automation scripts
│   ├── session.py           # SPeCTRUM Login
│   ├── dashboard.py         # Course enumeration
│   └── course.py            # Deep-dive module extraction
├── data/                    # User timetable and 'Up Next' data
├── courses/                 # Raw JSON and generated Markdown summaries
├── dashboard.html           # Main academic overview UI
├── course_hub.html          # Grid view of all enrolled modules
├── course_detail.html       # Interactive accordion syllabus view
└── ai_chat.html             # Smart Search interactive UI


🔒 Security Note

This project handles sensitive university credentials. Ensure your .env and venv/ directories are explicitly listed in your .gitignore file before making any commits.
