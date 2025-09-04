import os
import smtplib
import time
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# --- CONFIGURATION ---
# Add all the URLs you want to monitor in this list.
URLS_TO_CHECK = [
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1720020857770001nrcJ",
    # Add your other 15-20 URLs here. For example:
    # "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/ANOTHER_ID",
    # "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/YET_ANOTHER_ID",
]

# Email configuration will be read from environment variables for security.
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD") # Should be a Gmail App Password
RECEIVER_EMAIL = os.environ.get("RECEIVER_EMAIL")

ALERT_LOG_FILE = "sent_alerts.log"

# --- SCRIPT ---

def send_email_alert(subject, body, to_email):
    """
    Sends an email alert using a Gmail account.
    """
    if not all([SENDER_EMAIL, SENDER_PASSWORD, to_email]):
        print("ERROR: Email credentials are not fully configured. Cannot send email.")
        print("Please set SENDER_EMAIL, SENDER_PASSWORD, and RECEIVER_EMAIL environment variables.")
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
        wait = WebDriverWait(driver, 20)
        
        print("Page loaded. Searching for the 'Request meeting' button...")
        
        button_xpath = "//button[contains(., 'Request meeting')]"
        meeting_button = wait.until(EC.presence_of_element_located((By.XPATH, button_xpath)))
        
        print("Button found. Checking its status...")

        if meeting_button.is_enabled():
            print("✅ SUCCESS: The 'Request meeting' button is now ACTIVE!")
            button_is_active = True
        else:
            print("❌ STATUS: The button is still disabled (greyed out).")

    except TimeoutException:
        print("ERROR: Timed out waiting for the button to appear.")
    except NoSuchElementException:
        print("ERROR: Could not find the button on the page.")
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
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = None
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        for url in URLS_TO_CHECK:
            if url in sent_alerts:
                print(f"\nSkipping {url} (alert already sent).")
                continue

            is_active = check_button_status(driver, url)

            if is_active:
                company_name = url.split('/')[-1] # Simple way to get a unique identifier
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

