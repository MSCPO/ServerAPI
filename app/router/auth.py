from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.schemas.common import CaptchaBase, MessageResponse
from app.services.auth.crud import (
    cleanup_verification_data,
    create_user_account,
    send_email_verification,
    upload_avatar,
    validate_avatar_file,
    validate_user_data,
    verify_token_or_code,
    verify_verification_code,
    verify_verification_token,
)
from app.services.auth.schemas import (
    AuthToken,
    JWTData,
    RegisterRequest,
    UserLogin,
)
from app.services.auth.validation import (
    validate_captcha_response,
    validate_email_availability,
)
from app.services.conn.redis import redis_client
from app.services.user.crud import get_current_user
from app.services.utils import (
    send_verification_code_email,
    send_verification_email,
)

router = APIRouter()


async def get_real_client_ip(request: Request) -> str | None:
    """
    获取客户端真实的 IP 地址，如果存在反代理则从 X-Forwarded-For 中获取。
    """
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for is None or request.client is None:
        return None
    return forwarded_for.split(",")[0] if forwarded_for else request.client.host


# 用户登录，获取 token
@router.post(
    "/login",
    response_model=AuthToken,
    summary="Token 获取",
    responses={
        200: {
            "description": "成功登录，返回 JWT token",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                    }
                }
            },
        },
        400: {
            "description": "hCaptcha 验证失败",
            "content": {
                "application/json": {"example": {"detail": "Invalid hCaptcha response"}}
            },
        },
        401: {
            "description": "凭证无效，用户名或密码错误",
            "content": {
                "application/json": {"example": {"detail": "Invalid credentials"}}
            },
        },
    },
)
async def login(user: UserLogin, request: Request):
    """
    用户登录，验证凭证并返回 JWT token
    """
    from app.services.auth.crud import login_user

    return await login_user(user, request)


class hcaptcha_sitekey(BaseModel):
    hcaptcha_sitekey: str = Field(
        ..., title="hCaptcha 站点密钥", description="hCaptcha 站点密钥"
    )


class RegisterResponse(MessageResponse):
    user_id: int = Field(..., title="用户 ID", description="用户 ID")


class Email_Register(CaptchaBase):
    email: str = Field(..., title="邮箱", description="用户的邮箱")


@router.post(
    "/verifyemail",
    response_model=MessageResponse,
    summary="邮箱注册",
    description="验证邮箱是否存在，若不存在则发送注册邮件（有效期 15 分钟）或发送验证码（当 by=code 时）",
    responses={
        200: {
            "description": "通过验证，发送验证邮箱或验证码",
            "content": {
                "application/json": {
                    "examples": {
                        "邮件发送成功": {"detail": "验证邮件已发送，请查收您的邮箱"},
                        "验证码发送成功": {"detail": "验证码已发送，请查收您的邮箱"},
                    }
                }
            },
        },
        400: {
            "description": "参数错误",
            "content": {
                "application/json": {
                    "examples": {
                        "邮箱格式错误": {"detail": "邮箱格式错误"},
                        "无效的 hCaptcha 响应": {"detail": "无效的 hCaptcha 响应"},
                    }
                }
            },
        },
        409: {
            "description": "邮箱已存在",
            "content": {"application/json": {"example": {"detail": "邮箱已存在"}}},
        },
    },
)
async def verifyemail(
    request: Email_Register,
    background_tasks: BackgroundTasks,
    by: str | None = Query(None),
):
    await validate_captcha_response(request.captcha_response)
    await validate_email_availability(request.email)

    if by == "code":
        code = await send_email_verification(request.email, by="code")
        background_tasks.add_task(send_verification_code_email, request.email, code)
        return {"detail": "验证码已发送，请查收您的邮箱"}
    else:
        token = await send_email_verification(request.email)
        background_tasks.add_task(send_verification_email, request.email, token)
        return {"detail": "验证邮件已发送，请查收您的邮箱"}


@router.post(
    "/verify/{token}",
    summary="邮箱验证",
    description="验证邮箱注册的 Token，若验证成功则将 Token 标记为正在验证（有效期延长至 24 小时）",
    response_model=MessageResponse,
    responses={
        200: {
            "description": "验证成功",
            "content": {"application/json": {"example": {"detail": "Token 验证成功"}}},
        },
        404: {
            "description": "Token 未找到",
            "content": {"application/json": {"example": {"detail": "Token 无效"}}},
        },
    },
)
async def verify(token: str):
    await verify_verification_token(token)
    return {"detail": "Token 验证成功"}


@router.post(
    "/verify/code/{code}",
    summary="验证码验证",
    description="验证邮箱注册的 6 位数验证码，若验证成功则将验证码标记为已验证（有效期延长至 24 小时）",
    response_model=MessageResponse,
    responses={
        200: {
            "description": "验证成功",
            "content": {"application/json": {"example": {"detail": "验证码验证成功"}}},
        },
        404: {
            "description": "验证码未找到或已过期",
            "content": {
                "application/json": {"example": {"detail": "验证码无效或已过期"}}
            },
        },
        400: {
            "description": "验证码格式错误",
            "content": {
                "application/json": {"example": {"detail": "验证码必须是6位数字"}}
            },
        },
    },
)
async def verify_code(code: str):
    await verify_verification_code(code)
    return {"detail": "验证码验证成功"}


from app.log import logger


@router.post(
    "/register",
    response_model=RegisterResponse,
    summary="注册",
    description="用户注册，验证 Token 后注册用户",
    responses={
        200: {
            "description": "用户注册成功",
            "content": {
                "application/json": {
                    "example": {"detail": "用户注册成功", "user_id": 123}
                }
            },
        },
        400: {
            "description": "请求参数错误（如密码无效或显示名称已存在）",
            "content": {
                "application/json": {
                    "examples": {
                        "密码无效": {
                            "detail": "密码必须至少 8 个字符，并包含至少一个数字、一个大写字母和一个特殊字符"
                        },
                        "显示名称无效": {
                            "detail": "显示名称必须 (4-16 位中文、字毮、数字、下划线、减号)"
                        },
                        "显示名称已存在": {"detail": "显示名称已存在"},
                        "头像文件名无效": {"detail": "头像文件名无效"},
                        "头像文件格式无效": {"detail": "头像文件格式无效"},
                        "头像文件大小不能超过 2 MB": {
                            "detail": "头像文件大小不能超过 2 MB"
                        },
                        "头像必须是正方形": {"detail": "头像必须是正方形"},
                        "头像文件无效": {"detail": "头像文件无效"},
                    }
                }
            },
        },
        422: {
            "description": "hCaptcha 验证失败",
            "content": {
                "application/json": {"example": {"detail": "无效的 hCaptcha 响应"}}
            },
        },
        404: {
            "description": "Token 未找到或已过期",
            "content": {
                "application/json": {"example": {"detail": "Token 未找到或已过期"}}
            },
        },
        409: {
            "description": "Token 未验证",
            "content": {
                "application/json": {
                    "examples": {
                        "Token 未验证": {"detail": "Token 未被验证"},
                        "邮箱已存在": {"detail": "邮箱已存在"},
                    }
                }
            },
        },
        500: {
            "description": "服务器内部错误",
            "content": {"application/json": {"example": {"detail": "头像上传失败"}}},
        },
    },
)
async def register(
    password: str = Form(
        ...,
        description="8-16 位密码，至少包含数字、大写字母、小写字母和特殊字符中的两种",
    ),
    display_name: str = Form(..., description="用户的显示名称，长度为 4-16 位"),
    captcha_response: str = Form(..., description="hCaptcha 验证响应"),
    avatar: UploadFile = File(..., description="用户头像文件"),
    token: str | None = Form(
        None, description="用户注册的验证令牌（使用邮件链接验证时）"
    ),
    code: str | None = Form(None, description="6位数字验证码（使用验证码验证时）"),
):
    register_data = RegisterRequest(
        password=password,
        display_name=display_name,
        token=token,
        code=code,
        captcha_response=captcha_response,
    )
    logger.info(f"Register request: {register_data.model_dump()}")

    # 验证 hCaptcha
    await validate_captcha_response(register_data.captcha_response)

    # 验证 Token 或验证码并获取邮箱
    verify_data = await verify_token_or_code(register_data.token, register_data.code)

    # 验证用户数据
    await validate_user_data(
        verify_data["email"], register_data.display_name, register_data.password
    )

    # 验证头像文件
    if not isinstance(avatar.filename, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件名无效"
        )

    content = await avatar.read()
    await validate_avatar_file(content, avatar.filename)

    # 上传头像
    avatar_hash = await upload_avatar(content, avatar.filename)

    # 创建用户
    user = await create_user_account(
        verify_data["email"],
        register_data.display_name,
        register_data.password,
        avatar_hash,
    )

    # 清理验证数据
    await cleanup_verification_data(register_data.token, register_data.code)

    return {"detail": "用户注册成功", "user_id": user.id}


@router.get(
    "/hcaptcha_site_key",
    summary="hCaptcha site-key",
    response_model=hcaptcha_sitekey,
    responses={
        200: {
            "description": "成功获取 hCaptcha site-key",
            "content": {
                "application/json": {
                    "example": {
                        "hcaptcha_sitekey": "10000000-ffff-ffff-ffff-000000000001"
                    }
                }
            },
        },
        400: {
            "description": "hCaptcha site-key 未配置",
            "content": {
                "application/json": {
                    "example": {"detail": "hCaptcha site key not configured"}
                }
            },
        },
    },
)
def get_hcaptcha_site_key():
    """
    获取 hCaptcha 的站点密钥（site-key）。

    如果 hCaptcha site-key 已配置，返回该 key。若未配置，则返回错误信息。
    """
    if site_key := settings.HCAPTCHA_SITE_KEY:
        return hcaptcha_sitekey(hcaptcha_sitekey=site_key)
    else:
        return JSONResponse(
            status_code=400, content={"detail": "hCaptcha site key not configured"}
        )


# 注销
@router.post(
    "/logout",
    summary="注销",
    description="注销当前用户，使 JWT token 失效",
    responses={
        200: {
            "description": "注销成功",
            "content": {"application/json": {"example": {"detail": "注销成功"}}},
        },
        401: {
            "description": "未授权，缺少或无效的 Bearer token",
            "content": {
                "application/json": {
                    "example": {"detail": "Could not validate credentials"}
                }
            },
        },
    },
)
async def logout(user: JWTData = Depends(get_current_user)):
    """
    注销当前用户，使 JWT token 失效
    """
    token = getattr(user, "token", None)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    await redis_client.setex(f"token:invalid:{token}", 86400, "invalid")
    return {"detail": "注销成功"}
