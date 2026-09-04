"""
工具包：注册 3 个工具并统一导出注册表接口。

所有工具经 spec.ToolRegistry 统一管理：
- registry.call(name, kwargs) 完成参数校验 + 执行 + 异常兜底（绝不崩溃）
- registry.describe_all() 动态生成模型可用的工具描述
"""

from .calculator import calculator
from .search_notes import search_notes
from .spec import ToolRegistry, ToolSpec, registry
from .weather import get_weather_by_city

# 工具注册表：名称 -> 带元数据（描述、参数要求）的 ToolSpec
registry.register(
    ToolSpec(
        name="get_weather_by_city",
        func=get_weather_by_city,
        description="查询指定城市的实时天气",
        parameters={"city": {"required": True, "type": "string"}},
    )
)
registry.register(
    ToolSpec(
        name="calculator",
        func=calculator,
        description="计算四则运算表达式，如 '1 + 2 * 3'",
        parameters={"expression": {"required": True, "type": "string"}},
    )
)
registry.register(
    ToolSpec(
        name="search_notes",
        func=search_notes,
        description="在本地笔记中搜索匹配关键词的内容",
        parameters={
            "keyword": {"required": True, "type": "string"},
            "top_k": {"required": False, "type": int},
        },
    )
)

# 兼容入口：名称 -> 函数
TOOLS = registry.to_funcs()

__all__ = ["registry", "ToolRegistry", "ToolSpec", "TOOLS"]
