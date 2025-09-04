import os
import smtplib
import sys
import time
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


# --- CONFIGURATION ---
# Add all the URLs you want to monitor in this list.
URLS_TO_CHECK = [
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1720020857770001nrcJ",
    # Add your other URLs here.
]

# Email configuration will be read from environment variables for security.
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

ALERT_LOG_FILE = "sent_alerts.log"
WAIT_TIMEOUT = 30 # A generous timeout for page loads


# --- SCRIPT ---

def send_email_alert(subject, body, to_email):
    if not all([SENDER_EMAIL, SENDER_PASSWORD, to_email]):
        print("ERROR: Email credentials are not fully configured. Cannot send email.")
        return

    print(f"Attempting to send email alert to {to_email}...")
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp_server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
        print("Email alert sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")


def load_sent_alerts():
    if not os.path.exists(ALERT_LOG_FILE):
        return set()
    with open(ALERT_LOG_FILE, 'r') as f:
        return set(line.strip() for line in f)


def save_sent_alert(url):
    with open(ALERT_LOG_FILE, 'a') as f:
        f.write(f"{url}\n")


def check_button_status(driver, url):
    """
    Checks a single URL for the button status.
    Returns "active", "disabled", or "error".
    """
    print(f"\n--- Checking URL: {url} ---")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        # --- NEW: Handle Cookie Consent Banner ---
        try:
            print("Looking for cookie consent banner...")
            cookie_dismiss_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cc-btn.cc-dismiss")))
            cookie_dismiss_button.click()
            print("Cookie banner dismissed.")
        except TimeoutException:
            print("Cookie banner not found, continuing...")
        except Exception as e:
            print(f"Could not dismiss cookie banner: {e}")

        print("Searching for the primary action button...")
        
        # --- NEW: Using the correct selector based on debug files ---
        # This now looks for an <a> tag with the data-test attribute.
        button_selector = "a[data-test='rf-button']"
        meeting_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, button_selector)))

        print("Button found. Checking its status...")

        if meeting_button.is_enabled():
            print("✅ SUCCESS: The 'Request Meeting' button is now ACTIVE!")
            return "active"
        else:
            print("❌ STATUS: The button is present, but still disabled.")
            return "disabled"

    except TimeoutException:
        print("ERROR: Timed out waiting for the button to appear.")
        print("Saving debug files: debug_screenshot.png and debug_page_source.html")
        driver.save_screenshot('debug_screenshot.png')
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        return "error"

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Also save debug files for unexpected errors
        driver.save_screenshot('debug_screenshot.png')
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        return "error"


if __name__ == "__main__":
    print(f"[{time.ctime()}] --- AnitaB.org Career Fair Bot ---")
    
    script_failed = False
    sent_alerts = load_sent_alerts()
    print(f"Loaded {len(sent_alerts)} previously sent alerts.")

    # --- Initialize Selenium Driver ---
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # --- Anti-bot detection measures ---
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        for url in URLS_TO_CHECK:
            if url in sent_alerts:
                print(f"\nSkipping {url} (alert already sent).")
                continue

            status = check_button_status(driver, url)

            if status == "active":
                email_subject = "ACTION REQUIRED: Meeting Slot Open at AnitaB Fair!"
                email_body = f"The 'Request meeting' button is now ACTIVE for a company you are tracking.\n\nGo here now: {url}"
                send_email_alert(email_subject, email_body, RECEIVER_EMAIL)
                save_sent_alert(url)
                print(f"Logged {url} to prevent re-alerting.")
            elif status == "error":
                script_failed = True
                print("An error occurred. Halting further checks to generate artifacts.")
                break 

    except Exception as e:
        print(f"\n--- A critical error occurred during the main process ---")
        print(f"Error: {e}")
        script_failed = True
    finally:
        if driver:
            print("\nClosing browser session.")
            driver.quit()

    print("\n--- Run Complete ---")
    
    if script_failed:
        print("\nExiting with error status to trigger artifact upload.")
        sys.exit(1)

