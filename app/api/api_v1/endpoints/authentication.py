
from fastapi import APIRouter, Body, Depends
from starlette.status import HTTP_201_CREATED

from ....db.mongodb import AsyncIOMotorClient, get_database
from ....models.user import UserInCreate, UserInLogin, UserInResponse

from ....services.user import create_user_service
from ....services.authentication import authentication_service

router = APIRouter()


@router.post("/users/login", response_model=UserInResponse, tags=["authentication"])
async def login(
        user: UserInLogin = Body(..., embed=True),
        db: AsyncIOMotorClient = Depends(get_database),
):
    return await authentication_service(request=user, conn=db)


@router.post(
    "/users",
    response_model=UserInResponse,
    tags=["authentication"],
    status_code=HTTP_201_CREATED,
)
async def register(
        user: UserInCreate = Body(..., embed=True),
        db: AsyncIOMotorClient = Depends(get_database),
):
    return await create_user_service(user=user, conn=db)
