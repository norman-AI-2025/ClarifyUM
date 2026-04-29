from bs4 import BeautifulSoup
import time
import re

# Your known course IDs
KNOWN_COURSES = ['22232', '23372', '146', '126', '147', '23527', '26925']

def get_upcoming_tasks(driver) -> list:
    """
    Navigates to the SPeCTRUM Timeline and aggressively scrapes tasks using Regex and structural DOM parsing.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    print("[*] Navigating to Dashboard to fetch Timeline events...")
    driver.get("https://spectrum.um.edu.my/my/")

    # Give the Timeline block time to load its AJAX content
    time.sleep(3)
    
    # Scroll down to ensure all tasks lazy-load into the DOM
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    tasks = []

    # Find every event container box
    event_items = soup.select('[data-region="event-list-item"], .list-group-item.event-list-item')

    for item in event_items:
        # 1. TITLE & URL (Bulletproof Link Extraction)
        # Grab all anchor tags in the box that actually have text
        valid_links = [a for a in item.find_all('a', href=True) if a.get_text(strip=True)]
        if not valid_links:
            continue
        
        # The first valid link is almost always the assignment title
        title_el = valid_links[0]
        title = title_el.get_text(strip=True)
        url = title_el['href']

        # Clean the title of generic Moodle text (e.g., "is due")
        title = re.sub(r'\s+is due.*', '', title, flags=re.IGNORECASE).strip()

        # 2. COURSE NAME
        # The second link is usually the course name. If there's only 1 link, check the muted text.
        course_name = "General Course"
        if len(valid_links) > 1:
            course_name = valid_links[1].get_text(strip=True)
        else:
            muted = item.select_one('.text-muted, small')
            if muted:
                course_name = muted.get_text(strip=True)

        # 3. DUE TIME (Regex Hunt)
        time_str = ""
        # Look for a time format like '23:59' or '11:59 PM' anywhere in the item's text
        time_match = re.search(r'\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?', item.get_text(separator=' '))
        if time_match:
            time_str = time_match.group()

        # 4. DUE DATE (DOM Tree Climbing)
        date_str = ""
        # Method A: Look at the parent date grouping container
        date_container = item.find_parent(attrs={'data-region': 'event-list-content-date'})
        if date_container:
            header = date_container.find(['h4', 'h5', 'h6'])
            if header:
                date_str = header.get_text(strip=True)
        
        # Method B: If no parent container, crawl backwards up the page for the closest heading
        if not date_str:
            prev_header = item.find_previous(['h4', 'h5', 'h6'])
            if prev_header:
                date_str = prev_header.get_text(strip=True)

        # Cleanly combine date and time
        due_date = f"{date_str} {time_str}".strip()
        if not due_date:
            due_date = "Upcoming (Date unspecified)"

        tasks.append({
            'title': title,
            'course': course_name,
            'due_date': due_date,
            'due_time': due_date,  # Kept for backwards compatibility with main.py alerts
            'url': url
        })

    # Remove duplicates
    unique_tasks = []
    seen = set()
    for t in tasks:
        if t['title'] == "Unknown Task":
            continue
            
        ident = f"{t['title']}_{t['course']}"
        if ident not in seen:
            seen.add(ident)
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