from pathlib import Path

import pytest

from bingo.questions import Question, load_questions

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="session")
def questions() -> list[Question]:
    return load_questions(ROOT / "data" / "questions.csv")


def make_questions(n: int) -> list[Question]:
    return [
        Question(id=i, category="c", question=f"Q{i} or R{i}", label=f"L{i}")
        for i in range(1, n + 1)
    ]
