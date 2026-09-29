# ARCHITECTURE

## バックエンド（server.py）

| エンドポイント | メソッド | 説明 |
|---|---|---|
| `/api/open` | POST | 画像を開く・特徴キャッシュ |
| `/api/segment` | POST | ポイントプロンプトでセグメント |
| `/api/detect` | POST | テキスト一括検出 |
| `/api/export` | POST | PNG書き出し |
| `/api/open_folder` | POST | エクスプローラーで開く |

## フロントエンド（web/index.html）

- 単一HTMLファイル（JS + CSS インライン）
- Canvas 2D で画像描画 + マスクオーバーレイ
- ズーム・パン（wheel + drag）
- ポイント追加（左クリック=含める、右クリック=除外）

## モデル

| モデル | ファイル | サイズ | 役割 |
|---|---|---|---|
| SAM 2.1-L | sam2.1_l.pt | 428MB | 対話的セグメンテーション |
| Grounding DINO base | HF経由キャッシュ | ~660MB | テキスト→バウンディングボックス |
