import uuid
from datetime import datetime
from io import BytesIO
from zoneinfo import ZoneInfo

import ujson as json
from fastapi import HTTPException, Request, status
from PIL import Image

from app.file_storage.utils import upload_file_to_s3
from app.log import logger
from app.models import User
from app.services.auth.auth import create_access_token
from app.services.auth.captcha import verify_hcaptcha
from app.services.auth.schemas import AuthToken, JWTData, UserLogin
from app.services.auth.validation import (
    validate_user_registration_data,
    validate_verification_code_format,
)
from app.services.conn.redis import redis_client
from app.services.utils import (
    convert_to_webp,
    generate_token,
    generate_verification_code,
    get_code_data,
    get_token_data,
    hash_password,
    verify_password,
)


async def update_last_login(user: User, ip: str):
    # 获取上海时区的当前时间
    user.last_login = datetime.now(ZoneInfo("Asia/Shanghai"))
    user.last_login_ip = ip
    # 保存用户数据
    await user.save(update_fields=["last_login", "last_login_ip"])


async def login_user(user: UserLogin, request: Request) -> AuthToken:
    if not await verify_hcaptcha(user.captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid hCaptcha response"
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
    client_ip = request.headers.get("X-Forwarded-For") or (
        request.client.host if request.client else None
    )
    if client_ip is not None:
        await update_last_login(db_user, client_ip)
    access_token = create_access_token(
        data=JWTData(sub=db_user.username, id=db_user.id)
    )
    return AuthToken.model_validate(
        {"access_token": access_token, "token_type": "bearer"}
    )


async def create_verification_token(email: str) -> str:
    """创建邮箱验证 Token"""
    token = generate_token()
    # 检查 token 是否有重复
    while await redis_client.get(f"verify:{token}"):
        token = generate_token()

    await redis_client.setex(
        f"verify:{token}",
        900,
        json.dumps({"email": email, "verified": False}),
    )
    return token


async def create_verification_code(email: str) -> str:
    """创建邮箱验证码"""
    code = generate_verification_code()
    # 检查验证码是否有重复
    while await redis_client.get(f"verify_code:{code}"):
        code = generate_verification_code()

    await redis_client.setex(
        f"verify_code:{code}",
        900,
        json.dumps({"email": email, "verified": False}),
    )
    return code


async def verify_token_or_code(token: str | None, code: str | None) -> dict:
    """验证 Token 或验证码并返回验证数据"""
    if token:
        verify_data = await get_token_data(token)
        if verify_data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Token 未找到或已过期"
            )
        if not verify_data["verified"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Token 未被验证"
            )
        return verify_data
    elif code:
        validate_verification_code_format(code)
        verify_data = await get_code_data(code)
        if not verify_data["verified"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="验证码未被验证"
            )
        return verify_data
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="必须提供验证令牌或验证码"
        )


async def validate_avatar_file(avatar_content: bytes, filename: str) -> None:
    """验证头像文件"""
    if len(avatar_content) > 2 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件大小不能超过 2 MB"
        )

    try:
        image = Image.open(BytesIO(avatar_content))
        image.verify()

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


async def upload_avatar(content: bytes, filename: str) -> str:
    """上传头像并返回文件对象"""
    try:
        _, file_object = await upload_file_to_s3(convert_to_webp(content), filename)
        return file_object.hash_value
    except Exception as e:
        logger.error(f"Failed to upload avatar: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="头像上传失败"
        ) from e


async def generate_unique_username() -> str:
    """生成唯一用户名"""
    username = f"mscpo_{uuid.uuid4().hex[:8]}"
    while await User.get_or_none(username=username):
        username = f"mscpo_{uuid.uuid4().hex[:8]}"
    return username


async def create_user_account(
    email: str, display_name: str, password: str, avatar_hash: str
) -> User:
    """创建用户账户"""
    username = await generate_unique_username()

    try:
        return await User.create(
            username=username,
            email=email,
            display_name=display_name,
            hashed_password=hash_password(password),
            avatar_hash=avatar_hash,
            is_active=True,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="创建用户失败"
        ) from e


async def cleanup_verification_data(token: str | None, code: str | None) -> None:
    """清理验证数据"""
    if token:
        await redis_client.delete(f"verify:{token}")
    elif code:
        await redis_client.delete(f"verify_code:{code}")


async def validate_user_data(email: str, display_name: str, password: str) -> None:
    """验证用户数据"""
    await validate_user_registration_data(email, display_name, password)


async def send_email_verification(email: str, by: str | None = None) -> str:
    """发送邮箱验证（Token 或验证码）"""
    if by == "code":
        return await create_verification_code(email)
    return await create_verification_token(email)


async def verify_verification_token(token: str) -> None:
    """验证邮箱验证 Token"""
    verify_data = await get_token_data(token)
    await redis_client.setex(
        f"verify:{token}",
        86400,
        json.dumps({"email": verify_data["email"], "verified": True}),
    )


async def verify_verification_code(code: str) -> None:
    """验证邮箱验证码"""
    validate_verification_code_format(code)

    # 获取验证码数据
    verify_data = await get_code_data(code)

    # 更新验证码状态为已验证，延长有效期至24小时
    await redis_client.setex(
        f"verify_code:{code}",
        86400,
        json.dumps({"email": verify_data["email"], "verified": True}),
    )
