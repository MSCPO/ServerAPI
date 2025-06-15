"""工具函数模块"""

import io
import json as json
import random
import re
import string
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from zoneinfo import ZoneInfo

import aiosmtplib
import httpx
from fastapi import HTTPException
from jinja2 import Template
from passlib.context import CryptContext
from PIL import Image

from app.config import settings
from app.log import logger
from app.services.conn.redis import redis_client


def validate_password(password: str) -> bool:
    """
    密码规则认证
    """
    if len(password) < 8 or len(password) > 16:
        return False

    patterns = [r"\d", r"[A-Z]", r"[a-z]"]

    type_count = sum(bool(re.search(pattern, password)) for pattern in patterns)

    return type_count >= 2


def validate_email(email: str) -> bool:
    """邮箱格式认证"""
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


def generate_token() -> str:
    """生成 32 位随机字符串"""
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


def generate_verification_code() -> str:
    """生成 6 位数验证码"""
    return "".join(random.choices(string.digits, k=6))


async def asentence() -> dict:
    """获取一言"""
    async with httpx.AsyncClient() as client:
        response = await client.get("https://international.v1.hitokoto.cn")
        data: dict = response.json()
        return data


async def get_token_data(token) -> dict[str, str]:
    verify_data: str = await redis_client.get(f"verify:{token}")
    if verify_data is None:
        raise HTTPException(status_code=404, detail="token 无效")
    data: dict = json.loads(verify_data)
    return data


async def get_code_data(code: str) -> dict[str, str]:
    """获取验证码数据"""
    verify_data: str = await redis_client.get(f"verify_code:{code}")
    if verify_data is None:
        raise HTTPException(status_code=404, detail="验证码无效或已过期")
    data: dict = json.loads(verify_data)
    return data


def render_html_template(template_path, **kwargs):
    """渲染 HTML 模板"""
    with open(template_path, encoding="utf-8") as file:
        template_content = file.read()
    template = Template(template_content)
    return template.render(**kwargs)


async def send_verification_email(to_email: str, token: str):
    """发送验证邮件"""
    from_email = settings.FROM_EMAIL
    password = settings.FROM_EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = formataddr(pair=("MSCPO 验证系统", "support@crashvibe.cn"))
    msg["To"] = to_email
    msg["Subject"] = "[MSCPO] 登陆系统验证"
    asentence_data = await asentence()
    sentence = asentence_data["hitokoto"]
    author = asentence_data["from"]
    from_who = asentence_data["from_who"]
    body = render_html_template(
        "template/email_verify.html",
        token=token,
        fullyear=datetime.now(ZoneInfo("Asia/Shanghai")).year,
        sentence=sentence,
        sentence_from=author,
        from_who=from_who,
    )
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        await _send_email(from_email, password, msg, to_email)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


async def send_verification_code_email(to_email: str, code: str):
    """发送验证码邮件"""
    from_email = settings.FROM_EMAIL
    password = settings.FROM_EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = formataddr(pair=("MSCPO 验证系统", "support@crashvibe.cn"))
    msg["To"] = to_email
    msg["Subject"] = "[MSCPO] 邮箱验证码"
    asentence_data = await asentence()
    sentence = asentence_data["hitokoto"]
    author = asentence_data["from"]
    from_who = asentence_data["from_who"]
    body = render_html_template(
        "template/email_code_verify.html",
        code=code,
        fullyear=datetime.now(ZoneInfo("Asia/Shanghai")).year,
        sentence=sentence,
        sentence_from=author,
        from_who=from_who,
    )
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        await _send_email(from_email, password, msg, to_email)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


async def _send_email(
    from_email: str, password: str, msg: MIMEMultipart, to_email: str
):
    """发送邮件"""
    async with aiosmtplib.SMTP(
        hostname=settings.SMTP_SERVER, port=settings.SMTP_PORT, use_tls=True
    ) as server:
        await server.login(from_email, password)
        text = msg.as_string()
        await server.sendmail(from_email, to_email, text)


def validate_username(username: str) -> bool:
    """用户名认证 (4-16 位中文、字毮、数字、下划线、减号)"""
    if len(username) < 4 or len(username) > 16:
        return False
    return bool(re.match(r"[\u4e00-\u9fa5\w-]+", username))


PWD_CONTEXT = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """密码验证"""
    return PWD_CONTEXT.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """密码加密"""
    return PWD_CONTEXT.hash(password)


def convert_to_webp(file: bytes, quality: int | None = None) -> bytes:
    """
    将上传的图片文件转换为 WebP 格式并返回字节流。

    :param file: 输入的图片文件对象（如上传的文件）
    :param quality: WebP 图片的质量，默认为 80，范围是 0-100
    :return: 转换后的 WebP 图片的字节流
    """
    img = Image.open(io.BytesIO(file))  # 从文件读取图片
    img = img.convert("RGB")  # 确保图像为 RGB 模式

    byte_io = io.BytesIO()

    if quality is None:
        img.save(byte_io, "WEBP", lossless=True)
    else:
        img.save(byte_io, "WEBP", quality=quality)
    return byte_io.getvalue()
