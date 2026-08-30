from .calculator import calculator
from .search_notes import search_notes
from .weather import get_weather_by_city

# 工具注册表：名称 -> 可调用函数
TOOLS = {
    "get_weather_by_city": get_weather_by_city,
    "calculator": calculator,
    "search_notes": search_notes,
}
