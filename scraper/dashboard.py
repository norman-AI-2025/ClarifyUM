from bs4 import BeautifulSoup
import time

# Your known course IDs
KNOWN_COURSES = ['22232', '23372', '146', '126', '147', '23527', '26925']

def get_upcoming_tasks(driver) -> list:
    """
    Navigates to the SPeCTRUM Timeline 'Sort by dates' view and scrapes tasks.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    # Use the exact link provided for the 'Sort by dates' view
    target_url = "https://spectrum.um.edu.my/my/#view_dates_69edf6aa08b3969edf6aa030e45-1"
    print(f"[*] Navigating to Timeline: {target_url}")
    driver.get(target_url)

    # Wait for the timeline block to load its events
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-region="event-list-item"]'))
        )
    except Exception:
        print("  [~] Timeline events took too long or are empty. Parsing raw source...")

    # Small scroll to trigger lazy-loading
    driver.execute_script("window.scrollTo(0, 500);")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    tasks = []

    # Target the timeline event containers
    event_items = soup.select('[data-region="event-list-item"]')
    
    for item in event_items:
        # Title and URL
        title_el = item.select_one('a[data-action="view-event"]')
        title = title_el.get_text(strip=True) if title_el else "Unknown Task"
        url = title_el.get('href') if title_el else None

        # Deadline time (e.g., 23:59)
        time_el = item.select_one('.text-muted')
        due_time = time_el.get_text(strip=True) if time_el else ""

        # Extract course name from subtext
        course_info = "General"
        info_tags = item.select('.text-muted')
        for tag in info_tags:
            text = tag.get_text(strip=True)
            if "is due -" in text:
                course_info = text.split("-")[-1].strip()
                break

        tasks.append({
            'title': title,
            'due_time': due_time,
            'course': course_info,
            'url': url
        })

    print(f"[+] Scraped {len(tasks)} upcoming task(s) from Timeline.")
    return tasks

def get_enrolled_courses(driver) -> list:
    """
    Navigates to the dashboard and scrapes enrolled courses.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    print("[*] Loading /my/courses.php ...")
    driver.get('https://spectrum.um.edu.my/my/courses.php')

    try:
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-course-id]')),
                EC.presence_of_element_located((By.CSS_SELECTOR, 'a[href*="/course/view.php"]')),
            )
        )
    except Exception:
        pass

    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    courses = []
    seen = set()

    for card in soup.select('[data-course-id]'):
        cid = card.get('data-course-id', '').strip()
        if not cid or cid in seen: continue
        seen.add(cid)
        
        name_el = card.select_one('.multiline, .coursename, .card-title, h4, h3, a')
        name = name_el.get_text(strip=True) if name_el else f'Course {cid}'
        courses.append({'course_id': cid, 'course_name': name})

    found_ids = {c['course_id'] for c in courses}
    for cid in KNOWN_COURSES:
        if cid not in found_ids:
            courses.append({'course_id': cid, 'course_name': f'Course {cid}'})

    return courses