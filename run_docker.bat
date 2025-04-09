@echo off
echo Starting Docker container...

REM Check if .env exists, create if not
if not exist .env (
    echo Creating .env file...
    (
        echo GOOGLE_API_KEY=your_google_api_key_here
        echo DB_PATH=/app/data/news_cache.db
        echo NEWS_QUEUE_DB_PATH=/app/data/news_queue.db
        echo TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
        echo NEWS_SERVICE_BASE_URL=http://host.docker.internal:3000
        echo NEWS_SERVICE_API_KEY=your_api_key_here
        echo NEWS_SERVICE_AUTHOR_ID=your_author_id_here
    ) > .env
    echo Please update the .env file with your actual values
    pause
)

REM Start Docker container
docker-compose up -d --build

REM Show logs
docker-compose logs -f 