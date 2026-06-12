# Bot_Boxphone

A simple human-like bot for Android devices using ADB.

## What it does

- discovers connected Android devices via ADB
- launches the configured app package
- swipes through videos
- performs weighted "like" and "comment" actions
- uses per-device screen coordinate overrides from `devices_config.json`
- runs each device in a parallel thread

## Prerequisites

1. Python 3.10+ installed
2. ADB installed and available on `PATH`
3. Android devices connected and authorized for ADB debugging
4. Optional: `devices_config.json` entries for each device serial

## Install

Open a terminal in the project folder:

```powershell
python -m pip install -r requirements.txt
```

## Configure

1. Edit `config.py` to set your app package and timing settings.
2. Optionally override coordinates in `devices_config.json`:

```json
{
  "default": {
    "like_button_center": [400, 800],
    "like_button_size": [100, 50],
    "comment_button_center": [400, 900],
    "comment_button_size": [80, 40],
    "next_video_swipe_from": [500, 1000],
    "next_video_swipe_to": [500, 500]
  },
  "emulator-5554": {
    "like_button_center": [380, 790],
    "like_button_size": [100, 50],
    "comment_button_center": [380, 890],
    "comment_button_size": [80, 40],
    "next_video_swipe_from": [490, 1000],
    "next_video_swipe_to": [490, 500]
  }
}
```

## Telegram Notifications

1. Set your Telegram bot token and chat ID as environment variables:

```powershell
$env:TELEGRAM_BOT_TOKEN = "your_bot_token_here"
$env:TELEGRAM_CHAT_ID = "your_chat_id_here"
```

2. Alternatively, edit `telegram_config.py` and replace the placeholder values.
3. The bot sends messages when it starts, every 10 jobs, on throttle activation, on critical errors, and when it finishes.

## Run

```powershell
python bot_optimized.py
```

## Notes

- The bot uses `app_start` and falls back to a monkey launch command if needed.
- It stops when the daily action limit is reached or outside the configured active hours.
- Use `week = 1` in `bot_optimized.py` and adjust it as the account matures.
