"""仲間さがしビンゴ Streamlit アプリ（画面層）。ロジックは bingo/ にある。"""

from __future__ import annotations

from pathlib import Path
from urllib.parse import urlencode

import streamlit as st

from bingo.lines import bingo_count, cells_in_completed_lines
from bingo.questions import Question, QuestionDataError, load_questions
from bingo.sheet import CELL_COUNT, FREE_POS, SIZE, generate_sheet, new_seed
from bingo.state import (
    Opened,
    clean_name,
    decode_opened,
    encode_opened,
    parse_seed,
    same_person_positions,
)

DATA_PATH = Path(__file__).parent / "data" / "questions.csv"
NAME_MAX_CHARS = 20
CELL_NAME_MAX_CHARS = 4  # マス内に表示する名前の最大文字数

st.set_page_config(
    page_title="仲間さがしビンゴ",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 5×5 をスマホ幅でも横一列に保つための CSS。
# セレクタは Streamlit 1.50 の DOM に合わせている（key 付き要素に付く st-key-* クラスを使う）。
st.html(
    """
<style>
/* 各行のコンテナ（横並び）は折り返さない */
[class*="st-key-row"] > div[data-testid="stHorizontalBlock"],
[class*="st-key-row"] [data-testid="stHorizontalBlock"] {
  flex-wrap: nowrap !important;
  gap: 0.25rem !important;
}
/* 各マスは均等幅・最小幅なし */
[class*="st-key-cell"] {
  flex: 1 1 0 !important;
  min-width: 0 !important;
  width: auto !important;
}
[class*="st-key-cell"] button {
  width: 100% !important;
  min-height: 3.6rem !important;
  padding: 0.15rem 0.1rem !important;
  line-height: 1.2 !important;
}
[class*="st-key-cell"] button p {
  font-size: 0.74rem !important;
  white-space: normal !important;
  word-break: break-all !important;
  line-height: 1.2 !important;
}
[class*="st-key-cell"] button [data-testid="stMarkdownContainer"] {
  min-width: 0 !important;
}
/* 上下の余白を詰める */
/* 上の余白は Community Cloud のヘッダー（Fork表示など）に隠れない程度に残す */
.block-container { padding-top: 3.5rem !important; padding-bottom: 2rem !important; }
</style>
"""
)


@st.cache_data(show_spinner=False)
def get_questions() -> list[Question]:
    return load_questions(DATA_PATH)


def save_opened(opened: Opened) -> None:
    """開いたマスを URL の ``o`` に書き戻す。空なら ``o`` を消す。"""
    if opened:
        st.query_params["o"] = encode_opened(opened)
    elif "o" in st.query_params:
        del st.query_params["o"]


def load_state() -> tuple[int, Opened]:
    """URL から seed と開いたマスを復元する。s が不正なら新しいシートを作る。"""
    seed = parse_seed(st.query_params.get("s"))
    if seed is None:
        seed = new_seed()
        st.query_params.clear()
        st.query_params["s"] = str(seed)
        return seed, {}
    raw_o = st.query_params.get("o")
    opened = decode_opened(raw_o)
    if raw_o and encode_opened(opened) != raw_o:
        save_opened(opened)  # 壊れた部分を落とした状態で URL を書き直す
    return seed, opened


def apply_open(pos: int, name: str, opened: Opened) -> None:
    before = bingo_count(opened)
    opened[pos] = name
    after = bingo_count(opened)
    if after > before:
        st.session_state["celebrate"] = after
    st.session_state.pop("pending", None)
    save_opened(opened)
    st.rerun()


@st.dialog("マスを開ける")
def open_cell_dialog(pos: int, question: Question, opened: Opened) -> None:
    st.markdown(f"### {question.question}")
    st.caption("相手の答えが自分と同じなら開けます")

    with st.form(key=f"open_form_{pos}", border=False):
        raw_name = st.text_input(
            "相手の名前",
            placeholder="例：田中",
            max_chars=NAME_MAX_CHARS,
        )
        submitted = st.form_submit_button("開ける", type="primary", width="stretch")

    if submitted:
        name = clean_name(raw_name)
        if not name:
            st.error("相手の名前を入力してください。")
        else:
            dup = same_person_positions(opened, name)
            if dup and st.session_state.get("pending") != (pos, name):
                st.session_state["pending"] = (pos, name)
            else:
                apply_open(pos, name, opened)

    pending = st.session_state.get("pending")
    if pending and pending[0] == pos:
        pending_name = pending[1]
        count = len(same_person_positions(opened, pending_name))
        st.warning(
            f"**「{pending_name}」とはすでに話しています**（{count}マス）。"
            "なるべく違う人に聞いてみましょう。それでもよければもう一度「開ける」を押してください。"
        )
        if st.button("それでも開ける", key=f"force_open_{pos}", width="stretch"):
            apply_open(pos, pending_name, opened)

    if st.button("キャンセル", key=f"cancel_open_{pos}", width="stretch"):
        st.session_state.pop("pending", None)
        st.rerun()


@st.dialog("開いたマス")
def opened_cell_dialog(pos: int, question: Question, opened: Opened) -> None:
    st.markdown(f"### {question.question}")
    st.markdown(f"記録した名前：**{opened[pos]}**")

    with st.form(key=f"edit_form_{pos}", border=False):
        raw_name = st.text_input("名前を修正する", value=opened[pos], max_chars=NAME_MAX_CHARS)
        if st.form_submit_button("名前を更新", width="stretch"):
            name = clean_name(raw_name)
            if not name:
                st.error("名前を空にはできません。取り消す場合は下のボタンを使ってください。")
            else:
                opened[pos] = name
                save_opened(opened)
                st.rerun()

    if st.button("このマスを取り消す", key=f"undo_{pos}", type="primary", width="stretch"):
        del opened[pos]
        save_opened(opened)
        st.rerun()
    if st.button("閉じる", key=f"close_{pos}", width="stretch"):
        st.rerun()


def cell_label(question: Question, name: str | None) -> str:
    if name is None:
        return question.label
    shown = name if len(name) <= CELL_NAME_MAX_CHARS else name[:CELL_NAME_MAX_CHARS] + "…"
    return f"{question.label}  \n{shown}"


def highlight_css(cells: frozenset[int]) -> str:
    """成立したラインのマスに金色の枠を付ける CSS。"""
    selectors = ", ".join(f".st-key-cell{pos} button" for pos in sorted(cells))
    return f"<style>{selectors} {{ box-shadow: 0 0 0 3px #f5c400 inset !important; }}</style>"


def render_board(sheet: list[Question | None], opened: Opened) -> None:
    highlighted = cells_in_completed_lines(opened)
    if highlighted:
        st.html(highlight_css(highlighted))
    for r in range(SIZE):
        with st.container(horizontal=True, gap="small", key=f"row{r}"):
            for c in range(SIZE):
                pos = r * SIZE + c
                question = sheet[pos]
                key = f"cell{pos}"
                if question is None:
                    st.button("FREE", key=key, type="primary", width="stretch")
                    continue
                if pos in opened:
                    if st.button(
                        cell_label(question, opened[pos]),
                        key=key,
                        type="primary",
                        width="stretch",
                    ):
                        st.session_state.pop("pending", None)
                        opened_cell_dialog(pos, question, opened)
                else:
                    if st.button(question.label, key=key, width="stretch"):
                        st.session_state.pop("pending", None)
                        open_cell_dialog(pos, question, opened)


def resume_url() -> str:
    base = st.context.url.split("?", 1)[0] if st.context.url else ""
    return f"{base}?{urlencode(dict(st.query_params))}"


def main() -> None:
    try:
        questions = get_questions()
    except QuestionDataError as e:
        st.error(f"questions.csv に問題があります：{e}")
        st.stop()

    seed, opened = load_state()
    sheet = generate_sheet(questions, seed)

    st.markdown("### 🎯 仲間さがしビンゴ")
    bingos = bingo_count(opened)
    opened_count = len(opened) + 1  # FREE を含む
    st.markdown(f"**ビンゴ：{bingos} 本**　　開いたマス：{opened_count} / {CELL_COUNT}")
    st.caption("⚠️ このページ（タブ）は閉じないでください。閉じると別のシートになります。")

    render_board(sheet, opened)

    celebrated = st.session_state.pop("celebrate", None)
    if celebrated:
        st.balloons()
        st.toast(f"ビンゴ！ {celebrated} 本目です 🎉")

    with st.expander("遊び方"):
        st.markdown(
            """
1. 自分のシートを持って、任意の人に話しかける。
2. まだ開いていないマスの質問を **1つだけ** 聞く（例：「朝型と夜型、どっちですか？」）。
3. 相手の答えが自分と同じなら、そのマスをタップして相手の名前を入れて開ける。違えば開けない。
4. **なるべく違う人に聞く**。同じ人の名前を入れると注意が出るが、開けることはできる。
5. 間違えて開けたマスは、もう一度タップすると取り消したり名前を直したりできる。
6. 縦・横・斜めがそろったらビンゴ。順位はつけないので、会話を楽しむこと。

※ 答えが同じかどうかは本人が判断する（アプリは自動判定しない）。
"""
        )
    with st.expander("続きのURL（ページを閉じてしまったときの復帰用）"):
        st.markdown(
            "このURLを開くと、今のシートの続きから再開できます。"
            "右上のアイコンでコピーして、自分宛のチャットなどに送っておくと安心です。"
        )
        st.code(resume_url(), language=None, wrap_lines=True)


main()
