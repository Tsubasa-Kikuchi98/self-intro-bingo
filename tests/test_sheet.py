import pytest

from bingo.sheet import (
    CELL_COUNT,
    FREE_POS,
    QUESTION_CELLS,
    SEED_MAX,
    generate_sheet,
    new_seed,
)
from tests.conftest import make_questions


def test_sheet_has_25_cells_with_free_center(questions):
    sheet = generate_sheet(questions, seed=1)
    assert len(sheet) == CELL_COUNT
    assert sheet[FREE_POS] is None
    assert all(sheet[i] is not None for i in range(CELL_COUNT) if i != FREE_POS)


def test_24_unique_questions(questions):
    sheet = generate_sheet(questions, seed=42)
    ids = [q.id for q in sheet if q is not None]
    assert len(ids) == QUESTION_CELLS
    assert len(set(ids)) == QUESTION_CELLS


def test_same_seed_same_sheet(questions):
    assert generate_sheet(questions, 12345) == generate_sheet(questions, 12345)


@pytest.mark.parametrize("a,b", [(1, 2), (0, 1), (100, 101), (2**31 - 1, 2**31 - 2)])
def test_different_seeds_differ(questions, a, b):
    assert generate_sheet(questions, a) != generate_sheet(questions, b)


def test_independent_of_csv_row_order(questions):
    shuffled = list(reversed(questions))
    assert generate_sheet(shuffled, 7) == generate_sheet(questions, 7)


def test_too_few_questions_raises():
    with pytest.raises(ValueError):
        generate_sheet(make_questions(QUESTION_CELLS - 1), 1)


def test_new_seed_in_range():
    for _ in range(100):
        assert 0 <= new_seed() <= SEED_MAX
