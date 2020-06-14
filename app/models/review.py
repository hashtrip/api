from typing import List

from pydantic import conint

from .dbmodel import DBModelMixin
from .profile import Profile
from .rwmodel import RWModel


class ReviewInDB(DBModelMixin, RWModel):
    body: str
    rating: conint(ge=1, le=5)
    author: Profile


class Review(ReviewInDB):
    pass


class ReviewInCreate(RWModel):
    body: str


class ReviewInResponse(RWModel):
    comment: Review


class ManyReviewsInResponse(RWModel):
    comments: List[Review]
