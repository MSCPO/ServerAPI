from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse

from app.auth.auth import create_access_token
from app.auth.auth_crud import (
    UserLogin,
    get_user_by_username,
    verify_hcaptcha,
    verify_password,
)
from app.config import settings

router = APIRouter()


# 用户登录，获取 token
@router.post(
    "/login",
    response_model=dict,
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
            "description": "hCaptcha 验证失败",
            "content": {
                "application/json": {"example": {"detail": "Invalid hCaptcha response"}}
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
async def login(user: UserLogin):
    """
    用户登录，验证凭证并返回 JWT token。

    - `user`: 包含用户名、密码和验证码响应的登录数据。

    成功时返回访问令牌，失败时返回错误信息。
    """
    if not await verify_hcaptcha(user.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hCaptcha response"
        )
    db_user = await get_user_by_username(user.username)
    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 创建并返回 JWT token
    access_token = create_access_token(data={"sub": db_user.username})
    return {"access_token": access_token, "token_type": "bearer"}


# 获取 Hcaptcha site-key
@router.get(
    "/hcaptcha-site-key",
    summary="获取Hcaptcha site-key",
    responses={
        200: {
            "description": "成功获取 hCaptcha site-key",
            "content": {
                "application/json": {
                    "example": {"hcaptcha_site_key": "your_site_key_here"}
                }
            },
        },
        400: {
            "description": "hCaptcha site-key 未配置",
            "content": {
                "application/json": {
                    "example": {"message": "hCaptcha site key not configured"}
                }
            },
        },
    },
)
def get_hcaptcha_site_key():
    """
    获取 hCaptcha 的站点密钥（site-key）。

    如果 hCaptcha site-key 已配置，返回该 key。若未配置，则返回错误信息。
    """
    if site_key := settings.HCAPTCHA_SITE_KEY:
        return {"hcaptcha_site_key": site_key}
    else:
        return JSONResponse(
            status_code=400, content={"message": "hCaptcha site key not configured"}
        )
