from __future__ import annotations

import json
import logging
import urllib.parse
import urllib.request
from typing import Any

from telegram_config import BOT_TOKEN, CHAT_ID, ENABLE_TELEGRAM

logger = logging.getLogger(__name__)
TELEGRAM_API_URL = "https://api.telegram.org/bot"


def send_telegram(message: str) -> bool:
    if not ENABLE_TELEGRAM:
        logger.debug("Telegram disabled or not configured. Skipping send.")
        return False

    url = f"{TELEGRAM_API_URL}{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True,
    }
    data = urllib.parse.urlencode(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = response.read()
            parsed = json.loads(body)
            if parsed.get("ok"):
                return True
            logger.error("Telegram API returned error: %s", parsed)
    except Exception as exc:
        logger.error("Telegram send failed: %s", exc)

    return False
