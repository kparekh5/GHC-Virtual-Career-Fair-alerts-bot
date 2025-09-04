import os
import sys
import time
from datetime import date

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# --- CONFIGURATION ---
# The URLs will now be passed in as an environment variable from the workflow file.
URLS_TO_CHECK = os.environ.get("URLS_TO_CHECK", "").split()
# The bot will automatically stop running on and after this date.
# Format: YYYY, M, D
STOP_DATE = date(2025, 9, 10)

ALERT_LOG_FILE = "sent_alerts.log"
WAIT_TIMEOUT = 30 # A generous timeout for page loads
# Each parallel job will output its findings to a unique file
OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "active_urls.txt")


# --- SCRIPT ---

def load_sent_alerts():
    if not os.path.exists(ALERT_LOG_FILE):
        return set()
    with open(ALERT_LOG_FILE, 'r') as f:
        return set(line.strip() for line in f)


def check_button_status(driver, url):
    """
    Checks a single URL for the "No available meetings" text.
    Returns "active", "disabled", or "error".
    """
    print(f"\n--- Checking URL: {url} ---")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        # Handle Cookie Consent Banner
        try:
            cookie_dismiss_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cc-btn.cc-dismiss")))
            cookie_dismiss_button.click()
            print("Cookie banner dismissed.")
        except TimeoutException:
            print("Cookie banner not found, continuing...")
        except Exception as e:
            print(f"Could not dismiss cookie banner: {e}")

        # Check for the "No available meetings..." text
        no_meetings_text_selector = "//p[contains(text(),'No available meetings at this time.')]"
        try:
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, no_meetings_text_selector)))
            print("❌ STATUS: 'No available meetings' text is present. Button is inactive.")
            return "disabled"
        except TimeoutException:
            print("✅ SUCCESS: 'No available meetings' text is NOT present. Button is likely ACTIVE!")
            return "active"

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        driver.save_screenshot('debug_screenshot.png')
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        return "error"


if __name__ == "__main__":
    if date.today() >= STOP_DATE:
        print(f"Stop date of {STOP_DATE} has been reached. The bot will no longer run.")
        sys.exit(0)

    print(f"[{time.ctime()}] --- AnitaB.org Career Fair Bot (Parallel Checker) ---")
    
    if not URLS_TO_CHECK:
        print("No URLs provided to check. Exiting.")
        sys.exit(0)

    script_failed = False
    sent_alerts = load_sent_alerts()
    print(f"Loaded {len(sent_alerts)} previously sent alerts.")

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        newly_active_urls = []
        for url in URLS_TO_CHECK:
            if url in sent_alerts:
                print(f"\nSkipping {url} (alert already sent).")
                continue

            status = check_button_status(driver, url)
            if status == "active":
                newly_active_urls.append(url)
            elif status == "error":
                script_failed = True
                print("An error occurred. Halting further checks to generate artifacts.")
                break 

        # Write any found URLs to the output file for the final job to collect
        if newly_active_urls:
            with open(OUTPUT_FILE, 'w') as f:
                for url in newly_active_urls:
                    f.write(f"{url}\n")
            print(f"\nWrote {len(newly_active_urls)} active URLs to {OUTPUT_FILE}")

    except Exception as e:
        print(f"\n--- A critical error occurred ---")
        print(f"Error: {e}")
        script_failed = True
    finally:
        if driver:
            print("\nClosing browser session.")
            driver.quit()

    print("\n--- Checker Run Complete ---")
    
    if script_failed:
        print("\nExiting with error status to trigger artifact upload.")
        sys.exit(1)

