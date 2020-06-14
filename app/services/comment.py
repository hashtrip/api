from typing import List, Optional


from ..models.comment import CommentInCreate, CommentInDB
from ..db.mongodb import AsyncIOMotorClient
from ..core.config import comments_collection_name, database_name
from .profile import get_profile_service


async def get_comments(
    conn: AsyncIOMotorClient, slug: str, username: Optional[str] = None
) -> List[CommentInDB]:
    comments: List[CommentInDB] = []
    rows = conn[database_name][comments_collection_name].find(
        {"slug": slug},  # "username": username
    )
    async for row in rows:
        author = await get_profile_service(conn, username=row["username"])
        comments.append(CommentInDB(**row, author=author.profile))
    return comments


async def create_comment(
    conn: AsyncIOMotorClient, slug: str, comment: CommentInCreate, username: str
) -> CommentInDB:
    comment_doc = comment.dict()
    comment_doc["slug"] = slug
    comment_doc["username"] = username
    await conn[database_name][comments_collection_name].insert_one(comment_doc)
    author = await get_profile_service(conn, username=username)
    return CommentInDB(**comment_doc, author=author.profile)


async def delete_comment(conn: AsyncIOMotorClient, id: int, username: str):
    await conn[database_name][comments_collection_name].delete_many(
        {"_id": id, "username": username}
    )
