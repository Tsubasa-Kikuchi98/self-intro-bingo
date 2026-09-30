import pytest

from bingo.questions import (
    MIN_QUESTIONS,
    Question,
    QuestionDataError,
    load_questions,
    validate_questions,
)
from tests.conftest import ROOT, make_questions


def test_load_actual_csv(questions):
    assert len(questions) >= MIN_QUESTIONS
    assert [q.id for q in questions] == sorted(q.id for q in questions)
    assert all(" or " in q.question for q in questions)


def test_duplicate_id_raises():
    qs = make_questions(30)
    qs.append(Question(id=1, category="c", question="dup", label="dup"))
    with pytest.raises(QuestionDataError, match="重複"):
        validate_questions(qs)


def test_too_few_questions_raises():
    with pytest.raises(QuestionDataError, match="24問未満"):
        validate_questions(make_questions(MIN_QUESTIONS - 1))


def test_exactly_min_questions_ok():
    assert len(validate_questions(make_questions(MIN_QUESTIONS))) == MIN_QUESTIONS


def test_empty_label_raises():
    qs = make_questions(30)
    qs[0] = Question(id=1, category="c", question="q", label="  ")
    with pytest.raises(QuestionDataError, match="label が空"):
        validate_questions(qs)


def test_long_label_raises():
    qs = make_questions(30)
    qs[0] = Question(id=1, category="c", question="q", label="あいうえおかきくけ")
    with pytest.raises(QuestionDataError, match="8文字"):
        validate_questions(qs)


def test_result_sorted_by_id_regardless_of_input_order():
    qs = list(reversed(make_questions(30)))
    assert [q.id for q in validate_questions(qs)] == list(range(1, 31))


def test_csv_with_bom_and_crlf(tmp_path):
    src = (ROOT / "data" / "questions.csv").read_text(encoding="utf-8")
    p = tmp_path / "q.csv"
    p.write_bytes(b"\xef\xbb\xbf" + src.replace("\n", "\r\n").encode("utf-8"))
    assert len(load_questions(p)) == len(load_questions(ROOT / "data" / "questions.csv"))


def test_csv_missing_column(tmp_path):
    p = tmp_path / "q.csv"
    p.write_text("id,question\n1,a or b\n", encoding="utf-8")
    with pytest.raises(QuestionDataError, match="列がありません"):
        load_questions(p)


def test_csv_non_integer_id(tmp_path):
    p = tmp_path / "q.csv"
    p.write_text("id,category,question,label\nx,c,a or b,l\n", encoding="utf-8")
    with pytest.raises(QuestionDataError, match="整数"):
        load_questions(p)
