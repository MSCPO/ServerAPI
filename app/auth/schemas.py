from pydantic import BaseModel, Field


class UserLogin(BaseModel):
    username: str = Field(..., title="用户名", description="用户的用户名")
    password: str = Field(..., title="密码", description="用户的登录密码")
    captcha_response: str = Field(
        ..., title="验证码响应", description="用户填写的验证码响应，用于验证reCAPTCHA"
    )
