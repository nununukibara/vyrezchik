# CLAUDE.md

Claude Code 向けのプロジェクト情報。

## コマンド

- 起動: `.\run.bat`
- 状態確認: `.\status.bat`
- 停止: `.\stop.bat`
- テスト: 未整備（E2E は `test_e2e.py` を削除済み、要再作成）

## プロジェクト構造

- `server.py` — FastAPI バックエンド（SAM 2.1 + Grounding DINO）
- `web/index.html` — フロントエンド（単一ファイル、JS + CSS + HTML）

## スタック

- Python 3.14.5
- FastAPI + uvicorn
- ultralytics（SAM 2.1）
- transformers（Grounding DINO）
- Pillow, OpenCV, NumPy

## 既知の問題

- transformers 5.x で Grounding DINO のラベル抽出が空になる（実在語の検証は別途必要）
- PowerShell 環境で日本語・絵文字を含むインライン Python は文字化けする（`.py` ファイルへ書いて実行）
