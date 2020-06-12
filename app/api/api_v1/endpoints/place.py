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
from ....services.place import (
    add_place_to_favorites,
    create_place_by_slug,
    delete_place_by_slug,
    get_place_by_slug,
    get_places_with_filters,
    get_user_places,
    remove_place_from_favorites,
    update_place_by_slug,
)
from ....services.shortcuts import (
    check_place_for_existence_and_modifying_permissions,
    get_place_or_404,
)
from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.place import (
    PlaceFilterParams,
    PlaceInCreate,
    PlaceInResponse,
    PlaceInUpdate,
    ManyPlacesInResponse,
)
from ....models.user import User

router = APIRouter()


@router.get("/places", response_model=ManyPlacesInResponse, tags=["places"])
async def get_places(
        tag: str = "",
        author: str = "",
        favorited: str = "",
        limit: int = Query(20, gt=0),
        offset: int = Query(0, ge=0),
        user: User = Depends(get_current_user_authorizer(required=False)),
        db: AsyncIOMotorClient = Depends(get_database),
):
    filters = PlaceFilterParams(
        tag=tag, author=author, favorited=favorited, limit=limit, offset=offset
    )
    dbplaces = await get_places_with_filters(
        db, filters, user.username if user else None
    )
    return create_aliased_response(
        ManyPlacesInResponse(places=dbplaces, places_count=len(dbplaces))
    )


@router.get("/places/feed", response_model=ManyPlacesInResponse, tags=["places"])
async def places_feed(
        limit: int = Query(20, gt=0),
        offset: int = Query(0, ge=0),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbplaces = await get_user_places(db, user.username, limit, offset)
    return create_aliased_response(
        ManyPlacesInResponse(places=dbplaces, places_count=len(dbplaces))
    )


@router.get("/places/{slug}", response_model=PlaceInResponse, tags=["places"])
async def get_place(
        slug: str = Path(..., min_length=1),
        user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbplace = await get_place_by_slug(
        db, slug, user.username if user else None
    )
    if not dbplace:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Place with slug '{slug}' not found",
        )

    return create_aliased_response(PlaceInResponse(place=dbplace))


@router.post(
    "/places",
    response_model=PlaceInResponse,
    tags=["places"],
    status_code=HTTP_201_CREATED,
)
async def create_new_place(
        place: PlaceInCreate = Body(..., embed=True),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    place_by_slug = await get_place_by_slug(
        db, slugify(place.title), user.username
    )
    if place_by_slug:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"文章已存在 slug='{place_by_slug.slug}'",
        )

    dbplace = await create_place_by_slug(db, place, user.username)
    return create_aliased_response(PlaceInResponse(place=dbplace))


@router.put("/places/{slug}", response_model=PlaceInResponse, tags=["places"])
async def update_place(
        slug: str = Path(..., min_length=1),
        place: PlaceInUpdate = Body(..., embed=True),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    await check_place_for_existence_and_modifying_permissions(
        db, slug, user.username
    )

    dbplace = await update_place_by_slug(db, slug, place, user.username)
    return create_aliased_response(PlaceInResponse(place=dbplace))


@router.delete("/places/{slug}", tags=["places"], status_code=HTTP_204_NO_CONTENT)
async def delete_place(
        slug: str = Path(..., min_length=1),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    await check_place_for_existence_and_modifying_permissions(
        db, slug, user.username
    )

    await delete_place_by_slug(db, slug, user.username)


@router.post(
    "/places/{slug}/favorite", response_model=PlaceInResponse, tags=["places"]
)
async def favorite_place(
        slug: str = Path(..., min_length=1),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbplace = await get_place_or_404(db, slug, user.username)
    if dbplace.favorited:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="You already added this place to favorites",
        )

    dbplace.favorited = True
    dbplace.favorites_count += 1

    await add_place_to_favorites(db, slug, user.username)
    return create_aliased_response(PlaceInResponse(place=dbplace))


@router.delete(
    "/places/{slug}/favorite", response_model=PlaceInResponse, tags=["places"]
)
async def delete_place_from_favorites(
        slug: str = Path(..., min_length=1),
        user: User = Depends(get_current_user_authorizer()),
        db: AsyncIOMotorClient = Depends(get_database),
):
    dbplace = await get_place_or_404(db, slug, user.username)

    if not dbplace.favorited:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="You don't have this place in favorites",
        )

    dbplace.favorited = False
    dbplace.favorites_count -= 1

    await remove_place_from_favorites(db, slug, user.username)
    return create_aliased_response(PlaceInResponse(place=dbplace))
