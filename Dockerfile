# Dockerfile for the single container
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py .
COPY schedule_script.py .


CMD ["python", "-u", "schedule_script.py"]