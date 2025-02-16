from enum import Enum

from pydantic import BaseModel, Field
from tortoise import fields
from tortoise.models import Model

from .db import add_model

add_model(__name__)


class AuthModeEnum(Enum):
    OFFLINE = "OFFLINE"
    YGGDRASIL = "YGGDRASIL"
    OFFICIAL = "OFFICIAL"


class ServerTypeEnum(Enum):
    JAVA = "JAVA"
    BEDROCK = "BEDROCK"


class Server(Model):
    id = fields.IntField(pk=True, generated=True)
    name = fields.CharField(max_length=255)
    type = fields.CharField(
        max_length=50, choices=[(tag.name, tag.value) for tag in ServerTypeEnum]
    )
    version = fields.CharField(max_length=20)
    desc = fields.TextField()
    link = fields.CharField(max_length=255)
    ip = fields.CharField(max_length=255)
    is_member = fields.BooleanField(default=False)
    is_hide = fields.BooleanField(default=False)
    auth_mode = fields.CharField(
        max_length=50, choices=[(tag.name, tag.value) for tag in AuthModeEnum]
    )
    tags = fields.JSONField(default=list)

    class Meta:
        table = "server"


class ServerBase(BaseModel):
    id: None | int = None  # 作为数据库字段可能是自动生成，默认不需要填
    name: str = Field(
        ..., max_length=255, description="服务器的名称，用于唯一标识服务器。"
    )
    type: ServerTypeEnum = Field(
        ..., description="服务器类型，指定服务器是 Java 版本还是 Bedrock 版本。"
    )
    version: str = Field(
        ...,
        max_length=20,
        description="服务器的版本号，用于标识 Minecraft 服务器的版本。",
    )
    desc: str = Field(..., description="服务器的描述，包含服务器的特点、玩法等内容。")
    link: str = Field(
        ...,
        max_length=255,
        description="服务器相关的链接地址，通常是指向服务器的官方网站或其他说明页面。",
    )
    ip: str | None = Field(
        ..., max_length=255, description="服务器的 IP 地址，玩家用来连接服务器。"
    )
    is_member: bool = Field(
        description="标识服务器是否是成员服务器。如果该字段为 true，则表示服务器属于一个特定的成员群体或组织。",
    )
    is_hide: bool = Field(
        description="标识服务器是否被隐藏。如果为 true，则该服务器不会在公开的服务器列表中显示。",
    )
    auth_mode: AuthModeEnum = Field(
        default=AuthModeEnum.OFFLINE,
        description="服务器的认证方式，表示服务器是采用离线认证、外置认证系统还是正版认证。",
    )
    tags: list[str | None] = Field(
        default_factory=list,
        description="服务器的标签列表，用于分类或标记服务器的特性（如 PvP、Survival、Creative 等）。",
    )

    class Config:
        orm_mode = True  # 支持从 ORM 模型（如数据库）到 Pydantic 模型的转换
        min_anystr_length = 1  # 强制非空字符串字段的最小长度为1
        anystr_strip_whitespace = True  # 自动去除字符串字段的空白字符
