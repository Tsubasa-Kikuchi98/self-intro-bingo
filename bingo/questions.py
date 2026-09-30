"""questions.csv の読み込みと検証。"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REQUIRED_COLUMNS = ("id", "category", "question", "label")
MIN_QUESTIONS = 24
MAX_LABEL_LEN = 8


class QuestionDataError(ValueError):
    """questions.csv の内容に問題があるときに送出する。"""


@dataclass(frozen=True)
class Question:
    id: int
    category: str
    question: str
    label: str


def load_questions(path: str | Path) -> list[Question]:
    """CSVを読み込み、検証したうえで id 昇順のリストを返す。

    - Excelで保存したBOM付きUTF-8も読めるよう utf-8-sig で開く。
    - 行順に依存しないよう id でソートして返す（シート生成の再現性のため）。
    """
    path = Path(path)
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames or []
        missing = [c for c in REQUIRED_COLUMNS if c not in header]
        if missing:
            raise QuestionDataError(f"CSVに必要な列がありません: {', '.join(missing)}")
        rows = list(reader)
    return validate_questions(_rows_to_questions(rows))


def _rows_to_questions(rows: Iterable[dict[str, str | None]]) -> list[Question]:
    questions: list[Question] = []
    for line_no, row in enumerate(rows, start=2):  # 1行目はヘッダ
        raw_id = (row.get("id") or "").strip()
        try:
            qid = int(raw_id)
        except ValueError:
            raise QuestionDataError(f"{line_no}行目: id が整数ではありません: {raw_id!r}") from None
        questions.append(
            Question(
                id=qid,
                category=(row.get("category") or "").strip(),
                question=(row.get("question") or "").strip(),
                label=(row.get("label") or "").strip(),
            )
        )
    return questions


def validate_questions(questions: list[Question]) -> list[Question]:
    """重複ID・空欄・ラベル長・問題数を検証し、id 昇順に並べ替えて返す。"""
    seen: dict[int, Question] = {}
    for q in questions:
        if q.id in seen:
            raise QuestionDataError(f"id が重複しています: {q.id}")
        if not q.question.strip():
            raise QuestionDataError(f"id={q.id}: question が空です")
        if not q.label.strip():
            raise QuestionDataError(f"id={q.id}: label が空です")
        if len(q.label) > MAX_LABEL_LEN:
            raise QuestionDataError(
                f"id={q.id}: label が{MAX_LABEL_LEN}文字を超えています: {q.label!r}"
            )
        seen[q.id] = q
    if len(seen) < MIN_QUESTIONS:
        raise QuestionDataError(
            f"問題数が{MIN_QUESTIONS}問未満です（現在 {len(seen)} 問）"
        )
    return [seen[k] for k in sorted(seen)]
