"""
ui/error_handler.py — Centralized error handling for all tools.

Usage:
    from ui.error_handler import friendly_error, check_env_keys, with_retry

Import này trong tất cả tool.py thay vì try/except riêng lẻ.
"""
from __future__ import annotations

import functools
import os
import time
from typing import Any, Callable


# ── Friendly error message table ────────────────────────────────────────────
ERROR_MESSAGES: dict[str, str] = {
    # Auth errors
    "401": "❌ API key không hợp lệ hoặc hết hạn — kiểm tra lại .env",
    "403": "❌ Không có quyền truy cập — kiểm tra key và subscription",
    # Rate limiting
    "429": "⏳ Quá nhiều request — đợi 30 giây rồi thử lại",
    # Server errors (retryable)
    "500": "🔧 Server lỗi tạm thời — thử lại sau 10 giây",
    "502": "🔧 Bad gateway — API provider đang có vấn đề",
    "503": "🔧 Service không khả dụng — thử lại sau",
    "504": "🔧 Gateway timeout — server không phản hồi kịp",
    # Network issues
    "timeout": "⏱️ Request timeout — kiểm tra kết nối mạng hoặc VPN",
    "connection": "🌐 Không kết nối được — kiểm tra internet",
    # Missing credentials
    "missing_key": "🔑 Thiếu API key trong .env — xem TOOL-SETUP.md",
}

# Retryable HTTP status codes
RETRYABLE_CODES = {"429", "500", "502", "503", "504", "timeout"}


def friendly_error(exc: Exception, context: str = "") -> dict[str, Any]:
    """
    Chuyển exception thành dict lỗi thân thiện cho agent đọc và Streamlit hiển thị.

    Args:
        exc: Exception cần xử lý
        context: Tên tool/context để prefix vào message (vd: "timeline", "fetch")

    Returns:
        dict with "error" key and human-friendly message
    """
    msg = str(exc)
    exc_type = type(exc).__name__
    prefix = f"[{context}] " if context else ""

    # HTTP status code matching
    for code, friendly_msg in ERROR_MESSAGES.items():
        if code.isdigit() and code in msg:
            return {"error": prefix + friendly_msg}

    # Network error patterns
    if "timeout" in msg.lower() or "timed out" in msg.lower() or "ReadTimeout" in exc_type:
        return {"error": prefix + ERROR_MESSAGES["timeout"]}

    if any(p in msg.lower() for p in ["connectionerror", "connection refused", "connection reset"]):
        return {"error": prefix + ERROR_MESSAGES["connection"]}

    # Missing environment variable
    if "KeyError" in exc_type or "environ" in msg.lower():
        key_name = msg.strip("'\"")
        return {"error": prefix + f"🔑 Thiếu biến môi trường: {key_name} — thêm vào .env"}

    if "Missing" in msg and ("key" in msg.lower() or "token" in msg.lower()):
        return {"error": prefix + ERROR_MESSAGES["missing_key"]}

    # Fallback: truncated raw error
    return {"error": prefix + f"Lỗi không xác định ({exc_type}): {msg[:300]}"}


def check_env_keys(*keys: str) -> dict[str, Any] | None:
    """
    Kiểm tra các environment key bắt buộc.

    Returns:
        None nếu tất cả key đều có,
        dict {"error": "..."} nếu thiếu key nào đó.
    """
    missing = [k for k in keys if not os.environ.get(k)]
    if missing:
        return {
            "error": (
                f"🔑 Thiếu {len(missing)} key trong .env: {', '.join(missing)}\n"
                f"→ Xem hướng dẫn trong TOOL-SETUP.md"
            )
        }
    return None


def is_retryable_error(result: dict[str, Any]) -> bool:
    """Kiểm tra xem lỗi có thuộc loại có thể retry không."""
    if not isinstance(result, dict) or "error" not in result:
        return False
    err_msg = str(result["error"])
    return any(code in err_msg for code in ["429", "500", "502", "503", "504", "timeout", "⏱️", "🔧", "⏳"])


def with_retry(max_retries: int = 2, delay: float = 3.0):
    """
    Decorator tự động retry khi gặp lỗi tạm thời (429, 500, 502, 503, timeout).
    Dùng exponential backoff: delay * (attempt + 1).

    Usage:
        @with_retry(max_retries=2, delay=3.0)
        def run(query: str) -> dict:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_result: Any = None
            for attempt in range(max_retries + 1):
                result = func(*args, **kwargs)
                last_result = result
                if isinstance(result, dict) and is_retryable_error(result):
                    if attempt < max_retries:
                        wait_time = delay * (attempt + 1)
                        time.sleep(wait_time)
                        continue
                return result
            return last_result
        return wrapper
    return decorator


def safe_tool_call(tool_func: Callable, context: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
    """
    Bọc một tool call trong try/except, trả về friendly_error nếu có ngoại lệ.
    Tiện dụng hơn decorator khi cần gọi tool động.

    Usage:
        result = safe_tool_call(some_func, "timeline", screenname="OpenAI")
    """
    try:
        return tool_func(*args, **kwargs)
    except Exception as exc:
        return friendly_error(exc, context=context)
