from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

import requests

from tools._shared import TIMEOUT, err


OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

# Unit labels for display
UNIT_LABELS: dict[str, dict[str, str]] = {
    "metric": {"temp": "°C", "wind": "m/s"},
    "imperial": {"temp": "°F", "wind": "mph"},
    "standard": {"temp": "K", "wind": "m/s"},
}


def get_weather(
    city: str = "",
    units: str = "metric",
    lang: str = "vi",
) -> dict[str, Any]:
    """
    Lấy thông tin thời tiết hiện tại theo tên thành phố.

    Args:
        city: Tên thành phố (ví dụ: "Hanoi", "Ho Chi Minh City", "Tokyo").
        units: Đơn vị nhiệt độ — 'metric' (Celsius), 'imperial' (Fahrenheit),
               'standard' (Kelvin). Mặc định: metric.
        lang: Mã ngôn ngữ cho mô tả thời tiết (vi, en, ja, ko, zh_cn...).

    Returns:
        dict với thông tin thời tiết đầy đủ gồm nhiệt độ, độ ẩm, gió, trạng thái.
    """
    try:
        if not city or not city.strip():
            return {
                "tool": "weather",
                "error": "missing_city",
                "message": "Vui lòng cung cấp tên thành phố.",
            }

        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "Missing OPENWEATHER_API_KEY env var. "
                "Get a free key at https://openweathermap.org/api"
            )

        units = units if units in {"metric", "imperial", "standard"} else "metric"
        labels = UNIT_LABELS[units]

        response = requests.get(
            OPENWEATHER_BASE_URL,
            params={
                "q": city.strip(),
                "appid": api_key,
                "units": units,
                "lang": lang or "vi",
            },
            timeout=TIMEOUT,
        )

        if response.status_code == 404:
            return {
                "tool": "weather",
                "error": "city_not_found",
                "message": f"Không tìm thấy thành phố: '{city}'. Thử tên tiếng Anh hoặc tên chính xác hơn.",
            }
        response.raise_for_status()

        data = response.json()
        main = data.get("main", {})
        wind = data.get("wind", {})
        weather_list = data.get("weather", [{}])
        weather_info = weather_list[0] if weather_list else {}
        sys_info = data.get("sys", {})
        clouds = data.get("clouds", {})

        # Convert unix timestamp to readable datetime
        ts = data.get("dt")
        dt_str = datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M UTC") if ts else None

        return {
            "tool": "weather",
            "city": data.get("name", city),
            "country": sys_info.get("country", ""),
            "datetime": dt_str,
            "temperature": f"{main.get('temp')}{labels['temp']}",
            "feels_like": f"{main.get('feels_like')}{labels['temp']}",
            "temp_min": f"{main.get('temp_min')}{labels['temp']}",
            "temp_max": f"{main.get('temp_max')}{labels['temp']}",
            "condition": weather_info.get("main", ""),
            "description": weather_info.get("description", ""),
            "humidity": f"{main.get('humidity')}%",
            "pressure": f"{main.get('pressure')} hPa",
            "wind_speed": f"{wind.get('speed')} {labels['wind']}",
            "wind_direction": wind.get("deg"),
            "cloudiness": f"{clouds.get('all', 0)}%",
            "visibility": f"{data.get('visibility', 0) // 1000} km" if data.get("visibility") else None,
            "units": units,
            "lang": lang,
            "source": "openweathermap.org",
        }
    except Exception as exc:
        return err("weather", exc)
