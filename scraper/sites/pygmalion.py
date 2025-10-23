from typing import cast

from scraper.sites.base import BaseScraper, ScraperCursorType
from scraper.schemas import Character, HttpUrl, CreatorInput


class PygmalionScraper(BaseScraper):
    """
    https://pygmalion.chat/
    """

    async def scrape_character(self, character_url: str) -> Character:
        """
        Pygmalion scraper does not implement per-character scraping. Use scrape_site.
        """
        raise ValueError(
            "Pygmalion scraper does not have a separate character scraping logic. Use scrape_site instead."
        )

    async def scrape_site(
        self, site_url: str, cursor: ScraperCursorType = None
    ) -> tuple[list[HttpUrl] | list[Character], ScraperCursorType]:
        page = cursor or 1
        page_size = 100
        api_url = "https://server.pygmalion.chat/galatea.v1.PublicCharacterService/CharacterSearch"

        response = await self.http_client.post(
            api_url,
            json={
                "page": page,
                "orderBy": "approved_at",
                "orderDescending": True,
                "includeSensitive": False,
                "pageSize": page_size,
            },
            headers={
                "accept": "application/json, text/plain, */*",
                "content-type": "application/json",
                "referer": "https://pygmalion.chat/explore",
                "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            },
        )
        print(
            f"Scraped '{api_url}' (page={page}): {response.status_code}, {response.text[:100]}{'...' if len(response.text) > 100 else ''}"
        )
        response.raise_for_status()
        payload = response.json()

        items = payload.get("characters", []) or []

        characters: list[Character] = []
        for item in items:
            char_id = item.get("id") or ""
            if not char_id:
                continue

            page_url = cast(HttpUrl, f"https://pygmalion.chat/character/{char_id}")

            avatar_url = item.get("avatarUrl")
            if not avatar_url:
                continue

            name = item.get("displayName") or ""
            description = item.get("description") or ""

            like_raw = (
                item.get("stars") or item.get("starCount") or item.get("favorites") or 0
            )
            like_count = (
                int(like_raw)
                if isinstance(like_raw, int)
                or (isinstance(like_raw, str) and like_raw.isdigit())
                else 0
            )

            chat_count = item.get("chatCount") or 0

            owner = item.get("owner") or {}
            owner_display_name = owner.get("displayName")
            owner_id = owner.get("id")
            owner_avatar = owner.get("avatarUrl") or None

            if not owner_display_name or not owner_id:
                print(
                    f"Skipping character without owner information: {page_url}. owner_display_name: {owner_display_name}, owner_id: {owner_id}"
                )
                continue

            characters.append(
                Character(
                    name=name,
                    description=description,
                    url=page_url,
                    image_url=cast(HttpUrl, avatar_url),
                    chat_count=int(chat_count) if isinstance(chat_count, int) else 0,
                    like_count=like_count,
                    creator=CreatorInput(
                        name=owner_display_name,
                        image_url=owner_avatar,
                        site_unique_identifier=str(owner_id),
                    ),
                )
            )

        total_items_raw = payload.get("totalItems") or 0
        total_items = int(total_items_raw)
        next_page: int | None = page + 1 if page * page_size < total_items else None
        return characters, next_page
