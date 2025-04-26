# spiders/elsevier_links_spider.py
import scrapy
import logging
from pathlib import Path
from urllib.parse import urljoin
import json
import os

class ElsevierLinksSpider(scrapy.Spider):
    name = "elsevier_links"

    def __init__(self, journal_name: str, **kwargs):
        super().__init__(**kwargs)
        self.journal_name = journal_name.lower().replace(" ", "-")
        self.base_url = f"https://www.sciencedirect.com/journal/{self.journal_name}/issues"
        self.vol_base_url = f"https://www.sciencedirect.com/journal/{self.journal_name}/vol"
        self.output_dir = Path(f"static/{self.journal_name}/volumes")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy = f"http://scraperapi:{os.environ['SCRAPER_API_KEY']}@proxy-server.scraperapi.com:8001"

    def start_requests(self):
        logging.info(f"Visiting issues page: {self.base_url}")
        logging.info(f"Using ScraperAPI proxy for requests: {self.proxy}")

        yield scrapy.Request(
            url=self.base_url,
            callback=self.parse_issues,
            meta={"proxy": self.proxy}
        )

    def parse_issues(self, response):
        heading_text = response.xpath(
            "(//div[contains(@class, 'js-issues-archive-container')]//span[contains(@class, 'accordion-title')]//text())[1]"
        ).get()
        if not heading_text:
            self.logger.error("Failed to extract volume heading text.")
            return

        # modify this to handle both cases ("2025 — Volume 11" & "2025 — Volumes 153-158")
        
        if "Volumes" in heading_text:
            # Extract the range and get the last volume number
            max_volume = int(heading_text.split("Volumes")[-1].split("-")[-1].strip())
        elif "Volume" in heading_text:
            max_volume = int(heading_text.split("Volume")[-1].strip())
        else:
            self.logger.error("Unexpected format for volume heading text.")

        self.logger.info(f"Found total volumes: {max_volume}")
        
        for vol in range(1, max_volume + 1):
            vol_url = f"{self.vol_base_url}/{vol}"
            yield scrapy.Request(
                url=vol_url,
                callback=self.parse_volume,
                meta={"volume": vol, "proxy": self.proxy}
            )

    def parse_volume(self, response):
        volume = response.meta["volume"]
        articles = []
        links = response.xpath("//ol[contains(@class, 'article-list')]//a[contains(@class, 'article-content-title')]/@href").getall()
        titles = response.xpath("//ol[contains(@class, 'article-list')]//a[contains(@class, 'article-content-title')]//text()").getall()

        for link, title in zip(links, titles):
            full_url = urljoin("https://www.sciencedirect.com", link)
            articles.append({"title": title.strip(), "url": full_url})

        paper_path = self.output_dir / f"volume_{volume}.json"
        with open(paper_path, "w", encoding="utf-8") as f:
            json.dump(articles, f, ensure_ascii=False, indent=4)

        self.logger.info(f"Saved {len(articles)} articles for Volume {volume} to {paper_path}")
