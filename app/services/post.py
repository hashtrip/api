from typing import List, Optional
from bson import ObjectId
from slugify import slugify
from datetime import datetime

from ..models.post import (
    PostFilterParams,
    PostInCreate,
    PostInDB,
    PostInUpdate,
)
from ..db.mongodb import AsyncIOMotorClient
from ..db.repositories.profile_repository import get_profile_by_username
from ..core.config import (
    database_name,
    likes_collection_name,
    users_collection_name,
    post_collection_name,
)
from .tag import create_tags_that_not_exist, get_tags


async def is_post_liked_by_user(
    conn: AsyncIOMotorClient, slug: str, username: str
) -> bool:
    user_doc = await conn[database_name][users_collection_name].find_one(
        {"username": username}, projection={"id": True}
    )
    post_doc = await conn[database_name][post_collection_name].find_one(
        {"slug": slug}, projection={"id": True}
    )
    if post_doc and user_doc:
        count = await conn[database_name][likes_collection_name].count_documents(
            {"user_id": user_doc["_id"], "post_id": post_doc["_id"]}
        )
        return count > 0
    else:
        raise RuntimeError(
            f"没有找到对应的user_id或post_id,"
            f" 用户名={username} user={user_doc},slug={slug} post={post_doc}"
        )


async def add_post_to_likes(conn: AsyncIOMotorClient, slug: str, username: str):
    user_doc = await conn[database_name][users_collection_name].find_one(
        {"username": username}, projection={"id": True}
    )
    post_doc = await conn[database_name][post_collection_name].find_one(
        {"slug": slug}, projection={"id": True}
    )
    if post_doc and user_doc:
        await conn[database_name][likes_collection_name].insert_one(
            {"user_id": user_doc["_id"], "post_id": post_doc["_id"]}
        )
    else:
        raise RuntimeError(
            f"没有找到对应的user_id或post_id,"
            f" 用户名={username} user_id={user_doc},slug={slug} post_id={post_doc}"
        )


async def remove_post_from_likes(
    conn: AsyncIOMotorClient, slug: str, username: str
):
    user_doc = await conn[database_name][users_collection_name].find_one(
        {"username": username}
    )
    post_doc = await conn[database_name][post_collection_name].find_one(
        {"slug": slug}
    )
    if post_doc and user_doc:
        await conn[database_name][likes_collection_name].delete_many(
            {"user_id": user_doc["_id"], "post_id": post_doc["_id"]}
        )
    else:
        raise RuntimeError(
            f"没有找到对应的user_id或post_id,"
            f" 用户名={username} user_id={user_doc},slug={slug} post_id={post_doc}"
        )


async def get_likes_count_for_post(conn: AsyncIOMotorClient, slug: str) -> int:
    post_doc = await conn[database_name][post_collection_name].find_one(
        {"slug": slug}, projection={"id": True}
    )
    if post_doc:
        return await conn[database_name][likes_collection_name].count_documents(
            {"post_id": post_doc["_id"]}
        )
    else:
        raise RuntimeError(f"没有找到对应的post_id," f" slug={slug} post_id={post_doc}")


async def get_post_by_slug(
    conn: AsyncIOMotorClient, slug: str, username: Optional[str] = None
) -> PostInDB:
    post_doc = await conn[database_name][post_collection_name].find_one(
        {"slug": slug}
    )
    if post_doc:
        post_doc["likes_count"] = await get_likes_count_for_post(conn, slug)
        post_doc["liked"] = await is_post_liked_by_user(conn, slug, username) if username else False
        post_doc["author"] = await get_profile_by_username(conn, target_username=post_doc["author_id"])

        return PostInDB(
            **post_doc, created_at=ObjectId(post_doc["_id"]).generation_time
        )


async def create_post_by_slug(
    conn: AsyncIOMotorClient, post: PostInCreate, username: str
) -> PostInDB:
    slug = slugify(post.title)
    post_doc = post.dict()
    post_doc["slug"] = slug
    post_doc["author_id"] = username
    post_doc["updated_at"] = datetime.now()
    await conn[database_name][post_collection_name].insert_one(post_doc)

    if post.tag_list:
        await create_tags_that_not_exist(conn, post.tag_list)

    author = await get_profile_by_username(conn, target_username=username)
    return PostInDB(
        **post_doc,
        created_at=ObjectId(post_doc["_id"]).generation_time,
        author=author,
        likes_count=1,
        liked=True,
    )


async def update_post_by_slug(
    conn: AsyncIOMotorClient, slug: str, post: PostInUpdate, username: str
) -> PostInDB:
    dbpost = await get_post_by_slug(conn, slug, username)

    if post.title:
        dbpost.slug = slugify(post.title)
        dbpost.title = post.title
    dbpost.body = post.body if post.body else dbpost.body
    dbpost.description = (
        post.description if post.description else dbpost.description
    )
    if post.tag_list:
        await create_tags_that_not_exist(conn, post.tag_list)
        dbpost.tag_list = post.tag_list

    dbpost.updated_at = datetime.now()
    await conn[database_name][post_collection_name].repost_one(
        {"slug": slug, "author_id": username}, dbpost.dict()
    )

    dbpost.created_at = ObjectId(dbpost.id).generation_time
    return dbpost


async def delete_post_by_slug(conn: AsyncIOMotorClient, slug: str, username: str):
    await conn[database_name][post_collection_name].delete_many(
        {"author_id": username, "slug": slug}
    )


async def get_user_posts(
    conn: AsyncIOMotorClient, username: str, limit=20, offset=0
) -> List[PostInDB]:
    posts: List[PostInDB] = []
    post_docs = conn[database_name][post_collection_name].find(
        {"author_id": username}, limit=limit, skip=offset
    )
    async for row in post_docs:
        slug = row["slug"]
        author = await get_profile_by_username(conn, target_username=row["author_id"])
        await get_tags(conn, slug, doc_name=post_collection_name)
        likes_count = await get_likes_count_for_post(conn, slug)
        liked_by_user = await is_post_liked_by_user(conn, slug, username) if username else False
        posts.append(
            PostInDB(
                **row,
                author=author,
                created_at=ObjectId(row["_id"]).generation_time,
                likes_count=likes_count,
                liked=liked_by_user,
            )
        )
    return posts


async def get_posts_with_filters(
    conn: AsyncIOMotorClient, filters: PostFilterParams, username: Optional[str] = None
) -> List[PostInDB]:
    posts: List[PostInDB] = []
    base_query = {}

    if filters.tag:
        base_query["tag_list"] = f'$all: ["{filters.tag}"]'

    if filters.liked:
        base_query["slug"] = f'$in: ["{filters.liked}"]'

    if filters.author:
        base_query["author"] = f'$in: ["{filters.author}]"'

    rows = conn[database_name][post_collection_name].find(
        {}, limit=filters.limit, skip=filters.offset
    )

    async for row in rows:
        slug = row["slug"]
        author = await get_profile_by_username(conn, target_username=row["author_id"])
        await get_tags(conn, slug, doc_name=post_collection_name)
        likes_count = await get_likes_count_for_post(conn, slug)
        liked_by_user = await is_post_liked_by_user(conn, slug, username) if username else False
        posts.append(
            PostInDB(
                **row,
                author=author,
                created_at=ObjectId(row["_id"]).generation_time,
                likes_count=likes_count,
                liked=liked_by_user,
            )
        )
    return posts
