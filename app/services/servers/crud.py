import asyncio

from fastapi import HTTPException, status

from app.services.servers.models import (
    Server,
    ServerStatus,
)
from app.services.servers.schemas import (
    GetServer,
    GetServerIdShowAPI,
    GetServerManagers,
    GetServerShowAPI,
    GetServerStatusAPI,
    Motd,
    UserBase,
)
from app.services.user.models import UserServer
from app.services.user.utils import get_user_avatar_url


async def GetServers(limit: int | None = None, offset: int = 0) -> GetServerShowAPI:
    # 利用数据库 count() 查询总数，避免加载所有数据到内存中
    total_servers, total_member = await asyncio.gather(
        Server.all().count(), Server.filter(is_member=True).count()
    )

    # 构建分页查询
    query = Server.all().offset(offset)
    if limit is not None:
        query = query.limit(limit)
    server_query = await query

    # 转换数据（假设 model_validate 为数据转换方法）
    server_list = [GetServer.model_validate(server) for server in server_query]

    return GetServerShowAPI(
        server_list=server_list, total_member=total_member, total=total_servers
    )


async def GetServer_by_id(
    server_id: int, user: int | None
) -> None | GetServerIdShowAPI:
    # 首先查询服务器，如果不存在则直接返回 None
    server = await Server.get_or_none(id=server_id)
    if not server:
        return None

    # 并发查询服务器状态和用户在该服务器中的权限（user_server）
    server_status_task = ServerStatus.get_or_none(server=server)
    user_server_task = (
        UserServer.get_or_none(user=user, server=server_id)
        if user
        else asyncio.sleep(0, result=None)
    )
    server_status, user_server = await asyncio.gather(
        server_status_task, user_server_task
    )

    # 用户权限，如果不存在对应记录，默认为 "guest"
    permission = user_server.role if user_server else "guest"

    # 构造服务器状态数据，如果存在状态数据
    status_data = None
    if server_status and server_status.stat_data:
        stat_data = server_status.stat_data
        status_data = GetServerStatusAPI(
            players=stat_data["players"],
            delay=stat_data["delay"],
            version=stat_data["version"],
            motd=Motd(
                plain=stat_data["motd"]["plain"],
                html=stat_data["motd"]["html"],
                minecraft=stat_data["motd"]["minecraft"],
                ansi=stat_data["motd"]["ansi"],
            ),
            icon=stat_data["icon"],
        )

    return GetServerIdShowAPI(
        id=server.id,
        name=server.name,
        ip=None if server.is_hide else server.ip,
        type=server.type,
        version=server.version,
        desc=server.desc,
        link=server.link,
        is_member=server.is_member,
        auth_mode=server.auth_mode,
        tags=server.tags,
        is_hide=server.is_hide,
        status=status_data,
        permission=permission,
    )


async def GetServer_by_id_editor(
    server_id: int, current_user: dict
) -> GetServerIdShowAPI | None:
    """查看服务器详细信息（详细信息）"""

    # 并发查询服务器和当前用户在该服务器中的角色
    server, user_server = await asyncio.gather(
        Server.get_or_none(id=server_id),
        UserServer.get_or_none(user=current_user["id"], server=server_id),
    )

    if not user_server:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="你咩有权限编辑它！它拒绝了你！",
        )

    if not server:
        return None

    # 获取服务器状态信息
    server_status = await ServerStatus.get_or_none(server=server)

    # 用户权限
    permission = user_server.role  # 此时 user_server 已存在

    # 生成服务器状态数据
    status_data = None
    if server_status and server_status.stat_data:
        stat_data = server_status.stat_data
        status_data = GetServerStatusAPI(
            players=stat_data["players"],
            delay=stat_data["delay"],
            version=stat_data["version"],
            motd=Motd(
                plain=stat_data["motd"]["plain"],
                html=stat_data["motd"]["html"],
                minecraft=stat_data["motd"]["minecraft"],
                ansi=stat_data["motd"]["ansi"],
            ),
            icon=stat_data["icon"],
        )

    return GetServerIdShowAPI(
        id=server.id,
        name=server.name,
        ip=server.ip,
        type=server.type,
        version=server.version,
        desc=server.desc,
        link=server.link,
        is_member=server.is_member,
        auth_mode=server.auth_mode,
        tags=server.tags,
        is_hide=server.is_hide,
        status=status_data,
        permission=permission,
    )


# 返回一个服务器的所有主人
async def GetServerOwners_by_id(server_id: int) -> GetServerManagers:
    # 查找是否有这个服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在"
        )

    # 查找服务器的所有者和管理员
    owners = await UserServer.filter(server=server_id, role="owner")
    admins = await UserServer.filter(server=server_id, role="admin")

    async def to_user_base(user_server) -> UserBase:
        user = await user_server.user
        avatar_url = await get_user_avatar_url(user)
        return UserBase(
            id=user.id,
            display_name=user.display_name,
            role=user.role,
            is_active=user.is_active,
            avatar_url=avatar_url,
        )

    # 并发转换管理员和所有者列表
    admins_list, owners_list = await asyncio.gather(
        asyncio.gather(*(to_user_base(admin) for admin in admins)),
        asyncio.gather(*(to_user_base(owner) for owner in owners)),
    )

    return GetServerManagers(admins=admins_list, owners=owners_list)
