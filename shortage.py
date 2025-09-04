import requests
import json
from email.mime.text import MIMEText
import smtplib
import configparser
import logging
import sys
import argparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # Output to stdout for Docker logs
    ]
)
logger = logging.getLogger(__name__)

# Parse command line arguments
parser = argparse.ArgumentParser(description='Weekly Drug Shortages Summary Script')
parser.add_argument('--config', default='config.ini', help='Path to the configuration file')
parser.add_argument('--drugs', default='drugs.txt', help='Path to the drug keys file')
parser.add_argument('--recipients', default='recipients.txt', help='Path to the recipients file')
args = parser.parse_args()

# Read configuration from ini file
try:
    config = configparser.ConfigParser()
    config.read(args.config)
    logger.info(f"Successfully read {args.config}")
except Exception as e:
    logger.error(f"Failed to read {args.config}: {e}")
    sys.exit(1)

# Email and API configuration from ini
try:
    SMTP_SERVER = config['email']['smtp_server']
    SMTP_PORT = int(config['email']['smtp_port'])
    SENDER_EMAIL = config['email']['sender_email']
    SENDER_PASSWORD = config['email']['sender_password']
    EMAIL_SUBJECT = config['email']['subject']
    API_KEY = config['api']['api_key']
    BASE_URL = config['api']['base_url']
    logger.info("Email and API configuration loaded successfully")
except KeyError as e:
    logger.error(f"Missing configuration in {args.config}: {e}")
    sys.exit(1)

# Read subscribed keys from external file
def read_subscribed_keys(file_path):
    try:
        with open(file_path, 'r') as f:
            keys = [int(line.strip()) for line in f if line.strip().isdigit()]
        logger.info(f"Read {len(keys)} drug keys from {file_path}")
        return keys
    except FileNotFoundError:
        logger.error(f"Drug keys file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading drug keys from {file_path}: {e}")
        return []

# Read recipients from external file
def read_recipients(file_path):
    try:
        with open(file_path, 'r') as f:
            recipients = [line.strip() for line in f if '@' in line]
        logger.info(f"Read {len(recipients)} recipients from {file_path}")
        return recipients
    except FileNotFoundError:
        logger.error(f"Recipients file not found: {file_path}")
        return []
    except Exception as e:
        logger.error(f"Error reading recipients from {file_path}: {e}")
        return []

SUBSCRIBED_KEYS = read_subscribed_keys(args.drugs)
RECIPIENTS = read_recipients(args.recipients)

def query_drug_shortage(key):
    url = f"{BASE_URL}drugShortages/{key}/latest.json?auth={API_KEY}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data is None:
                logger.warning(f"No data found for key {key}")
                return None, "Not Found"
            logger.info(f"Successfully queried drug shortage for key {key}")
            return data, None
        else:
            logger.error(f"Error querying key {key}: {response.status_code} - {response.text}")
            return None, f"Error: {response.status_code}"
    except Exception as e:
        logger.error(f"Exception querying key {key}: {e}")
        return None, f"Exception: {str(e)}"

def generate_summary():
    shortages = []
    resolved_shortages = []

    for key in SUBSCRIBED_KEYS:
        data, error = query_drug_shortage(key)
        if error:
            shortages.append(f"Key {key}: {error}")
        elif data:
            search_string = data.get('searchString', 'Unknown Name')
            create_date = data.get('shortageCreateDate', 'Unknown Date')
            status = data.get('shortageStatus', 'Unknown Status')
            entry = f"{search_string} (Key: {key}, Created: {create_date}, Type: {status})"
            if status == "Resolved":
                resolved_shortages.append(entry)
            else:
                shortages.append(entry)
        else:
            logger.warning(f"No data returned for key {key}")
            shortages.append(f"Key {key}: No Data")

    summary = "Weekly Drug Shortages Summary:\n\n"
    summary += "Shortages (Active, Not Found, or Other):\n" + ("\n".join(shortages) if shortages else "None\n")
    summary += "\n\nResolved Shortages:\n" + ("\n".join(resolved_shortages) if resolved_shortages else "None\n")

    logger.info("Generated summary successfully")
    return summary

def send_email(summary):
    if not RECIPIENTS:
        logger.error("No recipients specified, skipping email")
        return

    msg = MIMEText(summary)
    msg['Subject'] = EMAIL_SUBJECT
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(RECIPIENTS)

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())
        server.quit()
        logger.info(f"Email sent successfully to {len(RECIPIENTS)} recipients")
    except Exception as e:
        logger.error(f"Error sending email: {e}")

if __name__ == "__main__":
    logger.info("Starting weekly drug shortage check")
    summary = generate_summary()
    logger.info("Summary:\n%s", summary)
    send_email(summary)
    logger.info("Script execution completed")
