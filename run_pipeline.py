import os
import json
import traceback
from scraper.session import get_authenticated_driver
from scraper.dashboard import get_enrolled_courses, get_upcoming_tasks
from scraper.course import get_course_content
from summarize_courses import summarize_course
from time_manager import get_up_next
from query_ai import run_ai_query
from main import sync_timeline_tasks, check_for_updates

def run_full_sync():
    """
    Step 1 & 6: Auto-scrape everything and handle Delta Sync/Notifications.
    Matches the logic from main.py.
    """
    driver = None
    try:
        print("\n--- Phase 1: Authentication & Timeline Sync ---")
        driver = get_authenticated_driver()

        # Sync Timeline / Upcoming Tasks and send ntfy alerts
        current_tasks = get_upcoming_tasks(driver)
        sync_timeline_tasks(current_tasks)

        print("\n--- Phase 2: Course Scraping & Delta Sync ---")
        enrolled_courses = get_enrolled_courses(driver)
        
        courses_dir = 'courses'
        os.makedirs(courses_dir, exist_ok=True)

        # Save general dashboard data
        with open('dashboard.json', 'w', encoding='utf-8') as f:
            json.dump({'total_courses': len(enrolled_courses), 'courses': enrolled_courses}, f, indent=4)

        for course in enrolled_courses:
            c_name = course['course_name']
            c_id = course['course_id']
            print(f"[*] Processing: {c_name}...")

            # Scrape course content
            details = get_course_content(driver, c_id, c_name)

            safe_name = c_name.replace('/', '_').replace('\\', '_')
            filename = f"{courses_dir}/{c_id}_{safe_name}.json"
            
            # Step 6: Delta Sync check
            has_updates = check_for_updates(filename, details)
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(details, f, indent=4, ensure_ascii=False)
                
            # Step 2: Gemini Summarization if updates found
            if has_updates:
                print(f"  [🧠] New content detected. Generating Markdown summary...")
                summarize_course(filename)

        print("\n[+] Scraping and Summarization complete.")

    except Exception as e:
        print(f"\n[!] Sync Error: {e}")
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

def check_timetable_status():
    """
    Step 4: Manages the Timetable state.
    Provides data for the 'Up Next' feature or helps frontend trigger the + sign.
    """
    print("\n--- Phase 3: Timetable & Live Status ---")
    if not os.path.exists("timetable.json"):
        print("[!] No timetable found. Frontend will display the '+' sign.")
        # Ensure up_next.json is cleared if no timetable exists
        if os.path.exists("up_next.json"):
            os.remove("up_next.json")
    else:
        # Update current/next class status for the dashboard
        get_up_next()

def start_ai_chat():
    """
    Step 5: Entry point for the AI Assistant chat interface.
    """
    print("\n--- Phase 4: AI Assistant (Smart Search) ---")
    print("AI Backend is ready. Frontend can now send queries to run_ai_query().")

if __name__ == "__main__":
    # The complete backend flow
    run_full_sync()         # Scrape, Sync, ntfy, Summarize
    check_timetable_status() # Refresh 'Up Next' status
    start_ai_chat()         # Readiness check for query_ai