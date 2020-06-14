from typing import List

from ..db.mongodb import AsyncIOMotorClient
from ..models.tag import TagInDB
from ..core.config import database_name, tags_collection_name, place_collection_name


async def fetch_all_tags(conn: AsyncIOMotorClient) -> List[TagInDB]:
    tags = []
    rows = conn[database_name][tags_collection_name].find()
    async for row in rows:
        tags.append(TagInDB(**row))

    return tags


async def get_tags(conn: AsyncIOMotorClient, slug: str, doc_name: str = place_collection_name) -> List[TagInDB]:
    tags = []
    place_tags = await conn[database_name][doc_name].find_one(
        {"slug": slug}, projection={"tag_list": True}
    )
    for row in place_tags["tag_list"]:
        tags.append(TagInDB(tag=row))

    return tags


async def create_tags_that_not_exist(conn: AsyncIOMotorClient, tags: List[str]):
    dbconn = conn[database_name][tags_collection_name]
    existing = await dbconn.find({}, projection={"_id": False}).to_list(None)
    existing = list(map(lambda x: x["tag"], existing))

    filtered = list(filter(lambda x: x not in existing, tags))

    await dbconn.insert_many(
        [{"tag": tag} for tag in filtered]
    ) if filtered else None
