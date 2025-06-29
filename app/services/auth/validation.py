"""认证相关的验证函数"""

from fastapi import HTTPException, status

from app.models import User
from app.services.auth.captcha import verify_hcaptcha
from app.services.utils import validate_email, validate_password, validate_username


async def validate_captcha_response(captcha_response: str) -> None:
    """验证 hCaptcha 响应"""
    if not await verify_hcaptcha(captcha_response):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="无效的 hCaptcha 响应"
        )


async def validate_email_availability(email: str) -> None:
    """验证邮箱是否可用"""
    if await User.get_or_none(email=email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已存在")

    if not validate_email(email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="邮箱格式错误"
        )


async def validate_user_registration_data(
    email: str, display_name: str, password: str
) -> None:
    """验证用户注册数据"""
    # 检查数据库中是否存在该邮箱
    if await User.get_or_none(email=email):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已存在")

    # 验证密码强度
    if not validate_password(password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="密码必须 8～16 个字符，并包含至少一个数字、一个大写字母",
        )

    # 验证用户名是否有效
    if not validate_username(display_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="显示名称必须 (4-16 位中文、字毮、数字、下划线、减号)",
        )

    # 验证用户名是否唯一
    if await User.get_or_none(display_name=display_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="显示名称已存在"
        )


def validate_verification_code_format(code: str) -> None:
    """验证验证码格式"""
    if not code.isdigit() or len(code) != 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="验证码必须是6位数字"
        )


def validate_avatar_filename(filename: str | None) -> None:
    """验证头像文件名"""
    if not isinstance(filename, str):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="头像文件名无效"
        )
