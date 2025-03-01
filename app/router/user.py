from fastapi import APIRouter, HTTPException, Request, status

from app.services.user.crud import get_current_user
from app.services.user.models import User, UserServer
from app.services.user.schemas import User as UserSchema
from app.services.user.utils import get_user_avatar_url

router = APIRouter()


@router.get(
    "/me",
    response_model=UserSchema,
    summary="获取当前用户信息",
    description="获取当前登录用户的详细信息，包括用户名、邮箱、姓名和账户状态。",
    responses={
        200: {
            "description": "成功返回当前用户信息",
        },
        401: {
            "description": "未授权，缺少或无效的 Bearer token",
        },
        404: {
            "description": "未找到用户，token 验证通过但未能找到对应的用户",
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

    token = authorization.split(" ")[1]

    user = await get_current_user(token)
    user_data: User = await User.get(username=user["sub"])

    avatar_url = await get_user_avatar_url(user_data)

    UserServer_instance: list[UserServer] = await UserServer.filter(user=user_data)
    servers = [
        (server.role, (await server.server).id) for server in UserServer_instance
    ]

    return UserSchema(
        id=user_data.id,
        username=user_data.username,
        email=user_data.email,
        display_name=user_data.display_name,
        role=user_data.role,
        is_active=user_data.is_active,
        created_at=user_data.created_at,
        last_login=user_data.last_login,
        last_login_ip=user_data.last_login_ip,
        avatar_url=avatar_url,
        servers=servers,
    )
