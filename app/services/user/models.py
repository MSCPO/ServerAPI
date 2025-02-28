from enum import Enum

from tortoise import fields
from tortoise.models import Model

from app.file_storage.models import File
from app.services.conn.db import add_model
from app.services.user.schemas import RoleEnum

add_model(__name__)


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
    avatar_hash: fields.ForeignKeyRelation[File] | None = fields.ForeignKeyField(
        "default.File", related_name="avatar_hash", on_delete=fields.SET_NULL, null=True
    )
    role: RoleEnum = fields.CharEnumField(RoleEnum, default=RoleEnum.user)
    is_active = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    last_login = fields.DatetimeField(null=True)
    last_login_ip = fields.CharField(max_length=15, null=True)

    class Meta:
        table = "users"


class SerRoleEnum(str, Enum):
    owner = "owner"
    admin = "admin"


class UserServer(Model):
    user = fields.ForeignKeyField("default.User", on_delete=fields.CASCADE)
    server = fields.ForeignKeyField("default.Server", on_delete=fields.CASCADE)
    role: SerRoleEnum = fields.CharEnumField(max_length=50, enum_type=SerRoleEnum)

    class Meta:
        table = "user_server"
