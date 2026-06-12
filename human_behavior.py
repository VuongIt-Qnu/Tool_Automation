# human_behavior.py
from __future__ import annotations

import datetime
import logging
import random
import time
from typing import Any

from config import Config, Coord

logger = logging.getLogger(__name__)


def _adaptive_jitter(button_width: int, button_height: int) -> int:
    """Return click jitter (px) proportional to button area."""
    area = button_width * button_height
    if area < 2_500:   # < 50×50 px
        return 5
    if area < 6_000:   # < ~100×60 px
        return 10
    return 15


class HumanBehavior:
    def __init__(self, device: Any, cfg: Config) -> None:
        self.device = device
        self.cfg = cfg

    # ------------------------------------------------------------------
    # Delays
    # ------------------------------------------------------------------

    def random_delay(self, min_sec: float | None = None, max_sec: float | None = None) -> float:
        """Gaussian delay clamped to [min_sec, max_sec].

        Gaussian gives a natural bell-curve distribution — most delays land
        near the mean, with rare short/long outliers, just like real user timing.
        """
        if min_sec is None:
            min_sec = self.cfg.DELAY_MIN
        if max_sec is None:
            max_sec = self.cfg.DELAY_MAX

        mean = (min_sec + max_sec) / 2
        std_dev = max(0.1, (max_sec - min_sec) / 4)
        delay = random.gauss(mean, std_dev)
        delay = max(min_sec, min(max_sec, delay))
        time.sleep(delay)
        return delay

    def uniform_delay(self, min_sec: float, max_sec: float) -> float:
        """Simple uniform delay for short micro-pauses (trail animation)."""
        delay = random.uniform(min_sec, max_sec)
        time.sleep(delay)
        return delay

    # ------------------------------------------------------------------
    # Click
    # ------------------------------------------------------------------

    def human_click(self, center_x: int, center_y: int, jitter: int) -> Coord:
        """Click with Gaussian offset from center to mimic finger imprecision."""
        click_x = int(center_x + random.gauss(0, jitter))
        click_y = int(center_y + random.gauss(0, jitter))

        # Clamp to screen bounds when device exposes dimensions
        try:
            click_x = max(0, min(self.device.width - 1, click_x))
            click_y = max(0, min(self.device.height - 1, click_y))
        except AttributeError:
            pass

        self.device.click(click_x, click_y)
        logger.debug("click center(%d,%d) → actual(%d,%d)", center_x, center_y, click_x, click_y)
        return click_x, click_y

    def click_with_trail(self, target_x: int, target_y: int, jitter: int) -> Coord:
        """Simulate: move finger to a random position → pause (looking) → tap target."""
        start_x = random.randint(100, 800)
        start_y = random.randint(100, 600)

        try:
            self.device.touch(start_x, start_y)
        except Exception:
            pass  # not all SDK versions expose touch separately

        self.uniform_delay(0.2, 0.6)           # time to "look at" the button
        result = self.human_click(target_x, target_y, jitter)
        self.uniform_delay(0.1, 0.3)           # brief pause after tap
        return result

    def jitter_for_button(self, width: int, height: int) -> int:
        return _adaptive_jitter(width, height)

    # ------------------------------------------------------------------
    # Swipe
    # ------------------------------------------------------------------

    def human_swipe_next_video(self) -> None:
        """Swipe to next video with jittered endpoints and random duration."""
        x1, y1 = self.cfg.NEXT_VIDEO_SWIPE_FROM
        x2, y2 = self.cfg.NEXT_VIDEO_SWIPE_TO

        # Jitter swipe endpoints so x-coordinate is not always identical
        endpoint_jitter = 15
        x1 += random.randint(-endpoint_jitter, endpoint_jitter)
        x2 += random.randint(-endpoint_jitter, endpoint_jitter)

        duration_ms = random.randint(800, 1500)

        try:
            self.device.swipe(x1, y1, x2, y2, duration=duration_ms)
        except TypeError:
            self.device.swipe(x1, y1, x2, y2, duration_ms)
        except Exception:
            try:
                self.device.swipe(x1, y1, x2, y2)
            except Exception:
                logger.warning("Swipe failed – device may not support swipe API")

        self.random_delay(5, 15)    # "watch" the video before acting

    # ------------------------------------------------------------------
    # Schedule guard
    # ------------------------------------------------------------------

    def is_natural_activity_time(self) -> bool:
        hour = datetime.datetime.now().hour
        return self.cfg.ACTIVE_HOUR_START <= hour < self.cfg.ACTIVE_HOUR_END


class RiskMonitor:
    """Track action error rate and return a throttle multiplier when risk is high."""

    def __init__(self, error_threshold: float) -> None:
        self.error_threshold = error_threshold
        self._errors = 0
        self._total = 0

    def record(self, success: bool) -> float:
        """Call after each action. Returns 1.0 (normal) or 2.0 (throttle)."""
        self._total += 1
        if not success:
            self._errors += 1

        # Guard: need at least 5 samples before judging
        if self._total < 5:
            return 1.0

        if self.error_rate > self.error_threshold:
            logger.warning("Error rate %.0f%% exceeds threshold — throttling", self.error_rate * 100)
            return 2.0
        return 1.0

    @property
    def error_rate(self) -> float:
        return self._errors / self._total if self._total else 0.0
