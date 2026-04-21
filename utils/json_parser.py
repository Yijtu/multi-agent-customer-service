"""JSON 解析辅助工具。

LLM 返回的 JSON 经常被 Markdown 代码块包裹，或混有前后说明文字。
本模块提供容错的解析函数，避免主流程因格式问题崩溃。
"""

import json


def safe_parse_json(text: str, default: dict | None = None) -> dict:
    """安全地解析 LLM 返回的 JSON 文本。

    Args:
        text: LLM 返回的原始字符串。
        default: 解析失败时的兜底值。传入 None 时使用空字典 {}。

    Returns:
        解析后的字典；解析失败则返回 default。

    处理的边界情况:
        - Markdown 代码块: ```json ... ``` 或 ``` ... ```
        - 前后的空白字符
        - 非法 JSON 格式
    """
    if default is None:
        default = {}

    content = text.strip()

    # 剥离 Markdown 代码块
    if "```json" in content:
        try:
            content = content.split("```json")[1].split("```")[0]
        except IndexError:
            pass
    elif "```" in content:
        try:
            parts = content.split("```")
            if len(parts) >= 2:
                content = parts[1]
        except IndexError:
            pass

    content = content.strip()

    try:
        return json.loads(content)
    except json.JSONDecodeError as e:
        print(f"   ⚠️ JSON 解析失败: {e}")
        return default
