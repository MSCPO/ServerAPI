from pydantic import BaseModel, Field


class CaptchaBase(BaseModel):
    captcha_response: str = Field(
        ..., title="reCAPTCHA 响应", description="reCAPTCHA 验证码响应"
    )


class MessageResponse(BaseModel):
    detail: str = Field(..., title="消息", description="返回的消息")
