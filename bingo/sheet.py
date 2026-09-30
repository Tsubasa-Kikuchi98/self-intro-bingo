"""シードからのシート生成。"""

from __future__ import annotations

import random
import secrets

from .questions import Question

SIZE = 5
CELL_COUNT = SIZE * SIZE
FREE_POS = 12  # 3行3列目（row * 5 + col）
QUESTION_CELLS = CELL_COUNT - 1
SEED_MAX = 2**31 - 1  # URLに載せる整数の上限


def new_seed() -> int:
    """暗号学的乱数で新しいシードを作る。"""
    return secrets.randbelow(SEED_MAX + 1)


def generate_sheet(questions: list[Question], seed: int) -> list[Question | None]:
    """25マス分のリストを返す。FREE（12番）は None。

    同じ questions（id 昇順）と同じ seed からは必ず同じ結果になる。
    questions は id 昇順に並べ替えてから使うので、CSVの行順には依存しない。
    """
    ordered = sorted(questions, key=lambda q: q.id)
    if len(ordered) < QUESTION_CELLS:
        raise ValueError(f"問題数が{QUESTION_CELLS}問未満です")
    rng = random.Random(seed)
    picked = rng.sample(ordered, QUESTION_CELLS)  # 重複なし・順序もランダム
    sheet: list[Question | None] = []
    it = iter(picked)
    for pos in range(CELL_COUNT):
        sheet.append(None if pos == FREE_POS else next(it))
    return sheet
