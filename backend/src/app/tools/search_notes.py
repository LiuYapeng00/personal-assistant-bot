"""在本地 notes 目录中按关键词搜索 md 笔记（按文件名与内容匹配）。"""

from pathlib import Path

# 搜索根目录：backend/notes
# __file__ = backend/src/app/tools/search_notes.py，向上回溯到 backend 根
NOTES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "notes"


def _match(needle: str, haystack: str) -> bool:
    return needle.lower() in (haystack or "").lower()


def search_notes(keyword: str, top_k: int = 5) -> dict:
    """
    在 notes/ 目录中搜索包含关键词的 md 笔记。
    :param keyword: 搜索关键词
    :param top_k: 最多返回的命中条数
    :return: {"count": n, "results": [{"file": "...", "match": "..."}], "note": "说明"}
    """
    keyword = (keyword or "").strip()
    if not keyword:
        return {"count": 0, "results": [], "note": "关键词为空"}

    if not NOTES_DIR.is_dir():
        return {"count": 0, "results": [], "note": f"笔记目录不存在：{NOTES_DIR}"}

    hits = []
    for path in sorted(NOTES_DIR.rglob("*.md")):
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        matched_line = ""
        if _match(keyword, path.name):
            matched_line = "（文件名匹配）"
        else:
            for line in content.splitlines():
                if _match(keyword, line):
                    matched_line = line.strip()[:80]
                    break

        if matched_line:
            hits.append({"file": str(path.relative_to(NOTES_DIR)), "match": matched_line})
            if len(hits) >= top_k:
                break

    return {
        "count": len(hits),
        "results": hits,
        "note": "已搜索到匹配内容" if hits else "没有找到相关笔记",
    }
