import requests
from bs4 import BeautifulSoup
from twilio.rest import Client
import time
import os
import logging
import json
from dotenv import load_dotenv

load_dotenv()

# Load environment variables
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
YOUR_PHONE_NUMBER = os.getenv("YOUR_PHONE_NUMBER")

# URLs to monitor
URLS = [
    "https://www.mgu.ac.in/exam-category/exam-time-tables/",
    "https://www.mgu.ac.in/exam-category/exam-notifications/",
]

# File to store latest notifications
NOTIFICATIONS_FILE = "latest_notifications.json"

# Keywords to filter notifications
KEYWORDS = ["I semester CBCSS", "II semester CBCSS"]


def load_latest_notifications():
    """Load stored notifications from a JSON file."""
    if os.path.exists(NOTIFICATIONS_FILE):
        try:
            with open(NOTIFICATIONS_FILE, "r") as file:
                return json.load(file)
        except (json.JSONDecodeError, FileNotFoundError):
            logging.error("Error reading notifications file. Resetting storage.")
            return {}
    return {}


def save_latest_notifications(data):
    """Save updated notifications to a JSON file."""
    with open(NOTIFICATIONS_FILE, "w") as file:
        json.dump(data, file)


def send_sms_alert(message):
    """Send an SMS alert using Twilio."""
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message, from_=TWILIO_PHONE_NUMBER, to=YOUR_PHONE_NUMBER
        )
        logging.info("Alert Sent: " + message)
    except Exception as e:
        logging.error(f"Failed to send SMS: {e}")


def fetch_url(url, retries=3, delay=5):
    """Fetch URL content with retry mechanism."""
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logging.error(f"Error fetching {url}, attempt {attempt+1}: {e}")
            time.sleep(delay)
    return None


# Keywords to check in notifications
KEYWORDS = ["I semester CBCSS", "II semester CBCSS", "I Semester BA Multimedia"]


def check_for_updates():
    latest_notifications = load_latest_notifications()

    for url in URLS:
        html = fetch_url(url)
        if html:
            soup = BeautifulSoup(html, "html.parser")

            # Find all <a> tags with class 'read-more'
            notifications = soup.find_all("a", class_="read-more")

            for notification in notifications:
                title = notification.get_text(strip=True)
                link = notification.get("href")

                # Check if any keyword is present in the notification title
                if any(keyword.lower() in title.lower() for keyword in KEYWORDS):
                    if (
                        url not in latest_notifications
                        or latest_notifications[url] != title
                    ):
                        latest_notifications[url] = title
                        message = f"New CBCSS Notification: {title} ({link})"
                        send_sms_alert(message)
                        logging.info("Alert Sent: " + message)

    save_latest_notifications(latest_notifications)


if __name__ == "__main__":
    logging.basicConfig(
        filename="notification_log.txt",
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )
    logging.info("Script started.")

    while True:
        check_for_updates()
        time.sleep(3600)  # Check every hour
