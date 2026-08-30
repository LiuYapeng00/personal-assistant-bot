"""四则运算计算器：用 ast 安全解析表达式，禁止 eval。"""

import ast
import operator

# 支持的二元运算符映射
_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_NODE_TYPES = (
    ast.Expression,
    ast.BinOp,
    ast.UnaryOp,
    ast.Constant,
    ast.USub,
    ast.UAdd,
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
)


def _check_node(node):
    """递归校验节点类型，确保表达式不含变量、函数调用等。"""
    if not isinstance(node, _ALLOWED_NODE_TYPES):
        raise ValueError(f"不支持的表达式类型：{type(node).__name__}")
    for child in ast.iter_child_nodes(node):
        _check_node(child)


def _eval(node):
    if isinstance(node, ast.Constant):
        val = node.value
        if not isinstance(val, (int, float)):
            raise ValueError(f"只支持数字，收到：{val!r}")
        return val
    if isinstance(node, ast.UnaryOp):
        return _BIN_OPS[type(node.op)](0, _eval(node.operand))
    if isinstance(node, ast.BinOp):
        op = _BIN_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的运算符：{type(node.op).__name__}")
        return op(_eval(node.left), _eval(node.right))
    raise ValueError(f"无法求值：{type(node).__name__}")


def calculator(expression: str) -> str:
    """
    计算四则运算表达式。
    :param expression: 数学表达式字符串，如 "1 + 2 * 3"
    :return: 结果字符串
    :raises: ValueError（非法表达式、除零等）
    """
    expr = (expression or "").strip().replace("×", "*").replace("÷", "/").replace("^", "**")
    if not expr:
        raise ValueError("表达式不能为空")

    try:
        tree = ast.parse(expr, mode="eval")
        _check_node(tree)
        result = _eval(tree.body)
    except ZeroDivisionError:
        raise ValueError("除数不能为零") from None
    except (SyntaxError, ValueError) as e:
        raise ValueError(f"非法表达式：{e}") from None

    if isinstance(result, float) and result.is_integer():
        result = int(result)
    return str(result)
