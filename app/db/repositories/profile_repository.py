from typing import Optional, List

from starlette.exceptions import HTTPException
from starlette.status import HTTP_404_NOT_FOUND

from .user_repository import get_user
from ...db.mongodb import AsyncIOMotorClient
from ...core.config import database_name, followers_collection_name
from ...models.profile import Profile


async def get_profile_by_username(
    conn: AsyncIOMotorClient,
    target_username: str,
    current_username: Optional[str] = None,
) -> Profile:
    user = await get_user(conn, target_username)
    if not user:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND, detail=f"User {target_username} not found"
        )

    profile = Profile(**user.dict())
    profile.following = await is_following_for_user(
        conn, current_username, target_username
    )

    return profile


async def is_following_for_user(
    conn: AsyncIOMotorClient, current_username: str, target_username: str
) -> bool:
    count = await conn[database_name][followers_collection_name].count_documents(
        {"follower": current_username, "following": target_username}
    )
    return count > 0


async def get_followings(
    conn: AsyncIOMotorClient, username: str
) -> List[Profile]:
    cursor = conn[database_name][followers_collection_name].find(
        {"follower": username}
    )

    result: List[Profile] = []
    async for item in cursor:
        profile = await get_profile_by_username(
            conn,
            current_username=username,
            target_username=item["following"],
        )
        print(item)
        result.append(profile)

    return result


async def follow_for_user(
    conn: AsyncIOMotorClient, current_username: str, target_username: str
):
    await conn[database_name][followers_collection_name].insert_one(
        {"follower": current_username, "following": target_username}
    )


async def unfollow_user(
    conn: AsyncIOMotorClient, current_username: str, target_username: str
):
    await conn[database_name][followers_collection_name].delete_many(
        {"follower": current_username, "following": target_username}
    )
