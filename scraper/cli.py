from typing import cast

from scraper.app import app
from scraper.schemas import Character
from scraper.registry import get_scraper


@app.function()
async def cli_scrape_site(url: str, first_page_only: bool = False) -> list[dict]:
    async with get_scraper(url) as scraper:
        all_characters: list[dict] = []
        cursor = None
        while True:
            results, cursor = await scraper.scrape_site(url, cursor=cursor)
            characters = cast(list[Character], results)
            all_characters.extend([c.model_dump() for c in characters])
            if first_page_only or not cursor:
                break

        return all_characters


@app.function()
async def cli_scrape_character(url: str) -> dict:
    async with get_scraper(url) as scraper:
        character = await scraper.scrape_character(url)
        return character.model_dump()


@app.local_entrypoint()
def main(
    url: str,
    mode: str,
    first_page_only: bool = True,
):
    if mode == "site":
        results = cli_scrape_site.remote(url, first_page_only)
        print(f"Scraped {len(results)} characters")
        for i, c in enumerate(results[:5], 1):
            name = c.get("name", "")
            page_url = c.get("url", "")
            print(f"[{i}] {name} {page_url}")
    elif mode == "character":
        result = cli_scrape_character.remote(url)
        print(result)
    else:
        raise ValueError(f"Invalid mode: {mode}")
