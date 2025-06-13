import asyncio

from fastapi import APIRouter, HTTPException, Request, status

from app.services.user.models import User, UserServer
from app.services.user.schemas import User as UserSchema
from app.services.user.schemas import UserPublicInfo
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
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "username": "testuser",
                        "email": "test@example.com",
                        "display_name": "测试用户",
                        "role": "user",
                        "is_active": True,
                        "created_at": "2025-06-14T12:00:00",
                        "last_login": "2025-06-14T12:00:00",
                        "last_login_ip": "127.0.0.1",
                        "avatar_url": "/static/avatar.png",
                        "servers": [["owner", 2], ["admin", 3]],
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
            "content": {"application/json": {"example": {"detail": "用户不存在"}}},
        },
    },
)
async def get_me(request: Request):
    """
    获取当前登录用户的详细信息
    """
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token missing or invalid",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_data: User = await User.get(id=user.id)

    # 并发获取头像和用户服务器数据
    avatar_task = get_user_avatar_url(user_data)
    user_servers_task = UserServer.filter(user=user_data)
    avatar_url, user_servers = await asyncio.gather(avatar_task, user_servers_task)

    # 并发获取每个 UserServer 关联的 Server 对象，避免顺序 await 带来的性能损失
    server_objs = await asyncio.gather(*(us.server for us in user_servers))
    servers = [(us.role, server.id) for us, server in zip(user_servers, server_objs)]

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


@router.get(
    "/user/{user_id}/public",
    response_model=UserPublicInfo,
    summary="获取用户公开信息",
    description="根据用户 ID 获取用户的公开基本信息，无需鉴权。",
    responses={
        200: {
            "description": "成功返回用户公开信息",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "display_name": "公开用户",
                        "role": "user",
                        "is_active": True,
                        "avatar_url": "/static/avatar_public.png",
                        "created_at": "2025-06-14T12:00:00",
                        "last_login": "2025-06-14T12:00:00",
                        "servers": [["owner", 2], ["admin", 3]],
                    }
                }
            },
        },
        404: {
            "description": "未找到指定用户",
            "content": {"application/json": {"example": {"detail": "用户不存在"}}},
        },
    },
)
async def get_user_public_info(user_id: int):
    # 查询用户是否存在
    user = await User.get_or_none(id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="用户不存在")

    # 并发获取头像和用户服务器数据
    avatar_task = get_user_avatar_url(user)
    user_servers_task = UserServer.filter(user=user).prefetch_related("server").all()
    avatar_url, user_servers = await asyncio.gather(avatar_task, user_servers_task)

    # 处理服务器列表
    servers = [(us.role, us.server.id) for us in user_servers]

    # 构建并返回公开信息模型
    return UserPublicInfo(
        id=user.id,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        avatar_url=avatar_url,
        created_at=user.created_at,
        last_login=user.last_login,
        servers=servers,
    )
