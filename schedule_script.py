# schedule_script.py
import time

import schedule

from scrapers.bbc_scraper import BBCScraper

if __name__ == "__main__":
    bbc_scraper = BBCScraper()


    def scrape_bbc():
        news = bbc_scraper.fetch_updated_news()
        print(news)


    schedule.every(10).seconds.do(scrape_bbc)

    while True:
        schedule.run_pending()
        time.sleep(1)
