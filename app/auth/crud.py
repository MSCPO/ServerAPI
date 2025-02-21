from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from passlib.context import CryptContext
from tortoise.exceptions import DoesNotExist

from app.config import settings
from app.log import logger
from app.user.models import User

# 密码加密和验证工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

RECAPTCHA_VERIFY_URL = "https://recaptcha.net/recaptcha/api/siteverify"


# 获取用户信息
async def get_user_by_username(username: str):
    try:
        return await User.get(username=username)
    except DoesNotExist:
        return None


# 验证密码
def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


async def verify_recaptcha(captcha_response: str) -> bool:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            RECAPTCHA_VERIFY_URL,
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": captcha_response,
            },
        )
        result: dict = response.json()
        logger.info(result)
        return result.get("success")


async def update_last_login(user: User, ip: str):
    # 获取上海时区的当前时间
    user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
    user.last_login_ip = ip
    # 保存用户数据
    await user.save(update_fields=["last_login", "last_login_ip"])
