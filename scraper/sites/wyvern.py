from typing import cast

from scraper.sites.base import BaseScraper, ScraperCursorType
from scraper.schemas import Character, HttpUrl, CreatorInput


class WyvernScraper(BaseScraper):
    """
    https://wyvern.chat/
    """

    async def scrape_character(self, character_url: str) -> Character:
        """
        Wyvern scraper does not implement per-character scraping. Use scrape_site.
        """
        raise ValueError(
            "Wyvern scraper does not have a separate character scraping logic. Use scrape_site instead."
        )

    async def scrape_site(
        self, site_url: str, cursor: ScraperCursorType = None
    ) -> tuple[list[HttpUrl] | list[Character], ScraperCursorType]:
        page = cursor or 1
        limit = 100
        api_url = f"https://api.wyvern.chat/exploreSearch/characters?page={page}&limit={limit}&sort=created_at&order=DESC"

        response = await self.http_client.get(
            api_url,
            headers={
                "accept": "application/json, text/plain, */*",
                "accept-language": "en-US,en;q=0.8",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://wyvern.chat/explore",
                "sec-ch-ua": '"Brave";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
                "sec-ch-ua-mobile": "?0",
                "sec-ch-ua-platform": '"macOS"',
                "sec-fetch-dest": "empty",
                "sec-fetch-mode": "cors",
                "sec-fetch-site": "same-origin",
                "sec-gpc": "1",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            },
        )
        print(
            f"Scraped '{api_url}': {response.status_code}, {response.text[:100]}{'...' if len(response.text) > 100 else ''}"
        )
        response.raise_for_status()
        payload = response.json()

        items = payload.get("results", []) or []

        characters: list[Character] = []
        for item in items:
            char_id = item.get("id") or ""
            if not char_id:
                continue

            # Best-effort page URL construction; adjust if frontend path changes
            page_url = cast(HttpUrl, f"https://wyvern.chat/characters/{char_id}")

            avatar_url = item.get("avatar")
            if not avatar_url:
                # Skip entries without a usable image URL to keep consistency with other scrapers
                continue

            name = item.get("name")
            description = item.get("tagline")

            entity_stats = item.get("entity_statistics") or {}
            message_count = entity_stats.get("total_messages") or 0
            like_count = entity_stats.get("total_likes") or 0

            creator_obj = item.get("creator") or {}
            creator_name = creator_obj.get("displayName") or creator_obj.get(
                "vanityUrl"
            )
            creator_id = creator_obj.get("uid")
            creator_image = creator_obj.get("photoURL") or None

            if not creator_name or not creator_id:
                print(
                    f"Skipping character without creator information: {page_url}. creator_name: {creator_name}, creator_id: {creator_id}"
                )
                continue

            characters.append(
                Character(
                    name=name,
                    description=description,
                    url=page_url,
                    image_url=cast(HttpUrl, avatar_url),
                    message_count=int(message_count)
                    if isinstance(message_count, int)
                    else 0,
                    like_count=int(like_count) if isinstance(like_count, int) else 0,
                    creator=CreatorInput(
                        name=creator_name,
                        image_url=creator_image,
                        site_unique_identifier=creator_id,
                    ),
                )
            )

        next_page: int | None = page + 1 if payload.get("hasMore") else None
        return characters, next_page
