"""ブラウザでの E2E テスト（Playwright + Chromium、スマホ幅）。

実行方法:
    pip install -r requirements-dev.txt
    python -m playwright install chromium
    python -m pytest tests/test_e2e.py

playwright が無い環境ではスキップされる。
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest

playwright = pytest.importorskip("playwright.sync_api")
from playwright.sync_api import expect  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SEED = 777


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def base_url():
    port = _free_port()
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
            "--server.port", str(port), "--server.headless", "true",
            "--browser.gatherUsageStats", "false",
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/"
    try:
        for _ in range(60):
            try:
                urllib.request.urlopen(url, timeout=1)
                break
            except Exception:
                time.sleep(0.5)
        else:
            pytest.fail("Streamlit が起動しませんでした")
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()


@pytest.fixture
def page(base_url):
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 360, "height": 780},
            is_mobile=True,
            has_touch=True,
        )
        pg = ctx.new_page()
        try:
            pg.goto(f"{base_url}?s={SEED}")
            pg.wait_for_selector(".st-key-cell0 button", timeout=30000)
            settle(pg)
            yield pg
        finally:
            browser.close()


def settle(pg, ms: int = 1200) -> None:
    pg.wait_for_timeout(ms)


def cell(pg, pos: int):
    return pg.locator(f".st-key-cell{pos} button")


def dialog(pg):
    return pg.locator('[role="dialog"]')


def open_cell(pg, pos: int, name: str) -> None:
    cell(pg, pos).click()
    expect(dialog(pg)).to_be_visible(timeout=10000)
    dialog(pg).locator("input").first.fill(name)
    dialog(pg).get_by_role("button", name="開ける").first.click()
    settle(pg)
    expect(dialog(pg)).to_have_count(0, timeout=10000)


def test_grid_is_5x5_without_horizontal_scroll(page):
    rows = page.evaluate(
        """() => [...document.querySelectorAll('[class*="st-key-row"]')].map(r =>
             [...r.querySelectorAll('button')].map(b => Math.round(b.getBoundingClientRect().y)))"""
    )
    assert len(rows) == 5
    for ys in rows:
        assert len(ys) == 5
        assert len(set(ys)) == 1, f"横並びになっていない: {ys}"
    scroll_w, client_w = page.evaluate(
        "[document.documentElement.scrollWidth, document.documentElement.clientWidth]"
    )
    assert scroll_w <= client_w


def test_open_undo_and_url_state(page):
    cell(page, 0).click()
    expect(dialog(page)).to_be_visible(timeout=10000)
    dialog(page).get_by_role("button", name="開ける").first.click()
    settle(page)
    expect(dialog(page).get_by_text("入力してください")).to_be_visible()
    dialog(page).get_by_role("button", name="キャンセル").click()
    settle(page)
    expect(dialog(page)).to_have_count(0)

    open_cell(page, 0, "田中")
    expect(cell(page, 0)).to_contain_text("田中")
    expect(page.get_by_text("開いたマス：2 / 25")).to_be_visible()
    assert "o=" in page.url

    # 同じ人の警告 → それでも開ける
    cell(page, 1).click()
    expect(dialog(page)).to_be_visible(timeout=10000)
    dialog(page).locator("input").first.fill("田中さん")
    dialog(page).get_by_role("button", name="開ける").first.click()
    settle(page)
    expect(dialog(page).get_by_text("すでに話しています")).to_be_visible()
    dialog(page).get_by_role("button", name="それでも開ける").click()
    settle(page)
    expect(dialog(page)).to_have_count(0, timeout=10000)

    # 名前の修正と取り消し
    cell(page, 1).click()
    expect(dialog(page)).to_be_visible(timeout=10000)
    dialog(page).locator("input").first.fill("佐々木小次郎")
    dialog(page).get_by_role("button", name="名前を更新").click()
    settle(page)
    expect(cell(page, 1)).to_contain_text("佐々木小…")
    cell(page, 1).click()
    expect(dialog(page)).to_be_visible(timeout=10000)
    dialog(page).get_by_role("button", name="このマスを取り消す").click()
    settle(page)
    expect(cell(page, 1)).not_to_contain_text("佐々木")
    expect(page.get_by_text("開いたマス：2 / 25")).to_be_visible()

    # リロードで復元される
    url = page.url
    page.reload()
    page.wait_for_selector(".st-key-cell0 button", timeout=30000)
    settle(page)
    assert page.url == url
    expect(cell(page, 0)).to_contain_text("田中")


def test_bingo_celebration_once_and_not_on_reload(page):
    for pos, name in [(10, "鈴木"), (11, "高橋"), (13, "伊藤")]:
        open_cell(page, pos, name)
    expect(page.get_by_text("ビンゴ：0 本")).to_be_visible()
    assert page.locator('[data-testid="stBalloons"]').count() == 0

    open_cell(page, 14, "渡辺")
    expect(page.get_by_text("ビンゴ：1 本")).to_be_visible()
    assert page.locator('[data-testid="stBalloons"]').count() == 1

    page.reload()
    page.wait_for_selector(".st-key-cell0 button", timeout=30000)
    settle(page)
    expect(page.get_by_text("ビンゴ：1 本")).to_be_visible()
    assert page.locator('[data-testid="stBalloons"]').count() == 0


def test_invalid_params_are_repaired(page, base_url):
    page.goto(f"{base_url}?s={SEED}&o=%%%bad")
    page.wait_for_selector(".st-key-cell0 button", timeout=30000)
    settle(page)
    expect(page.get_by_text("開いたマス：1 / 25")).to_be_visible()
    assert page.url.rstrip("/").endswith(f"?s={SEED}")

    page.goto(f"{base_url}?s=abc&o=xyz")
    page.wait_for_selector(".st-key-cell0 button", timeout=30000)
    settle(page)
    assert "s=" in page.url and "s=abc" not in page.url and "o=" not in page.url


def test_resume_url_matches_current_state(page):
    open_cell(page, 3, "山田")
    page.get_by_text("続きのURL").click()
    settle(page)
    code = page.locator("code").first.inner_text()
    assert code.split("?", 1)[1] == page.url.split("?", 1)[1]
