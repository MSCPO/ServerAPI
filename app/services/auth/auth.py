from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import jwt

from app.config import settings


def create_access_token(data: dict, expires_delta: None | timedelta = None):
    if expires_delta:
        expire = datetime.now(ZoneInfo("Asia/Shanghai")) + expires_delta
    else:
        expire = datetime.now(ZoneInfo("Asia/Shanghai")) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = data.copy()
    to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str):
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
