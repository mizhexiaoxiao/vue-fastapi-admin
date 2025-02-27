import os
from jinja2 import Template
from passlib import pwd
from passlib.context import CryptContext
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from loguru import logger

from app.settings import settings


pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def generate_password() -> str:
    return pwd.genword()


async def send_forgot_password_email(language: str, reset_url: str, app_title: str, to_address: str):
    if language == 'cn':
        template_path = os.path.join(settings.TEMPLATES_ROOT, 'cn', 'reset_password.html')
    else:
        template_path = os.path.join(settings.TEMPLATES_ROOT, 'en', 'reset_password.html')

    with open(template_path, 'r', encoding='utf-8') as f:
        template = Template(f.read())

    render = template.render(reset_url=reset_url, app_title=app_title)
    msg = MIMEMultipart()
    msg['From'] = settings.EMAIL_ADDRESS
    msg['To'] = to_address
    msg['Subject'] = f'[{app_title}] Password Reset Request'

    # 添加邮件内容
    msg.attach(MIMEText(render, 'html'))

    try:
        with SMTP(**settings.MAIL_AUTH) as smtp:
            smtp.send_message(
                msg
            )
            logger.debug(f"send email success({to_address})")
    except Exception as e:
        logger.error(f"send email error({to_address}): %s", e)