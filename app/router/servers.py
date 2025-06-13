from typing import Annotated

from fastapi import (
    APIRouter,
    Form,
    HTTPException,
    Query,
    Request,
    status,
)

from app.services.servers.crud import (
    AddGalleryImage,
    GetAllPlayersNum,
    GetGallerylist,
    GetServer_by_id,
    GetServer_by_id_editor,
    GetServerOwners_by_id,
    GetServers,
    RemoveGalleryImage,
    update_server_by_id,
)
from app.services.servers.schemas import (
    GallerySchema,
    GetServerManagers,
    ServerDetail,
    ServerFilter,
    ServerGallery,
    ServerList,
    ServerTotalPlayers,
    UpdateServerRequest,
)

router = APIRouter()


# 获取服务器列表
@router.get(
    "/servers",
    response_model=ServerList,
    summary="获取服务器列表",
    responses={
        200: {
            "description": "成功获取服务器列表",
            "content": {
                "application/json": {
                    "example": {
                        "server_list": [
                            {
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
                                    "delay": 59.97,
                                    "version": "1.21.60",
                                    "motd": {
                                        "plain": "服务器名称 2",
                                        "html": "<p>服务器名称 2</p>",
                                        "minecraft": "服务器名称 2",
                                        "ansi": "\u001b[0m 服务器名称 2\u001b[0m",
                                    },
                                    "icon": None,
                                },
                                "permission": "owner",
                                "cover_url": "/static/cover.png",
                            }
                        ],
                        "total_member": 1,
                        "total": 1,
                        "random_seed": 123456,
                    }
                }
            },
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
    is_member: bool = Query(True, description="是否为成员服务器"),
    modes: str | None = Query(None, description="模式"),
    authModes: list[str] = Query(["OFFLINE", "YGGDRASIL", "OFFICIAL"]),
    tags: list[str] = Query(None),
    limit: int = Query(5, ge=1),
    offset: int = Query(0, ge=0),
    random: bool = Query(True),
    seed: int | None = Query(None, ge=0),
):
    """
    获取服务器列表。
    """
    if limit is not None and limit > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="limit 不能超过 50"
        )
    user = request.state.user.id if request.state.user else None
    filter = ServerFilter(
        is_member=is_member,
        modes=modes,
        authModes=authModes,
        tags=tags,
    )
    return await GetServers(
        limit=limit,
        offset=offset,
        is_random=random,
        seed=seed,
        user=user,
        filter=filter,
    )


# 获取服务器的具体信息
@router.get(
    "/servers/info/{server_id}",
    response_model=ServerDetail,
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
                            "delay": 59.97,
                            "version": "1.21.60",
                            "motd": {
                                "plain": "服务器名称 2",
                                "html": "<p>服务器名称 2</p>",
                                "minecraft": "服务器名称 2",
                                "ansi": "\u001b[0m 服务器名称 2\u001b[0m",
                            },
                            "icon": None,
                        },
                        "permission": "guest",
                        "cover_url": "/static/cover.png",
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
    user = request.state.user.id if request.state.user else None
    server = await GetServer_by_id(server_id, user)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器"
        )
    return server


@router.get(
    "/servers/{server_id}/editor",
    response_model=ServerDetail,
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
        404: {
            "description": "未找到该服务器",
            "content": {"application/json": {"example": {"detail": "未找到该服务器"}}},
        },
    },
)
async def get_server_editor(server_id: int, request: Request):
    """
    获取指定 ID 服务器的详细信息（编辑者）。
    """
    current_user = request.state.user
    if server := await GetServer_by_id_editor(server_id, current_user):
        return server
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该服务器")


@router.put(
    "/servers/{server_id}",
    response_model=ServerDetail,
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
    request: Request,
):
    """
    更新指定 ID 服务器的详细信息（编辑者）。
    """
    current_user = request.state.user
    return await update_server_by_id(server_id, update_data, current_user)


# 返回这个服务器的所有管理人员
@router.get(
    "/servers/{server_id}/managers",
    response_model=GetServerManagers,
    summary="获取服务器的所有管理人员",
    response_description="成功获取服务器的所有管理人员",
    responses={
        200: {
            "description": "成功获取服务器的所有管理人员",
            "content": {
                "application/json": {
                    "example": {
                        "owners": [
                            {
                                "id": 1,
                                "display_name": "服主A",
                                "role": "owner",
                                "is_active": True,
                                "avatar_url": "/static/avatar1.png",
                            }
                        ],
                        "admins": [
                            {
                                "id": 2,
                                "display_name": "管理员B",
                                "role": "admin",
                                "is_active": True,
                                "avatar_url": "/static/avatar2.png",
                            }
                        ],
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
async def get_server_managers(server_id: int):
    """
    获取指定 ID 服务器的所有管理人员。
    """
    return await GetServerOwners_by_id(server_id)


@router.get(
    "/servers/{server_id}/gallerys",
    response_model=ServerGallery,
    summary="获取服务器的相册",
    response_description="成功获取服务器的相册",
    responses={
        200: {
            "description": "成功获取服务器的相册",
            "content": {
                "application/json": {
                    "example": {
                        "id": 2,
                        "name": "服务器名称",
                        "gallerys_url": [
                            {
                                "id": 10,
                                "title": "建筑全景",
                                "description": "主城鸟瞰图",
                                "image_url": "/static/gallery1.png",
                            },
                            {
                                "id": 11,
                                "title": "活动合影",
                                "description": "周年庆典合影",
                                "image_url": "/static/gallery2.png",
                            },
                        ],
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
    response_description="成功添加服务器画册图片",
    responses={
        201: {
            "description": "成功添加服务器画册图片",
            "content": {
                "application/json": {"example": {"detail": "成功添加服务器画册图片"}}
            },
        },
        401: {
            "description": "无权限操作",
            "content": {"application/json": {"example": {"detail": "无权限操作"}}},
        },
        404: {
            "description": "未找到服务器",
            "content": {"application/json": {"example": {"detail": "未找到该服务器"}}},
        },
    },
)
async def add_server_gallerys(
    server_id: int,
    gallery_data: Annotated[GallerySchema, Form()],
    request: Request,
):
    """
    添加服务器画册图片。
    """
    current_user = request.state.user
    await GetServer_by_id_editor(server_id, current_user)
    await AddGalleryImage(server_id, gallery_data)
    return {"detail": "成功添加服务器画册图片"}


# 删除服务器画册图片
@router.delete(
    "/servers/{server_id}/gallerys/{image_id}",
    summary="删除服务器画册图片",
    status_code=status.HTTP_200_OK,
    response_description="成功删除服务器画册图片",
    responses={
        200: {
            "description": "成功删除服务器画册图片",
            "content": {
                "application/json": {"example": {"detail": "成功删除服务器画册图片"}}
            },
        },
        401: {
            "description": "无权限操作",
            "content": {"application/json": {"example": {"detail": "无权限操作"}}},
        },
        404: {
            "description": "未找到服务器或图片",
            "content": {
                "application/json": {"example": {"detail": "未找到该服务器或图片"}}
            },
        },
    },
)
async def remove_server_gallerys(
    server_id: int,
    image_id: int,
    request: Request,
):
    """
    删除服务器画册图片。
    """
    current_user = request.state.user
    await GetServer_by_id_editor(server_id, current_user)
    await RemoveGalleryImage(server_id, image_id)
    return {"detail": "成功删除服务器画册图片"}


# 获取所有服务器玩家总数
@router.get(
    "/servers/players",
    summary="获取所有服务器玩家总数",
    response_model=ServerTotalPlayers,
    response_description="成功获取所有服务器玩家总数",
    responses={
        200: {
            "description": "成功获取所有服务器玩家总数",
            "content": {"application/json": {"example": {"total_players": 1234}}},
        }
    },
)
async def get_all_servers_players() -> ServerTotalPlayers:
    """
    获取所有服务器的玩家总数。
    """
    return await GetAllPlayersNum()
