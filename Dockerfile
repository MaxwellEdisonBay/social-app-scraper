# Dockerfile for the single container
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scrapers/ ./scrapers/
COPY handlers/ ./handlers/
COPY schedule_script.py .


CMD ["python", "-u", "schedule_script.py"]