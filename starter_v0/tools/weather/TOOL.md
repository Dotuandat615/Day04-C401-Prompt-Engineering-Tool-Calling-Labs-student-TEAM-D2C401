---
name: weather
track: bonus
kind: live_api
provider: OpenWeatherMap (free tier)
requires_env: [OPENWEATHER_API_KEY]
inputs: [city, units, lang]
outputs: [tool, city, country, temperature, feels_like, condition, description, humidity, wind_speed, visibility, datetime]
side_effect: false
---
# weather

Lấy thông tin thời tiết hiện tại theo tên thành phố.

Sử dụng **OpenWeatherMap Current Weather API** (free tier, không giới hạn số thành phố,
2.5M calls/tháng miễn phí).

Đăng ký key miễn phí tại: https://openweathermap.org/api

`units`:
- `metric` → nhiệt độ Celsius (mặc định)
- `imperial` → Fahrenheit
- `standard` → Kelvin

`lang`: mã ngôn ngữ cho mô tả thời tiết (vi, en, ja, ko...). Mặc định: vi.
