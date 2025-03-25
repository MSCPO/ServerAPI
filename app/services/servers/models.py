from enum import Enum

from tortoise import Model, fields
from tortoise.fields.base import Field

from app.file_storage.models import File
from app.services.conn.db import add_model

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
    cover_hash: fields.ForeignKeyRelation[File] | None = fields.ForeignKeyField(
        "default.File", related_name="cover_hash", on_delete=fields.SET_NULL, null=True
    )
    gallery: fields.ForeignKeyRelation[Gallery] | None = fields.ForeignKeyField(
        "default.Gallery",
        related_name="servers",
        on_delete=fields.CASCADE,  # 级联删除
        null=True,
    )

    class Meta:
        table = "server"


class GalleryImage(Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    description = fields.TextField()
    image_hash: fields.ForeignKeyRelation[File] = fields.ForeignKeyField(
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
    stat_data: Field[dict] = fields.JSONField(
        default=dict, null=True
    )  # 用于存储查询结果

    class Meta:
        table = "server_stats"
