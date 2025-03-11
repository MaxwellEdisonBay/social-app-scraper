# Dockerfile for the cron job scheduler
FROM debian:bullseye-slim

RUN apt-get update && apt-get install -y cron

WORKDIR /app

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab

COPY start_cron.sh .
RUN chmod +x start_cron.sh

CMD ["./start_cron.sh"]