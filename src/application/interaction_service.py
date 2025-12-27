"""
相互作用サービス（リプライ・リアクション処理）

ファサードとして各コンポーネントを組み合わせる
"""

from __future__ import annotations

from ..config import AffinitySettings
from ..domain import (
    Affinity,
    ContentStrategy,
    InteractionManager,
    NpcKey,
    NpcProfile,
    NpcState,
    PersonalityAnalyzer,
    PostType,
    QueueEntry,
    QueueStatus,
    format_npc_name,
)
from ..infrastructure import (
    LLMProvider,
    LogRepository,
    MemoryRepository,
    ProfileRepository,
    QueueRepository,
    RelationshipRepository,
)
from .affinity_service import AffinityService
from .interaction import FeedbackHandler, ReactionGenerator, ReplyGenerator


class InteractionService:
    """住人間の相互作用を処理するサービス（ファサード）"""

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

        # 分割されたコンポーネント
        self.reply_generator = ReplyGenerator(
            llm_provider=llm_provider,
            content_strategy=content_strategy,
            profile_repo=profile_repo,
        )
        self.reaction_generator = ReactionGenerator(
            interaction_manager=self.interaction_manager,
        )
        self.feedback_handler = FeedbackHandler(
            memory_repo=memory_repo,
            log_repo=log_repo,
            affinity_settings=self.affinity_settings,
            npcs=npcs,
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

        posted_entries = self.queue_repo.get_all(QueueStatus.POSTED)
        if not posted_entries:
            return 0

        generated = 0
        for npc_id in target_npc_ids:
            generated += await self._process_npc_interactions(npc_id, posted_entries)
        return generated

    async def _process_npc_interactions(self, npc_id: int, posted_entries: list[QueueEntry]) -> int:
        """単一NPCの相互作用処理"""
        if npc_id not in self.npcs:
            return 0

        _, profile, _ = self.npcs[npc_id]
        npc_name = format_npc_name(npc_id)
        affinity = self.relationship_repo.load_affinity(npc_name)
        sociability = self._get_sociability(profile)

        generated = 0
        for entry in posted_entries:
            generated += await self._process_single_entry(
                npc_id, profile, npc_name, affinity, sociability, entry
            )
        return generated

    def _get_sociability(self, profile: NpcProfile) -> float:
        """社交性パラメータを取得"""
        if profile.traits_detail:
            return profile.traits_detail.sociability
        return 0.5

    def _should_process_entry(self, npc_id: int, entry: QueueEntry) -> bool:
        """エントリーを処理すべきかを判定"""
        if entry.npc_id == npc_id:
            return False
        if not entry.event_id:
            return False
        if self._already_replied(npc_id, entry.event_id):
            return False
        return True

    async def _process_single_entry(
        self,
        npc_id: int,
        profile: NpcProfile,
        npc_name: str,
        affinity: "Affinity",
        sociability: float,
        entry: QueueEntry,
    ) -> int:
        """単一エントリーへの反応処理"""
        if not self._should_process_entry(npc_id, entry):
            return 0

        target_bot_name = f"npc{entry.npc_id:03d}"
        target_affinity = affinity.get_affinity(target_bot_name)

        should_react, reaction_type = self.interaction_manager.should_react_to_post(
            from_bot=npc_name,
            to_bot=target_bot_name,
            post_content=entry.content,
            affinity=target_affinity,
            sociability=sociability,
        )

        if not should_react:
            return 0

        if reaction_type == "reply":
            return await self._handle_reply(
                npc_id, profile, entry, target_affinity, npc_name, target_bot_name
            )
        if reaction_type == "reaction":
            return self._handle_reaction(npc_id, profile, entry, npc_name)
        return 0

    async def _handle_reply(
        self,
        npc_id: int,
        profile: NpcProfile,
        entry: QueueEntry,
        target_affinity: float,
        npc_name: str,
        target_bot_name: str,
    ) -> int:
        """リプライ処理"""
        relationship_type = self._get_relationship_type(npc_name, target_bot_name)

        new_entry = await self.reply_generator.generate_reply(
            npc_id,
            profile,
            entry,
            target_affinity,
            relationship_type,
        )
        if not new_entry:
            return 0

        self.queue_repo.add(new_entry)

        # 好感度を更新（元投稿者 → リプライした人）
        old_affinity = target_affinity
        self.affinity_service.update_on_interaction(npc_id, entry.npc_id, "reply")
        new_affinity = self._get_affinity(entry.npc_id, npc_id)

        # 記憶を強化（元投稿者の記憶）
        self.feedback_handler.update_memory_on_feedback(entry.npc_id, entry.content, "reply")

        # 気分を更新（元投稿者）
        old_mood = self.feedback_handler.get_mood(entry.npc_id)
        self.feedback_handler.update_mood_on_feedback(entry.npc_id, "reply")
        new_mood = self.feedback_handler.get_mood(entry.npc_id)

        # 状態パラメータを更新（元投稿者）
        state_changes = self.feedback_handler.update_state_on_feedback(entry.npc_id, "reply")

        print(f"      💬 {profile.name} → {entry.npc_name}")

        # ログ記録
        self.feedback_handler.log_reply_interaction(
            sender_npc_id=npc_id,
            receiver_npc_id=entry.npc_id,
            sender_name=profile.name,
            receiver_name=entry.npc_name,
            content=new_entry.content,
            relationship_type=relationship_type,
            old_affinity=old_affinity,
            new_affinity=new_affinity,
            old_mood=old_mood,
            new_mood=new_mood,
            state_changes=state_changes,
        )

        return 1

    def _handle_reaction(
        self,
        npc_id: int,
        profile: NpcProfile,
        entry: QueueEntry,
        npc_name: str,
    ) -> int:
        """リアクション処理"""
        personality_type = PersonalityAnalyzer.classify(profile)

        new_entry = self.reaction_generator.generate_reaction(
            npc_id,
            profile,
            entry,
            personality_type,
        )
        if not new_entry:
            return 0

        self.queue_repo.add(new_entry)

        # 好感度を更新（元投稿者 → リアクションした人）
        target_bot_name = f"npc{entry.npc_id:03d}"
        affinity_map = self.relationship_repo.load_affinity(npc_name)
        old_affinity = affinity_map.get_affinity(target_bot_name)
        self.affinity_service.update_on_interaction(npc_id, entry.npc_id, "reaction")
        new_affinity = self._get_affinity(entry.npc_id, npc_id)

        # 記憶を強化（元投稿者の記憶）
        self.feedback_handler.update_memory_on_feedback(entry.npc_id, entry.content, "reaction")

        # 気分を更新（元投稿者）
        old_mood = self.feedback_handler.get_mood(entry.npc_id)
        self.feedback_handler.update_mood_on_feedback(entry.npc_id, "reaction")
        new_mood = self.feedback_handler.get_mood(entry.npc_id)

        # 状態パラメータを更新（元投稿者）
        state_changes = self.feedback_handler.update_state_on_feedback(entry.npc_id, "reaction")

        print(f"      ❤️  {profile.name} → {entry.npc_name}")

        # ログ記録
        self.feedback_handler.log_reaction_interaction(
            sender_npc_id=npc_id,
            receiver_npc_id=entry.npc_id,
            sender_name=profile.name,
            original_content=entry.content,
            emoji=new_entry.content,
            old_affinity=old_affinity,
            new_affinity=new_affinity,
            old_mood=old_mood,
            new_mood=new_mood,
            state_changes=state_changes,
        )

        return 1

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

        posted_entries = self.queue_repo.get_all(QueueStatus.POSTED)
        reply_entries = [e for e in posted_entries if e.post_type == PostType.REPLY]

        generated = 0
        for entry in reply_entries:
            generated += await self._process_chain_entry(entry, target_npc_ids)
        return generated

    def _extract_target_bot_id(self, entry: QueueEntry) -> int | None:
        """リプライ先のNPC IDを抽出"""
        if not entry.reply_to:
            return None
        target_bot_name = entry.reply_to.resident
        if not target_bot_name.startswith("npc"):
            return None
        try:
            return int(target_bot_name[3:])
        except ValueError:
            return None

    def _should_process_chain(
        self, target_bot_id: int, entry: QueueEntry, target_npc_ids: list[int]
    ) -> bool:
        """チェーンリプライを処理すべきかを判定"""
        if target_bot_id not in target_npc_ids:
            return False
        if target_bot_id not in self.npcs:
            return False
        if not entry.event_id:
            return False
        if self._already_replied(target_bot_id, entry.event_id):
            return False
        return True

    async def _process_chain_entry(self, entry: QueueEntry, target_npc_ids: list[int]) -> int:
        """単一のチェーンエントリーを処理"""
        target_bot_id = self._extract_target_bot_id(entry)
        if target_bot_id is None:
            return 0

        if not self._should_process_chain(target_bot_id, entry, target_npc_ids):
            return 0

        _, profile, _ = self.npcs[target_bot_id]
        target_bot_name = f"npc{target_bot_id:03d}"
        sender_name = f"npc{entry.npc_id:03d}"

        # 会話を続けるか判定
        depth = entry.conversation.depth if entry.conversation else 1
        affinity = self.relationship_repo.load_affinity(target_bot_name)
        from_affinity = affinity.get_affinity(sender_name)

        should_continue = self.interaction_manager.should_continue_conversation(
            from_bot=target_bot_name,
            to_bot=sender_name,
            incoming_content=entry.content,
            depth=depth,
            affinity=from_affinity,
        )
        if not should_continue:
            return 0

        # 返信を生成
        relationship_type = self._get_relationship_type(target_bot_name, sender_name)
        reply_entry = await self.reply_generator.generate_chain_reply(
            target_bot_id, profile, entry, from_affinity, relationship_type
        )

        if not reply_entry:
            return 0

        self.queue_repo.add(reply_entry)
        self.affinity_service.update_on_interaction(target_bot_id, entry.npc_id, "reply")
        self.feedback_handler.update_memory_on_feedback(entry.npc_id, entry.content, "reply")
        print(f"      💬 {profile.name} ↩️ {entry.npc_name}")
        return 1

    def process_affinity_decay(self, target_npc_ids: list[int]) -> int:
        """好感度の減衰処理を実行（AffinityServiceに委譲）"""
        return self.affinity_service.process_decay(target_npc_ids, self.npcs)

    def process_ignored_posts(self, target_npc_ids: list[int]) -> int:
        """無視された投稿による好感度減衰を処理（AffinityServiceに委譲）"""
        return self.affinity_service.process_ignored_posts(target_npc_ids)
