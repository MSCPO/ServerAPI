import httpx
from passlib.context import CryptContext
from pydantic import BaseModel
from tortoise.exceptions import DoesNotExist

from .. import logger
from ..config import settings
from ..models import User

# 密码加密和验证工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

HCAPTCHA_VERIFY_URL = "https://hcaptcha.com/siteverify"


class UserInDB(BaseModel):
    username: str
    email: str
    hashed_password: str


class UserLogin(BaseModel):
    username: str
    password: str
    captcha_response: str


# 获取用户信息
async def get_user_by_username(username: str):
    try:
        return await User.get(username=username)
    except DoesNotExist:
        return None


# 验证密码
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


async def verify_hcaptcha(captcha_response: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            HCAPTCHA_VERIFY_URL,
            data={
                "secret": settings.HCAPTCHA_SECRET_KEY,
                "response": captcha_response,
            },
        )
        result: dict = response.json()
        logger.info(result)
        return result.get("success")
