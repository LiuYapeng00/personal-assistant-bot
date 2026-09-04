"""
Demo：方式二 —— 用装饰器注册工具（仅演示写法，不影响项目运行）。

对照 spec.py 中 ToolRegistry.__call__ 的装饰器用法（即 @demo_registry(...)，而非 register 方法）。
注意：这里用的是独立新建的 demo_registry，而不是项目全局 registry，
避免演示工具污染真实可用的工具集。
"""

import datetime

from app.tools.spec import ToolRegistry

demo_registry = ToolRegistry()


@demo_registry(
    "get_time",
    "返回当前日期时间",
    {"format": {"required": False, "type": "string"}},
)
def get_time(format: str = "YYYY-MM-DD HH:MM:SS") -> str:  # noqa: A002
    """返回当前时间，format 支持 'date' / 'time' / 其余默认完整格式。"""
    now = datetime.datetime.now()
    if format == "date":
        return now.strftime("%Y-%m-%d")
    if format == "time":
        return now.strftime("%H:%M:%S")
    return now.strftime("%Y-%m-%d %H:%M:%S")


@demo_registry(
    "echo",
    "原样返回你传入的文本",
    {"text": {"required": True, "type": "string"}},
)
def echo(text: str) -> str:
    return text


if __name__ == "__main__":
    print("可用工具:", demo_registry.names())
    print("describe_all:")
    print(demo_registry.describe_all())
    print("-" * 40)
    print("call get_time:", demo_registry.call("get_time", {}))
    print("call get_time(date):", demo_registry.call("get_time", {"format": "date"}))
    print("call echo:", demo_registry.call("echo", {"text": "你好"}))
    print("缺参兜底:", demo_registry.call("echo", {}))
    print("未知工具兜底:", demo_registry.call("nope", {}))
