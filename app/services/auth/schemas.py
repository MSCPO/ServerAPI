from pydantic import BaseModel, Field


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
        description="用户的注册token",
    )
    captcha_response: str = Field(
        ...,
        title="reCAPTCHA 响应",
        description="reCAPTCHA 响应",
    )
