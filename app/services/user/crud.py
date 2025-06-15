from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.services.auth.auth import verify_token
from app.services.auth.schemas import JWTData
from app.services.user.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> JWTData:
    payload: JWTData = JWTData.model_validate(await verify_token(token))

    user = await User.get_or_none(username=payload.sub)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return payload


async def get_optional_user(request: Request) -> JWTData | None:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1]
        try:
            payload: JWTData = JWTData.model_validate(await verify_token(token))
            user = await User.get_or_none(username=payload.sub)
            return payload if user else None
        except Exception:
            return None
    return None
