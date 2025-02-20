from pydantic import BaseModel, Field


class UserInDB(BaseModel):
    username: str = Field(..., title="用户名", description="存储在数据库中的用户名")
    email: str = Field(..., title="邮箱", description="用户的邮箱地址")
    hashed_password: str = Field(
        ..., title="哈希密码", description="存储的用户密码的哈希值"
    )


class UserLogin(BaseModel):
    username: str = Field(..., title="用户名", description="用户的用户名")
    password: str = Field(..., title="密码", description="用户的登录密码")
    captcha_response: str = Field(
        ..., title="验证码响应", description="用户填写的验证码响应，用于验证hCaptcha"
    )
