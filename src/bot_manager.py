"""
ボット管理システムのメインモジュール
"""
import asyncio
import json
import random
from datetime import datetime
from pathlib import Path
from typing import Optional

import httpx
import yaml
from nostr_sdk import Event, EventBuilder, Keys, Kind, Tag

from .llm import LLMClient
from .types import Background, Behavior, BotKey, BotProfile, BotState, Interests, Personality, Social


class BotManager:
    """ボット管理クラス"""
    
    def __init__(
        self,
        profiles_dir: Path,
        states_file: Path,
        api_endpoint: str,
        relays: list[str],
        llm_client: Optional[LLMClient] = None,
        dry_run: bool = False,
    ):
        self.profiles_dir = profiles_dir
        self.states_file = states_file
        self.api_endpoint = api_endpoint
        self.relays = relays
        self.llm_client = llm_client
        self.dry_run = dry_run
        
        self.bots: dict[int, tuple[BotKey, BotProfile, BotState]] = {}
        self.keys: dict[int, Keys] = {}  # Nostr署名鍵
    
    async def load_bots(self) -> None:
        """ボットのデータを読み込み"""
        print("Loading bot profiles...")
        
        # プロフィールディレクトリからYAMLファイルを検索
        profile_files = sorted(self.profiles_dir.glob("bot*.yaml"))
        
        if not profile_files:
            print("⚠️  No bot profiles found in bots/profiles/")
            return
        
        for profile_file in profile_files:
            try:
                # プロフィール読み込み
                bot_profile = self._load_profile(profile_file)
                bot_id = bot_profile.id
                
                # 環境変数から鍵を読み込み
                try:
                    bot_key = BotKey.from_env(bot_id)
                except Exception as e:
                    print(f"⚠️  Keys not found for {profile_file.name}: {e}, skipping...")
                    continue
                
                # 状態読み込み（存在しない場合は初期化）
                bot_state = self._load_or_create_state(bot_id)
                
                self.bots[bot_id] = (bot_key, bot_profile, bot_state)
            except Exception as e:
                print(f"⚠️  Failed to load {profile_file.name}: {e}, skipping...")
                continue
        
        print(f"✅ Loaded {len(self.bots)} bots")
    
    def _load_profile(self, profile_file: Path) -> BotProfile:
        """YAMLからプロフィールを読み込み"""
        try:
            with open(profile_file) as f:
                data = yaml.safe_load(f)
            
            # Pydanticでバリデーション
            profile = BotProfile.model_validate(data)
            return profile
        except Exception as e:
            raise ValueError(f"Failed to load profile from {profile_file}: {e}") from e
    
    def _load_or_create_state(self, bot_id: int) -> BotState:
        """状態を読み込み、存在しない場合は初期化"""
        if self.states_file.exists():
            try:
                with open(self.states_file) as f:
                    states_data = json.load(f)
                
                for state_dict in states_data:
                    if state_dict["id"] == bot_id:
                        # Pydanticでバリデーション
                        return BotState.model_validate(state_dict)
            except Exception as e:
                print(f"⚠️  Failed to load state for bot {bot_id}: {e}")
        
        # 新規作成
        return BotState(
            id=bot_id,
            last_post_time=0,
            next_post_time=0,
            total_posts=0,
        )
    
    def _save_states(self) -> None:
        """全ボットの状態を保存"""
        states_data = []
        for _, _, state in self.bots.values():
            # Pydanticのmodel_dumpを使用
            states_data.append(state.model_dump(mode='json'))
        
        with open(self.states_file, "w") as f:
            json.dump(states_data, f, indent=2, ensure_ascii=False)
    
    async def initialize_keys(self) -> None:
        """Nostr署名鍵を初期化"""
        print("Initializing Nostr keys...")
        for bot_id, (key, _, _) in self.bots.items():
            try:
                keys = Keys.parse(key.nsec)
                self.keys[bot_id] = keys
            except Exception as e:
                print(f"⚠️  Failed to parse key for bot {bot_id}: {e}")
        
        print(f"✅ Initialized {len(self.keys)} bot keys")
    
    def should_post_now(self, bot_id: int) -> bool:
        """このボットが今投稿すべきかを判定"""
        _, profile, state = self.bots[bot_id]
        
        current_time = int(datetime.now().timestamp())
        current_hour = datetime.now().hour
        
        # 活動時間帯かチェック
        if current_hour not in profile.behavior.active_hours:
            return False
        
        # 次回投稿時刻が未設定または過去の場合は投稿
        if state.next_post_time == 0 or current_time >= state.next_post_time:
            return True
        
        return False
    
    def _calculate_next_post_time(self, bot_id: int) -> int:
        """次回投稿時刻を計算"""
        _, profile, _ = self.bots[bot_id]
        
        # 1日の投稿頻度から平均間隔を計算（秒）
        avg_interval = 86400 / profile.behavior.post_frequency
        
        # ばらつきを考慮した実際の間隔
        variance = profile.behavior.post_frequency_variance
        actual_interval = avg_interval * random.uniform(1 - variance, 1 + variance)
        
        current_time = int(datetime.now().timestamp())
        next_time = current_time + int(actual_interval)
        
        return next_time
    
    async def generate_post_content(self, bot_id: int) -> str:
        """投稿内容を生成"""
        _, profile, _ = self.bots[bot_id]
        
        if not self.llm_client:
            raise RuntimeError("LLM client is not available")
        
        import re
        
        # 最大3回までリトライ
        for attempt in range(3):
            # LLMを使って生成
            prompt = self._create_prompt(profile)
            content = await self.llm_client.generate(
                prompt,
                max_length=profile.behavior.post_length_max
            )
            
            # 余計な記号を削除
            content = content.replace("###", "").replace("```", "").strip()
            
            # 改行を整理（2つ以上の連続改行は1つに）
            content = re.sub(r'\n{2,}', '\n', content)
            
            # 連続空白を1つに
            content = re.sub(r'\s+', ' ', content).strip()
            
            # 中国語文字チェック（簡体字・繁体字）
            if re.search(r'[\u4e00-\u9fff]', content):
                print(f"⚠️  Retry {attempt + 1}/3: Chinese characters detected")
                continue
            
            # 禁止文字チェック
            if '```' in content or '###' in content:
                print(f"⚠️  Retry {attempt + 1}/3: Forbidden characters detected")
                continue
            
            # 検証OK
            break
        else:
            # リトライ失敗
            raise RuntimeError("Failed to generate valid content after 3 attempts")
        
        # 長さチェック
        if len(content) < profile.behavior.post_length_min:
            # 最小長に満たない場合は補完
            content = content + " " * (profile.behavior.post_length_min - len(content))
        elif len(content) > profile.behavior.post_length_max:
            # 最大長を超える場合はトリミング
            content = content[:profile.behavior.post_length_max].rsplit(" ", 1)[0] + "..."
        
        return content
    
    def _create_prompt(self, profile: BotProfile) -> str:
        """LLM用のプロンプトを生成"""
        topic = profile.interests.topics[0] if profile.interests.topics else "プログラミング"
        
        prompt = f"""以下の条件でSNS投稿を1つ書け:

テーマ: {topic}
文字数: 最大{profile.behavior.post_length_max}文字
条件: 1文か2文のカジュアルな日本語、記号禁止

投稿:"""
        
        return prompt
    
    async def post(self, bot_id: int, content: str) -> None:
        """投稿を実行（MYPACE API経由）"""
        try:
            _, profile, state = self.bots[bot_id]
            
            # 投稿内容のバリデーション
            if not content or len(content.strip()) == 0:
                raise ValueError("Post content is empty")
            
            # Dry runモード
            if self.dry_run:
                print(f"[DRY RUN] {profile.name}:")
                print(f"  {content}")
                print()
                return
            
            # 以下は実際の投稿処理
            keys = self.keys[bot_id]
            
            # イベント作成（kind:1、署名済み）
            # Nostr event: kind=1 (text note), tags, content
            from nostr_sdk import EventBuilder
            
            # タグを作成
            mypace_tag = Tag.hashtag("mypace")
            client_tag = Tag.parse(["client", "sinov"])
            
            # EventBuilderの正しいAPI: text_note().tags([...]).sign_with_keys()
            event = EventBuilder.text_note(content).tags([mypace_tag, client_tag]).sign_with_keys(keys)
            
            # NostrイベントをJSON化
            event_json = json.loads(event.as_json())
            
            # MYPACE APIに送信 (SSL検証を無効化、プロキシ設定は環境変数から自動取得)
            async with httpx.AsyncClient(timeout=30.0, verify=False, trust_env=True) as client:
                response = await client.post(
                    f"{self.api_endpoint}/api/publish",
                    json={"event": event_json},
                    headers={"Content-Type": "application/json"},
                )
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get("content-type") == "application/json" else {}
                    raise RuntimeError(f"API error: {response.status_code} - {error_data}")
                
                result = response.json()
                if not result.get("success"):
                    raise RuntimeError(f"Publish failed: {result}")
            
            # 状態を更新
            current_time = int(datetime.now().timestamp())
            state.last_post_time = current_time
            state.next_post_time = self._calculate_next_post_time(bot_id)
            state.total_posts += 1
            state.last_post_content = content
            state.last_event_id = event.id().to_hex()
            
            next_datetime = datetime.fromtimestamp(state.next_post_time)
            print(f"📝 {profile.name} posted: {content[:50]}... (next: {next_datetime.strftime('%H:%M:%S')})")
        except Exception as e:
            _, profile, _ = self.bots[bot_id]
            print(f"❌ Failed to post for {profile.name}: {e}")
            raise
    
    async def run_once(self) -> None:
        """全ボットをチェックして投稿が必要なら投稿"""
        for bot_id in self.bots.keys():
            if self.should_post_now(bot_id):
                try:
                    content = await self.generate_post_content(bot_id)
                    await self.post(bot_id, content)
                except Exception as e:
                    _, profile, _ = self.bots[bot_id]
                    print(f"❌ Error posting for {profile.name}: {e}")
        
        # 状態を保存
        self._save_states()
    
    async def run_forever(self, check_interval: int = 60) -> None:
        """定期的に投稿をチェックして実行（メインループ）"""
        print(f"\n🤖 Starting bot manager (checking every {check_interval}s)...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                await self.run_once()
                await asyncio.sleep(check_interval)
        except KeyboardInterrupt:
            print("\n\n🛑 Shutting down...")
            self._save_states()
