from typing import Any, Generator

from supabase import Client

from scraper.schemas import Character, CreatorInput, TagType


def upsert_characters(
    db: Client, characters: list[Character], site_id: str
) -> list[dict[str, Any]]:
    """
    Upsert multiple characters in a batch operation.

    First upserts all creators, then upserts all characters with the correct creator_id.
    """
    if not characters:
        return []

    # Deduplicate creators by site_unique_identifier within the same site to avoid Postgres
    # "ON CONFLICT DO UPDATE command cannot affect row a second time" errors
    # when multiple rows in the same payload target the same unique key.
    deduped_creators_by_identifier: dict[str, CreatorInput] = {}
    for character in characters:
        incoming_creator: CreatorInput = character.creator
        existing_creator = deduped_creators_by_identifier.get(
            incoming_creator.site_unique_identifier
        )
        if existing_creator is None:
            deduped_creators_by_identifier[incoming_creator.site_unique_identifier] = (
                incoming_creator
            )
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

        # Keep the maximum known follower_count when both are present
        if incoming_creator.follower_count is not None:
            if (
                existing_creator.follower_count is None
                or incoming_creator.follower_count > existing_creator.follower_count
            ):
                existing_creator.follower_count = incoming_creator.follower_count

    # Prepare payload for upsert with site_id included
    creator_data_list: list[dict[str, Any]] = [
        {
            "name": creator.name,
            "image_url": str(creator.image_url) if creator.image_url else None,
            "urls": [str(url) for url in creator.urls],
            "site_id": site_id,
            "site_unique_identifier": creator.site_unique_identifier,
            "follower_count": creator.follower_count,
        }
        for creator in deduped_creators_by_identifier.values()
    ]

    creators_response = (
        db.table("creators")
        .upsert(creator_data_list, on_conflict="site_id,site_unique_identifier")
        .execute()
    )

    creator_site_unique_identifier_to_id = {
        creator["site_unique_identifier"]: creator["id"]
        for creator in creators_response.data
    }

    # Deduplicate characters by URL, always taking the one that appears last
    deduped_characters_by_url: dict[str, Character] = {}
    for character in characters:
        url_str = str(character.url)
        deduped_characters_by_url[url_str] = character

    characters_data = [
        {
            "name": character.name,
            "description": character.description,
            "url": str(character.url),
            "image_url": str(character.image_url),
            "like_count": character.like_count,
            "message_count": character.message_count,
            "chat_count": character.chat_count,
            "token_count": character.token_count,
            "creator_id": creator_site_unique_identifier_to_id[
                character.creator.site_unique_identifier
            ],
        }
        for character in deduped_characters_by_url.values()
    ]

    characters_response = (
        db.table("characters").upsert(characters_data, on_conflict="url").execute()
    )

    return characters_response.data


def get_characters_for_tagging(
    client: Client, batch_size: int = 500
) -> Generator[list[dict[str, Any]], None, None]:
    """
    Yield characters that have name and description but no tags, in batches.

    Returns batches of character dictionaries with id, name, and description fields.
    """
    offset = 0

    while True:
        all_characters = (
            client.table("characters")
            .select("id, name, description")
            .not_.is_("name", "null")
            .not_.is_("description", "null")
            .filter("name", "neq", "")
            .filter("description", "neq", "")
            .range(offset, offset + batch_size - 1)
            .execute()
        )

        if not all_characters.data:
            break

        character_ids = [char["id"] for char in all_characters.data]

        tagged_character_ids_response = (
            client.table("character_tags")
            .select("character_id")
            .in_("character_id", character_ids)
            .execute()
        )

        tagged_ids = {row["character_id"] for row in tagged_character_ids_response.data}

        untagged_characters = [
            char for char in all_characters.data if char["id"] not in tagged_ids
        ]

        if untagged_characters:
            yield untagged_characters

        if len(all_characters.data) < batch_size:
            break

        offset += batch_size


def upsert_tags(db: Client, tag_names: list[str], tag_type: TagType) -> list[str]:
    """
    Upsert tags to the tags table using composite uniqueness on (name, type).

    Returns a list of tag IDs corresponding to the input tag names.
    """
    if not tag_names:
        return []

    tag_data = [
        {"name": tag_name.lower().strip(), "type": tag_type} for tag_name in tag_names
    ]

    response = db.table("tags").upsert(tag_data, on_conflict="name,type").execute()

    return [tag["id"] for tag in response.data]


def tag_character(db: Client, character_id: str, tag_ids: list[str]) -> None:
    """
    Associate tags with a character by inserting into character_tags junction table.
    """
    if not tag_ids:
        return

    character_tag_data = [
        {"character_id": character_id, "tag_id": tag_id} for tag_id in tag_ids
    ]

    db.table("character_tags").insert(character_tag_data).execute()
