from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RoleEnum(str, Enum):
    user = "user"
    admin = "admin"


class BanTypeEnum(str, Enum):
    mute = "mute"  # 禁言
    ban = "ban"  # 封号
    temp_ban = "temp_ban"  # 临时封禁


class UserBase(BaseModel):
    username: str = Field(..., max_length=32, description="用户的用户名")
    email: str = Field(..., max_length=100, description="用户的电子邮箱")
    display_name: str = Field(max_length=16, description="用户的显示名称")
    avatar_url: str | None = Field(None, max_length=255, description="用户的头像URL")
    role: RoleEnum = Field(RoleEnum.user, description="用户角色")
    is_active: bool = Field(False, description="用户是否激活")

    class Config:
        from_attributes = True


class UserCreate(UserBase):
    hashed_password: str = Field(..., max_length=60, description="用户的加密密码")

    class Config:
        from_attributes = True


class UserUpdate(UserBase):
    hashed_password: str | None = Field(
        None, max_length=60, description="用户的新密码，若更新则提供"
    )

    class Config:
        from_attributes = True


class User(UserBase):
    id: int = Field(..., description="用户的唯一标识符")
    created_at: datetime = Field(..., description="用户创建时间")
    last_login: datetime | None = Field(None, description="用户最后登录时间")
    last_login_ip: str | None = Field(
        None, max_length=15, description="用户最后登录IP地址"
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
    user_id: int = Field(..., description="封禁记录对应的用户ID")

    class Config:
        from_attributes = True
