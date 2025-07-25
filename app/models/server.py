from enum import Enum
from typing import TYPE_CHECKING, Any

from tortoise import Model, fields
from tortoise.fields.base import Field

from app.services.conn.db import add_model

if TYPE_CHECKING:
    from app.models.file import File
    from app.models.user import User

add_model(__name__)


class AuthModeEnum(Enum):
    OFFLINE = "OFFLINE"
    YGGDRASIL = "YGGDRASIL"
    OFFICIAL = "OFFICIAL"


class ServerTypeEnum(Enum):
    JAVA = "JAVA"
    BEDROCK = "BEDROCK"


class Gallery(Model):
    id = fields.IntField(pk=True)
    images: fields.ReverseRelation["GalleryImage"]
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "gallery"


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
    tags: Field[list[str]] = fields.JSONField(default=list)
    cover_hash: fields.ForeignKeyRelation["File"] | None = fields.ForeignKeyField(
        "default.File", related_name="cover_hash", on_delete=fields.SET_NULL, null=True
    )
    gallery: fields.ForeignKeyRelation[Gallery] | None = fields.ForeignKeyField(
        "default.Gallery",
        related_name="servers",
        on_delete=fields.CASCADE,  # 级联删除
        null=True,
    )

    async def save_with_user(self, user: "User") -> None:
        """
        保存模型并记录变更日志（仅在更新时有变更才生成日志）。
        """
        changed_fields: dict[str, Any] = {}

        # 只有已有 ID（即更新操作）时，才计算变更
        if self.id:
            # 取旧数据
            old = await type(self).get(id=self.id)
            # 字段列表一次性取出
            fields = self._meta.db_fields
            # 一次性构建 changed_fields
            changed_fields = {
                field: getattr(old, field)
                for field in fields
                if getattr(old, field) != getattr(self, field)
            }

        await self.save()

        if changed_fields:
            await ServerLog.create(
                server=self, user=user, changed_fields=changed_fields
            )

    class Meta:
        table = "server"


class GalleryImage(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    description = fields.TextField()
    image_hash: fields.ForeignKeyRelation["File"] = fields.ForeignKeyField(
        "default.File", related_name="gallery_images", on_delete=fields.CASCADE
    )
    gallery: fields.ForeignKeyRelation[Gallery] = fields.ForeignKeyField(
        "default.Gallery", related_name="images"
    )

    class Meta:
        table = "gallery_image"


class ServerStatus(Model):
    server = fields.ForeignKeyField("default.Server", related_name="stats")
    timestamp = fields.DatetimeField(auto_now_add=True)
    stat_data: Field[dict | None] = fields.JSONField(
        default=dict, null=True
    )  # 用于存储查询结果

    class Meta:
        table = "server_stats"


class ServerLog(Model):
    id = fields.IntField(pk=True, generated=True)
    server: fields.ForeignKeyRelation["Server"] = fields.ForeignKeyField(
        "default.Server", related_name="logs", on_delete=fields.CASCADE
    )
    user: fields.ForeignKeyRelation["User"] | None = fields.ForeignKeyField(
        "default.User", related_name="server_logs", on_delete=fields.SET_NULL, null=True
    )
    changed_fields = fields.JSONField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "server_log"
