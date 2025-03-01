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


async def GetServers(limit: int | None = None, offset: int = 0) -> GetServerShowAPI:
    server_query = await Server.all()

    # 计算总数
    total_member = sum(bool(server.is_member) for server in server_query)
    total_servers = len(server_query)

    # 如果有分页需求，应用 limit 和 offset
    if limit:
        server_query = server_query[offset : offset + limit]
    else:
        server_query = server_query[offset:]

    # 生成服务器列表
    server_list = [GetServer.model_validate(server) for server in server_query]

    # 返回数据
    return GetServerShowAPI(
        server_list=server_list, total_member=total_member, total=total_servers
    )


async def GetServer_by_id(
    server_id: int, user: int | None
) -> None | GetServerIdShowAPI:
    server = await Server.get_or_none(id=server_id)
    server_status = await ServerStatus.get_or_none(server=server)
    user_server = None
    if user:
        user_server = await UserServer.get_or_none(user=user, server=server_id)

    if server:
        permission = user_server.role if user_server else "guest"
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
            status=GetServerStatusAPI(
                players=server_status.stat_data["players"],
                delay=server_status.stat_data["delay"],
                version=server_status.stat_data["version"],
                motd=Motd(
                    plain=server_status.stat_data["motd"]["plain"],
                    html=server_status.stat_data["motd"]["html"],
                    minecraft=server_status.stat_data["motd"]["minecraft"],
                    ansi=server_status.stat_data["motd"]["ansi"],
                ),
                icon=server_status.stat_data["icon"],
            )
            if server_status and server_status.stat_data
            else None,
            permission=permission,
        )
    return None


async def GetServer_by_id_editor(
    server_id: int, current_user: dict
) -> GetServerIdShowAPI | None:
    """查看服务器详细信息（详细信息）"""
    is_role = await UserServer.filter(
        user=current_user["id"], server=server_id
    ).exists()
    if not is_role:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="你咩有权限编辑它！它拒绝了你！",
        )
    server = await Server.get_or_none(id=server_id)
    server_status = await ServerStatus.get_or_none(server=server)
    user_server = await UserServer.get_or_none(
        user=current_user["id"], server=server_id
    )

    if server:
        permission = user_server.role if user_server else "guest"

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
            status=GetServerStatusAPI(
                players=server_status.stat_data["players"],
                delay=server_status.stat_data["delay"],
                version=server_status.stat_data["version"],
                motd=Motd(
                    plain=server_status.stat_data["motd"]["plain"],
                    html=server_status.stat_data["motd"]["html"],
                    minecraft=server_status.stat_data["motd"]["minecraft"],
                    ansi=server_status.stat_data["motd"]["ansi"],
                ),
                icon=server_status.stat_data["icon"],
            )
            if server_status and server_status.stat_data
            else None,
            permission=permission,
        )
    return None


# 返回一个服务器的所有主人
async def GetServerOwners_by_id(server_id: int) -> GetServerManagers:
    # 查找是否有这个服务器
    server = await Server.get_or_none(id=server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="服务器不存在"
        )

    user_server = await UserServer.filter(server=server_id)
    owners = [UserBase.model_validate(await user.user) for user in user_server]
    admins = [
        UserBase.model_validate(await user.user)
        for user in user_server
        if user.role == "admin"
    ]
    return GetServerManagers(owners=owners, admins=admins)
