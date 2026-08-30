"""
查询指定城市天气（基于 Open-Meteo 免费 API）
"""

import sys
import time
from functools import wraps

import requests

# 自定义请求头，标识客户端
HEADERS = {
    "User-Agent": "weather-demo/1.0 (learning script)",
    "Accept": "application/json",
}

# Open-Meteo WMO 天气代码映射
WEATHER_CODES = {
    0: "晴朗",
    1: "大部晴朗",
    2: "多云",
    3: "阴天",
    45: "有雾",
    48: "雾凇",
    51: "小毛毛雨",
    53: "毛毛雨",
    55: "大毛毛雨",
    56: "冻毛毛雨",
    57: "强冻毛毛雨",
    61: "小雨",
    63: "中雨",
    65: "大雨",
    66: "冻雨",
    67: "强冻雨",
    71: "小雪",
    73: "中雪",
    75: "大雪",
    77: "雪粒",
    80: "小阵雨",
    81: "阵雨",
    82: "强阵雨",
    85: "小阵雪",
    86: "大阵雪",
    95: "雷暴",
    96: "雷暴伴小冰雹",
    99: "雷暴伴大冰雹",
}


def retry(max_attempts=3, delay=1, exceptions=(Exception,)):
    """
    装饰器：当函数抛出指定异常时自动重试。
    :param max_attempts: 最大尝试次数（含首次）
    :param delay: 每次重试间隔（秒）
    :param exceptions: 需要重试的异常类型元组
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        print(f"第 {attempt} 次请求失败，{delay}秒后重试... 错误：{e}")
                        time.sleep(delay)
                    else:
                        print(f"达到最大重试次数 {max_attempts}，最终失败。")
            raise last_exception

        return wrapper

    return decorator


@retry(max_attempts=3, delay=2, exceptions=(requests.exceptions.RequestException,))
def get_coordinates(city: str):
    """通过 Open-Meteo Geocoding API 获取城市经纬度"""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "zh", "format": "json"}
    # 演示：GET 请求 + params + headers + timeout
    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    results = data.get("results")
    if not results:
        print(f"未找到城市：{city}")
        sys.exit(1)
    location = results[0]
    return (
        location["name"],
        location["latitude"],
        location["longitude"],
        location.get("country", ""),
    )


@retry(max_attempts=3, delay=2, exceptions=(requests.exceptions.RequestException,))
def get_weather(lat: float, lon: float):
    """通过 Open-Meteo Forecast API 获取当前天气和今日气温"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
        "forecast_days": 1,
    }

    resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_weather_by_city(city: str) -> dict:
    """
    查询指定城市的实时天气和今日最高/最低温度。
    返回字典包含以下字段：
        city_name, country, latitude, longitude,
        weather_text, temperature, max_temp, min_temp,
        humidity, wind_speed
    若查询失败，抛出异常（requests.RequestException, ValueError 等）。
    """
    city_name, lat, lon, country = get_coordinates(city)
    data = get_weather(lat, lon)

    current = data.get("current") or {}
    daily = data.get("daily") or {}

    temp = current.get("temperature_2m")
    humidity = current.get("relative_humidity_2m")
    wind_speed = current.get("wind_speed_10m")
    weather_code = current.get("weather_code")
    weather_text = WEATHER_CODES.get(weather_code, f"未知代码({weather_code})")

    max_temp = daily.get("temperature_2m_max", [None])[0]
    min_temp = daily.get("temperature_2m_min", [None])[0]

    return {
        "city_name": city_name,
        "country": country,
        "latitude": lat,
        "longitude": lon,
        "weather_text": weather_text,
        "temperature": temp,
        "max_temp": max_temp,
        "min_temp": min_temp,
        "humidity": humidity,
        "wind_speed": wind_speed,
    }


# def main():
#     print("argv:", sys.argv)
#     if len(sys.argv) < 2:
#         city = input("请输入城市名（中英文均可）：").strip()
#         if not city:
#             print("城市名不能为空")
#             sys.exit(1)
#     else:
#         city = sys.argv[1]

#     print(f"正在查询 {city} 的天气...")

#     try:
#         info = get_weather_by_city(city)
#         # 打印信息，使用 info 字典中的字段
#         print("\n" + "=" * 40)
#         print(f"城市：{info['city_name']}（{info['country']}）")
#         print(f"经纬度：{info['latitude']:.4f}, {info['longitude']:.4f}")
#         print(f"天气：{info['weather_text']}")
#         print(f"当前温度：{info['temperature']}°C")
#         print(f"今日最高/最低：{info['max_temp']}°C / {info['min_temp']}°C")
#         print(f"相对湿度：{info['humidity']}%")
#         print(f"风速：{info['wind_speed']} km/h")
#         print("=" * 40)
#     except (
#         requests.exceptions.RequestException,
#         json.JSONDecodeError,
#         ValueError,
#     ) as e:
#         # 这里可以针对不同异常输出更友好的提示，但为了简洁，统一捕获
#         print(f"查询失败：{e}")
#         sys.exit(1)


# if __name__ == "__main__":
#     main()
