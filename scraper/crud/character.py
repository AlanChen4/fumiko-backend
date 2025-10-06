from typing import Any

from supabase import Client

from scraper.schemas import Character, CreatorInput


def upsert_characters(
    client: Client, characters: list[Character], site_id: str
) -> list[dict[str, Any]]:
    """
    Upsert multiple characters in a batch operation.

    First upserts all creators, then upserts all characters with the correct creator_id.
    """
    if not characters:
        return []

    # Deduplicate creators by name within the same site to avoid Postgres
    # "ON CONFLICT DO UPDATE command cannot affect row a second time" errors
    # when multiple rows in the same payload target the same unique key.
    deduped_creators_by_name: dict[str, CreatorInput] = {}
    for character in characters:
        incoming_creator: CreatorInput = character.creator
        existing_creator = deduped_creators_by_name.get(incoming_creator.name)
        if existing_creator is None:
            deduped_creators_by_name[incoming_creator.name] = incoming_creator
            continue

        # Prefer an existing non-null image_url; otherwise take the new one
        if (
            existing_creator.image_url is None
            and incoming_creator.image_url is not None
        ):
            existing_creator.image_url = incoming_creator.image_url

        # Merge and de-duplicate URLs while preserving order
        existing_urls_set = {str(u) for u in existing_creator.urls}
        for url in incoming_creator.urls:
            url_str = str(url)
            if url_str not in existing_urls_set:
                existing_creator.urls.append(url)
                existing_urls_set.add(url_str)

        # Keep the maximum known followers count when both are present
        if incoming_creator.followers is not None:
            if (
                existing_creator.followers is None
                or incoming_creator.followers > existing_creator.followers
            ):
                existing_creator.followers = incoming_creator.followers

    # Prepare payload for upsert with site_id included
    creator_data_list: list[dict[str, Any]] = [
        {
            "name": creator.name,
            "image_url": str(creator.image_url) if creator.image_url else None,
            "urls": [str(url) for url in creator.urls],
            "site_id": site_id,
            "followers": creator.followers,
        }
        for creator in deduped_creators_by_name.values()
    ]

    creators_response = (
        client.table("creators")
        .upsert(creator_data_list, on_conflict="name,site_id")
        .execute()
    )

    creator_name_to_id = {
        creator["name"]: creator["id"] for creator in creators_response.data
    }

    characters_data = [
        {
            "name": character.name,
            "description": character.description,
            "url": str(character.url),
            "image_url": str(character.image_url),
            "likes": character.likes,
            "tokens": character.tokens,
            "creator_id": creator_name_to_id[character.creator.name],
        }
        for character in characters
    ]

    characters_response = (
        client.table("characters").upsert(characters_data, on_conflict="url").execute()
    )

    return characters_response.data
