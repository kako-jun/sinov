"""
相互作用サービス（リプライ・リアクション処理）
"""

from datetime import datetime

from ..config import AffinitySettings
from ..domain import (
    ActivityLogger,
    ContentStrategy,
    NpcProfile,
    NpcState,
    ParameterChange,
    PersonalityAnalyzer,
    PostType,
    QueueEntry,
    QueueStatus,
    TextProcessor,
    format_npc_name,
)
from ..domain.interaction import InteractionManager
from ..domain.models import NpcKey
from ..domain.queue import ConversationContext, ReplyTarget
from ..infrastructure import (
    LLMProvider,
    LogRepository,
    MemoryRepository,
    ProfileRepository,
    QueueRepository,
)
from ..infrastructure.storage.relationship_repo import RelationshipRepository
from .affinity_service import AffinityService


class InteractionService:
    """住人間の相互作用を処理するサービス"""

    def __init__(
        self,
        llm_provider: LLMProvider | None,
        queue_repo: QueueRepository,
        relationship_repo: RelationshipRepository,
        content_strategy: ContentStrategy,
        npcs: dict[int, tuple[NpcKey, NpcProfile, NpcState]],
        memory_repo: MemoryRepository | None = None,
        affinity_settings: AffinitySettings | None = None,
        profile_repo: ProfileRepository | None = None,
        log_repo: LogRepository | None = None,
    ):
        self.llm_provider = llm_provider
        self.queue_repo = queue_repo
        self.relationship_repo = relationship_repo
        self.content_strategy = content_strategy
        self.npcs = npcs
        self.memory_repo = memory_repo
        self.affinity_settings = affinity_settings or AffinitySettings()
        self.profile_repo = profile_repo
        self.log_repo = log_repo

        # 関係性データを読み込み
        self.relationship_data = relationship_repo.load_all()
        self.interaction_manager = InteractionManager(self.relationship_data)

        # 好感度サービス
        self.affinity_service = AffinityService(
            relationship_repo=relationship_repo,
            queue_repo=queue_repo,
            relationship_data=self.relationship_data,
            affinity_settings=self.affinity_settings,
        )

    async def process_interactions(self, target_npc_ids: list[int]) -> int:
        """
        指定された住人に対して相互作用処理を実行

        Args:
            target_npc_ids: 処理対象の住人ID一覧

        Returns:
            生成されたリプライ/リアクション数
        """
        if not self.llm_provider:
            return 0

        # 投稿済みエントリーを取得
        posted_entries = self.queue_repo.get_all(QueueStatus.POSTED)

        if not posted_entries:
            return 0

        generated = 0

        for npc_id in target_npc_ids:
            if npc_id not in self.npcs:
                continue

            _, profile, _ = self.npcs[npc_id]
            npc_name = format_npc_name(npc_id)

            # 好感度を読み込み
            affinity = self.relationship_repo.load_affinity(npc_name)

            # 他住人の投稿をチェック
            for entry in posted_entries:
                # 自分の投稿はスキップ
                if entry.npc_id == npc_id:
                    continue

                # event_idがない投稿はスキップ（Nostrに投稿されていない）
                if not entry.event_id:
                    continue

                # 既にリプライ済みの投稿はスキップ（同一event_idへの重複防止）
                if self._already_replied(npc_id, entry.event_id):
                    continue

                target_bot_name = f"npc{entry.npc_id:03d}"
                target_affinity = affinity.get_affinity(target_bot_name)

                # 社交性パラメータを取得
                sociability = 0.5  # デフォルト
                if profile.traits_detail:
                    sociability = profile.traits_detail.sociability

                # 反応すべきか判定
                should_react, reaction_type = self.interaction_manager.should_react_to_post(
                    from_bot=npc_name,
                    to_bot=target_bot_name,
                    post_content=entry.content,
                    affinity=target_affinity,
                    sociability=sociability,
                )

                if not should_react:
                    continue

                if reaction_type == "reply":
                    # リプライを生成
                    new_entry = await self._generate_reply(
                        npc_id,
                        profile,
                        entry,
                        target_affinity,
                    )
                    if new_entry:
                        self.queue_repo.add(new_entry)
                        # 好感度を更新（元投稿者 → リプライした人）
                        old_affinity = target_affinity
                        self.affinity_service.update_on_interaction(npc_id, entry.npc_id, "reply")
                        new_affinity = self._get_affinity(entry.npc_id, npc_id)
                        # 記憶を強化（元投稿者の記憶）
                        self._update_memory_on_feedback(entry.npc_id, entry.content, "reply")
                        # 気分を更新（元投稿者）
                        old_mood = self._get_mood(entry.npc_id)
                        self._update_mood_on_feedback(entry.npc_id, "reply")
                        new_mood = self._get_mood(entry.npc_id)
                        generated += 1
                        print(f"      💬 {profile.name} → {entry.npc_name}")

                        # ログ記録
                        if self.log_repo:
                            rel_type = self._get_relationship_type(npc_name, target_bot_name)
                            # 送信側のログ（リプライ送信）
                            self.log_repo.add_entry(
                                npc_id,
                                ActivityLogger.log_reply_sent(
                                    entry.npc_name,
                                    new_entry.content,
                                    rel_type,
                                ),
                            )
                            # 受信側のログ（リプライ受信 + パラメータ変化）
                            changes = []
                            if old_affinity != new_affinity:
                                changes.append(ParameterChange(
                                    name="好感度",
                                    old_value=old_affinity,
                                    new_value=new_affinity,
                                    reason="リプライを受けた",
                                    target=profile.name,
                                ))
                            if old_mood != new_mood:
                                changes.append(ParameterChange(
                                    name="気分",
                                    old_value=old_mood,
                                    new_value=new_mood,
                                    reason="リプライを受けた",
                                ))
                            self.log_repo.add_entry(
                                entry.npc_id,
                                ActivityLogger.log_reply_received(
                                    profile.name,
                                    new_entry.content,
                                    rel_type,
                                    changes,
                                ),
                            )

                elif reaction_type == "reaction":
                    # リアクションを生成
                    new_entry = self._generate_reaction(
                        npc_id,
                        profile,
                        entry,
                    )
                    if new_entry:
                        self.queue_repo.add(new_entry)
                        # 好感度を更新（元投稿者 → リアクションした人）
                        old_affinity = target_affinity
                        self.affinity_service.update_on_interaction(
                            npc_id, entry.npc_id, "reaction"
                        )
                        new_affinity = self._get_affinity(entry.npc_id, npc_id)
                        # 記憶を強化（元投稿者の記憶）
                        self._update_memory_on_feedback(entry.npc_id, entry.content, "reaction")
                        # 気分を更新（元投稿者）
                        old_mood = self._get_mood(entry.npc_id)
                        self._update_mood_on_feedback(entry.npc_id, "reaction")
                        new_mood = self._get_mood(entry.npc_id)
                        generated += 1
                        print(f"      ❤️  {profile.name} → {entry.npc_name}")

                        # ログ記録
                        if self.log_repo:
                            emoji = new_entry.content  # リアクションは絵文字
                            # 送信側のログ
                            self.log_repo.add_entry(
                                npc_id,
                                ActivityLogger.log_reaction_sent(
                                    entry.npc_name, emoji, entry.content
                                ),
                            )
                            # 受信側のログ
                            changes = []
                            if old_affinity != new_affinity:
                                changes.append(ParameterChange(
                                    name="好感度",
                                    old_value=old_affinity,
                                    new_value=new_affinity,
                                    reason="リアクションを受けた",
                                    target=profile.name,
                                ))
                            if old_mood != new_mood:
                                changes.append(ParameterChange(
                                    name="気分",
                                    old_value=old_mood,
                                    new_value=new_mood,
                                    reason="リアクションを受けた",
                                ))
                            self.log_repo.add_entry(
                                entry.npc_id,
                                ActivityLogger.log_reaction_received(
                                    profile.name, emoji, entry.content, changes
                                ),
                            )

        return generated

    def _already_replied(self, npc_id: int, event_id: str | None) -> bool:
        """既にリプライ済みかチェック"""
        if not event_id:
            return False

        # pending, approved, posted を全てチェック
        for status in [QueueStatus.PENDING, QueueStatus.APPROVED, QueueStatus.POSTED]:
            entries = self.queue_repo.get_all(status)
            for entry in entries:
                if (
                    entry.npc_id == npc_id
                    and entry.reply_to
                    and entry.reply_to.event_id == event_id
                ):
                    return True
        return False

    async def _generate_reply(
        self,
        npc_id: int,
        profile: NpcProfile,
        target_entry: QueueEntry,
        affinity: float,
    ) -> QueueEntry | None:
        """リプライを生成"""
        if not self.llm_provider:
            return None

        # リプライ先情報を作成
        reply_to = ReplyTarget(
            resident=f"npc{target_entry.npc_id:03d}",
            event_id=target_entry.event_id or "",
            content=target_entry.content,
        )

        # 関係タイプを取得
        npc_name = format_npc_name(npc_id)
        relationship_type = self._get_relationship_type(npc_name, f"npc{target_entry.npc_id:03d}")

        # マージ済みプロンプトを取得
        merged_prompts = None
        if self.profile_repo:
            merged_prompts = self.profile_repo.get_merged_prompts(profile)

        # プロンプト生成
        prompt = self.content_strategy.create_reply_prompt(
            profile=profile,
            reply_to=reply_to,
            conversation=None,  # 新規リプライなのでコンテキストなし
            relationship_type=relationship_type,
            affinity=affinity,
            merged_prompts=merged_prompts,
        )

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # 文章スタイル加工
        if profile.writing_style:
            text_processor = TextProcessor(profile.writing_style)
            content = text_processor.process(content)

        # 会話コンテキストを作成
        conversation = ConversationContext(
            thread_id=target_entry.event_id or target_entry.id,
            depth=1,
            history=[
                {
                    "author": target_entry.npc_name,
                    "content": target_entry.content,
                    "depth": 0,
                }
            ],
        )

        return QueueEntry(
            npc_id=npc_id,
            npc_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.REPLY,
            reply_to=reply_to,
            conversation=conversation,
        )

    def _generate_reaction(
        self,
        npc_id: int,
        profile: NpcProfile,
        target_entry: QueueEntry,
    ) -> QueueEntry | None:
        """リアクションを生成"""
        # 性格に応じた絵文字を選択
        personality_type = self._get_personality_type(profile)
        emoji = self.interaction_manager.select_reaction_emoji(
            target_entry.content, personality_type
        )

        reply_to = ReplyTarget(
            resident=f"npc{target_entry.npc_id:03d}",
            event_id=target_entry.event_id or "",
            content="",  # リアクションでは内容不要
        )

        return QueueEntry(
            npc_id=npc_id,
            npc_name=profile.name,
            content=emoji,
            status=QueueStatus.PENDING,
            post_type=PostType.REACTION,
            reply_to=reply_to,
        )

    def _get_relationship_type(self, from_bot: str, to_bot: str) -> str:
        """2人の関係タイプを取得"""
        # ペア関係をチェック
        for pair in self.relationship_data.pairs:
            if from_bot in pair.members and to_bot in pair.members:
                type_names = {
                    "close_friends": "親しい友人",
                    "couple": "恋人",
                    "siblings": "兄弟",
                    "rivals": "ライバル",
                    "mentor": "師弟",
                    "awkward": "微妙な関係",
                }
                return type_names.get(pair.type.value, "知り合い")

        # グループ関係をチェック
        for group in self.relationship_data.groups:
            if from_bot in group.members and to_bot in group.members:
                return f"{group.name}の仲間"

        return "知り合い"

    def _get_personality_type(self, profile: NpcProfile) -> str:
        """プロフィールから性格タイプを推定（PersonalityAnalyzerに委譲）"""
        return PersonalityAnalyzer.classify(profile)

    def _update_memory_on_feedback(
        self,
        npc_id: int,
        original_content: str,
        interaction_type: str,
    ) -> None:
        """
        リプライ/リアクションをもらった時に記憶を強化

        Args:
            npc_id: 元投稿者のNPC ID（記憶が強化される側）
            original_content: 元投稿の内容
            interaction_type: "reply" or "reaction"
        """
        if not self.memory_repo:
            return

        # 元投稿者の記憶を読み込み
        memory = self.memory_repo.load(npc_id)

        # feedback_sensitivityを取得（元投稿者のプロファイルから）
        feedback_sensitivity = 0.5  # デフォルト
        if npc_id in self.npcs:
            _, profile, _ = self.npcs[npc_id]
            if profile.traits_detail:
                feedback_sensitivity = profile.traits_detail.feedback_sensitivity

        # 記憶の強化量
        if interaction_type == "reply":
            boost = 0.3  # リプライは強い反応
        elif interaction_type == "reaction":
            boost = 0.15  # リアクションは軽い反応
        else:
            return

        # 元投稿の内容に関連する短期記憶を強化
        # キーワードを抽出（単純に単語分割）
        keywords = original_content.split()[:5]  # 最初の5単語
        reinforced = False

        for keyword in keywords:
            if len(keyword) >= 2:  # 短すぎる単語は除外
                if memory.reinforce_short_term(keyword, boost, feedback_sensitivity):
                    reinforced = True

        # 元投稿自体も強化
        if memory.reinforce_short_term(original_content[:20], boost, feedback_sensitivity):
            reinforced = True

        # 昇格チェック
        promoted = memory.check_and_promote(threshold=0.95)

        # 記憶を保存
        if reinforced or promoted:
            memory.last_updated = datetime.now().isoformat()
            self.memory_repo.save(memory)

        # ログ出力
        if promoted:
            for content in promoted:
                print(f"         🧠 長期記憶に昇格: {content[:30]}...")

    def _update_mood_on_feedback(
        self,
        npc_id: int,
        interaction_type: str,
    ) -> None:
        """
        リプライ/リアクションをもらった時に気分を更新

        Args:
            npc_id: 元投稿者のNPC ID（気分が上がる側）
            interaction_type: "reply" or "reaction"
        """
        if npc_id not in self.npcs:
            return

        key, profile, state = self.npcs[npc_id]

        # 気分の変動量
        if interaction_type == "reply":
            delta = self.affinity_settings.mood_reply
        elif interaction_type == "reaction":
            delta = self.affinity_settings.mood_reaction
        else:
            return

        old_mood = state.mood
        new_mood = max(-1.0, min(1.0, state.mood + delta))
        state.mood = new_mood

        # NPCデータを更新（stateは参照なので自動的に反映）
        if new_mood != old_mood:
            print(f"         😊 bot{npc_id:03d}の気分: {old_mood:.2f} → {new_mood:.2f}")

    def _get_mood(self, npc_id: int) -> float:
        """NPCの現在の気分を取得"""
        if npc_id not in self.npcs:
            return 0.0
        _, _, state = self.npcs[npc_id]
        return state.mood

    def _get_affinity(self, from_bot_id: int, to_bot_id: int) -> float:
        """NPC間の好感度を取得"""
        from_name = format_npc_name(from_bot_id)
        to_name = format_npc_name(to_bot_id)
        affinity_map = self.relationship_repo.load_affinity(from_name)
        return affinity_map.get_affinity(to_name)

    async def process_reply_chains(self, target_npc_ids: list[int]) -> int:
        """
        既存の会話スレッドへの返信を処理

        Returns:
            生成された返信数
        """
        if not self.llm_provider:
            return 0

        # 自分宛のリプライ（posted）を探して返信を検討
        posted_entries = self.queue_repo.get_all(QueueStatus.POSTED)
        reply_entries = [e for e in posted_entries if e.post_type == PostType.REPLY]

        generated = 0

        for entry in reply_entries:
            if not entry.reply_to:
                continue

            # リプライ先のNPC IDを取得
            target_bot_name = entry.reply_to.resident
            if not target_bot_name.startswith("npc"):
                continue

            try:
                target_bot_id = int(target_bot_name[3:])
            except ValueError:
                continue

            # 処理対象でなければスキップ
            if target_bot_id not in target_npc_ids:
                continue

            if target_bot_id not in self.npcs:
                continue

            _, profile, _ = self.npcs[target_bot_id]

            # event_idがない投稿はスキップ
            if not entry.event_id:
                continue

            # 既に返信済みかチェック
            if self._already_replied(target_bot_id, entry.event_id):
                continue

            # 会話の深さを取得
            depth = entry.conversation.depth if entry.conversation else 1

            # 好感度を読み込み
            affinity = self.relationship_repo.load_affinity(target_bot_name)
            from_affinity = affinity.get_affinity(f"npc{entry.npc_id:03d}")

            # 会話を続けるか判定
            should_continue = self.interaction_manager.should_continue_conversation(
                from_bot=target_bot_name,
                to_bot=f"npc{entry.npc_id:03d}",
                incoming_content=entry.content,
                depth=depth,
                affinity=from_affinity,
            )

            if not should_continue:
                continue

            # 返信を生成
            reply_entry = await self._generate_chain_reply(
                target_bot_id,
                profile,
                entry,
                from_affinity,
            )

            if reply_entry:
                self.queue_repo.add(reply_entry)
                # 好感度を更新（リプライを送ってきた人 → 返信した人）
                self.affinity_service.update_on_interaction(target_bot_id, entry.npc_id, "reply")
                # 記憶を強化（リプライを送ってきた人の記憶）
                self._update_memory_on_feedback(entry.npc_id, entry.content, "reply")
                generated += 1
                print(f"      💬 {profile.name} ↩️ {entry.npc_name}")

        return generated

    async def _generate_chain_reply(
        self,
        npc_id: int,
        profile: NpcProfile,
        incoming_entry: QueueEntry,
        affinity: float,
    ) -> QueueEntry | None:
        """会話チェーンへの返信を生成"""
        if not self.llm_provider:
            return None

        # 会話コンテキストを更新
        existing_conv = incoming_entry.conversation
        new_depth = (existing_conv.depth + 1) if existing_conv else 1

        new_history = existing_conv.history.copy() if existing_conv else []
        new_history.append(
            {
                "author": incoming_entry.npc_name,
                "content": incoming_entry.content,
                "depth": existing_conv.depth if existing_conv else 0,
            }
        )

        conversation = ConversationContext(
            thread_id=existing_conv.thread_id if existing_conv else incoming_entry.id,
            depth=new_depth,
            history=new_history,
        )

        # リプライ先情報
        reply_to = ReplyTarget(
            resident=f"npc{incoming_entry.npc_id:03d}",
            event_id=incoming_entry.event_id or "",
            content=incoming_entry.content,
        )

        # 関係タイプを取得
        npc_name = format_npc_name(npc_id)
        relationship_type = self._get_relationship_type(npc_name, f"npc{incoming_entry.npc_id:03d}")

        # マージ済みプロンプトを取得
        merged_prompts = None
        if self.profile_repo:
            merged_prompts = self.profile_repo.get_merged_prompts(profile)

        # プロンプト生成
        prompt = self.content_strategy.create_reply_prompt(
            profile=profile,
            reply_to=reply_to,
            conversation=conversation,
            relationship_type=relationship_type,
            affinity=affinity,
            merged_prompts=merged_prompts,
        )

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # 文章スタイル加工
        if profile.writing_style:
            text_processor = TextProcessor(profile.writing_style)
            content = text_processor.process(content)

        return QueueEntry(
            npc_id=npc_id,
            npc_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.REPLY,
            reply_to=reply_to,
            conversation=conversation,
        )

    def process_affinity_decay(self, target_npc_ids: list[int]) -> int:
        """好感度の減衰処理を実行（AffinityServiceに委譲）"""
        return self.affinity_service.process_decay(target_npc_ids, self.npcs)

    def process_ignored_posts(self, target_npc_ids: list[int]) -> int:
        """無視された投稿による好感度減衰を処理（AffinityServiceに委譲）"""
        return self.affinity_service.process_ignored_posts(target_npc_ids)
