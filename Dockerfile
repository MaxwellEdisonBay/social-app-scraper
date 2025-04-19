# Dockerfile for the social app scraper
FROM python:3.9-slim

WORKDIR /app

# Install Chrome and its dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg2 \
    apt-transport-https \
    ca-certificates \
    curl \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# Copy all necessary files
COPY . .

# Create directory for logs and data
RUN mkdir -p /app/data /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DB_PATH=/app/data/news_cache.db
ENV NEWS_QUEUE_DB_PATH=/app/data/news_queue.db

# Run the schedule script
CMD ["python", "-u", "schedule_script.py"]