from typing import Optional
from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from ..models.profile import ProfileInResponse
from ..models.user import User
from ..db.mongodb import AsyncIOMotorClient
from ..db.repositories.profile_repository import (
    get_profile_by_username,
    follow_for_user,
    unfollow_user,
)


async def get_profile_service(
    conn: AsyncIOMotorClient, *, username: str, current_user: Optional[User] = None
) -> ProfileInResponse:
    profile = await get_profile_by_username(
        conn, username, current_user.username if current_user else None
    )
    return ProfileInResponse(profile=profile)


async def follow_user_service(user: User, username: str, conn: AsyncIOMotorClient):
    if username == user.username:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User can not follow them self",
        )

    profile = await get_profile_by_username(conn, username, user.username)
    if profile.following:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"You follow this user already",
        )

    await follow_for_user(conn, user.username, profile.username)
    profile.following = True

    return ProfileInResponse(profile=profile)


async def unfollow_user_service(user: User, username: str, conn: AsyncIOMotorClient):
    if username == user.username:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"User can not describe from them self",
        )

    profile = await get_profile_by_username(conn, username, user.username)

    if not profile.following:
        raise HTTPException(
            status_code=HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"You did not follow this user",
        )

    await unfollow_user(conn, user.username, profile.username)
    profile.following = False

    return ProfileInResponse(profile=profile)
