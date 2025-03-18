import uuid
from io import BytesIO

import ujson as json
from fastapi import (
    APIRouter,
    BackgroundTasks,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from PIL import Image
from pydantic import BaseModel, Field

from app.config import settings
from app.file_storage.utils import upload_file_to_s3
from app.services.auth.auth import create_access_token
from app.services.auth.crud import (
    update_last_login,
    verify_recaptcha,
)
from app.services.auth.schemas import (
    Auth_Token,
    RegisterRequest,
    UserLogin,
    captchaResponse,
    jwt_data,
)
from app.services.conn.redis import redis_client
from app.services.user.crud import get_current_user
from app.services.user.models import User
from app.services.utils import (
    generate_token,
    get_token_data,
    hash_password,
    send_verification_email,
    validate_email,
    validate_password,
    validate_username,
    verify_password,
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
    response_model=Auth_Token,
    summary="Token 获取",
    responses={
        200: {
            "description": "成功登录，返回 JWT token",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "your_token_here",
                        "token_type": "bearer",
                    }
                }
            },
        },
        400: {
            "description": "reCAPTCHA 验证失败",
            "content": {
                "application/json": {
                    "example": {"detail": "Invalid reCAPTCHA response"}
                }
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
    if not await verify_recaptcha(user.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reCAPTCHA response"
        )
    if "@" in user.username_or_email:
        db_user = await User.get_or_none(email=user.username_or_email)
    else:
        db_user = await User.get_or_none(username=user.username_or_email)
    if db_user is None or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 获取真实客户端 IP
    client_ip = await get_real_client_ip(request)
    if client_ip is not None:
        await update_last_login(db_user, client_ip)

    # 创建并返回 JWT token
    access_token = create_access_token(
        data=jwt_data(sub=db_user.username, id=db_user.id)
    )
    return Auth_Token.model_validate(
        {"access_token": access_token, "token_type": "bearer"}
    )


class recapcha_sitekey(BaseModel):
    recapcha_sitekey: str = Field(
        ..., title="reCAPTCHA 站点密钥", description="reCAPTCHA 站点密钥"
    )


class ReturnResponse(BaseModel):
    detail: str = Field(..., title="消息", description="状态返回消息")


class ReturnResponse_Register(ReturnResponse):
    user_id: int = Field(..., title="用户 ID", description="用户 ID")


class Email_Register(captchaResponse):
    email: str = Field(..., title="邮箱", description="用户的邮箱")


@router.post(
    "/verifyemail",
    response_model=ReturnResponse,
    summary="邮箱注册",
    description="验证邮箱是否存在，若不存在则发送注册邮件（有效期 15 分钟）",
    responses={
        200: {
            "description": "通过验证，发送验证邮箱",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "验证邮件已发送，请查收您的邮箱",
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
                        "无效的 reCAPTCHA 响应": {"detail": "无效的 reCAPTCHA 响应"},
                    }
                }
            },
        },
        409: {
            "description": "邮箱已存在",
            "content": {"application/json": {"邮箱已存在": {"detail": "邮箱已存在"}}},
        },
    },
)
async def verifyemail(request: Email_Register, background_tasks: BackgroundTasks):
    if not await verify_recaptcha(request.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的 reCAPTCHA 响应"
        )
    if await User.get_or_none(email=request.email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已存在")

    if not validate_email(request.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱格式错误"
        )

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
    response_model=ReturnResponse,
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


from app.log import logger


@router.post(
    "/register",
    response_model=ReturnResponse_Register,
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
                        "File type image/jpeg not allowed": {
                            "detail": "File type image/jpeg not allowed"
                        },
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
            "description": "reCAPTCHA 验证失败",
            "content": {
                "application/json": {"example": {"detail": "无效的 reCAPTCHA 响应"}}
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
            "content": {"application/json": {"Token 未验证": {"detail": "未被验证"}}},
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

    if not await verify_recaptcha(register_data.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="无效的 reCAPTCHA 响应",
        )

    # 验证密码强度
    if not validate_password(register_data.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须至少 8 个字符，并包含至少一个数字、一个大写字母和一个特殊字符",
        )

    # 验证 Token
    verify_data = await get_token_data(register_data.token)
    if verify_data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Token 未找到或已过期"
        )
    if not verify_data["verified"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Token 未被验证"
        )

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

    allowed_content_types = ["image/jpeg", "image/png", "image/webp"]

    if avatar.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {avatar.content_type} not allowed",
        )

    content = await avatar.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件大小不能超过 2 MB"
        )

    try:
        avatar.file.seek(0)
        image = Image.open(BytesIO(await avatar.read()))
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
        avatar_file = (await upload_file_to_s3(content, avatar.filename))[1]
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
            avatar_hash=avatar_file,
            is_active=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建用户失败"
        ) from e

    # 删除 token
    await redis_client.delete(f"verify:{register_data.token}")

    return {"detail": "用户注册成功", "user_id": user.id}


@router.get(
    "/reCAPTCHA_site_key",
    summary="reCAPTCHA site-key",
    response_model=recapcha_sitekey,
    responses={
        200: {
            "description": "成功获取 reCAPTCHA site-key",
            "content": {
                "application/json": {
                    "example": {"reCAPTCHA_site_key": "your_site_key_here"}
                }
            },
        },
        400: {
            "description": "reCAPTCHA site-key 未配置",
            "content": {
                "application/json": {
                    "example": {"detail": "reCAPTCHA site key not configured"}
                }
            },
        },
    },
)
def get_reCAPTCHA_site_key():
    """
    获取 reCAPTCHA 的站点密钥（site-key）。

    如果 reCAPTCHA site-key 已配置，返回该 key。若未配置，则返回错误信息。
    """
    if site_key := settings.RECAPTCHA_SITE_KEY:
        return recapcha_sitekey(recapcha_sitekey=site_key)
    else:
        return JSONResponse(
            status_code=400, content={"detail": "reCAPTCHA site key not configured"}
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
    # 使用 redis 黑名单

    token = request.headers.get("Authorization")
    if token is None or not token.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
    token = token.split(" ")[1]
    await get_current_user(token)
    await redis_client.setex(f"token:invalid:{token}", 86400, "invalid")
    return {"detail": "注销成功"}
