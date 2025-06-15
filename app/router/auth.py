import uuid
from io import BytesIO

import ujson as json
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, Field

from app.config import settings
from app.file_storage.utils import upload_file_to_s3
from app.schemas.common import CaptchaBase, MessageResponse
from app.services.auth.crud import (
    verify_hcaptcha,
)
from app.services.auth.schemas import (
    AuthToken,
    RegisterRequest,
    UserLogin,
)
from app.services.conn.redis import redis_client
from app.services.user.models import User
from app.services.utils import (
    convert_to_webp,
    generate_token,
    generate_verification_code,
    get_code_data,
    get_token_data,
    hash_password,
    send_verification_email,
    send_verification_code_email,
    validate_email,
    validate_password,
    validate_username,
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
                        "验证码发送成功": {"detail": "验证码已发送，请查收您的邮箱"}
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
async def verifyemail(request: Email_Register, background_tasks: BackgroundTasks, by: str | None = Query(None)):
    if not await verify_hcaptcha(request.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的 hCaptcha 响应"
        )
    if await User.get_or_none(email=request.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已存在")

    if not validate_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱格式错误"
        )

    if by == "code":
        # 生成6位数验证码
        code = generate_verification_code()
        # 检查验证码是否有重复
        while await redis_client.get(f"verify_code:{code}"):
            code = generate_verification_code()

        await redis_client.setex(
            f"verify_code:{code}", 900, json.dumps({"email": request.email, "verified": False})
        )
        background_tasks.add_task(send_verification_code_email, request.email, code)
        return {"detail": "验证码已发送，请查收您的邮箱"}
    else:
        # 原有的token验证逻辑
        token = generate_token()
        # 检擦 token 是否有重复
        while await redis_client.get(f"verify:{token}"):
            token = generate_token()

        await redis_client.setex(
            f"verify:{token}", 900, json.dumps({"email": request.email, "verified": False})
        )
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
    verify_data = await get_token_data(token)
    await redis_client.setex(
        f"verify:{token}",
        86400,
        json.dumps({"email": verify_data["email"], "verified": True}),
    )

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
            "content": {"application/json": {"example": {"detail": "验证码无效或已过期"}}},
        },
        400: {
            "description": "验证码格式错误",
            "content": {"application/json": {"example": {"detail": "验证码必须是6位数字"}}},
        },
    },
)
async def verify_code(code: str):
    # 验证码格式检查
    if not code.isdigit() or len(code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="验证码必须是6位数字"
        )
    
    # 获取验证码数据
    verify_data = await get_code_data(code)
    
    # 更新验证码状态为已验证，延长有效期至24小时
    await redis_client.setex(
        f"verify_code:{code}",
        86400,
        json.dumps({"email": verify_data["email"], "verified": True}),
    )

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
    request: str = Form(...),  # 接收字符串形式的 JSON
    avatar: UploadFile = File(...),  # 接收上传的文件
):
    request_data: dict = json.loads(request)
    logger.info(f"Register request: {request_data}")
    register_data = RegisterRequest(**request_data)

    if not await verify_hcaptcha(register_data.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="无效的 hCaptcha 响应",
        )

    # 验证密码强度
    if not validate_password(register_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须 8～16 个字符，并包含至少一个数字、一个大写字母",
        )

    # 验证 Token 或验证码
    if register_data.token:
        # 使用 Token 验证
        verify_data = await get_token_data(register_data.token)
        if verify_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Token 未找到或已过期"
            )
        if not verify_data["verified"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Token 未被验证"
            )
    elif register_data.code:
        # 使用验证码验证
        if not register_data.code.isdigit() or len(register_data.code) != 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="验证码必须是6位数字"
            )
        verify_data = await get_code_data(register_data.code)
        if not verify_data["verified"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="验证码未被验证"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="必须提供验证令牌或验证码"
        )
    # 检查数据库中是否存在该邮箱
    if await User.get_or_none(email=verify_data["email"]):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已存在")

    # 验证用户名是否唯一
    if not validate_username(register_data.display_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="显示名称必须 (4-16 位中文、字毮、数字、下划线、减号)",
        )

    if await User.get_or_none(display_name=register_data.display_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="显示名称已存在"
        )

    if not isinstance(avatar.filename, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件名无效"
        )

    content = await avatar.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件大小不能超过 2 MB"
        )

    try:
        avatar.file.seek(0)  # 归零指针，确保后续读取正常
        image = Image.open(BytesIO(await avatar.read()))
        image.verify()  # 验证图片文件是否有效

        # 检查图片格式
        if image.format not in ["JPEG", "PNG", "WEBP"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件格式无效"
            )

        width, height = image.size
        if width != height:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="头像必须是正方形"
            )

    except Exception as e:
        logger.error(f"Failed to open image: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件无效"
        ) from e

    try:
        avatar_hash = (
            await upload_file_to_s3(convert_to_webp(content), avatar.filename)
        )[1]
    except Exception as e:
        logger.error(f"Failed to upload avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="头像上传失败"
        ) from e

    # 生成唯一用户名
    username = f"mscpo_{uuid.uuid4().hex[:8]}"
    while await User.get_or_none(username=username):
        username = f"mscpo_{uuid.uuid4().hex[:8]}"

    try:
        user = await User.create(
            username=username,
            email=verify_data["email"],
            display_name=register_data.display_name,
            hashed_password=hash_password(register_data.password),
            avatar_hash=avatar_hash,
            is_active=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建用户失败"
        ) from e

    # 删除 token 或验证码
    if register_data.token:
        await redis_client.delete(f"verify:{register_data.token}")
    elif register_data.code:
        await redis_client.delete(f"verify_code:{register_data.code}")

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
async def logout(request: Request):
    """
    注销当前用户，使 JWT token 失效
    """
    # 统一用 request.state.user 认证
    user = getattr(request.state, "user", None)
    if user is None or not hasattr(user, "token"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    token = user.token
    await redis_client.setex(f"token:invalid:{token}", 86400, "invalid")
    return {"detail": "注销成功"}
