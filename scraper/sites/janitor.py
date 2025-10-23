from typing import cast

from scraper.sites.base import BaseScraper, ScraperCursorType
from scraper.schemas import Character, HttpUrl, CreatorInput


class JanitorScraper(BaseScraper):
    """
    https://janitor.ai/
    """

    async def scrape_character(self, character_url: str) -> Character:
        """
        Janitor scraper does not implement per-character scraping. Use scrape_site.
        """
        raise ValueError(
            "Janitor scraper does not have a separate character scraping logic. Use scrape_site instead."
        )

    async def scrape_site(
        self, site_url: str, cursor: ScraperCursorType = None
    ) -> tuple[list[HttpUrl] | list[Character], ScraperCursorType]:
        page = cursor or 1
        api_url = (
            f"https://janitorai.com/hampter/characters?page={page}&mode=all&sort=latest"
        )

        response = await self.http_client.get(
            api_url,
            headers={
                "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "accept-language": "en-US,en;q=0.8",
                "cache-control": "no-cache",
                "pragma": "no-cache",
                "priority": "u=1, i",
                "referer": "https://janitorai.com/hampter/characters?mode=all&sort=latest",
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

        items = payload.get("data", []) or []

        characters: list[Character] = []
        for item in items:
            # Build page URL and image URL; use stable fallbacks based on id and avatar filename
            char_id = item.get("id") or ""
            page_url = cast(HttpUrl, f"https://janitorai.com/characters/{char_id}")

            avatar_filename = item.get("avatar") or ""
            if not avatar_filename:
                # Skip if we cannot construct a valid image URL
                # Consistency with other scrapers: require a usable image
                continue
            image_url = cast(
                HttpUrl, f"https://janitorai.com/avatars/{avatar_filename}"
            )

            name = item.get("name") or ""
            description = item.get("description") or ""
            stats = item.get("stats", {}) or {}
            chat_count = stats.get("chat") or 0
            message_count = stats.get("message") or 0
            token_count = item.get("total_tokens") or 0

            creator_name = item.get("creator_name")
            creator_id = item.get("creator_id")
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
                    image_url=image_url,
                    chat_count=int(chat_count) if isinstance(chat_count, int) else 0,
                    message_count=int(message_count)
                    if isinstance(message_count, int)
                    else 0,
                    token_count=int(token_count) if isinstance(token_count, int) else 0,
                    creator=CreatorInput(
                        name=creator_name, site_unique_identifier=creator_id
                    ),
                )
            )

        # Paginate while there are items; stop when empty
        next_page: int | None = page + 1 if len(items) > 0 else None
        return characters, next_page
