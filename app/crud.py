from pydantic import BaseModel, Field

from .models import Server, ServerStats


class Motd(BaseModel):
    plain: str = Field(..., title="motd纯文本", description="motd纯文本")
    html: str = Field(..., title="motd HTML", description="motd HTML")
    minecraft: str = Field(..., title="motd Minecraft", description="motd Minecraft")
    ansi: str = Field(..., title="motd ANSI", description="motd ANSI")


class get_ServerStats_api(BaseModel):
    players: dict[str, int] = Field(
        ..., title="在线玩家数量", description="在线玩家数量"
    )
    delay: float = Field(None, title="延迟", description="服务器的延迟")
    version: str = Field(..., title="版本", description="服务器的版本")
    motd: Motd = Field(..., title="MOTD", description="服务器的MOTD")
    icon: None | str = Field(None, title="图标", description="服务器的图标")


# 输出json schema


class get_Server(BaseModel):
    id: int = Field(..., title="服务器ID", description="服务器的唯一标识符")
    name: str = Field(..., title="服务器名称", description="服务器的名称")
    ip: None | str = Field(
        None, title="服务器IP", description="服务器的IP地址，隐藏服务器时为None"
    )
    type: str = Field(
        ...,
        title="服务器类型",
        description="服务器的类型（例如：Minecraft、World of Warcraft等）",
    )
    version: str = Field(..., title="服务器版本", description="服务器的版本")
    desc: str = Field(..., title="服务器描述", description="关于服务器的简短描述")
    link: str = Field(..., title="服务器链接", description="指向服务器更多信息的链接")
    is_member: bool = Field(..., title="是否成员", description="是否是会员服务器")
    auth_mode: str = Field(..., title="认证模式", description="服务器的认证方式")
    tags: list = Field(
        ..., title="标签", description="与服务器相关的标签（例如：生存、创造、PVP等）"
    )
    is_hide: bool = Field(
        ..., title="是否隐藏", description="服务器是否为隐藏状态，隐藏时部分信息不显示"
    )


class get_ServerShow_api(BaseModel):
    server_list: list[get_Server] = Field(
        ..., title="服务器列表", description="服务器列表"
    )  # type: ignore
    total: int = Field(..., title="服务器总数", description="服务器的总数")


class get_ServerId_Show_api(get_Server):
    stats: get_ServerStats_api | None = Field(
        ..., title="服务器状态", description="服务器的在线状态信息"
    )


async def get_servers(limit: int | None = None, offset: int = 0) -> list[get_Server]:
    # 获取符合条件的服务器数据，分页处理
    server_query = Server.all().offset(offset)
    if limit:
        server_query = server_query.limit(limit)

    server_result: list[Server] = await server_query

    server_list = [
        get_Server(
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
        for server in server_result
    ]

    return get_ServerShow_api(
        server_list=server_list,
        total=len(server_list),
    )


async def get_server_by_id(server_id: int) -> None | get_Server:
    server = await Server.get_or_none(id=server_id)
    server_stats = await ServerStats.get_or_none(server=server)
    if server:
        return get_ServerId_Show_api(
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
            stats=get_ServerStats_api(
                players=server_stats.stat_data["players"],
                delay=server_stats.stat_data["delay"],
                version=server_stats.stat_data["version"],
                motd=Motd(
                    plain=server_stats.stat_data["motd"]["plain"],
                    html=server_stats.stat_data["motd"]["html"],
                    minecraft=server_stats.stat_data["motd"]["minecraft"],
                    ansi=server_stats.stat_data["motd"]["ansi"],
                ),
                icon=server_stats.stat_data["icon"],
            )
            if server_stats and server_stats.stat_data
            else None,
        )
    return None


print(get_ServerId_Show_api.schema())
# print(get_ServerShow_api.schema())
# print(get_ServerStats_api.schema())
