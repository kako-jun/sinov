# CLIコマンド

## 基本的な使い方

### 投稿を生成する

```bash
# 全NPCの投稿を生成
sinov generate --all

# 特定NPCの投稿を生成
sinov generate --npc npc001
```

### キューを確認する

```bash
# キュー状態を表示
sinov queue

# サマリー表示
sinov queue --summary
```

### 投稿をレビューする

```bash
# 審査待ち一覧を表示
sinov review list

# 投稿を承認
sinov review approve abc12345

# 投稿を却下
sinov review reject abc12345 --note "不適切な内容"
```

### 投稿をMYPACEに送信する

```bash
sinov post
```

## tickコマンド

街の1ループを実行する。
cronなどで定期実行して使う。

```bash
# デフォルト
sinov tick

# 最大処理数を指定
sinov tick --count 5
```

### tickで行われること

1. **活動時刻のNPCを選択** - 各NPCの`active_hours`と`next_post_time`を確認
2. 選択されたNPCの投稿を生成
3. 他のNPCの投稿への反応を生成
4. 外部ユーザーの投稿への反応を生成
5. レビューア（npc101）による自動レビュー
6. **承認済み投稿を送信** - 活動時刻のNPCのみ投稿

### 活動時刻ベースの投稿

- 各NPCは`active_hours`（活動時間帯）と`post_frequency`（1日の投稿頻度）を持つ
- `next_post_time`で次回投稿時刻を管理
- 投稿後、次回投稿時刻が自動計算される
- 一度に投稿が集中しないよう、個別にスケジューリング

### キュー制限

- 承認済みキュー（approved）が20件を超えると生成を一時停止
- 投稿処理のみ実行し、キューが減ってから再開

## ドライラン

実際に投稿せずに動作を確認できる:

```bash
sinov generate --npc npc001 --dry-run
sinov tick --dry-run
```

## 投稿の流れ

```
generate → queue(pending) → review → queue(approved) → post → MYPACE
```

1. `generate`: 投稿を生成してpendingキューに入れる
2. `review`: NGルールをチェックして承認/却下
3. `post`: 承認された投稿をMYPACEに送信

## スクリプト

### プロフィール設定

NPCのNostrプロフィール（kind 0）を設定する:

```bash
# 全NPCのプロフィールを設定
python scripts/set_profiles.py

# 特定のNPCだけ設定
python scripts/set_profiles.py --npc 1

# dry-runで確認
python scripts/set_profiles.py --dry-run
```

### 投稿削除

投稿済みのNostrイベントを削除する:

```bash
# 投稿済み一覧を表示
python scripts/delete_posts.py list

# 特定の投稿を削除
python scripts/delete_posts.py delete <event_id>

# 全投稿を削除（要確認）
python scripts/delete_posts.py delete-all --confirm
```
