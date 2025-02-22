from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    username: str = Field(..., title="用户名", description="用户的用户名")
    password: str = Field(..., title="密码", description="用户的登录密码")
    captcha_response: str = Field(
        ..., title="验证码响应", description="用户填写的验证码响应，用于验证reCAPTCHA"
    )


class UserRegister(UserLogin):
    display_name: str = Field(
        None, title="显示名称", description="用户的显示名称，可选"
    )
    avatar_url: str | None = Field(
        None, title="头像URL", description="用户的头像URL，可选"
    )


class RegisterRequest(BaseModel):
    email: str = Field(..., title="邮箱", description="用户的邮箱地址")
    captcha_response: str = Field(
        ..., title="验证码响应", description="用户填写的验证码响应，用于验证reCAPTCHA"
    )
