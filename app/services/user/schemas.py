from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field

from app.services.user.models import RoleEnum, SerRoleEnum


class BanTypeEnum(str, Enum):
    mute = "mute"  # 禁言
    ban = "ban"  # 封号
    temp_ban = "temp_ban"  # 临时封禁


class UserBase(BaseModel):
    id: int = Field(..., title="用户 ID", description="用户的唯一标识符")
    display_name: str = Field(
        max_length=16, title="显示名称", description="用户的显示名称"
    )
    role: RoleEnum = Field(RoleEnum.user, title="用户角色", description="用户角色")
    is_active: bool = Field(False, title="是否激活", description="用户是否激活")
    avatar_url: str | None = Field(None, title="头像链接", description="用户的头像 URL")

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    password: str = Field(
        ..., max_length=60, title="加密密码", description="用户的加密密码"
    )
    token: str = Field(
        ..., title="验证令牌", description="用户注册时的验证令牌"
    )


class UserUpdate(UserBase):
    password: str | None = Field(
        None,
        max_length=60,
        title="新密码",
        description="用户的新密码，若更新则提供",
    )

    class Config:
        from_attributes = True


class User(UserBase):
    username: str = Field(
        ..., max_length=32, title="用户名", description="用户的用户名"
    )
    email: str = Field(..., max_length=100, title="邮箱", description="用户的电子邮箱")
    created_at: datetime = Field(..., title="创建时间", description="用户创建时间")
    last_login: datetime | None = Field(
        None, title="最后登录时间", description="用户最后登录时间"
    )
    last_login_ip: str | None = Field(
        None, title="最后登录 IP", description="用户最后登录 IP 地址"
    )
    servers: list[tuple[SerRoleEnum, int]] = Field(
        [], title="拥有的服务器", description="用户拥有的服务器 ID 列表"
    )

    class Config:
        from_attributes = True


class UserPublicInfo(BaseModel):
    id: int = Field(..., title="用户 ID", description="用户的唯一标识符")
    display_name: str = Field(
        max_length=16, title="显示名称", description="用户的显示名称"
    )
    role: RoleEnum = Field(RoleEnum.user, title="用户角色", description="用户角色")
    is_active: bool = Field(False, title="是否激活", description="用户是否激活")
    avatar_url: str | None = Field(None, title="头像链接", description="用户的头像 URL")
    created_at: datetime = Field(..., title="创建时间", description="用户创建时间")
    last_login: datetime | None = Field(None, title="最后登录时间", description="用户最后登录时间")
    servers: list[tuple[SerRoleEnum, int]] = Field(
        [], title="拥有的服务器", description="用户拥有的服务器 ID 列表"
    )

    class Config:
        from_attributes = True


class BanRecordBase(BaseModel):
    ban_type: BanTypeEnum = Field(..., title="封禁类型", description="封禁类型")
    reason: str | None = Field(None, title="封禁原因", description="封禁原因")
    started_at: datetime = Field(..., title="开始时间", description="封禁开始时间")
    ended_at: datetime | None = Field(None, title="结束时间", description="封禁结束时间")

    class Config:
        from_attributes = True


class BanRecord(BanRecordBase):
    id: int = Field(..., title="记录 ID", description="封禁记录的唯一标识符")
    user_id: int = Field(..., title="用户 ID", description="封禁记录对应的用户 ID")

    class Config:
        from_attributes = True
