# DESIGN

## 概要

画像内の被写体をAIで高精度に切り抜くローカルGUIツール。LLMや外部APIに依存しない。

## アーキテクチャ

```
[Browser] ←→ [FastAPI :8765] ←→ [SAM 2.1 + Grounding DINO]
   │              │
   └─ Canvas ─────┘
        ↑
   PNG Overlay (mask preview)
```

## セグメンテーションフロー

1. 画像アップロード → SAM Image Encoder で特徴キャッシュ（初回のみ、約20ms）
2. ユーザー操作（クリック or テキスト入力）
3. SAM Mask Decoder でマスク生成（約10〜40ms）
4. フロントエンドでオーバーレイ表示
5. 書き出し（透過PNG or 白背景合成）

## テキスト検出フロー

1. Grounding DINO でテキスト→バウンディングボックス（約250ms）
2. NMS で重複除去
3. 各BoxをSAMに渡してマスク化
4. フロントエンドに一覧表示
