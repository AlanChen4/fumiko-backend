from abc import ABC, abstractmethod
from typing import TypeAlias, Optional
import os

from pydantic import HttpUrl
from httpx import AsyncClient

from scraper.schemas import Character

ScraperCursorType: TypeAlias = int | None


class BaseScraper(ABC):
    def __init__(
        self,
        use_proxy: bool = False,
        timeout: float = 10.0,
    ):
        if not use_proxy:
            self.http_client = AsyncClient(timeout=timeout)
        else:
            host, port = (
                os.getenv("PROXY_HOST"),
                os.getenv("PROXY_PORT"),
            )
            if not host or not port:
                raise EnvironmentError(
                    f"Proxy variables are not set. PROXY_HOST: {host}, PROXY_PORT: {port}"
                )
            username, password = (
                os.getenv("PROXY_USERNAME"),
                os.getenv("PROXY_PASSWORD"),
            )
            if not username or not password:
                raise EnvironmentError(
                    f"Proxy credentials are not set. PROXY_USERNAME: {username}, PROXY_PASSWORD: {password}"
                )
            self.http_client = AsyncClient(
                timeout=timeout,
                proxy=f"http://{username}:{password}@{host}:{port}",
            )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exception_type, exception_value, traceback):
        await self.http_client.aclose()

    @abstractmethod
    async def scrape_character(self, character_url: str) -> Character:
        """
        Scrape the character and return character data.

        For instance, input could be 'https://chub.ai/user123/character123' and the implementation should return:
        - character data
        """
        ...

    @abstractmethod
    async def scrape_site(
        self, site_url: str, cursor: Optional[ScraperCursorType] = None
    ) -> tuple[list[HttpUrl] | list[Character], ScraperCursorType]:
        """
        Scrape the site and return a list of URLs to individual characters OR just the characters themselves, if possible.

        For instance, input could be 'https://example.ai/' and the implementation should step through:
        - https://example.ai/?category=all&page=1
        - https://example.ai/?category=all&page=2
        - ...
        - https://example.ai/?category=all&page=10

        On each page, it should return:
        - a list of URLs to individual characters OR a list of characters themselves
        - the next page number if there is one, otherwise None
        """
        ...
