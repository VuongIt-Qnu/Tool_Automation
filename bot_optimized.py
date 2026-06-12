# bot_optimized.py
# Xiaowei/BoxPhone channel-nurturing bot.
# Runs one HumanLikeBot per device in parallel threads, each with its own
# per-device config, risk monitor, and randomised behaviour patterns.

from __future__ import annotations

import logging
import random
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from config import Config
from human_behavior import HumanBehavior, RiskMonitor
from telegram_formatter import (
    format_error,
    format_finish,
    format_progress,
    format_start,
    format_throttle,
)
from telegram_logger import send_telegram

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bot
# ---------------------------------------------------------------------------

class HumanLikeBot:
    def __init__(self, device: Any, week: int = 1) -> None:
        self.device = device
        self.serial: str = getattr(device, "serial", str(device))
        self.week = week
        self.cfg = Config.from_device(self.serial)
        self.behavior = HumanBehavior(device, self.cfg)
        self.risk = RiskMonitor(self.cfg.ERROR_THRESHOLD)
        self.daily_limit = self.cfg.daily_limit(week)
        self.action_count = 0
        self.like_ok = 0
        self.comment_ok = 0
        self.error_count = 0
        self.last_throttle = 1.0
        # Randomise first long-break checkpoint to prevent all devices
        # pausing at the same cycle count when run in parallel.
        self._next_break_at = random.randint(
            self.cfg.LONG_BREAK_EVERY_MIN,
            self.cfg.LONG_BREAK_EVERY_MAX,
        )

    # ------------------------------------------------------------------
    # App lifecycle
    # ------------------------------------------------------------------

    def _open_app(self) -> bool:
        for attempt in range(1, 4):
            try:
                self.device.app_start(self.cfg.APP_PACKAGE)
                self.behavior.random_delay(1, 2)
                return True
            except Exception as exc:
                logger.warning(
                    "[%s] App start attempt %d failed: %s",
                    self.serial,
                    attempt,
                    exc,
                )
                try:
                    self.device.shell(
                        f"monkey -p {self.cfg.APP_PACKAGE}"
                        " -c android.intent.category.LAUNCHER 1"
                    )
                    self.behavior.random_delay(1, 2)
                    return True
                except Exception as exc2:
                    logger.warning(
                        "[%s] Monkey launch attempt %d failed: %s",
                        self.serial,
                        attempt,
                        exc2,
                    )
                    self.behavior.random_delay(2, 4)

        err_msg = format_error(
            device_name=self.serial,
            action=f"MỞ APP {self.cfg.APP_PACKAGE}",
            detail="Thử lại 3 lần đều thất bại",
            decision="DỪNG BOT CHO MÁY NÀY",
        )
        send_telegram(err_msg)
        logger.error("[%s] Could not open app %s after 3 attempts", self.serial, self.cfg.APP_PACKAGE)
        return False

    # ------------------------------------------------------------------
    # Individual actions
    # ------------------------------------------------------------------

    def _like_video(self) -> None:
        cx, cy = self.cfg.LIKE_BUTTON_CENTER
        w, h = self.cfg.LIKE_BUTTON_SIZE
        jitter = self.behavior.jitter_for_button(w, h)
        self.behavior.click_with_trail(cx, cy, jitter)

    def _comment_video(self) -> None:
        cx, cy = self.cfg.COMMENT_BUTTON_CENTER
        w, h = self.cfg.COMMENT_BUTTON_SIZE
        jitter = self.behavior.jitter_for_button(w, h)
        self.behavior.human_click(cx, cy, jitter)

    def _pick_actions(self) -> list[str]:
        """Weighted-random action selection.

        Uses ACTION_WEIGHTS so 'like' fires most often, 'none' causes a
        natural skip that mimics a real user just watching without engaging.
        Picking 1 or 2 actions per video also avoids a fixed pattern.
        """
        pool = list(self.cfg.ACTION_WEIGHTS.keys())
        weights = list(self.cfg.ACTION_WEIGHTS.values())
        count = random.randint(1, 2)
        return random.choices(pool, weights=weights, k=count)

    # ------------------------------------------------------------------
    # Cycle: one video + actions
    # ------------------------------------------------------------------

    def _run_one_cycle(self) -> None:
        self.behavior.human_swipe_next_video()
        actions = self._pick_actions()

        for act in actions:
            success = True
            try:
                if act == "like":
                    self._like_video()
                    self.like_ok += 1
                elif act == "comment":
                    self._comment_video()
                    self.comment_ok += 1
                # "none" → passive watch, intentionally no click
            except Exception as exc:
                logger.warning("[%s] Action '%s' failed: %s", self.serial, act, exc)
                self.error_count += 1
                error_msg = format_error(
                    device_name=self.serial,
                    action=f"CLICK_{act.upper()}",
                    detail=str(exc),
                )
                send_telegram(error_msg)
                success = False

            throttle = self.risk.record(success)
            if throttle > 1.0 and self.last_throttle == 1.0:
                throttle_msg = format_throttle(
                    device_name=self.serial,
                    error_rate=self.risk.error_rate * 100,
                    threshold=self.cfg.ERROR_THRESHOLD * 100,
                    factor=throttle,
                )
                send_telegram(throttle_msg)
            self.last_throttle = throttle
            self.behavior.random_delay(
                self.cfg.DELAY_MIN * throttle,
                self.cfg.DELAY_MAX * throttle,
            )

        self.action_count += 1
        self.behavior.random_delay(self.cfg.COOLDOWN_MIN, self.cfg.COOLDOWN_MAX)

        # Long break at a randomised checkpoint so cadence looks organic
        if self.action_count >= self._next_break_at:
            logger.info("[%s] Long break – %d cycles done", self.serial, self.action_count)
            self.behavior.random_delay(self.cfg.LONG_BREAK_MIN, self.cfg.LONG_BREAK_MAX)
            self._next_break_at = self.action_count + random.randint(
                self.cfg.LONG_BREAK_EVERY_MIN,
                self.cfg.LONG_BREAK_EVERY_MAX,
            )

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run(self) -> None:
        start_msg = format_start(
            device_name=self.serial,
            week=self.week,
            daily_target=self.daily_limit,
        )
        send_telegram(start_msg)

        logger.info(
            "[%s] Start – week %d, daily limit %d",
            self.serial,
            self.week,
            self.daily_limit,
        )

        if not self._open_app():
            return

        while (
            self.action_count < self.daily_limit
            and self.behavior.is_natural_activity_time()
        ):
            self._run_one_cycle()

            if self.action_count % 10 == 0:
                progress_msg = format_progress(
                    device_name=self.serial,
                    done_jobs=self.action_count,
                    total_jobs=self.daily_limit,
                    like_ok=self.like_ok,
                    comment_ok=self.comment_ok,
                    error_count=self.error_count,
                )
                send_telegram(progress_msg)

        finish_msg = format_finish(
            device_name=self.serial,
            week=self.week,
            target=self.daily_limit,
            like_ok=self.like_ok,
            comment_ok=self.comment_ok,
            error_count=self.error_count,
        )
        send_telegram(finish_msg)

        logger.info(
            "[%s] Done – %d/%d cycles, error rate %.0f%%",
            self.serial,
            self.action_count,
            self.daily_limit,
            self.risk.error_rate * 100,
        )


# ---------------------------------------------------------------------------
# Device discovery
# ---------------------------------------------------------------------------

def get_devices() -> list[Any]:
    try:
        from ppadb.client import Client as AdbClient  # type: ignore[import]
        client = AdbClient(host="127.0.0.1", port=5037)
        devices = client.devices()
        logger.info("Found %d device(s) via ADB", len(devices))
        return devices
    except Exception as exc:
        logger.error("ADB connection failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# Parallel entry point
# ---------------------------------------------------------------------------

def _run_device(device: Any, week: int) -> str:
    """Thread target: optional stagger → run bot → return serial."""
    serial = getattr(device, "serial", str(device))

    # Random start delay so devices don't all act in lockstep from t=0
    stagger = random.uniform(0.0, 30.0)
    logger.info("[%s] Stagger start %.1fs", serial, stagger)
    time.sleep(stagger)

    HumanLikeBot(device, week=week).run()
    return serial


def main() -> None:
    devices = get_devices()
    if not devices:
        logger.error("No devices found. Check BoxPhone/ADB connection.")
        return

    week = 1                                # change to 2/3/4 as account matures
    max_workers = min(len(devices), 8)      # cap threads to avoid resource overload

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {pool.submit(_run_device, d, week): d for d in devices}

        for future in as_completed(futures):
            try:
                serial = future.result()
                logger.info("Finished: %s", serial)
            except Exception as exc:
                logger.error("Thread error: %s", exc)


if __name__ == "__main__":
    main()
