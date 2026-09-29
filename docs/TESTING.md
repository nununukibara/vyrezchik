# TESTING

## 検証済み（2026-09-28）

| テスト | 方法 | 結果 |
|---|---|---|
| 画像読み込み | 2923x4000 JPEG | ✅ |
| クリックセグメント | 1点、2点、除外ポイント | ✅ |
| テキスト検出 | "flower", "vase" | ✅ |
| 書き出し | 透過PNG、白背景、feather | ✅ |
| E2E | Playwright + headless Chrome | ✅ |

## 再テスト方法

```powershell
# 別途test_e2e.pyとPlaywrightが必要
pip install playwright
playwright install chromium
.\venv\Scripts\python.exe test_e2e.py
```
