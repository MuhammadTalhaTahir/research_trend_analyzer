# spiders/springer_details_spider.py
import scrapy
import json
import os
from pathlib import Path
from utils import extract_country_from_affiliation

class SpringerDetailsSpider(scrapy.Spider):
    name = "springer_details"

    def __init__(self, journal_id: str, **kwargs):
        super().__init__(**kwargs)
        self.journal_id = journal_id.strip()
        self.input_dir = Path(f"static/springer-{self.journal_id}/volumes")
        self.output_dir = Path(f"static/springer-{self.journal_id}/papers")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.proxy = f"http://scraperapi:{os.environ['SCRAPER_API_KEY']}@proxy-server.scraperapi.com:8001"

    def start_requests(self):
        for file in self.input_dir.glob("volume_*.json"):
            with open(file, encoding="utf-8") as f:
                papers = json.load(f)
                for paper in papers:
                    self.logger.info(f"Processing article: {paper['title']}")
                    self.logger.info(f"Article URL: {paper['url']}")
                    self.logger.info(f"Proxy URL: {self.proxy}")
                    yield scrapy.Request(
                        url=paper['url'],
                        callback=self.parse_paper,
                        meta={"proxy": self.proxy, "title": paper['title']}
                    )

    def parse_paper(self, response):
        def meta_content(name):
            return response.xpath(f"//meta[@name='{name}']/@content").get()

        title = meta_content("citation_title") or response.meta['title']
        abstract = meta_content("dc.description") or meta_content("description")
        year = meta_content("citation_publication_date")
        keywords = response.xpath("//meta[@name='dc.subject']/@content").getall()

        authors = response.xpath("//meta[@name='citation_author']/@content").getall()
        affiliations = response.xpath("//meta[@name='citation_author_institution']/@content").getall()

        author_info = []
        for i, author in enumerate(authors):
            aff = affiliations[i] if i < len(affiliations) else ""
            author_info.append({
                "name": author,
                "country": extract_country_from_affiliation(aff)
            })

        # Estimate citation count from number of meta[citation_reference] tags
        citation_count = len(response.xpath("//meta[@name='citation_reference']"))

        data = {
            "url": response.url,
            "title": title,
            "abstract": abstract,
            "citation_count": citation_count,
            "year": year,
            "authors": author_info,
            "keywords": keywords
        }

        filename = self.output_dir / f"{title[:100].replace('/', '_').replace('\\', '_')}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        self.logger.info(f"Saved metadata for: {title}")
