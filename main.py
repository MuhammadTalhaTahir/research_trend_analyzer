# main.py
import argparse
import os
from scrapy.crawler import CrawlerProcess
from dotenv import load_dotenv
from spiders.elsevier_links_spider import ElsevierLinksSpider
from spiders.elsevier_details_spider import ElsevierDetailsSpider

load_dotenv()

SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY")
if not SCRAPER_API_KEY:
    raise ValueError("SCRAPER_API_KEY not found in .env file")

def run_spider(spider_class, **kwargs):
    process = CrawlerProcess(settings={
        "LOG_LEVEL": "INFO",
        "FEEDS": {},
        "DOWNLOADER_MIDDLEWARES": {
            'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 110,
        },
        "SCRAPER_API_KEY": SCRAPER_API_KEY
    })
    process.crawl(spider_class, **kwargs)
    process.start()

def main():
    parser = argparse.ArgumentParser(description="Scrape journal data.")
    parser.add_argument("--journal", required=True, help="Name of the journal (e.g., image and vision computing)")
    parser.add_argument("--website", required=True, choices=["elsevier"], help="Target website to scrape")
    parser.add_argument("--extract-links", action="store_true", help="Extract list of papers for each volume")
    parser.add_argument("--scrape-details", action="store_true", help="Extract detailed metadata from saved paper links")
    args = parser.parse_args()

    if args.website == "elsevier":
        if args.extract_links:
            run_spider(ElsevierLinksSpider, journal_name=args.journal, SCRAPER_API_KEY=SCRAPER_API_KEY)
        elif args.scrape_details:
            run_spider(ElsevierDetailsSpider, journal_name=args.journal, SCRAPER_API_KEY=SCRAPER_API_KEY)
        else:
            print("Please specify either --extract-links or --scrape-details")

if __name__ == "__main__":
    main()