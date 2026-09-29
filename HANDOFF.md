# HANDOFF

## 製品概要

Vyrezchik は画像内の被写体を高精度に切り抜くローカルGUIツール。Notionプロジェクト 202_Vyrezchik / Вырезchik に対応。

## 環境

- **Python**: 3.14.5
- **GPU**: NVIDIA CUDA（Optional、ない場合はCPU動作）
- **OS**: Windows 11
- **パッケージマネージャ**: pip + venv

## ディレクトリ構成

```
202_Vyrezchik/
├── server.py          # FastAPI バックエンド
├── web/
│   └── index.html     # フロントエンド（vanilla JS + Canvas）
├── requirements.txt   # 依存パッケージ
├── run.bat            # 起動スクリプト
├── status.bat         # 状態確認スクリプト
├── stop.bat           # 停止スクリプト
├── sam2.1_l.pt        # SAM 2.1 モデル（自動DL、Git除外）
├── .venv/             # 仮想環境（Git除外）
├── exports/           # 書き出し先（Git除外）
└── docs/              # ドキュメント
```

## 落とし穴

1. **モデルファイル**: sam2.1_l.pt（428MB）は GitHub 上限超。初回起動時に Ultralytics 経由で自動 DL。`.gitignore` に除外済み。
2. **Python 3.14**: PyTorch 2.11 が必要。`--extra-index-url` で CUDA 版を指定。
3. **transformers 5.x API**: `box_threshold` → `threshold` に変更済み。
4. **PowerShell + Python スクリプト**: 日本語・絵文字はUTF-8エンコード必須。`-c` インラインは避け `.py` ファイル経由で実行。
5. **Notion API**: 絵文字アイコンは `{"type": "emoji", "emoji": "✂️"}` 形式。`ensure_ascii=False` 必須。

## 起動・停止

```powershell
.\run.bat      # 起動（ブラウザ自動オープン）
.\status.bat   # 状態確認
.\stop.bat     # 停止
```
