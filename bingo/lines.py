"""ビンゴ判定。"""

from __future__ import annotations

from typing import Iterable

from .sheet import FREE_POS, SIZE

Line = tuple[int, ...]


def _build_lines() -> tuple[Line, ...]:
    rows = [tuple(r * SIZE + c for c in range(SIZE)) for r in range(SIZE)]
    cols = [tuple(r * SIZE + c for r in range(SIZE)) for c in range(SIZE)]
    diag1 = tuple(i * SIZE + i for i in range(SIZE))
    diag2 = tuple(i * SIZE + (SIZE - 1 - i) for i in range(SIZE))
    return tuple(rows + cols + [diag1, diag2])


LINES: tuple[Line, ...] = _build_lines()  # 縦5・横5・斜め2の計12本


def opened_cells(opened: Iterable[int]) -> frozenset[int]:
    """開いたマスの集合。FREE を常に含める。"""
    return frozenset(opened) | {FREE_POS}


def completed_lines(opened: Iterable[int]) -> list[Line]:
    cells = opened_cells(opened)
    return [line for line in LINES if all(p in cells for p in line)]


def bingo_count(opened: Iterable[int]) -> int:
    return len(completed_lines(opened))


def cells_in_completed_lines(opened: Iterable[int]) -> frozenset[int]:
    """成立したラインに含まれるマス（強調表示用）。"""
    result: set[int] = set()
    for line in completed_lines(opened):
        result.update(line)
    return frozenset(result)
