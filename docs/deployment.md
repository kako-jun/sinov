# 実行・デプロイガイド

## ローカル実行

### 初回セットアップ

```bash
# 1. リポジトリのクローン
git clone <repository-url>
cd sinov

# 2. 依存関係のインストール
pip install nostr-sdk pyyaml python-dotenv httpx ollama pydantic pydantic-settings

# 3. 環境設定
cp .env.example .env
cp .env.keys.example .env.keys
# .envを編集（API_ENDPOINT, OLLAMA_HOST, OLLAMA_MODEL, DRY_RUN）

# 4. ボットの鍵を生成
python scripts/generate_keys.py

# 5. ボット履歴書を作成
# bots/profiles/bot001.yaml, bot002.yaml などを作成

# 6. Ollama起動（オプション）
ollama serve
# 別ターミナルで:
ollama pull llama3.2:3b

# 7. 実行
python -m src.main
```

### 2 回目以降

```bash
# Ollama起動（使う場合）
ollama serve

# 別ターミナルで実行
cd sinov
source .venv/bin/activate  # 仮想環境使用時
python -m src.main
```

### 停止

```bash
# Ctrl+C で停止
# 状態は自動的に bots/states.json に保存される
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
Environment="PATH=/path/to/sinov/.venv/bin"
ExecStart=/path/to/sinov/.venv/bin/python -m src.main
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

# 依存関係のインストール
RUN pip install --no-cache-dir \
    nostr-sdk \
    pyyaml \
    python-dotenv \
    httpx \
    ollama \
    pydantic \
    pydantic-settings

# アプリケーションのコピー
COPY src/ ./src/
COPY scripts/ ./scripts/
COPY bots/ ./bots/
COPY .env .env

# 実行
CMD ["python", "-m", "src.main"]
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
    environment:
      - NOSTR_RELAYS=wss://nos.lol,wss://relay.damus.io
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
docker-compose exec ollama ollama pull llama3.2:3b
```

## VPS デプロイ

### 推奨スペック

**最小構成（LLM なし）:**

- CPU: 1 コア
- メモリ: 512MB
- ストレージ: 10GB

**推奨構成（LLM 使用）:**

- CPU: 2 コア以上
- メモリ: 4GB 以上（llama3.2:3b 使用時）
- ストレージ: 20GB 以上

### VPS プロバイダ例

- DigitalOcean Droplet
- Vultr
- Linode
- AWS EC2 t3.small
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

# Ollama（オプション）
curl -fsSL https://ollama.com/install.sh | sh
```

#### 3. アプリケーションのデプロイ

```bash
# プロジェクトのクローン
cd /opt
sudo git clone <repository-url> sinov
sudo chown -R $USER:$USER /opt/sinov
cd sinov

# 仮想環境作成
python3.11 -m venv .venv
source .venv/bin/activate

# 依存関係インストール
pip install nostr-sdk pyyaml python-dotenv httpx ollama pydantic pydantic-settings

# 環境設定
cp .env.example .env
nano .env

# 鍵生成
python scripts/generate_keys.py

# ボット履歴書を配置
# （ローカルから scp でアップロード）
scp -r bots/profiles/* user@your-vps-ip:/opt/sinov/bots/profiles/
```

#### 4. Ollama モデルのダウンロード（使う場合）

```bash
# Ollama起動
ollama serve &

# モデルダウンロード
ollama pull llama3.2:3b
```

#### 5. systemd サービス化

上記の「systemd サービス化」セクションを参照。

#### 6. ファイアウォール設定（必要に応じて）

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
source .venv/bin/activate
pip install --upgrade nostr-sdk pyyaml python-dotenv httpx ollama pydantic

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
bots/keys.json         # 秘密鍵（最重要）
bots/states.json       # 実行状態
bots/profiles/*.yaml   # ボット履歴書
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
  bots/keys.json \
  bots/states.json \
  bots/profiles/ \
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
source .venv/bin/activate
python -m src.main
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

3. **状態ファイル確認**
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

## パフォーマンスチューニング

### 投稿チェック間隔の調整

```python
# src/main.py
await manager.run_forever(check_interval=30)  # 30秒に変更
```

### 並列投稿

大量のボットを並列処理する場合：

```python
# src/bot_manager.py の run_once() を修正
async def run_once(self) -> None:
    tasks = []
    for bot_id in self.bots.keys():
        if self.should_post_now(bot_id):
            task = self._process_single_bot(bot_id)
            tasks.append(task)

    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)

    self._save_states()

async def _process_single_bot(self, bot_id: int) -> None:
    try:
        content = await self.generate_post_content(bot_id)
        await self.post(bot_id, content)
    except Exception as e:
        print(f"Error for bot {bot_id}: {e}")
```

## セキュリティ

### ファイルパーミッション

```bash
# 秘密鍵ファイルを保護
chmod 600 bots/keys.json

# ディレクトリ権限
chmod 700 bots/
```

### 環境変数の暗号化

機密情報をハードコードしない：

```bash
# 良い例
NOSTR_RELAYS=wss://nos.lol,wss://relay.damus.io

# 悪い例（コード内にハードコード）
RELAYS = ["wss://nos.lol"]
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

### Q: LLM なしでも動く？

A: はい。Ollama がない場合は自動的にシンプルなテンプレート生成にフォールバックします。

### Q: リレーは変更できる？

A: はい。`.env`の`NOSTR_RELAYS`を編集してください。

### Q: 鍵を再生成したい

A:

```bash
rm bots/keys.json
python scripts/generate_keys.py
```

**注意**: 新しい鍵になるため、以前の投稿とは別のアカウントになります。

### Q: ボットの行動を変更するには？

A: `bots/profiles/botXXX.yaml`を編集して、アプリケーションを再起動してください。
