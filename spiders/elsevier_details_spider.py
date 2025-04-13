# spiders/elsevier_details_spider.py
import scrapy
import json
import os
from pathlib import Path
from utils import (
    extract_authors_with_affiliations
)

class ElsevierDetailsSpider(scrapy.Spider):
    name = "elsevier_details"

    def __init__(self, journal_name: str, **kwargs):
        super().__init__(**kwargs)
        self.journal_name = journal_name.lower().replace(" ", "-")
        self.input_dir = Path(f"static/{self.journal_name}/volumes")
        self.output_dir = Path(f"static/{self.journal_name}/papers")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy = f"http://scraperapi:{os.environ['SCRAPER_API_KEY']}@proxy-server.scraperapi.com:8001"

    def start_requests(self):
        for file in self.input_dir.glob("volume_*.json"):
            with open(file, encoding="utf-8") as f:
                articles = json.load(f)
                for article in articles:
                    self.logger.info(f"Processing article: {article['title']}")
                    self.logger.info(f"Article URL: {article['url']}")
                    yield scrapy.Request(
                        url=article['url'],
                        callback=self.parse_article,
                        meta={"proxy": self.proxy, "title": article['title']}
                    ) 

    def parse_article(self, response):
        def extract_meta(name):
            return response.xpath(f"//meta[@name='{name}']/@content").get()

        def extract_property(prop):
            return response.xpath(f"//meta[@property='{prop}']/@content").get()

        title = extract_meta("citation_title") or response.meta["title"]
        abstract = response.xpath('//div[contains(@class, "abstract author")]/h2[text() = "Abstract"]/following-sibling::div//text()').getall()
        abstract = " ".join(abstract).strip() if abstract else ""
        year = extract_meta("citation_publication_date")
        authors = extract_authors_with_affiliations(response)
        keywords = extract_meta("keywords")
        citation_count = response.xpath("//header[@id='citing-articles-header']//text()").get().split(' ')[-1].lstrip('(').rstrip(')')

        data = {
            "url": response.url,
            "title": title,
            "abstract": abstract,
            "citation_count": citation_count,
            "year": year,
            "authors": authors,
            "keywords": keywords.split(",") if keywords else []
        }

        filename = self.output_dir / f"{title[:100].replace('/', '_').replace('\\', '_')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.logger.info(f"Saved metadata for: {title}")
