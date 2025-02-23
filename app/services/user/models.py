from enum import Enum

from tortoise import fields
from tortoise.models import Model

from app.services.conn.db import add_model

add_model(__name__)


class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"


class BanTypeEnum(str, Enum):
    mute = "mute"  # 禁言
    ban = "ban"  # 封号
    temp_ban = "temp_ban"  # 临时封禁


class BanRecord(Model):
    user = fields.ForeignKeyField(
        "default.User", related_name="ban_records"
    )  # 外键，指向 User
    ban_type = fields.CharEnumField(BanTypeEnum)
    reason = fields.TextField(null=True)
    started_at = fields.DatetimeField(auto_now_add=True)  # 封禁开始时间
    ended_at = fields.DatetimeField(null=True)

    class Meta:
        table = "ban_records"


class User(Model):
    id = fields.IntField(pk=True, generated=True)
    username = fields.CharField(max_length=32, unique=True)
    email = fields.CharField(max_length=100, unique=True)
    display_name = fields.CharField(max_length=16)
    hashed_password = fields.CharField(max_length=60)
    avatar_url = fields.CharField(max_length=255, null=True)
    role = fields.CharEnumField(RoleEnum, default=RoleEnum.user)
    is_active = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    last_login = fields.DatetimeField(null=True)
    last_login_ip = fields.CharField(max_length=15, null=True)

    class Meta:
        table = "users"


class UserServer(Model):
    user = fields.ForeignKeyField("default.User", on_delete=fields.CASCADE)
    server = fields.ForeignKeyField("default.Server", on_delete=fields.CASCADE)
    role = fields.CharField(
        max_length=50, choices=[("owner", "Owner"), ("admin", "Admin")]
    )

    class Meta:
        table = "user_server"
