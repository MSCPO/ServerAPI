from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.services.user.models import RoleEnum, SerRoleEnum


class BanTypeEnum(str, Enum):
    mute = "mute"  # 禁言
    ban = "ban"  # 封号
    temp_ban = "temp_ban"  # 临时封禁


class UserBase(BaseModel):
    id: int = Field(..., description="用户的唯一标识符")
    display_name: str = Field(max_length=16, description="用户的显示名称")
    role: RoleEnum = Field(RoleEnum.user, description="用户角色")
    is_active: bool = Field(False, description="用户是否激活")
    avatar_url: str | None = Field(None, description="用户的头像 URL")

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str = Field(..., max_length=60, description="用户的加密密码")
    token: str = Field(..., description="用户的注册验证码")


class UserUpdate(UserBase):
    password: str | None = Field(
        None, max_length=60, description="用户的新密码，若更新则提供"
    )

    class Config:
        from_attributes = True


class User(UserBase):
    username: str = Field(..., max_length=32, description="用户的用户名")
    email: str = Field(..., max_length=100, description="用户的电子邮箱")
    created_at: datetime = Field(..., description="用户创建时间")
    last_login: datetime | None = Field(None, description="用户最后登录时间")
    last_login_ip: str | None = Field(
        None, max_length=15, description="用户最后登录 IP 地址"
    )
    servers: list[tuple[SerRoleEnum, int]] = Field(
        [], description="用户拥有的服务器 ID 列表"
    )

    class Config:
        from_attributes = True


class UserPublicInfo(BaseModel):
    id: int = Field(..., description="用户的唯一标识符")
    display_name: str = Field(max_length=16, description="用户的显示名称")
    role: RoleEnum = Field(RoleEnum.user, description="用户角色")
    is_active: bool = Field(False, description="用户是否激活")
    avatar_url: str | None = Field(None, description="用户的头像 URL")
    created_at: datetime = Field(..., description="用户创建时间")
    last_login: datetime | None = Field(None, description="用户最后登录时间")
    servers: list[tuple[SerRoleEnum, int]] = Field(
        [], description="用户拥有的服务器 ID 列表"
    )

    class Config:
        from_attributes = True


class BanRecordBase(BaseModel):
    ban_type: BanTypeEnum = Field(..., description="封禁类型")
    reason: str | None = Field(None, description="封禁原因")
    started_at: datetime = Field(..., description="封禁开始时间")
    ended_at: datetime | None = Field(None, description="封禁结束时间")

    class Config:
        from_attributes = True


class BanRecord(BanRecordBase):
    id: int = Field(..., description="封禁记录的唯一标识符")
    user_id: int = Field(..., description="封禁记录对应的用户 ID")

    class Config:
        from_attributes = True
