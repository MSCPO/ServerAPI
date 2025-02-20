from app.servers.models import (
    Server,
    ServerStatus,
)
from app.servers.schemas import (
    GetServer,
    GetServerIdShowAPI,
    GetServerShowAPI,
    GetServerStatusAPI,
    Motd,
)


async def GetServers(limit: int | None = None, offset: int = 0) -> list[GetServer]:
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
    server_list = [
        GetServer(
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
        )
        for server in server_query
    ]

    # 返回数据
    return GetServerShowAPI(
        server_list=server_list, total_member=total_member, total=total_servers
    )


async def GetServer_by_id(server_id: int) -> None | GetServer:
    server = await Server.get_or_none(id=server_id)
    server_status = await ServerStatus.get_or_none(server=server)
    if server:
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
        )
    return None
