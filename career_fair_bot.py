import os
import smtplib
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
    # Add your other 15-20 URLs here. For example:
    # "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/ANOTHER_ID",
]

# Email configuration will be read from environment variables for security.
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")  # Should be a Gmail App Password
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

ALERT_LOG_FILE = "sent_alerts.log"
WAIT_TIMEOUT = 25 # Increased timeout for reliability on slow pages


# --- SCRIPT ---

def send_email_alert(subject, body, to_email):
    """
    Sends an email alert using a Gmail account.
    """
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
    """Reads the log file to see which URLs have already been alerted."""
    if not os.path.exists(ALERT_LOG_FILE):
        return set()
    with open(ALERT_LOG_FILE, 'r') as f:
        return set(line.strip() for line in f)


def save_sent_alert(url):
    """Adds a URL to the log file to prevent re-alerting."""
    with open(ALERT_LOG_FILE, 'a') as f:
        f.write(f"{url}\n")


def check_button_status(driver, url):
    """
    Uses an existing Selenium driver to check a single URL.
    """
    print(f"\n--- Checking URL: {url} ---")
    button_is_active = False
    try:
        driver.get(url)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        print("Page loaded. Searching for the primary action button...")
        
        # --- NEW: Using a more stable CSS Selector ---
        # This looks for a button with a 'data-testid' attribute, which is more reliable than text.
        button_selector = "button[data-testid='exhibitor-primary-action-button']"
        meeting_button = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, button_selector)))

        print("Button found. Checking its status...")

        if meeting_button.is_enabled():
            print("✅ SUCCESS: The 'Request meeting' button is now ACTIVE!")
            button_is_active = True
        else:
            print("❌ STATUS: The button is present, but still disabled (greyed out).")

    except TimeoutException:
        print("ERROR: Timed out waiting for the button to appear. The selector might be wrong or the page didn't load correctly.")
        print("Saving debug files: debug_screenshot.png and debug_page_source.html")
        # --- NEW: Save debugging files on failure ---
        driver.save_screenshot('debug_screenshot.png')
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    return button_is_active


if __name__ == "__main__":
    print(f"[{time.ctime()}] --- AnitaB.org Career Fair Bot (Multi-URL Run) ---")

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

            is_active = check_button_status(driver, url)

            if is_active:
                email_subject = f"ACTION REQUIRED: Meeting Slot Open at AnitaB Fair!"
                email_body = f"The 'Request meeting' button is now ACTIVE for a company you are tracking.\n\nGo here now: {url}"
                send_email_alert(email_subject, email_body, RECEIVER_EMAIL)
                save_sent_alert(url)
                print(f"Logged {url} to prevent re-alerting.")

    except Exception as e:
        print(f"\n--- A critical error occurred during the main process ---")
        print(f"Error: {e}")
    finally:
        if driver:
            print("\nClosing browser session.")
            driver.quit()

    print("\n--- Run Complete ---")

