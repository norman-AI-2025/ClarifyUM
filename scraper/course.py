from bs4 import BeautifulSoup
import re
import time

def get_course_content(driver, course_id: str, course_name: str | None = None) -> dict:
    """
    Navigates the live driver to a specific course page and extracts the content.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    driver.get(f'https://spectrum.um.edu.my/course/view.php?id={course_id}')

    # Wait for the course content to render
    try:
        WebDriverWait(driver, 15).until(
            EC.any_of(
                EC.presence_of_element_located((By.CSS_SELECTOR, '#nav-drawer li[data-key]')),
                EC.presence_of_element_located((By.CSS_SELECTOR, 'li.activity')),
                EC.presence_of_element_located((By.ID, 'region-main')),
            )
        )
    except Exception:
        pass # If it times out, we'll try to parse the raw source anyway

    # Scroll to trigger any lazy-loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1.5)

    # Expand any collapsed sections in the sidebar
    try:
        toggles = driver.find_elements(By.CSS_SELECTOR, '#nav-drawer [aria-expanded="false"]')
        for btn in toggles[:15]: 
            try:
                driver.execute_script("arguments[0].click();", btn)
                time.sleep(0.1)
            except Exception:
                pass
    except Exception:
        pass

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    return _parse_all(soup, course_id, course_name)

def _parse_all(soup: BeautifulSoup, course_id: str, course_name: str | None) -> dict:
    if not course_name:
        for sel in ['h1.page-header-headings', '.page-header h1', 'h1', '.breadcrumb-item:last-child span']:
            el = soup.select_one(sel)
            if el:
                course_name = el.get_text(strip=True)
                break
    course_name = course_name or f'Course {course_id}'

    summary_el = soup.select_one('div.summary, #course-description')
    course_summary = summary_el.get_text(strip=True) if summary_el else ''

    content = _parse_nav_drawer(soup) or _parse_region_main(soup) or _parse_flat_links(soup)

    return {
        'course_id':   course_id,
        'course_name': course_name,
        'summary':     course_summary,
        'content':     content,
    }

# --- Keep all your existing parser helpers exactly as they were ---
_NAV_SKIP_KEYS = {'coursehome', 'participants', 'grades', 'competencies', 'badgesview', 'courseadmin', 'myhome', 'home', 'calendar', 'messages', 'privatefiles', 'currentcourse', 'courses', 'mycourses', 'profile'}

def _parse_nav_drawer(soup: BeautifulSoup) -> list:
    content = []
    drawer = soup.select_one('#nav-drawer, [data-region="drawer"] ul[role="tree"], [data-region="nav-drawer"], .drawer [role="tree"], ul[role="tree"]')
    if not drawer: return content

    section_nodes = drawer.select('[data-node-type="section"]')
    if not section_nodes:
        section_nodes = [li for li in drawer.find_all('li', recursive=True) if li.get('data-key', '').startswith('section') and li.find('ul')]

    if section_nodes:
        for sec in section_nodes:
            section_name = _drawer_text(sec) or 'General'
            for act in sec.select('li[data-node-type="activity"], li[data-key^="cmid-"], li[data-key^="mod-"]'):
                item = _drawer_item(act)
                if item: content.append({**item, 'section': section_name})
    else:
        for li in drawer.find_all('li', recursive=True):
            key = li.get('data-key', '').lower()
            node_type = li.get('data-node-type', '')
            if key in _NAV_SKIP_KEYS: continue
            if node_type not in ('activity', '') and not key.startswith('cmid'): continue
            item = _drawer_item(li)
            if item: content.append({**item, 'section': 'General'})
    return content

def _drawer_text(li) -> str:
    for sel in ['.media-body', 'span.nav-link-text', 'a span', 'a']:
        el = li.select_one(sel)
        if el: return el.get_text(strip=True)
    return ''

def _drawer_item(li) -> dict | None:
    key = li.get('data-key', '').lower()
    if any(key.startswith(s) for s in _NAV_SKIP_KEYS): return None
    name = _drawer_text(li)
    if not name: return None
    link_tag = li.select_one('a[href]')
    url = link_tag['href'] if link_tag else None
    activity_type = 'unknown'
    if url:
        m = re.search(r'/mod/([^/]+)/', url)
        if m: activity_type = m.group(1)
    return {'title': name, 'type': activity_type, 'url': url}

def _parse_region_main(soup: BeautifulSoup) -> list:
    content = []
    sections = soup.select('li.section.main, li[id^="section-"], div.section.main, div[id^="section-"]')
    if not sections:
        for ul in soup.select('ul.topics, ul.weeks'):
            sections = ul.find_all('li', recursive=False)
            if sections: break

    for section in sections:
        name_tag = section.select_one('.sectionname, h3.section-title, h4.section-title, .content .sectionname')
        section_name = name_tag.get_text(strip=True) if name_tag else 'General'

        for activity in section.select('li.activity'):
            activity_type = 'unknown'
            for cls in activity.get('class', []):
                if cls.startswith('modtype_'):
                    activity_type = cls.replace('modtype_', '')
                    break
            name_span = activity.select_one('span.instancename, .activityname')
            if name_span:
                for hidden in name_span.find_all('span', class_='accesshide'): hidden.decompose()
                activity_name = name_span.get_text(strip=True)
            else:
                link = activity.find('a')
                activity_name = link.get_text(strip=True) if link else ''
            link_tag = activity.select_one('a[href]')
            url = link_tag['href'] if link_tag else None
            if activity_name:
                content.append({'title': activity_name, 'type': activity_type, 'section': section_name, 'url': url})
    return content

def _parse_flat_links(soup: BeautifulSoup) -> list:
    content = []
    seen = set()
    root = soup.select_one('#region-main, .course-content, main') or soup
    for a in root.select('a[href*="/mod/"]'):
        href = a['href']
        if href in seen: continue
        seen.add(href)
        name = a.get_text(strip=True)
        if not name: continue
        m = re.search(r'/mod/([^/]+)/', href)
        mod_type = m.group(1) if m else 'unknown'
        content.append({'title': name, 'type': mod_type, 'section': 'General', 'url': href})
    return content