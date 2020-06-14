from typing import List, Optional
from bson import ObjectId
from slugify import slugify
from datetime import datetime

from ..models.place import (
    PlaceFilterParams,
    PlaceInCreate,
    PlaceInDB,
    PlaceInUpdate,
)
from ..db.mongodb import AsyncIOMotorClient
from ..db.repositories.profile_repository import get_profile_by_username
from ..core.config import (
    database_name,
    favorites_collection_name,
    users_collection_name,
    place_collection_name,
)
from .tag import create_tags_that_not_exist, get_tags


async def is_place_favorited_by_user(
    conn: AsyncIOMotorClient, slug: str, username: str
) -> bool:
    user_doc = await conn[database_name][users_collection_name].find_one(
        {"username": username}, projection={"id": True}
    )
    place_doc = await conn[database_name][place_collection_name].find_one(
        {"slug": slug}, projection={"id": True}
    )
    if place_doc and user_doc:
        count = await conn[database_name][favorites_collection_name].count_documents(
            {"user_id": user_doc["_id"], "place_id": place_doc["_id"]}
        )
        return count > 0
    else:
        raise RuntimeError(
            f"没有找到对应的user_id或place_id,"
            f" 用户名={username} user={user_doc},slug={slug} place={place_doc}"
        )


async def add_place_to_favorites(conn: AsyncIOMotorClient, slug: str, username: str):
    user_doc = await conn[database_name][users_collection_name].find_one(
        {"username": username}, projection={"id": True}
    )
    place_doc = await conn[database_name][place_collection_name].find_one(
        {"slug": slug}, projection={"id": True}
    )
    if place_doc and user_doc:
        await conn[database_name][favorites_collection_name].insert_one(
            {"user_id": user_doc["_id"], "place_id": place_doc["_id"]}
        )
    else:
        raise RuntimeError(
            f"没有找到对应的user_id或place_id,"
            f" 用户名={username} user_id={user_doc},slug={slug} place_id={place_doc}"
        )


async def remove_place_from_favorites(
    conn: AsyncIOMotorClient, slug: str, username: str
):
    user_doc = await conn[database_name][users_collection_name].find_one(
        {"username": username}
    )
    place_doc = await conn[database_name][place_collection_name].find_one(
        {"slug": slug}
    )
    if place_doc and user_doc:
        await conn[database_name][favorites_collection_name].delete_many(
            {"user_id": user_doc["_id"], "place_id": place_doc["_id"]}
        )
    else:
        raise RuntimeError(
            f"没有找到对应的user_id或place_id,"
            f" 用户名={username} user_id={user_doc},slug={slug} place_id={place_doc}"
        )


async def get_favorites_count_for_place(conn: AsyncIOMotorClient, slug: str) -> int:
    place_doc = await conn[database_name][place_collection_name].find_one(
        {"slug": slug}, projection={"id": True}
    )
    if place_doc:
        return await conn[database_name][favorites_collection_name].count_documents(
            {"place_id": place_doc["_id"]}
        )
    else:
        raise RuntimeError(f"没有找到对应的place_id," f" slug={slug} place_id={place_doc}")


async def get_place_by_slug(
    conn: AsyncIOMotorClient, slug: str, username: Optional[str] = None
) -> PlaceInDB:
    place_doc = await conn[database_name][place_collection_name].find_one(
        {"slug": slug}
    )
    if place_doc:
        place_doc["favorites_count"] = await get_favorites_count_for_place(conn, slug)
        place_doc["favorited"] = await is_place_favorited_by_user(conn, slug, username) if username else False
        place_doc["author"] = await get_profile_by_username(conn, target_username=place_doc["author_id"])

        return PlaceInDB(
            **place_doc, created_at=ObjectId(place_doc["_id"]).generation_time
        )


#
#
# async def get_place_filters(
#     tag: str = "",
#     author: str = "",
#     favorited: str = "",
#     limit: int = Query(20, gt=0),
#     offset: int = Query(0, ge=0),
# ) -> PlaceFilterParams:
#     return PlaceFilterParams(
#         tag=tag, author=author, favorited=favorited, limit=limit, offset=offset
#     )


async def create_place_by_slug(
    conn: AsyncIOMotorClient, place: PlaceInCreate, username: str
) -> PlaceInDB:
    slug = slugify(place.title)
    place_doc = place.dict()
    place_doc["slug"] = slug
    place_doc["author_id"] = username
    place_doc["updated_at"] = datetime.now()
    await conn[database_name][place_collection_name].insert_one(place_doc)

    if place.tag_list:
        await create_tags_that_not_exist(conn, place.tag_list)

    author = await get_profile_by_username(conn, target_username=username)
    return PlaceInDB(
        **place_doc,
        created_at=ObjectId(place_doc["_id"]).generation_time,
        author=author,
        favorites_count=1,
        favorited=True,
    )


async def update_place_by_slug(
    conn: AsyncIOMotorClient, slug: str, place: PlaceInUpdate, username: str
) -> PlaceInDB:
    dbplace = await get_place_by_slug(conn, slug, username)

    if place.title:
        dbplace.slug = slugify(place.title)
        dbplace.title = place.title
    dbplace.body = place.body if place.body else dbplace.body
    dbplace.description = (
        place.description if place.description else dbplace.description
    )
    if place.tag_list:
        await create_tags_that_not_exist(conn, place.tag_list)
        dbplace.tag_list = place.tag_list

    dbplace.updated_at = datetime.now()
    await conn[database_name][place_collection_name].replace_one(
        {"slug": slug, "author_id": username}, dbplace.dict()
    )

    dbplace.created_at = ObjectId(dbplace.id).generation_time
    return dbplace


async def delete_place_by_slug(conn: AsyncIOMotorClient, slug: str, username: str):
    await conn[database_name][place_collection_name].delete_many(
        {"author_id": username, "slug": slug}
    )


async def get_user_places(
    conn: AsyncIOMotorClient, username: str, limit=20, offset=0
) -> List[PlaceInDB]:
    places: List[PlaceInDB] = []

    place_docs = conn[database_name][place_collection_name].find(
        {"author_id": username}, limit=limit, skip=offset
    )
    async for row in place_docs:
        slug = row["slug"]
        author = await get_profile_by_username(conn, target_username=row["author_id"])
        await get_tags(conn, slug)
        favorites_count = await get_favorites_count_for_place(conn, slug)
        favorited_by_user = await is_place_favorited_by_user(conn, slug, username)
        places.append(
            PlaceInDB(
                **row,
                author=author,
                created_at=ObjectId(row["_id"]).generation_time,
                favorites_count=favorites_count,
                favorited=favorited_by_user,
            )
        )
    return places


async def get_places_with_filters(
    conn: AsyncIOMotorClient, filters: PlaceFilterParams, username: Optional[str] = None
) -> List[PlaceInDB]:
    places: List[PlaceInDB] = []
    base_query = {}

    if filters.tag:
        base_query["tag_list"] = f'$all: ["{filters.tag}"]'

    if filters.favorited:
        base_query["slug"] = f'$in: ["{filters.favorited}"]'

    if filters.author:
        base_query["author"] = f'$in: ["{filters.author}]"'

    rows = conn[database_name][place_collection_name].find(
        {"author_id": filters.author} if filters.author else {}, limit=filters.limit, skip=filters.offset
    )

    async for row in rows:
        slug = row["slug"]
        author = await get_profile_by_username(conn, target_username=row["author_id"])
        await get_tags(conn, slug)
        favorites_count = await get_favorites_count_for_place(conn, slug)
        favorited_by_user = await is_place_favorited_by_user(conn, slug, username)
        places.append(
            PlaceInDB(
                **row,
                author=author,
                created_at=ObjectId(row["_id"]).generation_time,
                favorites_count=favorites_count,
                favorited=favorited_by_user,
            )
        )
    return places
