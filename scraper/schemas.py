from pydantic import BaseModel, HttpUrl, UUID4
from enum import IntEnum
from typing import Optional


class Site(BaseModel):
    id: UUID4
    name: str
    url: HttpUrl
    is_enabled: bool


class CreatorInput(BaseModel):
    """Creator data from scrapers, without id or site_id which are determined during upsert."""

    # Their handle/username, without the @
    name: str
    # Unique identifier within the site (e.g., username, user ID, etc.)
    site_unique_identifier: str
    image_url: Optional[HttpUrl] = None
    # Sometimes creators will include links to their other sites (e.g. Ko-Fi, Patreon, etc.)
    urls: list[HttpUrl] = []
    follower_count: Optional[int] = None


class Creator(CreatorInput):
    """Full creator model including database fields."""

    id: UUID4
    site_id: UUID4


class Character(BaseModel):
    name: str
    description: str
    url: HttpUrl
    image_url: HttpUrl

    chat_count: Optional[int] = None
    message_count: Optional[int] = None
    like_count: Optional[int] = None
    token_count: Optional[int] = None

    creator: CreatorInput


class TagType(IntEnum):
    CONTENT = 1
    PERSONALITY = 2
