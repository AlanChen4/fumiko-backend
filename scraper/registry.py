from scraper.sites.base import BaseScraper
from scraper.sites.chub import ChubScraper


def get_scraper(url: str) -> BaseScraper:
    if "chub.ai" in url:
        return ChubScraper(use_proxy=True)
    raise ValueError(f"No scraper found for URL: {url}")
