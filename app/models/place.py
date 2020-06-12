from typing import List, Optional

from pydantic import Schema

from .dbmodel import DateTimeModelMixin, DBModelMixin
from .profile import Profile
from .rwmodel import RWModel


class PlaceFilterParams(RWModel):
    tag: str = ""
    author: str = ""
    favorited: str = ""
    limit: int = 20
    offset: int = 0


class PlaceBase(RWModel):
    title: str
    description: str
    body: str
    tag_list: List[str] = Schema([], alias="tagList")


class Place(DateTimeModelMixin, PlaceBase):
    slug: str
    author: Profile
    favorited: bool
    favorites_count: int = Schema(..., alias="favoritesCount")


class PlaceInDB(DBModelMixin, Place):
    pass


class PlaceInResponse(RWModel):
    Place: Place


class ManyPlacesInResponse(RWModel):
    Places: List[Place]
    Places_count: int = Schema(..., alias="PlacesCount")


class PlaceInCreate(PlaceBase):
    pass


class PlaceInUpdate(RWModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    tag_list: List[str] = Schema([], alias="tagList")
