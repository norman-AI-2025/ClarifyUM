import json
import os
import traceback
import requests
from scraper.session import get_authenticated_driver
from scraper.dashboard import get_enrolled_courses, get_upcoming_tasks
from scraper.course import get_course_content

# IMPORT YOUR EXISTING GEMINI PROGRAM
from summarize_courses import summarize_course 

# ==========================================
# ⚙️ NTFY ALERT SETTINGS
# ==========================================
NTFY_TOPIC = "norman_spectrum_alerts_8829"

def send_ntfy_alert(source_name, new_items):
    """Sends a push notification directly to your phone via ntfy.sh."""
    if not NTFY_TOPIC: 
        print("  [!] ntfy topic not set. Skipping alert.")
        return
    
    message = f"🚨 New Assignment in {source_name} 🚨\n\n"
    for item in new_items:
        title = item.get('title', 'Unknown Item')
        course = item.get('course', 'General')
        due = item.get('due_time', 'N/A')
        url = item.get('url', '')
        
        message += f"• {title}\n"
        message += f"  Course: {course}\n"
        message += f"  Due: {due}\n"
        if url:
            message += f"  Link: {url}\n\n"
            
    try:
        response = requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}", 
            data=message.encode('utf-8'),
            headers={
                "Title": f"UM SPeCTRUM Timeline Alert!",
                "Tags": "warning,loudspeaker",
                "Click": "https://spectrum.um.edu.my/" 
            }
        )
        if response.status_code == 200:
            print(f"  [+] ntfy alert sent!")
    except Exception as e:
        print(f"  [!] Failed to connect to ntfy: {e}")

def sync_timeline_tasks(new_tasks):
    """
    Compares current timeline tasks with saved data and alerts on new posts.
    """
    filename = "upcoming_tasks.json"
    
    if not os.path.exists(filename):
        # Initial save, no alerts
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(new_tasks, f, indent=4)
        return

    with open(filename, 'r', encoding='utf-8') as f:
        old_tasks = json.load(f)

    # Identifier based on title and course name
    old_ids = {f"{t['title']}|{t['course']}" for t in old_tasks}
    
    newly_posted = [nt for nt in new_tasks if f"{nt['title']}|{nt['course']}" not in old_ids]

    if newly_posted:
        print(f"  [🔔] TIMELINE UPDATE: {len(newly_posted)} new assignment(s) found!")
        send_ntfy_alert("SPeCTRUM Timeline", newly_posted)
    
    # Update local storage for the frontend
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(new_tasks, f, indent=4)

def check_for_updates(course_filename, new_data):
    """Checks for new items within a specific course."""
    if not os.path.exists(course_filename):
        return True 
        
    try:
        with open(course_filename, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
    except json.JSONDecodeError:
        return True 
        
    old_identifiers = {item.get('url') or item.get('title') for item in old_data.get('content', [])}
    new_items = [item for item in new_data.get('content', []) if (item.get('url') or item.get('title')) not in old_identifiers]
            
    if new_items:
        print(f"  [🔔] COURSE UPDATE: New items in {new_data['course_name']}")
        return True 
    return False


def main():
    driver = None
    try:
        print("[*] Starting browser and authenticating with UM SPeCTRUM...")
        driver = get_authenticated_driver()

        # Phase 1: Sync Timeline / Upcoming Tasks
        print("\n[*] Syncing Timeline / Upcoming Tasks...")
        current_tasks = get_upcoming_tasks(driver)
        sync_timeline_tasks(current_tasks)

        # Phase 2: Sync Enrolled Courses
        print("\n[*] Fetching enrolled courses...")
        enrolled_courses = get_enrolled_courses(driver)

        courses_dir = 'courses'
        os.makedirs(courses_dir, exist_ok=True)

        with open('dashboard.json', 'w', encoding='utf-8') as f:
            json.dump({'total_courses': len(enrolled_courses), 'courses': enrolled_courses}, f, indent=4)

        for i, course in enumerate(enrolled_courses, 1):
            print(f"\n[{i}/{len(enrolled_courses)}] Scraping: {course['course_name']}...")
            details = get_course_content(driver, course['course_id'], course['course_name'])

            safe_name = course['course_name'].replace('/', '_').replace('\\', '_')
            course_filename = f"{courses_dir}/{course['course_id']}_{safe_name}.json"
            
            needs_summary_update = check_for_updates(course_filename, details)
            
            with open(course_filename, 'w', encoding='utf-8') as f:
                json.dump(details, f, indent=4, ensure_ascii=False)
                
            if needs_summary_update:
                print(f"  [🧠] Updates detected. Running Gemini summarizer...")
                summarize_course(course_filename)

        print(f"\n[+] Scraping complete!")

    except Exception as e:
        print(f"\n[!] Fatal error: {e}")
        traceback.print_exc()
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()