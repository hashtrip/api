from typing import List, Optional

from pydantic import Field

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
    location: str
    body: str
    tag_list: List[str] = Field([], alias="tagList")


class Place(DateTimeModelMixin, PlaceBase):
    slug: str
    author: Profile
    favorited: bool
    favorites_count: int = Field(..., alias="favoritesCount")


class PlaceInDB(DBModelMixin, Place):
    pass


class PlaceInResponse(RWModel):
    place: Place


class ManyPlacesInResponse(RWModel):
    places: List[Place]
    places_count: int = Field(..., alias="PlacesCount")


class PlaceInCreate(PlaceBase):
    pass


class PlaceInUpdate(RWModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    tag_list: List[str] = Field([], alias="tagList")
