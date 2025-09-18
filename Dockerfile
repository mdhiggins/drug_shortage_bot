FROM python:3.11-alpine

# Install dcron, tzdata
RUN apk add --no-cache dcron tzdata

# Set timezone
ENV TZ=America/New_York
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python -m venv /app/venv

# Install dependencies in virtual environment
COPY requirements.txt .
RUN /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy Python script
COPY drug_shortages.py .

# Copy and set up crontab
COPY crontab /etc/cron.d/drug_shortages
RUN chmod 0644 /etc/cron.d/drug_shortages && chown root:root /etc/cron.d/drug_shortages

# Start cron in foreground
CMD ["/bin/sh", "-c", "crond -L /tmp/cron.log && tail -f /tmp/cron.log"]
