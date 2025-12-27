# CLIコマンド

## コマンド一覧

### generate

投稿を生成してキューに追加。

```bash
# 全NPCの投稿を生成
sinov generate --all

# 特定NPCの投稿を生成
sinov generate --npc npc001

# ドライラン（実際にキューに追加しない）
sinov generate --npc npc001 --dry-run
```

### queue

キュー状態を表示。

```bash
# 全ステータスを表示
sinov queue

# 特定ステータスのみ表示
sinov queue --status pending

# サマリー表示
sinov queue --summary
```

### review

投稿をレビュー。

```bash
# 審査待ち一覧を表示
sinov review list

# 投稿を承認
sinov review approve abc12345

# 投稿を却下（理由付き）
sinov review reject abc12345 --note "不適切な内容"

# ドライラン
sinov review approve abc12345 --dry-run
```

### post

承認済み投稿をNostrに投稿。

```bash
# 全承認済み投稿を投稿
sinov post

# ドライラン
sinov post --dry-run
```

### tick

ワンループ処理を実行。

```bash
# デフォルト（10回分の処理）
sinov tick

# 回数指定
sinov tick --count 5

# ドライラン
sinov tick --dry-run
```

## tickコマンドのワークフロー

`--count N` で N 回分の処理を実行:
- 住人 N-1 人 + レビューア 1 回

### 処理フロー

1. **ラウンドロビンでNPC選定**
   - TickState から現在のインデックスを取得
   - 次の N-1 人を選定

2. **投稿生成**
   - 各NPCのコンテンツを生成
   - キュー（pending.json）に追加

3. **相互作用処理**
   - posted投稿へのリプライ/リアクション生成
   - スレッド内返信処理
   - 好感度減衰
   - 無視時処理

4. **外部反応処理**
   - 外部ユーザー投稿への反応
   - NPC1人あたり最大1件

5. **レビューア処理**
   - pending → approved/rejected
   - LLMでNGルール検査

6. **自動投稿**
   - approved → posted
   - Nostrに発行

7. **TickState更新**
   - 次回インデックスを記録

## 設定

`src/config/settings.py` で各種パラメータを設定:

```python
ContentSettings:
  context_continuation_probability: 0.7  # 前回投稿の続きを書く確率
  news_reference_probability: 0.2        # ニュースを参照する確率
  series_start_probability: 0.2          # 連作を開始する確率
  evolution_interval: 10                 # 興味進化の間隔（投稿数）
  llm_retry_count: 3                     # LLMリトライ回数
  history_check_count: 5                 # 重複チェックする履歴数
  max_history_size: 20                   # 保持する履歴の最大数
```
