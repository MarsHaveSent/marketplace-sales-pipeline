import logging

import requests

from scripts.common import config

logger = logging.getLogger(__name__)


def send_alert(message: str) -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        logger.warning(
            "TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID не заданы, алерт не отправлен"
        )
        return
    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    response = requests.post(
        url, json={"chat_id": config.TELEGRAM_CHAT_ID, "text": message}, timeout=10
    )
    response.raise_for_status()
