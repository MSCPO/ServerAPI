from pydantic import BaseModel, Field

from .models import Server


class ServerShow(BaseModel):
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

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "My Minecraft Server",
                "ip": "192.168.1.1",
                "type": "Minecraft",
                "version": "1.16.5",
                "desc": "一个极具挑战性的Minecraft生存服务器。",
                "link": "http://example.com",
                "is_member": True,
                "auth_mode": "official",
                "tags": ["生存", "多人", "挑战"],
                "is_hide": False,
            }
        }


server_show_schema = ServerShow.schema()

# 输出 JSON Schema
import json

print(json.dumps(server_show_schema, indent=2))


async def get_servers(limit: int | None = None, offset: int = 0) -> list[ServerShow]:
    # 获取符合条件的服务器数据，分页处理
    server_query = Server.all().offset(offset)
    if limit:
        server_query = server_query.limit(limit)

    server_list: list[Server] = await server_query

    # 使用 Pydantic 模型进行数据序列化
    return [
        ServerShow(
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
        for server in server_list
    ]


async def get_server_by_id(server_id: int) -> None | ServerShow:
    server = await Server.get_or_none(id=server_id)
    if server:
        return ServerShow(
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
    return None
