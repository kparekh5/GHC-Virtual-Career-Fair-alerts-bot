import os
import smtplib
import sys
import time
from email.mime.text import MIMEText

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
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
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1712942120293001LSc4",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188687975001PkXb",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1722441485393001ZFzy",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1712944582844001LZAP",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1754886602618001ip4b",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713189549333001dJUV",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713189549413001dSU4",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713361999237001RCeP",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1748405927054001couI",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713912142591001YeKA",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1720020857878001njZu",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1716336263629001WWCH",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188687826001P5dy",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1722441485163001Z0f4",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713189549743001dLGN",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188688172001PAPx",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188688221001PBYL",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1717597285016001U6Os",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1754493196793001TMGt",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188688480001Pktf",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188688528001PZX4",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1749533408322001SdGx",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1747784539000001oRmx",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1748405927235001cDQn",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1721836626068001VVzc",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188689116001PesZ",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713361999456001Re3O",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1750881473389001gMnU",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188689461001PWIM",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1719414268768001c7dq",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713189550555001dQJZ",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713189550644001dUTp",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713189550720001dUQC",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713188690247001Pw4B",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1714576726611001G3IM",
    "https://gracehoppercelebration.com/flow/anitab/vcf25/attendeeportal/page/exhibitor-catalog/exhibitor/1713189550799001dCWs"
    
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
    Checks a single URL for the "No available meetings" text.
    If the text is missing, the button is considered active.
    Returns "active", "disabled", or "error".
    """
    print(f"\n--- Checking URL: {url} ---")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, WAIT_TIMEOUT)

        # Handle Cookie Consent Banner
        try:
            print("Looking for cookie consent banner...")
            cookie_dismiss_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".cc-btn.cc-dismiss")))
            cookie_dismiss_button.click()
            print("Cookie banner dismissed.")
        except TimeoutException:
            print("Cookie banner not found, continuing...")
        except Exception as e:
            print(f"Could not dismiss cookie banner: {e}")

        # --- MORE RELIABLE LOGIC ---
        # Instead of checking the button, we check for the text that says meetings are unavailable.
        # Its absence is our signal that the button is active.
        print("Searching for 'No available meetings...' text...")
        no_meetings_text_selector = "//p[contains(text(),'No available meetings at this time.')]"
        
        try:
            # Use a short, 5-second timeout here. If the text exists, we'll find it quickly.
            WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, no_meetings_text_selector)))
            
            # If the line above succeeds, the text was found, so meetings are unavailable.
            print("❌ STATUS: 'No available meetings' text is present. Button is inactive.")
            return "disabled"
            
        except TimeoutException:
            # If we time out looking for the text, it means it's GONE, which is our success condition!
            print("✅ SUCCESS: 'No available meetings' text is NOT present. Button is likely ACTIVE!")
            return "active"

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        # Save debug files for any unexpected errors
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

        # After checking all URLs, send one consolidated email if any are active
        if newly_active_urls:
            print(f"\nFound {len(newly_active_urls)} newly active meeting opportunities.")
            email_subject = f"ACTION REQUIRED: {len(newly_active_urls)} Meeting Slot(s) Open at AnitaB Fair!"
            
            links_text = "\n\n".join(newly_active_urls)
            email_body = f"The 'Request meeting' button is now ACTIVE for the following opportunities:\n\n{links_text}"
            
            send_email_alert(email_subject, email_body, RECEIVER_EMAIL)
            
            # Log all newly sent alerts
            for url in newly_active_urls:
                save_sent_alert(url)
                print(f"Logged {url} to prevent re-alerting.")

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

