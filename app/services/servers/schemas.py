from fastapi import File, UploadFile
from pydantic import BaseModel, Field

from app.services.user.schemas import UserBase


class Motd(BaseModel):
    plain: str = Field(title="纯文本 MOTD", description="显示服务器的纯文本 MOTD")
    html: str = Field(title="HTML 格式 MOTD", description="显示服务器的 HTML 格式 MOTD")
    minecraft: str = Field(
        title="Minecraft 格式 MOTD", description="显示 Minecraft 格式的 MOTD"
    )
    ansi: str = Field(title="ANSI 格式 MOTD", description="显示 ANSI 格式的 MOTD")

    class Config:
        from_attributes = True


# 通用图片schema，支持上传和展示
class GallerySchema(BaseModel):
    id: int | None = Field(None, title="图片 ID", description="图片的唯一标识符")
    title: str = Field(title="图片标题", description="图片的标题")
    description: str = Field(title="图片描述", description="图片的描述")
    image_url: str | None = Field(None, title="图片链接", description="图片的链接")
    image: UploadFile | None = File(
        None, title="图片文件", description="上传的图片文件"
    )


class GetServerStatusAPI(BaseModel):
    players: dict[str, int] = Field(
        title="玩家数", description="当前在线的玩家数量以及最大可容纳的玩家数量"
    )
    delay: float = Field(title="延迟", description="服务器的延迟时间")
    version: str = Field(title="版本", description="服务器的软件版本")
    motd: Motd = Field(title="MOTD", description="服务器的 MOTD 信息")
    icon: str | None = Field(
        None, title="服务器图标", description="服务器的图标，若无则为 None"
    )

    class Config:
        from_attributes = True


# 服务器基础信息
class ServerBase(BaseModel):
    id: int = Field(title="服务器 ID", description="服务器的唯一标识符")
    name: str = Field(title="服务器名称", description="服务器的名称")

    class Config:
        from_attributes = True


# 服务器详细信息
class ServerDetail(ServerBase):
    ip: str | None = Field(
        None, title="服务器 IP", description="服务器的 IP 地址，若隐藏则为 None"
    )
    type: str = Field(title="服务器类型", description="服务器所属的类型")
    version: str = Field(title="服务器版本", description="服务器运行的版本")
    desc: str = Field(title="服务器描述", description="对服务器的简短描述")
    link: str = Field(title="服务器链接", description="指向服务器详情的链接")
    is_member: bool = Field(
        title="是否为成员服务器", description="是否是成员专属服务器"
    )
    auth_mode: str = Field(title="认证模式", description="服务器使用的认证模式")
    tags: list[str] = Field(
        default_factory=list, title="服务器标签", description="与服务器相关的标签"
    )
    is_hide: bool = Field(title="是否隐藏", description="服务器是否处于隐藏状态")
    status: GetServerStatusAPI | None = Field(
        None, title="服务器状态", description="显示服务器的在线状态信息"
    )
    permission: str = Field(
        title="服务器权限",
        description="服务器的权限",
    )
    cover_url: str | None = Field(
        title="服务器封面",
        description="服务器的封面图片链接",
    )


# 服务器相册
class ServerGallery(ServerBase):
    gallerys_url: list[GallerySchema] = Field(
        title="服务器相册", description="服务器的相册图片链接"
    )


# 服务器列表
class ServerList(BaseModel):
    server_list: list[ServerDetail] = Field(
        title="服务器列表", description="显示所有的服务器列表"
    )
    total_member: int = Field(
        title="会员服务器总数", description="当前会员服务器的总数"
    )
    total: int = Field(title="服务器总数", description="当前所有服务器的总数")
    random_seed: int | None = Field(
        None, title="随机种子", description="本次随机的随机种子，固定分页用"
    )  # 随机种子


class ServerFilter(BaseModel):
    is_member: bool = Field(
        True, title="是否为成员服务器", description="是否是成员专属服务器"
    )
    modes: str | None = Field(None, title="模式", description="服务器模式筛选")
    authModes: list[str] = Field(
        default_factory=lambda: ["OFFLINE", "YGGDRASIL", "OFFICIAL"],
        title="认证模式",
        description="服务器认证模式筛选",
    )
    tags: list[str] | None = Field(
        None, title="服务器标签", description="服务器标签筛选"
    )


class UpdateServerRequest(BaseModel):
    name: str = Field(title="服务器名称", description="服务器的名称")
    ip: str = Field(title="服务器 IP", description="服务器的 IP 地址")
    desc: str = Field(title="服务器描述", description="对服务器的简短描述")
    tags: list[str] = Field(title="服务器标签", description="与服务器相关的标签")
    version: str = Field(title="服务器版本", description="服务器运行的版本")
    link: str = Field(title="服务器链接", description="指向服务器详情的链接")
    cover: UploadFile | None = File(
        None, title="服务器封面", description="服务器封面文件"
    )


class GetServerManagers(BaseModel):
    owners: list[UserBase] = Field(title="服务器主人", description="服务器的所有主人")
    admins: list[UserBase] = Field(
        title="服务器管理员", description="服务器的所有管理员"
    )

    class Config:
        from_attributes = True


class ServerTotalPlayers(BaseModel):
    total_players: int = Field(title="服务器总玩家数", description="服务器的总玩家数")
