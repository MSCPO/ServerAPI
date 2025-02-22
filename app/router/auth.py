from fastapi import APIRouter, BackgroundTasks, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.services.auth.auth import create_access_token
from app.services.auth.crud import (
    update_last_login,
    verify_password,
    verify_recaptcha,
)
from app.services.auth.schemas import RegisterRequest, UserLogin
from app.services.conn.redis import redis_client
from app.services.user.models import User
from app.services.utils import generate_token, send_verification_email


class Auth_Token(BaseModel):
    access_token: str = Field(..., title="访问令牌", description="JWT 访问令牌")
    token_type: str = Field("bearer", title="令牌类型", description="令牌类型")


router = APIRouter()


async def get_real_client_ip(request: Request) -> str:
    """
    获取客户端真实的 IP 地址，如果存在反代理则从 X-Forwarded-For 中获取。
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    return forwarded_for.split(",")[0] if forwarded_for else request.client.host


# 用户登录，获取 token
@router.post(
    "/login",
    response_model=Auth_Token,
    summary="token 获取",
    responses={
        200: {
            "description": "成功登录，返回 JWT token",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "your_token_here",
                        "token_type": "bearer",
                    }
                }
            },
        },
        400: {
            "description": "reCAPTCHA 验证失败",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid reCAPTCHA response"}
                }
            },
        },
        401: {
            "description": "凭证无效，用户名或密码错误",
            "content": {
                "application/json": {"example": {"detail": "Invalid credentials"}}
            },
        },
    },
)
async def login(user: UserLogin, request: Request):
    """
    用户登录，验证凭证并返回 JWT token。

    - `user`: 包含用户名、密码和验证码响应的登录数据。

    成功时返回访问令牌，失败时返回错误信息。
    """
    if not await verify_recaptcha(user.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reCAPTCHA response"
        )
    db_user = await User.get_or_none(user.username)
    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 获取真实客户端 IP
    client_ip = await get_real_client_ip(request)
    await update_last_login(db_user, client_ip)

    # 创建并返回 JWT token
    access_token = create_access_token(data={"sub": db_user.username})
    return Auth_Token.model_validate(
        {"access_token": access_token, "token_type": "bearer"}
    )


class recapcha_sitekey(BaseModel):
    recapcha_sitekey: str = Field(
        ..., title="reCAPTCHA 站点密钥", description="reCAPTCHA 站点密钥"
    )


class RegisterResponse(BaseModel):
    message: str = Field(..., title="消息", description="注册成功消息")


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="用户注册",
    responses={
        200: {
            "description": "注册成功，返回注册成功消息",
            "content": {
                "application/json": {
                    "example": {"message": "验证邮件已发送，请查收您的邮箱"}
                }
            },
        },
        400: {
            "description": "reCAPTCHA 验证失败",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid reCAPTCHA response"}
                }
            },
        },
    },
)
async def register(request: RegisterRequest, background_tasks: BackgroundTasks):
    if not await verify_recaptcha(request.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reCAPTCHA response"
        )
    token = generate_token()
    redis_client.setex(f"verify:{token}", 900, request.email)
    background_tasks.add_task(send_verification_email, request.email, token)
    return {"message": "验证邮件已发送，请查收您的邮箱"}


# 获取 reCAPTCHA site-key
@router.get(
    "/reCAPTCHA_site_key",
    summary="reCAPTCHA site-key",
    response_model=recapcha_sitekey,
    responses={
        200: {
            "description": "成功获取 reCAPTCHA site-key",
            "content": {
                "application/json": {
                    "example": {"reCAPTCHA_site_key": "your_site_key_here"}
                }
            },
        },
        400: {
            "description": "reCAPTCHA site-key 未配置",
            "content": {
                "application/json": {
                    "example": {"message": "reCAPTCHA site key not configured"}
                }
            },
        },
    },
)
def get_reCAPTCHA_site_key():
    """
    获取 reCAPTCHA 的站点密钥（site-key）。

    如果 reCAPTCHA site-key 已配置，返回该 key。若未配置，则返回错误信息。
    """
    if site_key := settings.RECAPTCHA_SITE_KEY:
        return recapcha_sitekey(recapcha_sitekey=site_key)
    else:
        return JSONResponse(
            status_code=400, content={"message": "reCAPTCHA site key not configured"}
        )
