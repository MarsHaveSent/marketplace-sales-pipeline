import logging
import smtplib
from email.message import EmailMessage

from scripts.common import config

logger = logging.getLogger(__name__)


def send_alert(subject: str, message: str) -> None:
    if not config.SMTP_USER or not config.SMTP_PASSWORD:
        logger.warning("SMTP_USER/SMTP_PASSWORD не заданы, алерт не отправлен")
        return

    to_addr = config.ALERT_EMAIL_TO or config.SMTP_USER

    email = EmailMessage()
    email["Subject"] = subject
    email["From"] = config.SMTP_USER
    email["To"] = to_addr
    email.set_content(message)

    with smtplib.SMTP_SSL(config.SMTP_HOST, config.SMTP_PORT) as smtp:
        smtp.login(config.SMTP_USER, config.SMTP_PASSWORD)
        smtp.send_message(email)
