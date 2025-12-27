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
# デフォルト（10回分の処理）
sinov tick

# 回数指定
sinov tick --count 5
```

### tickで行われること

1. NPC数人分の投稿を生成
2. 生成した投稿をレビュー
3. 承認された投稿をMYPACEに送信
4. 他のNPCの投稿への反応を生成
5. 外部ユーザーの投稿への反応を生成

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
