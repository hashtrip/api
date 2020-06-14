from typing import Optional, Callable

from pydantic import EmailStr
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)

from .place import get_place_by_slug
from .user import get_user, get_user_by_email
from ..db.mongodb import AsyncIOMotorClient


async def check_free_username_and_email(
    conn: AsyncIOMotorClient,
    username: Optional[str] = None,
    email: Optional[EmailStr] = None,
):
    if username:
        user_by_username = await get_user(conn, username)
        if user_by_username:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this username already exists",
            )
    if email:
        user_by_email = await get_user_by_email(conn, email)
        if user_by_email:
            raise HTTPException(
                status_code=HTTP_422_UNPROCESSABLE_ENTITY,
                detail="User with this email already exists",
            )


async def get_by_slug_or_404(
    conn: AsyncIOMotorClient, slug: str, username: Optional[str] = None, fx: Callable = get_place_by_slug
):
    searched_item = await fx(conn, slug, username)
    if not searched_item:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Item with slug '{slug}' not found",
        )
    return searched_item


async def check_by_slug_for_existence_and_modifying_permissions(
    conn: AsyncIOMotorClient, slug: str, username: str = "", fx: Callable = get_place_by_slug
):
    searched_item = await fx(conn, slug, username)
    if not searched_item:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f"Article with slug '{slug}' not found",
        )
    if searched_item.author.username != username:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="You have no permission for modifying this place",
        )
