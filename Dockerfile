# Dockerfile for the social app scraper
FROM python:3.9-slim

WORKDIR /app

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