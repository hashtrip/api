from typing import Optional

from fastapi import APIRouter, Depends, Path
from starlette.exceptions import HTTPException
from starlette.status import HTTP_422_UNPROCESSABLE_ENTITY

from ....core.jwt import get_current_user_authorizer
from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.profile import ProfileInResponse
from ....models.user import User
from ....services.profile import get_profile_service, follow_user_service, unfollow_user_service

router = APIRouter()


@router.get("/profiles/{username}", response_model=ProfileInResponse, tags=["profiles"])
async def retrieve_profile(
    username: str = Path(..., min_length=1),
    user: Optional[User] = Depends(get_current_user_authorizer(required=False)),
    db: AsyncIOMotorClient = Depends(get_database),
):
    return await get_profile_service(user=user, username=username, conn=db)


@router.post(
    "/profiles/{username}/follow", response_model=ProfileInResponse, tags=["profiles"]
)
async def follow_user(
    username: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    return await follow_user_service(user=user, username=username, conn=db) 


@router.delete(
    "/profiles/{username}/follow", response_model=ProfileInResponse, tags=["profiles"]
)
async def describe_from_user(
    username: str = Path(..., min_length=1),
    user: User = Depends(get_current_user_authorizer()),
    db: AsyncIOMotorClient = Depends(get_database),
):
    return await unfollow_user_service(username=username, user=user, conn=db)
