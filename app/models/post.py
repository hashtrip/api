from enum import IntFlag
from typing import List, Optional

from pydantic import Field

from .dbmodel import DateTimeModelMixin, DBModelMixin
from .place import Place
from .profile import Profile
from .rwmodel import RWModel


class PostFilterParams(RWModel):
    tag: str = ""
    author: str = ""
    liked: str = ""
    limit: int = 20
    offset: int = 0


class PostType(IntFlag):
    ARTICLE = 0
    IMAGES = 1


class PostBase(RWModel):
    title: str
    type: PostType
    body: str
    place: Place
    tag_list: List[str] = Field([], alias="tagList")


class PostShallow(PostBase):
    place: str


class Post(DateTimeModelMixin, PostBase):
    slug: str
    author: Profile
    liked: bool
    likes_count: int = Field(..., alias="likesCount")


class PostInDB(DBModelMixin, Post):
    place: str
    pass


class PostInResponse(RWModel):
    post: Post


class ManyPostsInResponse(RWModel):
    posts: List[Post]
    posts_count: int = Field(..., alias="postsCount")


class PostInCreate(PostShallow):
    pass


class PostInUpdate(RWModel):
    title: Optional[str] = None
    description: Optional[str] = None
    body: Optional[str] = None
    tag_list: List[str] = Field([], alias="tagList")
