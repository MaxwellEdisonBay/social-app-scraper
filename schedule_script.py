# schedule_script.py
import schedule
import time

from scraper import WebCrawler

if __name__ == "__main__":
    scraper = WebCrawler("https://example.com")


    def job():
        scraper.crawl("/data")


    schedule.every(5).seconds.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)