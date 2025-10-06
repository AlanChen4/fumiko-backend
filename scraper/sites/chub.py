from urllib.parse import urljoin

from pydantic import HttpUrl
from typing import cast

from scraper.sites.base import BaseScraper, ScraperCursorType
from scraper.schemas import Character, CreatorInput


class ChubScraper(BaseScraper):
    """
    https://chub.ai/
    """

    async def scrape_character(self, character_url: str) -> Character:
        """
        TODO: Implement this.
        """
        raise ValueError(
            "Chub.ai scraper does not have a separate character scraping logic. Use scrape_site instead."
        )

    async def scrape_site(
        self, site_url: str, cursor: ScraperCursorType = None
    ) -> tuple[list[HttpUrl] | list[Character], ScraperCursorType]:
        page_size = 500
        page = cursor or 1
        api_url = f"https://gateway.chub.ai/search?page={page}&first={page_size}&sort=created_at"

        response = await self.http_client.get(
            api_url,
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.8",
                "cache-control": "max-age=0",
                "priority": "u=0, i",
                "sec-ch-ua": '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "document",
                "sec-fetch-mode": "navigate",
                "sec-fetch-site": "none",
                "sec-fetch-user": "?1",
                "sec-gpc": "1",
                "upgrade-insecure-requests": "1",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            },
        )
        print(
            f"Scraped '{api_url}': {response.status_code}, {response.text[:100]}{'...' if len(response.text) > 100 else ''}"
        )
        response.raise_for_status()
        payload = response.json()

        data = payload.get("data", {})
        nodes = data.get("nodes", []) or []

        characters: list[Character] = []
        for node in nodes:
            full_path = node.get("fullPath") or ""
            page_url = cast(HttpUrl, urljoin(site_url, full_path))

            avatar_url = node.get("avatar_url") or node.get("max_res_url")
            if not avatar_url:
                print(f"Skipping character without a usable image URL: {page_url}")
                continue

            name = node.get("name") or ""
            description = node.get("description") or ""
            likes = node.get("n_favorites") or node.get("starCount") or 0
            tokens = node.get("nTokens") or 0

            creator_name = ""
            if full_path and "/" in full_path:
                parts = full_path.strip("/").split("/")
                if len(parts) >= 2:
                    creator_name = parts[0]

            if not creator_name:
                print(f"Skipping character without creator information: {page_url}")
                continue

            characters.append(
                Character(
                    name=name,
                    description=description,
                    url=page_url,
                    image_url=cast(HttpUrl, avatar_url),
                    likes=int(likes) if isinstance(likes, int) else 0,
                    tokens=int(tokens) if isinstance(tokens, int) else 0,
                    creator=CreatorInput(name=creator_name),
                )
            )
        next_page: int | None = page + 1 if data.get("count") == page_size else None
        return characters, next_page
