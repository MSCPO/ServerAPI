import re
import smtplib
import string
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from random import random
from zoneinfo import ZoneInfo

from app.config import settings
from jinja2 import Template
from app.log import logger


def validate_password(password: str) -> str:
    """
    密码规则认证
    """
    if len(password) < 8 or len(password) > 16:
        return False

    patterns = [r"\d", r"[A-Z]", r"[a-z]", r"[@#$%^&+=!]"]

    type_count = sum(bool(re.search(pattern, password)) for pattern in patterns)

    return type_count >= 2


def generate_token() -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


def render_html_template(template_path, **kwargs):
    with open(template_path, encoding="utf-8") as file:
        template_content = file.read()
    template = Template(template_content)
    return template.render(**kwargs)


# 发送验证邮件
def send_verification_email(to_email: str, token: str):
    # 使用 settings 中的配置
    from_email = settings.FROM_EMAIL
    password = settings.FROM_EMAIL_PASSWORD

    msg = MIMEMultipart()
    msg["From"] = from_email
    msg["To"] = to_email
    msg["Subject"] = "[MSCPO] 登陆系统验证"

    body = render_html_template(
        "template/email_verify.html",
        token=token,
        fullyear=datetime.now(ZoneInfo("Asia/Shanghai")).year,
    )
    msg.attach(MIMEText(body, "html", "utf-8"))

    try:
        _send_mail(from_email, password, msg, to_email)
    except Exception as e:
        logger.error(f"Failed to send email: {e}")


def _send_mail(from_email: str, password: str, msg: MIMEMultipart, to_email: str):
    server = smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT)
    server.login(from_email, password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()
