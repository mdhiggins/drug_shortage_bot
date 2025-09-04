# Drug Shortages Weekly Report

This project is a Python script that queries the ASHP Drug Shortages API to generate a weekly summary of drug shortages and sends it via email. The script runs in a Docker container with a cron job to execute every Monday at 9 AM. Configuration files are mounted as volumes for easy updates.
Prerequisites

## Setup

### Prepare Configuration Files
Create a config directory with the following files:

config.ini:

```ini
[email]
smtp_server = smtp.gmail.com
smtp_port = 587
sender_email = your_email@example.com
sender_password = your_app_password
subject = Weekly Drug Shortages Summary

[api]
api_key = your_api_key_here
base_url = https://ahfs-staging.firebaseio.com/
```

Replace smtp_server, smtp_port, sender_email, and sender_password with your SMTP settings. For Gmail with 2FA, generate an App Password.
Obtain api_key from softwaresupport@ashp.org. Staging API example should only be used for testing purposes

drugs.txt:
```
113
114
115
```

List drug shortage keys (one per line).

recipients.txt:
```
recipient1@example.com
recipient2@example.com
```

List email recipients (one per line).


### Run with Docker Compose
Create a docker-compose.yml file:

```yaml
services:
  drug-shortages:
    image: ghcr.io/your-username/drug-shortages:latest
    container_name: drug-shortages-container
    restart: unless-stopped
    volumes:
      - ./config:/config:ro
    environment:
      - TZ=America/New_York
```

Replace your-username with your GitHub username.
Adjust TZ to your desired timezone (e.g., America/Los_Angeles).

Run immediately:

```bash
docker exec drug-shortages-container /app/venv/bin/python /app/drug_shortages.py --config /config/config.ini --drugs /config/drugs.txt --recipients /config/recipients.txt
```
