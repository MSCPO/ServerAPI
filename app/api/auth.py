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


@router.post("/login", response_model=dict, summary="token 获取")
async def login(user: UserLogin):
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


@router.get("/hcaptcha-site-key", summary="获取Hcaptcha site-key")
def get_hcaptcha_site_key():
    if site_key := settings.HCAPTCHA_SITE_KEY:
        return {"hcaptcha_site_key": site_key}
    else:
        return JSONResponse(
            status_code=400, content={"message": "hCaptcha site key not configured"}
        )
