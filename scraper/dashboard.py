from bs4 import BeautifulSoup
import time

# Your known course IDs fallback
KNOWN_COURSES = ['22232', '23372', '146', '126', '147', '23527', '26925']

def get_upcoming_tasks(driver) -> list:
    """
    Navigates to the SPeCTRUM Timeline and aggressively scrapes tasks, deadlines, and URLs.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    print("[*] Navigating to Dashboard to fetch Timeline events...")
    driver.get("https://spectrum.um.edu.my/my/")

    # Scroll down to ensure the timeline widget lazy-loads into the DOM
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    tasks = []

    # Look for the standard Moodle timeline event containers
    event_items = soup.select('.list-group-item[data-region="event-list-item"]')
    if not event_items:
        # Fallback broad selector
        event_items = soup.select('[data-region="event-list-item"]')

    for item in event_items:
        # 1. EXTRACT TITLE & URL
        # Hunt for the anchor tag holding the assignment/quiz link
        title_el = item.select_one('h6.event-name a') or item.select_one('a.aalink') or item.find('a', href=True)
        title = title_el.get_text(strip=True) if title_el else "Unknown Task"
        url = title_el['href'] if title_el else ""

        # Skip blank items that slipped through
        if title == "Unknown Task" or not url:
            continue

        # 2. EXTRACT COURSE NAME
        # The course is usually linked to course/view.php
        course_el = item.select_one('a[href*="course/view.php"]')
        if course_el:
            course_name = course_el.get_text(strip=True)
        else:
            # Fallback to the muted subtext
            muted = item.select_one('small.text-muted')
            course_name = muted.get_text(strip=True) if muted else "General Course"

        # 3. EXTRACT DUE DATE & TIME
        date_str = ""
        # SPeCTRUM groups events by date headers. Check the parent container for the date header.
        parent_group = item.find_parent('div', attrs={'data-region': 'event-list-content-date'})
        if parent_group:
            header = parent_group.select_one('h5, h6')
            if header:
                date_str = header.get_text(strip=True)

        # The specific time is usually aligned to the right inside the item
        time_el = item.select_one('.text-right, .text-md-right, .event-time, .text-muted')
        time_str = time_el.get_text(strip=True) if time_el else ""

        # Cleanly combine them
        due_date = f"{date_str} {time_str}".strip()
        
        # Strip out useless generic text
        due_date = due_date.replace("is due -", "").strip()
        if not due_date or due_date == title:
            due_date = "Upcoming (Date unspecified)"

        tasks.append({
            'title': title,
            'course': course_name,
            'due_date': due_date,
            'due_time': due_date, # Included for backwards compatibility with main.py's ntfy alerts
            'url': url
        })

    # Remove duplicates
    unique_tasks = []
    seen = set()
    for t in tasks:
        identifier = f"{t['title']}_{t['course']}"
        if identifier not in seen:
            seen.add(identifier)
            unique_tasks.append(t)

    print(f"[+] Scraped {len(unique_tasks)} upcoming task(s) from Timeline.")
    return unique_tasks

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