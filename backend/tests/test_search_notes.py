"""search_notes 工具测试 —— 命中、无命中、目录不存在。"""

import sys
from pathlib import Path

import pytest

import app.tools.search_notes  # noqa: F401 - 触发模块加载，供下方 sys.modules 取用

# 通过 sys.modules 取真正的模块，避免被 tools 包中同名函数导出遮蔽
sn = sys.modules["app.tools.search_notes"]


def _write(tmp_path: Path, files: dict[str, str]):
    for rel, content in files.items():
        p = tmp_path / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")


def test_hit_by_filename(tmp_path, monkeypatch):
    _write(tmp_path, {"北京天气.md": "# 北京天气\n今天晴朗。\n"})
    monkeypatch.setattr(sn, "NOTES_DIR", tmp_path)
    result = sn.search_notes("天气")
    assert result["count"] == 1
    assert result["results"][0]["file"] == "北京天气.md"
    assert "文件名匹配" in result["results"][0]["match"]


def test_hit_by_content(tmp_path, monkeypatch):
    _write(tmp_path, {"notes.md": "# 会议记录\n讨论了项目排期和加班安排。\n"})
    monkeypatch.setattr(sn, "NOTES_DIR", tmp_path)
    result = sn.search_notes("加班")
    assert result["count"] == 1
    assert "加班" in result["results"][0]["match"]


def test_no_hit(tmp_path, monkeypatch):
    _write(tmp_path, {"a.md": "内容没有任何关键词。\n"})
    monkeypatch.setattr(sn, "NOTES_DIR", tmp_path)
    result = sn.search_notes("不存在的词")
    assert result["count"] == 0
    assert result["results"] == []
    assert "没有找到" in result["note"]


def test_dir_not_exist(tmp_path, monkeypatch):
    missing = tmp_path / "nope"
    monkeypatch.setattr(sn, "NOTES_DIR", missing)
    result = sn.search_notes("任何词")
    assert result["count"] == 0
    assert "目录不存在" in result["note"]


def test_empty_keyword(tmp_path, monkeypatch):
    monkeypatch.setattr(sn, "NOTES_DIR", tmp_path)
    result = sn.search_notes("   ")
    assert result["count"] == 0
    assert "关键词为空" in result["note"]


def test_real_notes_dir_available():
    """仓库内置的示例笔记目录应能被真实命中，保证端到端可演示。"""
    result = sn.search_notes("待办")
    assert result["count"] >= 1
    assert any("待办" in r["file"] for r in result["results"])


@pytest.mark.parametrize(
    "expression",
    ["__import__('os').system('x')", "1/0", "1 +", "abc + 2"],
)
def test_calculator_error_becomes_observation_text(expression):
    """calculator 的错误经注册表 call() 后必须是文本，而不是抛异常。"""
    from app.tools import registry

    result = registry.call("calculator", {"expression": expression})
    assert isinstance(result, str)
    assert result  # 非空
