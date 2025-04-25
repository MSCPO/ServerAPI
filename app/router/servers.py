from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Form,
    HTTPException,
    Query,
    Request,
    status,
)

from app.services.auth.schemas import jwt_data
from app.services.servers.crud import (
    AddGalleryImage,
    GetGallerylist,
    GetServer_by_id,
    GetServer_by_id_editor,
    GetServerOwners_by_id,
    GetServers,
    RemoveGalleryImage,
)
from app.services.servers.models import Server
from app.services.servers.schemas import (
    AddServerGallerys,
    GetServerGallerys,
    GetServerIdShowAPI,
    GetServerManagers,
    GetServerShowAPI,
    UpdateServerRequest,
)
from app.services.servers.utils import (
    validate_and_upload_cover,
    validate_description,
    validate_ip,
    validate_link,
    validate_name,
    validate_tags,
    validate_version,
)
from app.services.user.crud import get_current_user
from app.services.user.models import User

router = APIRouter()


# 获取服务器列表
@router.get(
    "/servers",
    response_model=GetServerShowAPI,
    summary="获取服务器列表",
    responses={
        200: {
            "description": "成功获取服务器列表",
        },
        400: {
            "description": "无效的请求参数",
            "content": {
                "application/json": {"example": {"detail": "limit 不能超过 50"}}
            },
        },
    },
)
async def list_servers(
    request: Request,
    limit: int = Query(None, ge=1),
    offset: int = Query(0, ge=0),
):
    """
    获取服务器列表。

    - `limit`: 返回的服务器数量，默认为空，传入 1 及以上的值。
    - `offset`: 查询的起始位置，默认为 0。

    返回值为服务器列表，包含基本的服务器信息。
    """
    if limit is not None and limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="limit 不能超过 50"
        )
    authorization: str | None = request.headers.get("Authorization")
    current_user: jwt_data | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        current_user = await get_current_user(token)
    user = current_user.id if current_user else None
    return await GetServers(limit=limit, offset=offset, user=user)


# 获取服务器的具体信息
@router.get(
    "/servers/info/{server_id}",
    response_model=GetServerIdShowAPI,
    summary="获取对应服务器具体信息",
    responses={
        200: {
            "description": "成功获取指定服务器信息",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "name": "服务器名称",
                        "ip": "example.com:37581",
                        "type": "BEDROCK",
                        "version": "1.21",
                        "desc": "描述内容",
                        "link": "https://example.com",
                        "is_member": True,
                        "auth_mode": "OFFICIAL",
                        "tags": ["生存", "建筑", "原汁原味"],
                        "is_hide": False,
                        "status": {
                            "players": {"online": 0, "max": 15},
                            "delay": 59.96639499971934,
                            "version": "1.21.60",
                            "motd": {
                                "plain": "服务器名称 2",
                                "html": "<p>服务器名称 2</p>",
                                "minecraft": "服务器名称 2",
                                "ansi": "\u001b[0m 服务器名称 2\u001b[0m",
                            },
                            "icon": None,
                        },
                    }
                }
            },
        },
        404: {
            "description": "未找到该服务器",
            "content": {"application/json": {"example": {"detail": "未找到该服务器"}}},
        },
    },
)
async def get_server(server_id: int, request: Request):
    """
    获取指定 ID 服务器的详细信息。

    """
    authorization: str | None = request.headers.get("Authorization")

    current_user: jwt_data | None = None

    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        current_user = await get_current_user(token)
    user = current_user.id if current_user else None
    server = await GetServer_by_id(server_id, user)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器"
        )
    return server


@router.get(
    "/servers/{server_id}/editor",
    response_model=GetServerIdShowAPI,
    summary="获取对应服务器具体信息（编辑者）",
    responses={
        200: {
            "description": "成功获取指定服务器信息",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "name": "服务器名称",
                        "ip": "example.com:37581",
                        "type": "BEDROCK",
                        "version": "1.21",
                        "desc": "描述内容",
                        "link": "https://example.com",
                        "is_member": True,
                        "auth_mode": "OFFICIAL",
                        "tags": ["生存", "建筑", "原汁原味"],
                        "is_hide": False,
                        "status": {
                            "players": {"online": 0, "max": 15},
                            "delay": 59.96639499971934,
                            "version": "1.21.60",
                            "motd": {
                                "plain": "服务器名称 2",
                                "html": "<p>服务器名称 2</p>",
                                "minecraft": "服务器名称 2",
                                "ansi": "\u001b[0m 服务器名称 2\u001b[0m",
                            },
                            "icon": None,
                        },
                    }
                }
            },
        },
        401: {
            "description": "没权限编辑该服务器",
            "content": {
                "application/json": {
                    "example": {"detail": "你咩有权限编辑它！它拒绝了你！"}
                }
            },
        },
    },
)
async def get_server_editor(
    server_id: int, current_user: jwt_data = Depends(get_current_user)
):
    """
    获取指定 ID 服务器的详细信息（编辑者）。
    """
    if server := await GetServer_by_id_editor(server_id, current_user):
        return server
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器")


@router.put(
    "/servers/{server_id}",
    response_model=GetServerIdShowAPI,
    summary="更新对应服务器具体信息",
    responses={
        200: {
            "description": "成功更新服务器信息",
            "content": {"application/json": {"example": {"detail": "更新成功"}}},
        },
        400: {
            "description": "无效的请求参数",
            "content": {
                "application/json": {
                    "examples": {
                        "更新字段不能为空": {"detail": "更新字段不能为空"},
                        "tags 数量不能超过 7 个": {"detail": "tags 数量不能超过 7 个"},
                        "tags 长度限制为 1~4": {"detail": "tags 长度限制为 1~4"},
                        "简介必须大于 100 字": {"detail": "简介必须大于 100 字"},
                    }
                }
            },
        },
        404: {
            "description": "未找到该服务器",
            "content": {"application/json": {"example": {"detail": "未找到该服务器"}}},
        },
    },
)
async def update_server(
    server_id: int,
    update_data: Annotated[UpdateServerRequest, Form()],
    current_user: jwt_data = Depends(get_current_user),
):
    """
    更新指定 ID 服务器的详细信息（编辑者）。
    """
    # 获取用户是否有权限编辑该服务器
    await GetServer_by_id_editor(server_id, current_user)

    # 查找服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器"
        )

    # 字段校验
    if not update_data.name and not update_data.ip and not update_data.desc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="更新字段不能为空"
        )

    await validate_name(update_data.name)
    await validate_description(update_data.desc)
    await validate_tags(update_data.tags)
    await validate_ip(update_data.ip, server.type)
    await validate_version(update_data.version)
    await validate_link(update_data.link)

    # 封面文件处理
    if update_data.cover:
        cover_hash = await validate_and_upload_cover(update_data.cover)
        server.cover_hash = cover_hash  # 更新封面哈希值

    # 只更新允许的字段
    server.name = update_data.name
    server.ip = update_data.ip
    server.desc = update_data.desc
    server.tags = update_data.tags
    server.version = update_data.version
    server.link = update_data.link

    # 保存更新后的服务器信息
    await server.save_with_user(await User.get(id=current_user.id))

    # 返回更新后的服务器信息
    return await GetServer_by_id_editor(server_id, current_user)


# 返回这个服务器的所有管理人员
@router.get(
    "/servers/{server_id}/managers",
    response_model=GetServerManagers,
    summary="获取服务器的所有管理人员",
    responses={
        200: {
            "description": "成功获取服务器的所有管理人员",
        },
        404: {
            "description": "未找到该服务器",
            "content": {"application/json": {"example": {"detail": "未找到该服务器"}}},
        },
    },
)
async def get_server_managers(server_id: int):
    """
    获取指定 ID 服务器的所有管理人员。
    """
    return await GetServerOwners_by_id(server_id)


@router.get(
    "/servers/{server_id}/gallerys",
    response_model=GetServerGallerys,
    summary="获取服务器的相册",
    responses={
        200: {
            "description": "成功获取服务器的相册",
        },
        404: {
            "description": "未找到该服务器",
            "content": {"application/json": {"example": {"detail": "未找到该服务器"}}},
        },
    },
)
async def get_server_gallerys(server_id: int):
    """
    获取指定 ID 服务器的相册。
    """
    return await GetGallerylist(server_id)


# 添加服务器画册图片
@router.post(
    "/servers/{server_id}/gallerys",
    summary="添加服务器画册图片",
    status_code=status.HTTP_201_CREATED,
)
async def add_server_gallerys(
    server_id: int,
    gallery_data: Annotated[AddServerGallerys, Form()],
    current_user: jwt_data = Depends(get_current_user),
):
    # 获取用户是否有权限编辑该服务器
    await GetServer_by_id_editor(server_id, current_user)
    await AddGalleryImage(server_id, gallery_data)
    return {"detail": "成功添加服务器画册图片"}


# 删除服务器画册图片
@router.delete(
    "/servers/{server_id}/gallerys/{image_id}",
    summary="删除服务器画册图片",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_server_gallerys(
    server_id: int,
    image_id: int,
    current_user: jwt_data = Depends(get_current_user),
):
    # 获取用户是否有权限编辑该服务器
    await GetServer_by_id_editor(server_id, current_user)
    await RemoveGalleryImage(server_id, image_id)
    return {"detail": "成功删除服务器画册图片"}
