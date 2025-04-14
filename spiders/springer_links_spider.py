# spiders/springer_links_spider.py
import scrapy
import json
import logging
import os
from pathlib import Path
from urllib.parse import urljoin

class SpringerLinksSpider(scrapy.Spider):
    name = "springer_links"

    def __init__(self, journal_id: str, **kwargs):
        super().__init__(**kwargs)
        self.journal_id = journal_id.strip()
        self.base_url = f"https://link.springer.com/journal/{self.journal_id}/volumes-and-issues"
        self.output_dir = Path(f"static/springer-{self.journal_id}/volumes/")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy = f"http://scraperapi:{os.environ['SCRAPER_API_KEY']}@proxy-server.scraperapi.com:8001"

    def start_requests(self):
        self.logger.info(f"Visiting issues page: {self.base_url}")

        yield scrapy.Request(
            url=self.base_url,
            callback=self.parse_volume_listing,
            meta={"proxy": self.proxy}
        )

    def parse_volume_listing(self, response):
        # Parse first issue per volume (Springer shows all volumes/issue links together)
        # save response text to a file

        issue_links = response.xpath("//ul[contains(@data-test, 'volumes-and-issues')]/li//li[1]/a/@href").getall()

        self.logger.info(f"Found {len(issue_links)} volumes to scrape.")

        for relative_url in issue_links:
            full_url = urljoin(response.url, relative_url)
            logging.info(f"Visiting issues page: {full_url}")
            logging.info(f"Using ScraperAPI proxy for requests: {self.proxy}")

            yield scrapy.Request(
                url=full_url,
                callback=self.parse_issue
            )

    def parse_issue(self, response):
        url = response.url.split("?", 1)[0]
        volume_issue = url.rstrip("/").split("/")[-1]  # e.g., 49-3
        articles = []

        for article in response.xpath("//section[@data-test='article-listing']//li//a"):
            title = article.xpath("./text()").get()
            href = article.xpath("./@href").get()
            if title and href:
                articles.append({
                    "title": title.strip(),
                    "url": urljoin(response.url, href)
                })

        out_path = self.output_dir / f"volume_{volume_issue}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Saved {len(articles)} articles from issue {volume_issue} to {out_path}")
