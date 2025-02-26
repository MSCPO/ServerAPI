from pydantic import BaseModel, Field


class Motd(BaseModel):
    plain: str = Field(..., title="纯文本MOTD", description="显示服务器的纯文本MOTD")
    html: str = Field(..., title="HTML格式MOTD", description="显示服务器的HTML格式MOTD")
    minecraft: str = Field(
        ..., title="Minecraft格式MOTD", description="显示Minecraft格式的MOTD"
    )
    ansi: str = Field(..., title="ANSI格式MOTD", description="显示ANSI格式的MOTD")

    class Config:
        from_attributes = True


class GetServerStatusAPI(BaseModel):
    players: dict[str, int] = Field(
        ..., title="在线玩家数量", description="当前在线的玩家数量"
    )
    delay: float = Field(..., title="延迟", description="服务器的延迟时间")
    version: str = Field(..., title="版本", description="服务器的软件版本")
    motd: Motd = Field(..., title="MOTD", description="服务器的MOTD信息")
    icon: None | str = Field(
        None, title="服务器图标", description="服务器的图标，若无则为None"
    )

    class Config:
        from_attributes = True


class GetServer(BaseModel):
    id: int = Field(..., title="服务器ID", description="服务器的唯一标识符")
    name: str = Field(..., title="服务器名称", description="服务器的名称")

    class Config:
        from_attributes = True


class GetServerShowAPI(BaseModel):
    server_list: list[GetServer] = Field(
        ..., title="服务器列表", description="显示所有的服务器列表"
    )
    total_member: int = Field(
        ..., title="会员服务器总数", description="当前会员服务器的总数"
    )
    total: int = Field(..., title="服务器总数", description="当前所有服务器的总数")

    class Config:
        from_attributes = True


class GetServerIdShowAPI(GetServer):
    ip: None | str = Field(
        None, title="服务器IP", description="服务器的IP地址，若隐藏则为None"
    )
    type: str = Field(
        ...,
        title="服务器类型",
        description="服务器所属的类型（例如：Minecraft、World of Warcraft等）",
    )
    version: str = Field(..., title="服务器版本", description="服务器运行的版本")
    desc: str = Field(..., title="服务器描述", description="对服务器的简短描述")
    link: str = Field(..., title="服务器链接", description="指向服务器详情的链接")
    is_member: bool = Field(
        ..., title="是否为成员服务器", description="是否是成员专属服务器"
    )
    auth_mode: str = Field(..., title="认证模式", description="服务器使用的认证模式")
    tags: list = Field(
        ...,
        title="服务器标签",
        description="与服务器相关的标签（如：生存、创造、PVP等）",
    )
    is_hide: bool = Field(
        ...,
        title="是否隐藏",
        description="服务器是否处于隐藏状态，隐藏时部分信息不显示",
    )
    status: GetServerStatusAPI | None = Field(
        ..., title="服务器状态", description="显示服务器的在线状态信息"
    )

    class Config:
        from_attributes = True


class UpdateServerRequest(BaseModel):
    name: str = Field(..., title="服务器名称", description="服务器的名称")
    ip: str = Field(..., title="服务器IP", description="服务器的IP地址")
    desc: str = Field(..., title="服务器描述", description="对服务器的简短描述")
    tags: list[str] = Field(
        ...,
        title="服务器标签",
        description="与服务器相关的标签（如：生存、创造、PVP等）",
    )
