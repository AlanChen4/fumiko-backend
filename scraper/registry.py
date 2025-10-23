from scraper.sites.base import BaseScraper
from scraper.sites.chub import ChubScraper
from scraper.sites.janitor import JanitorScraper
from scraper.sites.wyvern import WyvernScraper
from scraper.sites.pygmalion import PygmalionScraper


def get_scraper(url: str) -> BaseScraper:
    if "chub.ai" in url:
        return ChubScraper(use_proxy=True)
    if "janitorai.com" in url:
        return JanitorScraper(use_proxy=True)
    if "wyvern.chat" in url:
        return WyvernScraper(use_proxy=False, timeout=60.0)
    if "pygmalion.chat" in url:
        return PygmalionScraper(use_proxy=True, timeout=30.0)
    raise ValueError(f"No scraper found for URL: {url}")
