from typing import cast

from pydantic import HttpUrl
import modal
from scraper.app import app
from scraper.database import create_db_client
from scraper.crud.character import (
    upsert_characters,
    get_characters_for_tagging,
    upsert_tags,
    tag_character,
)
from scraper.crud.site import get_sites
from scraper.registry import get_scraper
from scraper.schemas import Character, TagType, CharacterForTagging


@app.function()
async def scrape_character_url(character_url: str, site_id: str) -> None:
    """
    Scrape a single character URL and upsert it to the database.
    Returns the upserted character data or None if scraping failed.
    """
    db = create_db_client()
    async with get_scraper(character_url) as scraper:
        character = await scraper.scrape_character(character_url)
    result = upsert_characters(db, [character], site_id)
    print(f"Scraped character {character_url} {result[0] if result else None}")


@app.function(timeout=60 * 30)
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
    db = create_db_client()
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
    db = create_db_client()
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


@app.function(timeout=60 * 10)
async def create_tags_for_character(characters: list[CharacterForTagging]) -> None:
    """
    Create tags for a batch of characters within a single container invocation.

    Expects each character to have keys: id, name, description.
    """
    from scraper.ai import CHARACTER_TAGGING_AGENT

    db = create_db_client()

    for character in characters:
        character_id = character["id"]
        character_name = character["name"]
        character_description = character["description"]

        print(f"Creating tags for character {character_id}: {character_name}")

        try:
            llm_response = await CHARACTER_TAGGING_AGENT.run(
                f"Character Name: {character_name}\nCharacter Description: {character_description}"
            )

            content_tag_ids = upsert_tags(
                db, llm_response.output.content_tags, TagType.CONTENT
            )
            personality_tag_ids = upsert_tags(
                db, llm_response.output.personality_tags, TagType.PERSONALITY
            )
            all_tag_ids = content_tag_ids + personality_tag_ids
            tag_character(db, character_id, all_tag_ids)

            print(
                f"Created {len(all_tag_ids)} tags for character {character_id}: content={llm_response.output.content_tags}, personality={llm_response.output.personality_tags}"
            )
        except Exception as e:
            print(
                f"Failed to create tags for character {character_id} ({character_name}): {e}"
            )


@app.function(
    schedule=modal.Cron("0 9 * * *", timezone="America/New_York"), timeout=60 * 30
)
async def tag_characters() -> None:
    """
    Batch create tags for all characters that don't have tags yet.

    This runs 1 hour after the scrape_sites CRON job (9 AM vs 8 AM).
    Processes characters in batches of 500 and spawns parallel tag creation jobs.
    """
    db = create_db_client()

    total_characters_queued = 0
    batches_processed = 0

    for batch in get_characters_for_tagging(db, batch_size=100):
        batches_processed += 1

        # Narrow typing for batch to the expected payload
        typed_batch: list[CharacterForTagging] = [
            {"id": c["id"], "name": c["name"], "description": c["description"]}
            for c in batch
        ]
        create_tags_for_character.spawn(typed_batch)
        total_characters_queued += len(batch)

        print(f"Batch {batches_processed}: Queued {len(batch)} characters for tagging")

    print(
        {
            "batches_processed": batches_processed,
            "total_characters_queued": total_characters_queued,
        }
    )
