from bingo.lines import (
    LINES,
    bingo_count,
    cells_in_completed_lines,
    completed_lines,
    opened_cells,
)
from bingo.sheet import FREE_POS


def test_exactly_12_lines_of_5():
    assert len(LINES) == 12
    assert all(len(line) == 5 for line in LINES)
    assert len(set(LINES)) == 12


def test_free_is_always_opened():
    assert FREE_POS in opened_cells([])
    assert bingo_count([]) == 0


def test_middle_row_col_diagonals_need_only_4():
    assert bingo_count([10, 11, 13, 14]) == 1  # 3行目
    assert bingo_count([2, 7, 17, 22]) == 1  # 3列目
    assert bingo_count([0, 6, 18, 24]) == 1  # 斜め
    assert bingo_count([4, 8, 16, 20]) == 1  # 逆斜め


def test_corner_lines_need_5():
    assert bingo_count([0, 1, 2, 3]) == 0
    assert bingo_count([0, 1, 2, 3, 4]) == 1


def test_one_cell_can_complete_two_lines():
    # 斜め(0,6,12,18,24)は成立済み。1行目は 4 だけ残っている。
    opened = [0, 1, 2, 3, 6, 18, 24]
    assert bingo_count(opened) == 1
    assert bingo_count(opened + [4]) == 2


def test_undo_reduces_count():
    opened = {10: "a", 11: "b", 13: "c", 14: "d"}
    assert bingo_count(opened) == 1
    del opened[11]
    assert bingo_count(opened) == 0


def test_full_board_is_12():
    assert bingo_count([i for i in range(25) if i != FREE_POS]) == 12


def test_cells_in_completed_lines():
    assert cells_in_completed_lines([]) == frozenset()
    assert cells_in_completed_lines([10, 11, 13, 14]) == frozenset({10, 11, 12, 13, 14})
    assert completed_lines([10, 11, 13, 14]) == [(10, 11, 12, 13, 14)]
