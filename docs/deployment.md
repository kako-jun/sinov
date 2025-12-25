# 実行・デプロイガイド

## ローカル実行

### 初回セットアップ

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd sinov

# 2. uv のインストール
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 依存関係のインストール
uv sync

# 4. 環境設定
cp .env.example .env
cp .env.keys.example .env.keys
# .envを編集（API_ENDPOINT, OLLAMA_HOST, OLLAMA_MODEL）

# 5. ボットの鍵を生成
uv run python scripts/generate_keys.py

# 6. ボット履歴書を作成
# bots/profiles/bot001.yaml, bot002.yaml などを作成

# 7. Ollama起動（必須）
ollama serve
# 別ターミナルで:
ollama pull gemma2:2b

# 8. テスト実行（dry-run）
uv run python -m src.cli generate --all --dry-run
uv run python -m src.cli queue --status dry_run
```

### 2 回目以降

```bash
# Ollama起動（必須）
ollama serve

# 別ターミナルで実行
cd sinov
uv run python -m src.main
```

### 停止

```bash
# Ctrl+C で停止
# 状態は自動的に bots/states.json に保存される
```

## CLIワークフロー

投稿は必ずレビュープロセスを経てから本番投稿されます。

### 基本的な流れ

```bash
# 1. 投稿を生成（pending.json へ）
uv run python -m src.cli generate --all

# 2. キューを確認
uv run python -m src.cli queue --summary
uv run python -m src.cli review list

# 3. レビュー（承認/拒否）
uv run python -m src.cli review approve <entry_id>
uv run python -m src.cli review reject <entry_id> --note "修正必要"

# 4. 承認済みエントリーを投稿
uv run python -m src.cli post
```

### プレビュー（dry-run）

```bash
# レビュー不要で dry_run.json に直接保存
uv run python -m src.cli generate --all --dry-run

# 内容を確認
uv run python -m src.cli queue --status dry_run
```

## systemd サービス化（Linux）

常時稼働させる場合は systemd でサービス化します。

### 1. サービスファイルの作成

```bash
sudo nano /etc/systemd/system/sinov.service
```

内容：

```ini
[Unit]
Description=Sinov Bot Manager
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/sinov
ExecStart=/home/your-username/.local/bin/uv run python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**注意**: `your-username`と`/path/to/sinov`を実際のパスに置き換える。

### 2. サービスの有効化と起動

```bash
# リロード
sudo systemctl daemon-reload

# 有効化（起動時に自動起動）
sudo systemctl enable sinov

# 起動
sudo systemctl start sinov

# 状態確認
sudo systemctl status sinov

# ログ確認
sudo journalctl -u sinov -f
```

### 3. サービスの管理

```bash
# 停止
sudo systemctl stop sinov

# 再起動
sudo systemctl restart sinov

# 無効化
sudo systemctl disable sinov
```

## Docker 化

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# uv のインストール
RUN pip install uv

# 依存関係のインストール
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# アプリケーションのコピー
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY bots/ ./bots/
COPY .env .env

# 実行
CMD ["uv", "run", "python", "-m", "src.main"]
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  sinov:
    build: .
    container_name: sinov-bot-manager
    restart: unless-stopped
    volumes:
      - ./bots:/app/bots
      - ./.env:/app/.env
      - ./.env.keys:/app/.env.keys
    environment:
      - OLLAMA_HOST=http://ollama:11434
    depends_on:
      - ollama
    networks:
      - sinov-network

  ollama:
    image: ollama/ollama:latest
    container_name: ollama
    restart: unless-stopped
    volumes:
      - ollama-data:/root/.ollama
    ports:
      - "11434:11434"
    networks:
      - sinov-network

networks:
  sinov-network:
    driver: bridge

volumes:
  ollama-data:
```

### 実行

```bash
# ビルド
docker-compose build

# 起動
docker-compose up -d

# ログ確認
docker-compose logs -f sinov

# 停止
docker-compose down

# Ollamaモデルのダウンロード
docker-compose exec ollama ollama pull gemma2:2b
```

### Docker 内での CLI コマンド

```bash
# 投稿生成
docker-compose exec sinov uv run python -m src.cli generate --all --dry-run

# キュー確認
docker-compose exec sinov uv run python -m src.cli queue --summary

# レビュー
docker-compose exec sinov uv run python -m src.cli review list
docker-compose exec sinov uv run python -m src.cli review approve <id>

# 投稿
docker-compose exec sinov uv run python -m src.cli post
```

## VPS デプロイ

### 推奨スペック

**最小構成:**

- CPU: 2 コア
- メモリ: 4GB（LLM 使用時）
- ストレージ: 20GB

**推奨構成:**

- CPU: 4 コア以上
- メモリ: 8GB 以上
- ストレージ: 40GB 以上

### VPS プロバイダ例

- DigitalOcean Droplet
- Vultr
- Linode
- AWS EC2 t3.medium
- Hetzner Cloud

### デプロイ手順

#### 1. VPS への接続

```bash
ssh user@your-vps-ip
```

#### 2. 必要なパッケージのインストール

```bash
# システムアップデート
sudo apt update && sudo apt upgrade -y

# Python 3.11+
sudo apt install -y python3.11 python3-pip python3-venv

# Git
sudo apt install -y git

# Ollama（必須）
curl -fsSL https://ollama.com/install.sh | sh
```

#### 3. uv のインストール

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc  # または再ログイン
```

#### 4. アプリケーションのデプロイ

```bash
# プロジェクトのクローン
cd /opt
sudo git clone <repository-url> sinov
sudo chown -R $USER:$USER /opt/sinov
cd sinov

# 依存関係インストール
uv sync

# 環境設定
cp .env.example .env
cp .env.keys.example .env.keys
nano .env

# 鍵生成
uv run python scripts/generate_keys.py

# ボット履歴書を配置
# （ローカルから scp でアップロード）
scp -r bots/profiles/* user@your-vps-ip:/opt/sinov/bots/profiles/
```

#### 5. Ollama モデルのダウンロード

```bash
# Ollama起動
sudo systemctl start ollama

# モデルダウンロード
ollama pull gemma2:2b
```

#### 6. systemd サービス化

上記の「systemd サービス化」セクションを参照。

#### 7. ファイアウォール設定（必要に応じて）

```bash
sudo ufw allow ssh
sudo ufw enable
```

### アップデート手順

```bash
# VPSに接続
ssh user@your-vps-ip

# サービス停止
sudo systemctl stop sinov

# コード更新
cd /opt/sinov
git pull

# 依存関係更新（必要に応じて）
uv sync

# サービス再起動
sudo systemctl start sinov

# 状態確認
sudo systemctl status sinov
```

## モニタリング

### ログの確認

#### systemd の場合

```bash
# リアルタイムログ
sudo journalctl -u sinov -f

# 直近100行
sudo journalctl -u sinov -n 100

# 日時指定
sudo journalctl -u sinov --since "2024-01-01 00:00:00"
```

#### Docker の場合

```bash
# リアルタイムログ
docker-compose logs -f sinov

# 直近100行
docker-compose logs --tail=100 sinov
```

### 状態の確認

```bash
# 状態ファイルを確認
cat bots/states.json | jq '.[0]'

# 投稿数の合計
cat bots/states.json | jq '[.[].total_posts] | add'

# 最後に投稿したボット
cat bots/states.json | jq 'max_by(.last_post_time)'
```

### キューの確認

```bash
# サマリー
uv run python -m src.cli queue --summary

# ペンディング一覧
uv run python -m src.cli queue --status pending

# 投稿済み一覧
uv run python -m src.cli queue --status posted
```

### リソース使用量

```bash
# CPU・メモリ使用量
htop

# プロセス確認
ps aux | grep python

# ディスク使用量
df -h
du -sh /opt/sinov
```

## バックアップ

### 重要なファイル

```bash
# バックアップすべきファイル
.env.keys              # 秘密鍵（最重要）
bots/states.json       # 実行状態
bots/profiles/*.yaml   # ボット履歴書
bots/queue/*.json      # キューファイル
.env                   # 環境設定
```

### バックアップスクリプト

```bash
#!/bin/bash
# backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/path/to/backups"
SOURCE_DIR="/opt/sinov"

mkdir -p "$BACKUP_DIR"

tar -czf "$BACKUP_DIR/sinov_backup_$DATE.tar.gz" \
  -C "$SOURCE_DIR" \
  .env.keys \
  bots/states.json \
  bots/profiles/ \
  bots/queue/ \
  .env

# 古いバックアップを削除（30日以上前）
find "$BACKUP_DIR" -name "sinov_backup_*.tar.gz" -mtime +30 -delete

echo "Backup completed: sinov_backup_$DATE.tar.gz"
```

実行：

```bash
chmod +x backup.sh
./backup.sh
```

### crontab で自動バックアップ

```bash
crontab -e
```

追加：

```cron
# 毎日3時にバックアップ
0 3 * * * /opt/sinov/backup.sh >> /var/log/sinov_backup.log 2>&1
```

## トラブルシューティング

### サービスが起動しない

```bash
# ログ確認
sudo journalctl -u sinov -n 100

# 手動実行してエラー確認
cd /opt/sinov
uv run python -m src.main
```

### 投稿が送信されない

1. **Nostr 接続確認**

   ```bash
   # リレーに接続できるか確認
   ping relay.damus.io
   ```

2. **環境変数確認**

   ```bash
   cat .env
   ```

3. **キュー確認**
   ```bash
   uv run python -m src.cli queue --summary
   # approved が 0 なら、レビューが必要
   ```

4. **状態ファイル確認**
   ```bash
   cat bots/states.json | jq '.[0].next_post_time'
   # 未来の時刻が設定されているか確認
   ```

### メモリ不足

```bash
# スワップ追加
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### Ollama 接続エラー

```bash
# Ollamaステータス確認
systemctl status ollama

# 再起動
systemctl restart ollama

# ログ確認
journalctl -u ollama -f
```

## セキュリティ

### ファイルパーミッション

```bash
# 秘密鍵ファイルを保護
chmod 600 .env.keys

# ディレクトリ権限
chmod 700 bots/
```

### 環境変数の暗号化

機密情報をハードコードしない：

```bash
# 良い例
# .env.keys に nsec を保存

# 悪い例（コード内にハードコード）
NSEC = "nsec1..."
```

### SSH 鍵認証

```bash
# パスワード認証を無効化
sudo nano /etc/ssh/sshd_config
# PasswordAuthentication no
sudo systemctl restart sshd
```

## FAQ

### Q: 100 体すべて動かす必要がある？

A: いいえ。必要な数だけ履歴書を作成すれば OK です。`bots/profiles/`にある YAML ファイルの数だけボットが起動します。

### Q: レビューなしで直接投稿できる？

A: 現在の設計ではレビュープロセスが必須です。`generate` → `review approve` → `post` の流れになります。プレビュー目的なら `generate --dry-run` を使用してください。

### Q: リレーは変更できる？

A: はい。`.env`の`API_ENDPOINT`を編集してください。

### Q: 鍵を再生成したい

A:

```bash
# .env.keys を編集して該当の鍵を削除
# または全削除してから再生成
uv run python scripts/generate_keys.py
```

**注意**: 新しい鍵になるため、以前の投稿とは別のアカウントになります。

### Q: ボットの行動を変更するには？

A: `bots/profiles/botXXX.yaml`を編集して、アプリケーションを再起動してください。

### Q: キューをクリアしたい

A:

```bash
# 全キューをクリア
rm -f bots/queue/*.json

# 特定ステータスのみクリア
rm -f bots/queue/pending.json
rm -f bots/queue/rejected.json
```
