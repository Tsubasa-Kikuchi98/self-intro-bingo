"""URLクエリパラメータとの相互変換。Streamlit には依存しない純関数。

- ``s``: シード（整数）
- ``o``: 開いたマス。``[[pos, name], ...]`` の JSON を base64url（パディングなし）にしたもの
"""

from __future__ import annotations

import base64
import json
import re

from .sheet import CELL_COUNT, FREE_POS, SEED_MAX

Opened = dict[int, str]

_HONORIFICS = ("さん", "くん", "君", "ちゃん", "氏")
_WS = re.compile(r"\s+")  # 全角スペースも \s に含まれる


def encode_opened(opened: Opened) -> str:
    pairs = [[pos, opened[pos]] for pos in sorted(opened)]
    raw = json.dumps(pairs, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_opened(value: str | None) -> Opened:
    """``o`` を復元する。壊れていても例外を出さず、正しい要素だけを返す。"""
    if not value:
        return {}
    try:
        padded = value + "=" * (-len(value) % 4)
        data = json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))
    except Exception:
        return {}
    if not isinstance(data, list):
        return {}
    result: Opened = {}
    for item in data:
        if not (isinstance(item, list) and len(item) == 2):
            continue
        pos, name = item
        if isinstance(pos, bool) or not isinstance(pos, int):
            continue
        if not (0 <= pos < CELL_COUNT) or pos == FREE_POS:
            continue
        if not isinstance(name, str):
            continue
        name = clean_name(name)
        if not name:
            continue
        result[pos] = name
    return result


def parse_seed(value: str | None) -> int | None:
    """``s`` を整数にする。不正なら None（呼び出し側で再生成する）。"""
    if value is None:
        return None
    value = value.strip()
    if not value.isdigit():
        return None
    seed = int(value)
    if seed > SEED_MAX:
        return None
    return seed


def clean_name(name: str) -> str:
    """保存用の名前。前後の空白を落とし、連続する空白を1つにする。"""
    return _WS.sub(" ", name).strip()


def normalize_name(name: str) -> str:
    """同一人物かの比較用。空白をすべて除き、末尾の敬称を落とし、英字は小文字にする。"""
    n = _WS.sub("", name)
    for suffix in _HONORIFICS:
        if len(n) > len(suffix) and n.endswith(suffix):
            n = n[: -len(suffix)]
            break
    return n.casefold()


def same_person_positions(opened: Opened, name: str, exclude: int | None = None) -> list[int]:
    """すでに同じ人の名前が記録されているマスの位置を返す。"""
    key = normalize_name(name)
    if not key:
        return []
    return sorted(
        pos
        for pos, existing in opened.items()
        if pos != exclude and normalize_name(existing) == key
    )
