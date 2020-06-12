from starlette.exceptions import HTTPException
from starlette.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from datetime import timedelta
from ..db.mongodb import AsyncIOMotorClient
from .user import create_user, get_user_by_email
from ..models.user import UserInLogin, UserInResponse, User
from ..core.config import ACCESS_TOKEN_EXPIRE_MINUTES
from ..core.jwt import create_access_token


async def authentication_service(request: UserInLogin, conn: AsyncIOMotorClient):
    user = await get_user_by_email(conn, request.email)
    print(user)
    if not user or not user.check_password(request.password):
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST, detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    token = create_access_token(
        data={"username": user.username}, expires_delta=access_token_expires
    )
    return UserInResponse(user=User(**user.dict(), token=token))
