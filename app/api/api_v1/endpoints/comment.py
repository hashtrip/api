from fastapi import APIRouter, Body, Depends, Path
from starlette.status import HTTP_201_CREATED, HTTP_204_NO_CONTENT

from ....core.jwt import get_current_user_authorizer
from ....core.utils import create_aliased_response
from ....services.comment import create_comment, delete_comment, get_comments_for_place
from ....services.shortcuts import get_place_or_404
from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.comment import (
    CommentInCreate,
    CommentInResponse,
    ManyCommentsInResponse,
)
from ....models.user import User

router = APIRouter()


@router.post(
    "/places/{slug}/comments",
    response_model=CommentInResponse,
    tags=["comments"],
    status_code=HTTP_201_CREATED,
)
async def create_comment_for_place(
    *,
    slug: str = Path(..., min_length=1),
    comment: CommentInCreate = Body(..., embed=True),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    await get_place_or_404(db, slug, user.username)

    dbcomment = await create_comment(db, slug, comment, user.username)
    return create_aliased_response(CommentInResponse(comment=dbcomment))


@router.get(
    "/places/{slug}/comments",
    response_model=ManyCommentsInResponse,
    tags=["comments"],
)
async def get_comment_from_place(
    slug: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer(required=False)),
    db: AsyncIOMotorClient = Depends(get_database),
):
    await get_place_or_404(db, slug, user.username)

    dbcomments = await get_comments_for_place(db, slug, user.username)
    return create_aliased_response(ManyCommentsInResponse(comments=dbcomments))


@router.delete(
    "/places/{slug}/comments/{id}", tags=["comments"], status_code=HTTP_204_NO_CONTENT
)
async def delete_comment_from_place(
    slug: str = Path(..., min_length=1),
    id: int = Path(..., ge=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    await get_place_or_404(db, slug, user.username)

    await delete_comment(db, id, user.username)
