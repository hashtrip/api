from typing import Optional

from fastapi import APIRouter, Body, Depends, Path, Query
from slugify import slugify
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from ....core.jwt import get_current_user_authorizer
from ....core.utils import create_aliased_response
from ....services.post import (
    add_post_to_likes,
    create_post_by_slug,
    delete_post_by_slug,
    get_post_by_slug,
    get_posts_with_filters,
    get_user_posts,
    remove_post_from_likes,
    update_post_by_slug,
)
from ....services.shortcuts import (
    check_by_slug_for_existence_and_modifying_permissions,
    get_by_slug_or_404,
)
from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.post import (
    PostFilterParams,
    PostInCreate,
    PostInResponse,
    PostInUpdate,
    ManyPostsInResponse,
)
from ....models.user import User

router = APIRouter()


@router.get("/posts", response_model=ManyPostsInResponse, tags=["posts"])
async def get_posts(
    tag: str = "",
    author: str = "",
    liked: str = "",
    limit: int = Query(20, gt=0),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_authorizer(required=False)),
    db: AsyncIOMotorClient = Depends(get_database),
):
    filters = PostFilterParams(
        tag=tag, author=author, liked=liked, limit=limit, offset=offset
    )
    dbposts = await get_posts_with_filters(
        db, filters, user.username if user else None
    )
    return create_aliased_response(
        ManyPostsInResponse(posts=dbposts, posts_count=len(dbposts))
    )


@router.get("/posts/feed", response_model=ManyPostsInResponse, tags=["posts"])
async def posts_feed(
    limit: int = Query(20, gt=0),
    offset: int = Query(0, ge=0),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    dbposts = await get_user_posts(db, user.username, limit, offset)
    return create_aliased_response(
        ManyPostsInResponse(posts=dbposts, posts_count=len(dbposts))
    )


@router.get("/posts/{slug}", response_model=PostInResponse, tags=["posts"])
async def get_post(
    slug: str = Path(..., min_length=1),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    db: AsyncIOMotorClient = Depends(get_database),
):
    dbpost = await get_post_by_slug(db, slug, user.username if user else None)
    if not dbpost:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Post with slug '{slug}' not found",
        )

    return create_aliased_response(PostInResponse(post=dbpost))


@router.post(
    "/posts",
    response_model=PostInResponse,
    tags=["posts"],
    status_code=HTTP_201_CREATED,
)
async def create_new_post(
    post: PostInCreate = Body(..., embed=True),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    post_by_slug = await get_post_by_slug(db, slugify(post.title), user.username)
    if post_by_slug:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"文章已存在 slug='{post_by_slug.slug}'",
        )

    dbpost = await create_post_by_slug(db, post, user.username)
    return create_aliased_response(PostInResponse(post=dbpost))


@router.put("/posts/{slug}", response_model=PostInResponse, tags=["posts"])
async def update_post(
    slug: str = Path(..., min_length=1),
    post: PostInUpdate = Body(..., embed=True),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    await check_by_slug_for_existence_and_modifying_permissions(db, slug, user.username, fx=get_post_by_slug)

    dbpost = await update_post_by_slug(db, slug, post, user.username)
    return create_aliased_response(PostInResponse(post=dbpost))


@router.delete("/posts/{slug}", tags=["posts"], status_code=HTTP_204_NO_CONTENT)
async def delete_post(
    slug: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    await check_by_slug_for_existence_and_modifying_permissions(db, slug, user.username, fx=get_post_by_slug)

    await delete_post_by_slug(db, slug, user.username)


@router.post("/posts/{slug}/like", response_model=PostInResponse, tags=["posts"])
async def like_post(
    slug: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    dbpost = await get_by_slug_or_404(db, slug, user.username, fx=get_post_by_slug)
    if dbpost.liked:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="You already added this post to likes",
        )

    dbpost.liked = True
    dbpost.likes_count += 1

    await add_post_to_likes(db, slug, user.username)
    return create_aliased_response(PostInResponse(post=dbpost))


@router.delete(
    "/posts/{slug}/like", response_model=PostInResponse, tags=["posts"]
)
async def delete_post_from_likes(
    slug: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    dbpost = await get_by_slug_or_404(db, slug, user.username, fx=get_post_by_slug)

    if not dbpost.liked:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="You don't have this post in likes",
        )

    dbpost.liked = False
    dbpost.likes_count -= 1

    await remove_post_from_likes(db, slug, user.username)
    return create_aliased_response(PostInResponse(post=dbpost))
