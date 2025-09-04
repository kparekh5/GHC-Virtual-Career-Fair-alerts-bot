import os
import smtplib
import glob
from email.mime.text import MIMEText

# --- CONFIGURATION ---
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")
RECEIVER_EMAIL_STRING = os.environ.get("RECEIVER_EMAIL")

ARTIFACTS_DIR = "artifacts"
ALERT_LOG_FILE = "sent_alerts.log"

# --- SCRIPT ---

def send_email_alert(subject, body, to_emails_string):
    """Sends one email to a comma-separated list of recipients."""
    if not all([SENDER_EMAIL, SENDER_PASSWORD, to_emails_string]):
        print("ERROR: Email credentials are not fully configured. Cannot send email.")
        return

    recipients = [email.strip() for email in to_emails_string.split(',')]
    print(f"Attempting to send email alert to: {recipients}")
    
    msg = MIMEText(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_emails_string  # The 'To' header shows the full list

    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp_server:
            smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp_server.sendmail(SENDER_EMAIL, recipients, msg.as_string())
        print("Email alert sent successfully!")
    except Exception as e:
        print(f"Failed to send email. Error: {e}")

def load_sent_alerts():
    """Loads URLs for which alerts have already been sent."""
    if not os.path.exists(ALERT_LOG_FILE):
        return set()
    with open(ALERT_LOG_FILE, 'r') as f:
        return set(line.strip() for line in f)

def save_new_alerts(urls):
    """Appends newly alerted URLs to the log file."""
    with open(ALERT_LOG_FILE, 'a') as f:
        for url in urls:
            f.write(f"{url}\n")

if __name__ == "__main__":
    print("--- Consolidating Results and Reporting ---")
    
    all_active_urls = set()
    artifact_files = glob.glob(os.path.join(ARTIFACTS_DIR, '*.txt'))

    if not artifact_files:
        print("No artifact files found. Nothing to report.")
    else:
        print(f"Found {len(artifact_files)} artifact files to process.")
        for file_path in artifact_files:
            with open(file_path, 'r') as f:
                for line in f:
                    all_active_urls.add(line.strip())

    if not all_active_urls:
        print("No active URLs were found in any checker job.")
        print("--- Reporter Run Complete ---")
        exit(0)

    print(f"Found a total of {len(all_active_urls)} unique active URLs across all checkers.")
    
    previously_sent_alerts = load_sent_alerts()
    newly_active_urls = sorted(list(all_active_urls - previously_sent_alerts))

    if not newly_active_urls:
        print("No new alerts to send. All active URLs have been reported previously.")
    else:
        print(f"Found {len(newly_active_urls)} new URLs to alert:")
        for url in newly_active_urls:
            print(f"- {url}")

        # Send the consolidated email
        email_subject = f"ACTION REQUIRED: {len(newly_active_urls)} Meeting Slot(s) Open at AnitaB Fair!"
        links_text = "\n\n".join(newly_active_urls)
        email_body = f"The 'Request meeting' button is now ACTIVE for the following opportunities:\n\n{links_text}"
        
        send_email_alert(email_subject, email_body, RECEIVER_EMAIL_STRING)
        
        # Log the newly sent alerts to prevent future duplicates
        save_new_alerts(newly_active_urls)
        print("Updated sent_alerts.log with new URLs.")

    print("--- Reporter Run Complete ---")
