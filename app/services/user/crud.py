from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer

from app.models import User
from app.services.auth.auth import verify_token
from app.services.auth.schemas import JWTData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> JWTData:
    token_data = await verify_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload: JWTData = JWTData.model_validate(token_data)

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
            token_data = await verify_token(token)
            if token_data is None:
                return None
            payload: JWTData = JWTData.model_validate(token_data)
            user = await User.get_or_none(username=payload.sub)
            return payload if user else None
        except Exception:
            return None
    return None
