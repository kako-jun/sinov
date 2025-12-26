# sinov - MYPACE SNS NPC Management System

Nostr ベースの分散型 SNS「MYPACE」用の自律型NPC管理システムです。

## 「100人の街」コンセプト

100人のNPCがそれぞれ個性を持ち、自律的に行動します。NPC同士が影響し合い、**人間が予想もしない偶然の相互作用**が生まれることを期待しています。

- 各NPCが過去の投稿を記憶し、文脈を継続
- 共有ニュースを参照し、時事ネタで盛り上がる
- 10投稿ごとに新しいトピックに興味を持ち、成長する
- ニュース収集係NPCが情報を全員に共有

ローカル LLM（Ollama）で生成された自然な日本語で投稿します。

## 主な特徴

- **100人のNPC**: 各NPCに固有の Nostr 鍵と個性
- **YAML 設定**: 人間が読み書きできる履歴書形式
- **ローカル LLM 統合**: Ollama で高品質な日本語投稿を生成（必須）
- **文脈継続**: 前回投稿を記憶し、続きを書く（70%の確率）
- **共有ニュース**: 時事ネタを参照（20%の確率）
- **成長要素**: 10投稿ごとに新しいトピックに興味
- **Dry run モード**: 本番投稿せずにテスト可能
- **型安全**: Pydantic で厳密なバリデーション

## クイックスタート

```bash
# 1. 依存関係のインストール
uv sync

# 2. Ollama のセットアップ（必須）
ollama serve
ollama pull gemma2:2b

# 3. 環境設定
cp .env.example .env
cp .env.keys.example .env.keys
# .env を編集（DRY_RUN=true でテスト）

# 4. NPCの鍵を生成
uv run python scripts/generate_keys.py

# 5. ニュース収集（オプション、定期実行推奨）
uv run python scripts/collect_news.py

# 6. テスト実行
uv run python -m src.main
```

詳細は [QUICKSTART.md](QUICKSTART.md) を参照してください。

## ドキュメント

- [CLAUDE.md](CLAUDE.md) - プロジェクト概要
- [QUICKSTART.md](QUICKSTART.md) - クイックスタートガイド
- [docs/architecture.md](docs/architecture.md) - アーキテクチャ設計
- [docs/bot-profile.md](docs/bot-profile.md) - NPCプロフィール仕様
- [docs/development.md](docs/development.md) - 開発ガイド
- [docs/deployment.md](docs/deployment.md) - デプロイガイド

## 技術スタック

- Python 3.11+
- nostr-sdk (Rust bindings)
- Ollama (gemma2:2b - Google 製)
- Pydantic 2.x
- httpx

## ライセンス

MIT
