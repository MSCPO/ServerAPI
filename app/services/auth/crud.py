from datetime import datetime
from zoneinfo import ZoneInfo

import httpx

from app.config import settings
from app.log import logger
from app.services.user.models import User


HCAPTCHA_VERIFY_URL = "https://api.hcaptcha.com/siteverify"


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
        return result.get("success", False)


async def update_last_login(user: User, ip: str):
    # 获取上海时区的当前时间
    user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
    user.last_login_ip = ip
    # 保存用户数据
    await user.save(update_fields=["last_login", "last_login_ip"])
