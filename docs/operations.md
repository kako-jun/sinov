# 運用手順書

## 事前準備

### 1. 環境構築

```bash
# 依存パッケージのインストール
uv sync

# 環境変数の設定
cp .env.example .env
cp .env.keys.example .env.keys
```

### 2. 環境変数

**.env**
```
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma2:2b
API_ENDPOINT=https://api.mypace.llll-ll.com
```

**.env.keys**（各NPCの鍵）
```
BOT_001_PUBKEY=abcd1234...
BOT_001_NSEC=nsec1...
BOT_002_PUBKEY=...
...
```

### 3. Ollamaの起動

```bash
# Ollamaサーバー起動
ollama serve

# モデルのダウンロード（初回のみ）
ollama pull gemma2:2b
```

---

## 投稿の流れ

```
[1. tick] → [2. review] → [3. post]
   ↓            ↓            ↓
 生成+判定    承認/却下     Nostrへ投稿
 (pending)   (approved)    (posted)
```

---

## 基本コマンド

### tickコマンド（メイン処理）

1周分の処理を実行する。住人の投稿生成 → 相互作用 → レビューを一括実行。

```bash
# 10人分を処理（デフォルト）
uv run python -m src.cli tick

# 5人分を処理
uv run python -m src.cli tick --count 5
```

**処理内容:**
1. 住人N人が投稿を生成 → `pending.json`
2. 既存投稿への相互作用（リプライ/リアクション）を生成
3. 好感度の減衰処理
4. LLMがレビュー → `approved.json` or `rejected.json`

### キュー確認

```bash
# サマリー表示
uv run python -m src.cli queue --summary

# 承認待ちを確認
uv run python -m src.cli queue --status pending

# 承認済みを確認
uv run python -m src.cli queue --status approved
```

### 手動レビュー

```bash
# 承認
uv run python -m src.cli review approve <entry_id>

# 却下
uv run python -m src.cli review reject <entry_id> --note "理由"

# 一覧表示
uv run python -m src.cli review list
```

### 投稿実行

```bash
# dry-run（実際には投稿しない）
uv run python -m src.cli post --dry-run

# 本番投稿
uv run python -m src.cli post
```

---

## 典型的な運用サイクル

### 毎日の運用（手動）

```bash
# 1. tickを数回実行して投稿を溜める
uv run python -m src.cli tick
uv run python -m src.cli tick
uv run python -m src.cli tick

# 2. 承認済みを確認
uv run python -m src.cli queue --status approved

# 3. 問題なければ投稿
uv run python -m src.cli post
```

### 自動運用（cron）

```cron
# 1時間ごとにtick実行
0 * * * * cd /path/to/sinov && uv run python -m src.cli tick >> /var/log/sinov.log 2>&1

# 6時間ごとに投稿
0 */6 * * * cd /path/to/sinov && uv run python -m src.cli post >> /var/log/sinov.log 2>&1
```

---

## キューファイル構造

```
bots/data/queue/
├── pending.json    # 生成直後、レビュー待ち
├── approved.json   # レビュー通過、投稿待ち
├── rejected.json   # 却下されたもの
├── posted.json     # 投稿完了
└── dry_run.json    # テスト生成
```

各エントリーの状態遷移:
```
pending → approved → posted
       ↘ rejected
```

---

## トラブルシューティング

### Ollamaに接続できない

```bash
# Ollamaが起動しているか確認
curl http://localhost:11434/api/tags

# 起動していなければ
ollama serve
```

### 投稿が生成されない

```bash
# NPCプロファイルを確認
ls bots/profiles/

# 記憶ファイルを確認
ls bots/data/memories/

# tick状態を確認
cat bots/data/tick_state.json
```

### 投稿がNostrに反映されない

```bash
# キューの状態確認
uv run python -m src.cli queue --summary

# approvedに溜まっていれば手動投稿
uv run python -m src.cli post

# APIエンドポイントを確認
echo $API_ENDPOINT
```

---

## データファイル

| パス | 内容 |
|------|------|
| `bots/profiles/*.yaml` | 住人プロファイル |
| `bots/data/memories/*.json` | 各住人の記憶 |
| `bots/data/queue/*.json` | 投稿キュー |
| `bots/data/relationships/` | 関係性定義 |
| `bots/data/bulletin_board/` | ニュース・イベント |
| `bots/data/tick_state.json` | ラウンドロビン状態 |

---

## 単体テスト的な確認

```bash
# 特定NPCの投稿生成（dry-run）
uv run python -m src.cli generate --bot bot001 --dry-run

# 全NPCの投稿生成（dry-run）
uv run python -m src.cli generate --all --dry-run
```

---

## 投稿の削除

試運転中は失敗投稿が多くなる。削除スクリプトで対応する。

### 投稿済み一覧を確認

```bash
# 最近の投稿を確認
python scripts/delete_posts.py list

# 特定NPCの投稿のみ
python scripts/delete_posts.py list --bot bot001

# 件数指定
python scripts/delete_posts.py list --limit 50
```

### 個別削除

```bash
# イベントIDを指定して削除（前方一致OK）
python scripts/delete_posts.py delete abc123

# 確認をスキップ
python scripts/delete_posts.py delete abc123 --yes
```

### 一括削除

```bash
# 特定NPCの全投稿を削除
python scripts/delete_posts.py delete-all --bot bot001 --confirm

# 全NPCの全投稿を削除（危険）
python scripts/delete_posts.py delete-all --confirm
```

### 削除の仕組み

1. Nostrでは投稿を完全に消すことはできない
2. kind:5（削除イベント）を発行し、対応クライアントに非表示を依頼
3. 多くのクライアントは削除イベントを尊重するが、一部は無視する可能性あり
4. 削除後、`posted.json`からもエントリーを除去

---

## 試運転の推奨手順

初めて動かすときは以下の手順で慎重に：

```bash
# 1. dry-runで生成内容を確認
uv run python -m src.cli generate --bot bot001 --dry-run

# 2. 1人だけでtickを試す
uv run python -m src.cli tick --count 2  # 住人1人 + レビュー1回

# 3. 承認済みを確認
uv run python -m src.cli queue --status approved

# 4. dry-runで投稿内容を確認
uv run python -m src.cli post --dry-run

# 5. 問題なければ本番投稿
uv run python -m src.cli post

# 6. 投稿を確認
python scripts/delete_posts.py list

# 7. 問題があれば削除
python scripts/delete_posts.py delete <event_id>
```

---

## 注意事項

1. **鍵の管理**: `.env.keys`は絶対にコミットしない
2. **レート制限**: 短時間に大量投稿するとリレーからBANされる可能性
3. **内容確認**: 本番投稿前に`--dry-run`で確認推奨
4. **バックアップ**: `bots/data/`を定期的にバックアップ
5. **削除の限界**: Nostrの削除は「お願い」であり、完全削除は保証されない
