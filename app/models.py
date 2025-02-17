from enum import Enum

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

    class Config:
        orm_mode = True  # 支持从 ORM 模型（如数据库）到 Pydantic 模型的转换
        min_anystr_length = 1  # 强制非空字符串字段的最小长度为1
        anystr_strip_whitespace = True  # 自动去除字符串字段的空白字符


class ServerStatus(Model):
    server = fields.ForeignKeyField("default.Server", related_name="stats")
    timestamp = fields.DatetimeField(auto_now_add=True)
    stat_data = fields.JSONField(default=dict, null=True)  # 用于存储查询结果

    class Meta:
        table = "server_stats"
