# utils.py
import re
from scrapy.http import HtmlResponse


def extract_country_from_affiliation(affiliation: str) -> str:
    """
    Naive country extractor based on last word or known patterns.
    You can later improve this using pycountry or named entity recognition.
    """
    if not affiliation:
        return ""
    parts = [p.strip() for p in re.split(r'[;,]', affiliation) if p.strip()]
    return parts[-1] if parts else ""

def extract_authors_with_affiliations(response: HtmlResponse) -> list[dict]:
    """
    Extracts authors and their affiliations, inferring country from author affiliation blocks.
    """
    authors_given_name = response.xpath("//div[@id='author-group']//span[@class='given-name']//text()").getall()
    authors_sur_name = response.xpath("//div[@id='author-group']//span[@class='text surname']//text()").getall()
    #combine given and surname names
    authors = [f"{given} {surname}" for given, surname in zip(authors_given_name, authors_sur_name)]

    affiliations = response.xpath("//meta[@name='citation_author_institution']/@content").getall()
    fallback = response.xpath("//div[@id='author-group']//li[contains(@class, 'affiliation')]/text()").getall()

    result = []
    for i, author in enumerate(authors):
        aff = affiliations[i] if i < len(affiliations) else (fallback[i] if i < len(fallback) else "")
        result.append({
            "name": author,
            "country": extract_country_from_affiliation(aff)
        })
    return result
