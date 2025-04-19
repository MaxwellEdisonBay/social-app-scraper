from scrapers.experiment_bbc_scraper import ExperimentBBCScraper


# Example of how to run the asynchronous function
if __name__ == "__main__":
    async def main():
        scraper = ExperimentBBCScraper(enable_caching=False)
        url = "https://www.bbc.com/news/articles/c8073jzr1xko"
        result = await scraper.fetch_post_full_text(url)
        print(result)

    import asyncio
    asyncio.run(main())
