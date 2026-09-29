# Vyrezchik / Вырезчик

画像内の被写体（花瓶・花・個別の花など）を SAM 2.1 + Grounding DINO で高精度に切り抜き、透過PNGとして書き出すローカルGUIツール。

**プロジェクトの正本は[GitHub](https://github.com/nununukibara/202-vyrezchik)です。** 採用済みの基準はmain、開発中の変更はブランチとPRで確認します。現在地と未反映の作業は[STATUS.md](./STATUS.md)にまとめます。

## 読む順

| 順 | 文書 | 読むとき |
|---|---|---|
| 1 | [HANDOFF.md](./HANDOFF.md) | 初参加時。製品・環境・落とし穴 |
| 2 | [STATUS.md](./STATUS.md) | 毎回。現在地・次の一歩・判断待ち |
| 3 | [AGENTS.md](./AGENTS.md) | 作業・判断・記録・Git操作の規則 |
| 4 | [docs/RESOURCES.md](./docs/RESOURCES.md)・[WORKLOG.md](./WORKLOG.md) | 利用できる環境と未完了作業 |
| 5 | [docs/REQUIREMENTS.md](./docs/REQUIREMENTS.md)・[ROADMAP.md](./ROADMAP.md) | 対象要件、受け入れ条件、版と順序 |

二度目以降はSTATUSから始め、作業に関係する仕様と実コードを確認します。Claude Codeの入口は[CLAUDE.md](./CLAUDE.md)です。

## 試す

```powershell
.\run.bat
```

初回起動時にSAM 2.1モデル（約428MB）が自動ダウンロードされます。GPU（CUDA）がない場合はCPUモードで動作しますが、セグメンテーション速度が低下します。

## 情報の置き場

| 内容 | 正本 |
|---|---|
| 現在地・次の作業・判断待ち | [STATUS.md](./STATUS.md) |
| 判断理由・作業履歴・検証結果 | [WORKLOG.md](./WORKLOG.md) |
| 目標・版の計画 | [ROADMAP.md](./docs/ROADMAP.md) |
| 仕様・構造 | [docs/DESIGN.md](./docs/DESIGN.md)・[docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md) |
| 検証方法 | [docs/TESTING.md](./docs/TESTING.md) |
| 独立した課題・変更のレビュー | [Issues](https://github.com/nununukibara/202-vyrezchik/issues)・[Pull requests](https://github.com/nununukibara/202-vyrezchik/pulls) |

## 状態の言葉

機能は **提案 → 承認済み → 実装済み → 検証済み → 採用済み → リリース済み** を区別します。
