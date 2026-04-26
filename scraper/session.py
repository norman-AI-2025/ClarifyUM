import os
import time
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import logging

logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('WDM').setLevel(logging.ERROR)

load_dotenv()

def get_authenticated_driver():
    """
    Logs in to UM SPeCTRUM via Azure AD and returns a live, authenticated 
    Selenium WebDriver instance.
    """
    username = os.getenv('UM_USERNAME', '').strip()
    password = os.getenv('UM_PASSWORD', '').strip()

    if not username or not password:
        raise ValueError("[!] No credentials found in .env")

    opts = Options()
    #opts.add_argument('--headless')
    opts.add_argument('--no-sandbox')
    opts.add_argument('--disable-dev-shm-usage')
    opts.add_argument('--window-size=1920,1080')
    opts.add_argument('--disable-blink-features=AutomationControlled')
    opts.add_experimental_option('excludeSwitches', ['enable-automation'])
    opts.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    driver.set_page_load_timeout(30)
    wait = WebDriverWait(driver, 15)

    print("[*] Navigating to SPeCTRUM login page...")
    driver.get('https://spectrum.um.edu.my/login/index.php')

    # Step 1: Email
    print("[*] Entering credentials...")
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='email']"))).send_keys(username)
    wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
    time.sleep(1)

    # Step 2: Password
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='password']"))).send_keys(password)
    wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
    time.sleep(2)

    # Step 3: "Stay signed in?" prompt
    try:
        wait.until(EC.element_to_be_clickable((By.ID, "idSIButton9"))).click()
        time.sleep(1)
    except Exception:
        pass

    # Step 4: Wait for Moodle to fully load the user session
    print("[*] Waiting for redirect and Moodle session initialization...")
    wait.until(lambda d: 'spectrum.um.edu.my' in d.current_url)
    
    try:
        # Wait for the user menu, proving we are truly logged in
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".usermenu, #user-menu, [data-region='user-menu'], .userbutton")))
        print("[+] Login successful.")
    except Exception:
        print("[!] Warning: Timed out waiting for Moodle UI. Proceeding anyway.")

    return driver