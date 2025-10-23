from pydantic import BaseModel


class CharacterTags(BaseModel):
    content_tags: list[str]
    personality_tags: list[str]


CHARACTER_TAGGING_PROMPT = """You are an expert at analyzing SFW and NSFW character descriptions and writing the relevant tags.

Given a character name and description, write the ~15 tags that users might search for to find this character.

The tags should include:
- ~10 Content tags: genre, setting, themes (e.g., "fantasy", "sci-fi", "romance", "modern", "historical")
- ~5 Personality/trait tags: character traits, attitudes, roles (e.g., "dominant", "shy", "cheerful", "mysterious", "mentor")

Instructions:
- Use lowercase for all tags
- Ideally use 1-word tags. Only use 2-word tags if absolutely necessary.
- Be highly specific and descriptive; avoid redundant or overly generic tags
"""
