"""
工具注册表与参数校验。

注册表把"工具名称 -> 可调用函数"升级为带元数据的 ToolSpec：
- 每个工具声明参数要求（必填 / 类型）
- 通过 call() 统一完成：查表 -> 参数校验 -> 执行 -> 异常兜底
- 任何错误（未知工具、缺参、多余参、类型错、工具内部异常）都转为可回传给模型的文本，
  保证 ReAct 循环绝不因工具调用而崩溃。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


def _type_name(t: Any) -> str:
    """把类型注解转成可读名（如 int -> 'int'，'string' 兼容别名）。"""
    if isinstance(t, str):
        return t.lower()
    if hasattr(t, "__name__"):
        return t.__name__.lower()
    return str(t).lower()


@dataclass
class ToolSpec:
    """单个工具的元数据：函数 + 说明 + 参数要求。"""

    name: str
    func: Callable
    description: str
    parameters: dict[str, dict] = field(default_factory=dict)
    # parameters 结构：{字段名: {"required": bool, "type": <类型或类型名字符串>}}
    # 未列出但传进来的参数视为允许透传（工具自行忽略）。

    def validate(self, kwargs: dict) -> list[str]:
        """校验参数，返回错误信息列表；无错误返回空列表。"""
        errors: list[str] = []
        passed = set(kwargs)
        for name, rule in self.parameters.items():
            constr = rule or {}
            required = constr.get("required", False)
            expected = constr.get("type")

            if name not in passed:
                if required:
                    errors.append(f"缺少必填参数: {name}")
                continue

            value = kwargs[name]
            if value is None and not required:
                continue
            if expected is not None:
                # 字符串兼容：'string' 表示 str
                if isinstance(expected, str):
                    if expected == "string" and not isinstance(value, str):
                        errors.append(
                            f"参数 {name} 类型错误: 期望 string，得到 {type(value).__name__}"
                        )
                elif not isinstance(value, expected):
                    errors.append(
                        f"参数 {name} 类型错误: 期望 {_type_name(expected)}，"
                        f"得到 {type(value).__name__}"
                    )
        return errors

    def call(self, kwargs: dict) -> str:
        """校验并调用工具，任何异常都转为可回传文本（不抛出）。"""
        if not isinstance(kwargs, dict):
            return f"工具 {self.name} 参数必须是对象，得到 {type(kwargs).__name__}"

        errors = self.validate(kwargs)
        if errors:
            return f"工具 {self.name} 参数错误: {'; '.join(errors)}"

        try:
            result = self.func(**kwargs)
            return str(result)
        except Exception as e:  # noqa: BLE001 - 工具异常统一转为 Observation
            return f"工具 {self.name} 执行失败: {e}"


class ToolRegistry:
    """工具注册表：集中管理名称 -> ToolSpec，并提供带校验与容错的调用入口。"""

    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}

    def register(self, spec: ToolSpec) -> ToolSpec:
        self._tools[spec.name] = spec
        return spec

    def __call__(self, name: str, description: str, parameters: dict | None = None):
        """装饰器用法：@registry.register('name', 'desc', {...})"""
        parameters = parameters or {}

        def decorator(func: Callable) -> Callable:
            spec = ToolSpec(
                name=name,
                func=func,
                description=description,
                parameters=parameters,
            )
            self._tools[name] = spec
            return func

        return decorator

    def get(self, name: str) -> ToolSpec | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools)

    def to_funcs(self) -> dict[str, Callable]:
        """返回 名称 -> 原始函数 的字典（兼容简单调用场景）。"""
        return {name: spec.func for name, spec in self._tools.items()}

    def call(self, name: str, kwargs: dict) -> str:
        """按名称查表并调用；未知工具也返回友好文本，绝不抛异常。"""
        spec = self._tools.get(name)
        if spec is None:
            return f"未知工具，可用工具: {', '.join(self.names())}"
        return spec.call(kwargs)

    def describe_all(self) -> str:
        """生成供 SYSTEM_PROMPT 使用的工具列表描述。"""
        lines = []
        for spec in self._tools.values():
            params = []
            for pname, rule in spec.parameters.items():
                constr = rule or {}
                required = constr.get("required", False)
                params.append(f"{pname}{'' if required else '?'}")
            lines.append(f"- {spec.name}: {spec.description}，参数 {{{', '.join(params)}}}")
        return "\n".join(lines)


# 默认全局注册表（供实际运行使用）
registry = ToolRegistry()
