from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import Request

from app.config import settings
from app.log import logger
from app.services.auth.schemas import AuthToken, UserLogin
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


async def login_user(user: UserLogin, request: Request) -> AuthToken:
    from fastapi import HTTPException, status

    from app.services.auth.auth import create_access_token
    from app.services.auth.crud import update_last_login, verify_hcaptcha
    from app.services.auth.schemas import AuthToken, JWTData
    from app.services.user.models import User
    from app.services.utils import verify_password

    if not await verify_hcaptcha(user.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hCaptcha response"
        )
    if "@" in user.username_or_email:
        db_user = await User.get_or_none(email=user.username_or_email)
    else:
        db_user = await User.get_or_none(username=user.username_or_email)
    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    client_ip = request.headers.get("X-Forwarded-For") or (
        request.client.host if request.client else None
    )
    if client_ip is not None:
        await update_last_login(db_user, client_ip)
    access_token = create_access_token(
        data=JWTData(sub=db_user.username, id=db_user.id)
    )
    return AuthToken.model_validate(
        {"access_token": access_token, "token_type": "bearer"}
    )
