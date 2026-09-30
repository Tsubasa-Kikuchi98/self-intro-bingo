import base64
import json

import pytest

from bingo.state import (
    clean_name,
    decode_opened,
    encode_opened,
    normalize_name,
    parse_seed,
    same_person_positions,
)

B64URL_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_")


def _b64(obj) -> str:
    raw = json.dumps(obj, ensure_ascii=False).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")


@pytest.mark.parametrize(
    "opened",
    [
        {},
        {0: "田中"},
        {0: "田中", 24: "山田 太郎", 5: "Émile", 7: "😀", 3: 'a,"b"/c+d=e&f?g'},
    ],
)
def test_roundtrip(opened):
    encoded = encode_opened(opened)
    assert set(encoded) <= B64URL_CHARS
    assert decode_opened(encoded) == opened


def test_encoding_is_deterministic():
    assert encode_opened({3: "a", 1: "b"}) == encode_opened({1: "b", 3: "a"})


@pytest.mark.parametrize(
    "value",
    [None, "", "!!!", "not-base64", _b64({"a": 1}), _b64("str"), _b64(123)],
)
def test_invalid_returns_empty(value):
    assert decode_opened(value) == {}


def test_partially_invalid_keeps_valid_entries():
    data = [
        [0, "ok"],
        [12, "free"],  # FREE は捨てる
        [25, "range"],  # 範囲外
        [-1, "neg"],
        [1, 5],  # 名前が文字列でない
        [2, "   "],  # 空
        ["3", "x"],  # 位置が文字列
        [True, "bool"],
        [4],
        "junk",
        [5, "  前後空白  "],
    ]
    assert decode_opened(_b64(data)) == {0: "ok", 5: "前後空白"}


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ("", None),
        ("abc", None),
        ("-1", None),
        ("1.5", None),
        ("0", 0),
        (" 42 ", 42),
        ("2147483647", 2**31 - 1),
        ("2147483648", None),
    ],
)
def test_parse_seed(value, expected):
    assert parse_seed(value) == expected


def test_clean_name():
    assert clean_name("  山田　 太郎 ") == "山田 太郎"


@pytest.mark.parametrize(
    "a,b",
    [
        ("田中", "田中さん"),
        ("田中", "田中 "),
        ("Sato", "sato"),
        ("山田 太郎", "山田太郎"),
        ("鈴木くん", "鈴木ちゃん"),
    ],
)
def test_normalize_name_equal(a, b):
    assert normalize_name(a) == normalize_name(b)


def test_normalize_name_keeps_short_names():
    assert normalize_name("さん") == "さん"
    assert normalize_name("田中") != normalize_name("田村")


def test_same_person_positions():
    opened = {0: "田中", 5: "田中さん", 7: "佐藤"}
    assert same_person_positions(opened, "たなか") == []
    assert same_person_positions(opened, "田中") == [0, 5]
    assert same_person_positions(opened, "田中", exclude=5) == [0]
    assert same_person_positions(opened, "  ") == []
