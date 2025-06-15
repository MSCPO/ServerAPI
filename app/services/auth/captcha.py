"""hCaptcha 验证相关的工具函数"""

import httpx

from app.config import settings
from app.log import logger

HCAPTCHA_VERIFY_URL = "https://api.hcaptcha.com/siteverify"


async def verify_hcaptcha(captcha_response: str) -> bool:
    """验证 hCaptcha 响应"""
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
