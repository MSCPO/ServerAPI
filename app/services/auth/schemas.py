from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from app.config import settings


class captchaResponse(BaseModel):
    captcha_response: str = Field(
        ...,
        title="reCAPTCHA 响应",
        description="reCAPTCHA 响应",
    )


class UserLogin(captchaResponse):
    username_or_email: str = Field(
        ..., title="用户名或邮箱", description="用户的用户名或邮箱"
    )
    password: str = Field(..., title="密码", description="用户的登录密码")


class RegisterRequest(captchaResponse):
    password: str = Field(
        ...,
        title="密码",
        description="用户的密码，长度为 8-16 位，至少包含数字、大写字毸、小写字母和特殊字符中的两种",
    )
    display_name: str = Field(
        ...,
        title="显示名称",
        description="用户的显示名称，长度为 4-16 位",
    )
    token: str = Field(
        ...,
        title="Token",
        description="用户的注册 token",
    )


class Auth_Token(BaseModel):
    access_token: str = Field(..., title="访问令牌", description="JWT 访问令牌")
    token_type: str = Field("bearer", title="令牌类型", description="令牌类型")


class jwt_data(BaseModel):
    sub: str = Field(..., title="用户名", description="JWT 中的用户名")  # 用户名
    id: int = Field(..., title="用户 ID", description="JWT 中的用户 ID")  # 用户 ID
    exp: datetime = Field(
        default=datetime.now(ZoneInfo("Asia/Shanghai"))
        + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        title="过期时间",
        description="JWT 的过期时间",
    )
