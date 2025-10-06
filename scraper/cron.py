from typing import cast

from pydantic import HttpUrl
import modal
from scraper.app import app
from scraper.database import get_supabase_client
from scraper.crud.character import upsert_characters
from scraper.crud.site import get_sites
from scraper.registry import get_scraper
from scraper.schemas import Character


@app.function()
async def scrape_character_url(character_url: str, site_id: str) -> None:
    """
    Scrape a single character URL and upsert it to the database.
    Returns the upserted character data or None if scraping failed.
    """
    db = get_supabase_client()
    async with get_scraper(character_url) as scraper:
        character = await scraper.scrape_character(character_url)
    result = upsert_characters(db, [character], site_id)
    print(f"Scraped character {character_url} {result[0] if result else None}")


@app.function()
async def scrape_site(
    site_url: str,
    site_id: str,
) -> None:
    """
    Scrape a single site, handling pagination, and process results.

    This function handles two cases:
    1. The scraper returns Character objects directly - these are batch upserted
    2. The scraper returns HttpUrl objects - these are queued for individual scraping

    Returns statistics about the scraping operation.
    """
    db = get_supabase_client()
    async with get_scraper(site_url) as scraper:
        total_characters_upserted = 0
        total_urls_queued = 0
        pages_processed = 0
        current_cursor = None

        while True:
            print(f"[{site_url}] Scraping page {pages_processed}")
            characters_or_urls, next_cursor = await scraper.scrape_site(
                site_url, current_cursor
            )
            pages_processed += 1

            if characters_or_urls and isinstance(characters_or_urls[0], Character):
                characters = cast(list[Character], characters_or_urls)
                upsert_characters(db, characters, site_id)
                total_characters_upserted += len(characters)

            elif characters_or_urls and isinstance(characters_or_urls[0], HttpUrl):
                urls = cast(list[HttpUrl], characters_or_urls)
                for url in urls:
                    scrape_character_url.spawn(str(url), site_id)
                total_urls_queued += len(urls)

            if next_cursor is None:
                break
            current_cursor = next_cursor

    print(
        {
            "pages_processed": pages_processed,
            "characters_upserted": total_characters_upserted,
            "urls_queued": total_urls_queued,
        }
    )


@app.function(
    schedule=modal.Cron("0 8 * * *", timezone="America/New_York"), timeout=60 * 10
)
async def scrape_sites() -> None:
    """
    Batch scrape all sites in the database.

    This is the main entry point for scheduled scraping jobs.
    It fetches all sites and spawns a scraping job for each one.

    Returns a summary of the batch operation.
    """
    db = get_supabase_client()
    sites = get_sites(db)

    if not sites:
        print("No sites found in database")
        return

    for site in sites:
        scrape_site.spawn(str(site.url), str(site.id))

    print(
        {
            "total_sites": len(sites),
            "sites_queued": [
                {"id": str(site.id), "name": site.name, "url": str(site.url)}
                for site in sites
            ],
        }
    )
