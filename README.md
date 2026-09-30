# 仲間さがしビンゴ

新人歓迎会で使う、自分のスマホで遊ぶ仲間さがしビンゴの Streamlit アプリです。
サーバーには何も保存せず、シートの状態はすべて URL のクエリパラメータに持ちます。

仕様は [spec.md](spec.md) を参照してください。

## 動かし方（ローカル）

```
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run app.py
```

ブラウザで `http://localhost:8501` を開きます。スマホ表示の確認は、ブラウザの開発者ツールで幅 360〜430px にしてください。

## テスト

```
pip install -r requirements-dev.txt
python -m playwright install chromium   # E2E テストを動かす場合のみ
python -m pytest
```

- `tests/test_questions.py`, `test_sheet.py`, `test_lines.py`, `test_state.py`: ロジックのユニットテスト（Streamlit 不要）
- `tests/test_e2e.py`: Chromium をスマホ幅で起動し、5×5 の表示、開ける／取り消し、同じ人の警告、ビンゴ演出、リロード復元、不正な URL の修復を確認します。playwright が無い環境ではスキップされます。

## 質問の編集（幹事向け）

`data/questions.csv` を編集します。コードを触る必要はありません。

| 列 | 内容 |
|---|---|
| `id` | 一意の整数。重複するとエラーになります |
| `category` | 分野（表示には使いません） |
| `question` | ダイアログに出す質問文（「A or B」の形） |
| `label` | マスに出す短いラベル。**8文字以内**（超えるとエラーになります。6文字までが読みやすい目安） |

注意:

- 文字コードは **UTF-8** で保存してください。Excel で開いた場合は「CSV UTF-8（コンマ区切り）」で保存します（BOM 付きでも読めます）。
- 問題数は 24 問以上必要です。
- **当日、参加者に URL を配ったあとは CSV を変更しないでください。** シートはシードと CSV の内容から作られるので、CSV を変えると同じ URL でも別のシートになり、記録した名前が別の質問に付いてしまいます。行の並び替えだけなら影響しません（id 順に並べ替えてから使うため）。

## デプロイ（Streamlit Community Cloud）

1. このリポジトリを GitHub に push します。
2. [Streamlit Community Cloud](https://share.streamlit.io/) でリポジトリと `app.py` を指定してデプロイします。Python のバージョンは 3.13、依存関係は `requirements.txt` が使われます。
3. 発行された URL（`https://xxx.streamlit.app`）を QR コードにして配布します。

公開範囲やプライベートリポジトリの扱いは最新の公式ドキュメントで確認してください。

## 当日の運用

- 一定時間アクセスがないとアプリがスリープするので、**会の直前に幹事がアクセスして起動しておきます**。
- 参加者は QR コードから開きます。初回アクセスでシード付きの URL に切り替わり、その URL が自分専用のシートになります。
- 「ページを閉じないでください」と案内してください。閉じて QR から入り直すと別のシートになります。復帰したい場合は、画面下の「続きのURL」を事前にコピーしておいてもらいます。
- ブラウザの「戻る」は押さないよう案内してください。1操作ごとに履歴が積まれるため、「戻る」を押すと URL が1手前に戻り、次の操作から1手前の状態で続くことになります。
- 会場の通信環境（Wi-Fi やモバイル回線）を事前に確認してください。

## 画面の仕組み（開発者向け）

- `app.py` が画面、`bingo/` がロジックです。ロジックは Streamlit に依存しません。
- URL パラメータ: `s` がシード、`o` が開いたマス（`[[位置, 名前], ...]` の JSON を base64url にしたもの）。
- 5×5 の横並びは `st.container(horizontal=True)` と、`key` 付き要素に付く `st-key-*` クラスを狙った CSS で実現しています。Streamlit のバージョンは `requirements.txt` で固定しているので、上げるときは `tests/test_e2e.py` を通してスマホ幅の表示を確認してください。
- 実機（iOS Safari、Android Chrome）での確認は自動化していません。デプロイ後に一度実機で確認してください。
