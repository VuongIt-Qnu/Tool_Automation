from __future__ import annotations

import os

# Set your Telegram bot token and chat ID here, or provide them via environment
# variables to keep secrets out of source control.
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")

# If either value is missing or left as the default placeholder, Telegram
# notifications will be skipped.
ENABLE_TELEGRAM = bool(BOT_TOKEN and CHAT_ID and "YOUR_TELEGRAM" not in BOT_TOKEN)
