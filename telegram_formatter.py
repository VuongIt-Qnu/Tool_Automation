from __future__ import annotations

from datetime import datetime


def fmt_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def format_start(device_name: str, week: int, daily_target: int) -> str:
    return (
        f"📱 Device: {device_name}\n"
        f"🟢 Trạng thái: BẮT ĐẦU CHẠY\n"
        f"📆 Ngày: {fmt_time()}\n"
        f"📦 Tuần: {week}\n"
        f"🎯 Mục tiêu hôm nay: {daily_target} job"
    )


def format_progress(
    device_name: str,
    done_jobs: int,
    total_jobs: int,
    like_ok: int,
    comment_ok: int,
    error_count: int,
) -> str:
    error_rate = (error_count / max(1, (like_ok + comment_ok + error_count))) * 100
    return (
        f"📱 Device: {device_name}\n"
        f"📊 Tiến độ: {done_jobs} / {total_jobs} job\n\n"
        f"👍 Like OK: {like_ok}\n"
        f"💬 Comment OK: {comment_ok}\n"
        f"⚠️ Lỗi: {error_count}\n"
        f"⏱ Error rate: {error_rate:.1f} %"
    )


def format_finish(
    device_name: str,
    week: int,
    target: int,
    like_ok: int,
    comment_ok: int,
    error_count: int,
) -> str:
    return (
        f"📱 Device: {device_name}\n"
        f"✅ Trạng thái: HOÀN THÀNH\n"
        f"📆 Ngày: {fmt_time()}\n"
        f"📦 Tuần: {week}\n"
        f"👍 Like thành công: {like_ok}\n"
        f"💬 Comment thành công: {comment_ok}\n"
        f"⚠️ Lỗi nhẹ: {error_count}\n"
        f"🎯 Target: {target} job"
    )


def format_throttle(
    device_name: str,
    error_rate: float,
    threshold: float,
    factor: float,
) -> str:
    return (
        f"📱 Device: {device_name}\n"
        f"⚠️ Cảnh báo: THROTTLE TỐC ĐỘ\n\n"
        f"❗ Error rate: {error_rate:.1f} % (> {threshold:.1f} %)\n"
        f"🐢 Delay hiện tại: x{factor:.1f}"
    )


def format_error(
    device_name: str,
    action: str,
    detail: str,
    decision: str = "Tiếp tục chạy với throttle",
) -> str:
    return (
        f"📱 Device: {device_name}\n"
        f"⛔ LỖI NGHIÊM TRỌNG\n\n"
        f"❌ Hành động: {action}\n"
        f"📝 Chi tiết: {detail}\n"
        f"🔁 Xử lý: {decision}"
    )
