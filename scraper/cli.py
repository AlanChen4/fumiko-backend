from typing import cast

from scraper.app import SECRETS, app
from scraper.schemas import Character
from scraper.registry import get_scraper
from scraper.database import create_db_client


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


@app.function(secrets=SECRETS)
async def cli_create_tags(character_id: str) -> dict:
    from scraper.ai import CHARACTER_TAGGING_AGENT

    db = create_db_client()

    db_response = (
        db.table("characters")
        .select("id, name, description")
        .eq("id", character_id)
        .single()
        .execute()
    )

    if not db_response.data:
        return {"error": f"Character with ID {character_id} not found"}

    character = db_response.data
    character_name = character["name"]
    character_description = character["description"]

    if not character_name or not character_description:
        return {"error": "Character must have both name and description"}

    llm_response = await CHARACTER_TAGGING_AGENT.run(
        f"Character Name: {character_name}\nCharacter Description: {character_description}"
    )

    return {
        "character_id": character_id,
        "character_name": character_name,
        "content_tags": llm_response.output.content_tags,
        "personality_tags": llm_response.output.personality_tags,
        "tag_count": len(llm_response.output.content_tags)
        + len(llm_response.output.personality_tags),
    }


@app.local_entrypoint()
def main(
    mode: str,
    url: str = "",
    character_id: str = "",
    first_page_only: bool = True,
):
    if mode == "site":
        results = cli_scrape_site.remote(url, first_page_only)
        print(f"Scraped {len(results)} characters")
        for i, c in enumerate(results[:5], 1):
            name = c.get("name", "")
            page_url = c.get("url", "")
            print(
                f"[{i}] {name}\nDescription: {c.get('description', '')}\nCharacter URL: {page_url}\nCreator: {c.get('creator', {}).get('name')} ({c.get('creator', {}).get('site_unique_identifier')})\n=================="
            )
    elif mode == "character":
        result = cli_scrape_character.remote(url)
        print(result)
    elif mode == "create-tags":
        if not character_id:
            raise ValueError("character_id is required for create-tags mode")
        result = cli_create_tags.remote(character_id)
        if "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(
                f"Character: {result['character_name']} (ID: {result['character_id']})"
            )
            print(f"{result['tag_count']} tags:")
            for tag in result["content_tags"]:
                print(f"-Content: {tag}")
            for tag in result["personality_tags"]:
                print(f"-Personality: {tag}")
    else:
        raise ValueError(f"Invalid mode: {mode}")
