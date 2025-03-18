import jwt

from app.config import settings
from app.services.auth.schemas import jwt_data
from app.services.conn.redis import redis_client


def create_access_token(data: jwt_data) -> str:
    return jwt.encode(
        data.model_dump(), settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )


async def verify_token(token: str) -> None | dict:
    if await redis_client.get(f"token:invalid:{token}"):
        return None
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None
