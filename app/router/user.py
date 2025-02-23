from fastapi import APIRouter, HTTPException, Request, status

from app.services.user.crud import get_current_user
from app.services.user.models import User
from app.services.user.schemas import User as UserSchema

router = APIRouter()


@router.get(
    "/me",
    response_model=UserSchema,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息，包括用户名、邮箱、姓名和账户状态。",
    responses={
        200: {
            "description": "成功返回当前用户信息",
            "content": {
                "application/json": {
                    "example": {
                        "username": "test",
                        "email": "test@example.com",
                        "display_name": None,
                        "avatar_url": "https://www.gravatar.com/avatar/098f6bcd4621d373cade4e832627b4f6?s=100x100&d=retro",
                        "role": "user",
                        "is_active": False,
                        "id": 1,
                        "created_at": "2025-02-20T11:36:45.530878+08:00",
                        "last_login": "2025-02-22T00:15:56.934187+08:00",
                        "last_login_ip": "xxx.xxx.xxx.xxx",
                    }
                }
            },
        },
        401: {
            "description": "未授权，缺少或无效的 Bearer token",
            "content": {
                "application/json": {
                    "example": {"detail": "Authorization token missing or invalid"}
                }
            },
        },
        404: {
            "description": "未找到用户，token 验证通过但未能找到对应的用户",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def get_me(request: Request):
    """
    获取当前登录用户的详细信息
    """
    # 从请求头获取 Bearer token
    authorization: str | None = request.headers.get("Authorization")

    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 提取 token 字符串
    token = authorization[7:]

    user = get_current_user(token)

    return UserSchema.model_validate(await User.get(username=user["sub"]))
