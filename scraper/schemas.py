from pydantic import BaseModel, HttpUrl, UUID4
from typing import Optional


class Site(BaseModel):
    id: UUID4
    name: str
    url: HttpUrl


class CreatorInput(BaseModel):
    """Creator data from scrapers, without id or site_id which are determined during upsert."""

    # Their handle/username, without the @
    name: str
    image_url: Optional[HttpUrl] = None
    # Sometimes creators will include links to their other sites (e.g. Ko-Fi, Patreon, etc.)
    urls: list[HttpUrl] = []
    followers: Optional[int] = None


class Creator(CreatorInput):
    """Full creator model including database fields."""

    id: UUID4
    site_id: UUID4


class Character(BaseModel):
    name: str
    description: str
    url: HttpUrl
    image_url: HttpUrl

    likes: Optional[int] = None
    tokens: Optional[int] = None

    creator: CreatorInput
