from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.auth.auth import create_access_token
from app.auth.crud import (
    get_user_by_username,
    update_last_login,
    verify_password,
    verify_recaptcha,
)
from app.auth.schemas import UserLogin
from app.config import settings


class Auth_Token(BaseModel):
    access_token: str = Field(..., title="访问令牌", description="JWT 访问令牌")
    token_type: str = Field("bearer", title="令牌类型", description="令牌类型")


router = APIRouter()


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
    db_user = await get_user_by_username(user.username)
    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    await update_last_login(db_user, request.client.host)
    # 创建并返回 JWT token
    access_token = create_access_token(data={"sub": db_user.username})
    return Auth_Token.model_validate(
        {"access_token": access_token, "token_type": "bearer"}
    )


class recapcha_sitekey(BaseModel):
    recapcha_sitekey: str


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
