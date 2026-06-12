# config.py
from __future__ import annotations

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

Coord = tuple[int, int]
Size = tuple[int, int]

_DEVICES_CONFIG_PATH = Path(__file__).parent / "devices_config.json"


class Config:
    # --- App ---
    APP_PACKAGE: str = "com.xiaowei.app"

    # --- Warm-up: action limit per day by week number (DCA-style ramp-up) ---
    DAILY_LIMIT_BY_WEEK: dict[int, int] = {1: 40, 2: 100, 3: 200, 4: 300}

    # --- Active hours (match device/proxy timezone) ---
    ACTIVE_HOUR_START: int = 8
    ACTIVE_HOUR_END: int = 23

    # --- Delays in seconds (Gaussian distribution applied inside HumanBehavior) ---
    DELAY_MIN: float = 3.0
    DELAY_MAX: float = 10.0
    COOLDOWN_MIN: float = 5.0
    COOLDOWN_MAX: float = 15.0

    # --- Long break: randomised interval so cadence is not predictable ---
    LONG_BREAK_EVERY_MIN: int = 12
    LONG_BREAK_EVERY_MAX: int = 18
    LONG_BREAK_MIN: float = 60.0
    LONG_BREAK_MAX: float = 180.0

    # --- Screen coordinates – override per-device via devices_config.json ---
    LIKE_BUTTON_CENTER: Coord = (400, 800)
    LIKE_BUTTON_SIZE: Size = (100, 50)
    COMMENT_BUTTON_CENTER: Coord = (400, 900)
    COMMENT_BUTTON_SIZE: Size = (80, 40)
    NEXT_VIDEO_SWIPE_FROM: Coord = (500, 1000)
    NEXT_VIDEO_SWIPE_TO: Coord = (500, 500)

    # --- Risk control ---
    ERROR_THRESHOLD: float = 0.10

    # --- Weighted action probability (higher = more frequent) ---
    ACTION_WEIGHTS: dict[str, float] = {"like": 0.60, "comment": 0.25, "none": 0.15}

    def __init__(self) -> None:
        # Copy class-level defaults to instance so per-device overrides don't
        # pollute the class and affect other instances.
        self.APP_PACKAGE = Config.APP_PACKAGE
        self.DAILY_LIMIT_BY_WEEK = dict(Config.DAILY_LIMIT_BY_WEEK)
        self.ACTIVE_HOUR_START = Config.ACTIVE_HOUR_START
        self.ACTIVE_HOUR_END = Config.ACTIVE_HOUR_END
        self.DELAY_MIN = Config.DELAY_MIN
        self.DELAY_MAX = Config.DELAY_MAX
        self.COOLDOWN_MIN = Config.COOLDOWN_MIN
        self.COOLDOWN_MAX = Config.COOLDOWN_MAX
        self.LONG_BREAK_EVERY_MIN = Config.LONG_BREAK_EVERY_MIN
        self.LONG_BREAK_EVERY_MAX = Config.LONG_BREAK_EVERY_MAX
        self.LONG_BREAK_MIN = Config.LONG_BREAK_MIN
        self.LONG_BREAK_MAX = Config.LONG_BREAK_MAX
        self.LIKE_BUTTON_CENTER = Config.LIKE_BUTTON_CENTER
        self.LIKE_BUTTON_SIZE = Config.LIKE_BUTTON_SIZE
        self.COMMENT_BUTTON_CENTER = Config.COMMENT_BUTTON_CENTER
        self.COMMENT_BUTTON_SIZE = Config.COMMENT_BUTTON_SIZE
        self.NEXT_VIDEO_SWIPE_FROM = Config.NEXT_VIDEO_SWIPE_FROM
        self.NEXT_VIDEO_SWIPE_TO = Config.NEXT_VIDEO_SWIPE_TO
        self.ERROR_THRESHOLD = Config.ERROR_THRESHOLD
        self.ACTION_WEIGHTS = dict(Config.ACTION_WEIGHTS)

    def daily_limit(self, week: int) -> int:
        max_week = max(self.DAILY_LIMIT_BY_WEEK)
        return self.DAILY_LIMIT_BY_WEEK.get(week, self.DAILY_LIMIT_BY_WEEK[max_week])

    @classmethod
    def from_device(cls, device_serial: str) -> Config:
        """Build a Config with coordinates overridden for a specific device serial."""
        cfg = cls()

        if not _DEVICES_CONFIG_PATH.exists():
            return cfg

        try:
            data: dict = json.loads(_DEVICES_CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.warning("Cannot read devices_config.json: %s", exc)
            return cfg

        default_conf: dict = data.get("default", {})
        device_conf: dict = data.get(device_serial, {})
        merged = {**default_conf, **device_conf}

        def get_coord(key: str, fallback: Coord) -> Coord:
            raw = merged.get(key)
            return (int(raw[0]), int(raw[1])) if raw else fallback

        def get_size(key: str, fallback: Size) -> Size:
            raw = merged.get(key)
            return (int(raw[0]), int(raw[1])) if raw else fallback

        cfg.LIKE_BUTTON_CENTER = get_coord("like_button_center", cfg.LIKE_BUTTON_CENTER)
        cfg.LIKE_BUTTON_SIZE = get_size("like_button_size", cfg.LIKE_BUTTON_SIZE)
        cfg.COMMENT_BUTTON_CENTER = get_coord("comment_button_center", cfg.COMMENT_BUTTON_CENTER)
        cfg.COMMENT_BUTTON_SIZE = get_size("comment_button_size", cfg.COMMENT_BUTTON_SIZE)
        cfg.NEXT_VIDEO_SWIPE_FROM = get_coord("next_video_swipe_from", cfg.NEXT_VIDEO_SWIPE_FROM)
        cfg.NEXT_VIDEO_SWIPE_TO = get_coord("next_video_swipe_to", cfg.NEXT_VIDEO_SWIPE_TO)

        logger.debug("Config loaded for %s", device_serial)
        return cfg
