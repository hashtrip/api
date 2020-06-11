from typing import Optional
from datetime import timedelta
from ..db.mongodb import AsyncIOMotorClient
from pydantic import EmailStr
from bson.objectid import ObjectId
from starlette.exceptions import HTTPException
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
    HTTP_422_UNPROCESSABLE_ENTITY,
)
from ..core.jwt import create_access_token
from ..core.config import database_name, users_collection_name, ACCESS_TOKEN_EXPIRE_MINUTES
from ..models.user import UserInCreate, UserInDB, UserInUpdate, UserInResponse, User
from ..db.repositories.user_repository import create_user, get_user, get_user_by_email, update_user

async def create_user_service(user: UserInCreate, conn: AsyncIOMotorClient):
    await check_free_username_and_email(conn, user.username, user.email)
    async with await conn.start_session() as s:
        async with s.start_transaction():
            dbuser = await create_user(conn, user)
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            token = create_access_token(
                data={"username": dbuser.username}, expires_delta=access_token_expires
            )

            return UserInResponse(user=User(**dbuser.dict(), token=token))

async def check_free_username_and_email(
        conn: AsyncIOMotorClient, username: Optional[str] = None, email: Optional[EmailStr] = None
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

