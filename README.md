# Social App Scraper

A scraper for collecting news from various sources and sending them to a news service.

## Running in Docker

### Prerequisites

- Docker and Docker Compose installed on your system
- Environment variables set up in `.env` file

### Quick Start

#### For Linux/Mac users:

```bash
# Make the script executable
chmod +x run_docker.sh

# Run the container
./run_docker.sh
```

#### For Windows users:

```bash
# Run the container
run_docker.bat
```

### Manual Setup

1. Create necessary directories:
   ```bash
   mkdir -p data logs
   ```

2. Build and start the container:
   ```bash
   docker-compose up -d --build
   ```

3. View logs:
   ```bash
   docker-compose logs -f
   ```

### Environment Variables

Make sure your `.env` file contains the following variables:

```
GOOGLE_API_KEY=your_google_api_key
DB_PATH=/app/data/news_cache.db
NEWS_QUEUE_DB_PATH=/app/data/news_queue.db
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
NEWS_SERVICE_BASE_URL=http://your-news-service-url
NEWS_SERVICE_API_KEY=your_news_service_api_key
NEWS_SERVICE_AUTHOR_ID=your_author_id
```

## Development

### Running Tests

```bash
# Run all tests
python -m unittest discover

# Run a specific test
python -m unittest scrapers/test_ircc_scraper.py
```

### Project Structure

- `scrapers/`: Contains scrapers for different news sources
- `handlers/`: Contains handlers for database, API, etc.
- `common/`: Contains common models and utilities
- `schedule_script.py`: Main script for scheduling and running scrapers 