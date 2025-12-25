"""
相互作用サービス（リプライ・リアクション処理）
"""

from datetime import datetime, timedelta

from ..domain import BotProfile, BotState, ContentStrategy, PostType, QueueEntry, QueueStatus
from ..domain.interaction import InteractionManager
from ..domain.models import BotKey
from ..domain.queue import ConversationContext, ReplyTarget
from ..infrastructure import LLMProvider, MemoryRepository, QueueRepository
from ..infrastructure.storage.relationship_repo import RelationshipRepository

# 好感度変動値
AFFINITY_DELTA_REPLY = 0.05  # リプライをもらった時
AFFINITY_DELTA_REACTION = 0.02  # リアクションをもらった時
AFFINITY_DELTA_IGNORED = -0.01  # 無視された時（未実装）
AFFINITY_DECAY_WEEKLY = -0.02  # 疎遠期間の週次減衰（未実装）


class InteractionService:
    """住人間の相互作用を処理するサービス"""

    def __init__(
        self,
        llm_provider: LLMProvider | None,
        queue_repo: QueueRepository,
        relationship_repo: RelationshipRepository,
        content_strategy: ContentStrategy,
        bots: dict[int, tuple[BotKey, BotProfile, BotState]],
        memory_repo: MemoryRepository | None = None,
    ):
        self.llm_provider = llm_provider
        self.queue_repo = queue_repo
        self.relationship_repo = relationship_repo
        self.content_strategy = content_strategy
        self.bots = bots
        self.memory_repo = memory_repo

        # 関係性データを読み込み
        self.relationship_data = relationship_repo.load_all()
        self.interaction_manager = InteractionManager(self.relationship_data)

    async def process_interactions(self, target_bot_ids: list[int]) -> int:
        """
        指定された住人に対して相互作用処理を実行

        Args:
            target_bot_ids: 処理対象の住人ID一覧

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

        for bot_id in target_bot_ids:
            if bot_id not in self.bots:
                continue

            _, profile, _ = self.bots[bot_id]
            bot_name = f"bot{bot_id:03d}"

            # 好感度を読み込み
            affinity = self.relationship_repo.load_affinity(bot_name)

            # 他住人の投稿をチェック
            for entry in posted_entries:
                # 自分の投稿はスキップ
                if entry.bot_id == bot_id:
                    continue

                # event_idがない投稿はスキップ（Nostrに投稿されていない）
                if not entry.event_id:
                    continue

                # 既にリプライ済みの投稿はスキップ（同一event_idへの重複防止）
                if self._already_replied(bot_id, entry.event_id):
                    continue

                target_bot_name = f"bot{entry.bot_id:03d}"
                target_affinity = affinity.get_affinity(target_bot_name)

                # 反応すべきか判定
                should_react, reaction_type = self.interaction_manager.should_react_to_post(
                    from_bot=bot_name,
                    to_bot=target_bot_name,
                    post_content=entry.content,
                    affinity=target_affinity,
                )

                if not should_react:
                    continue

                if reaction_type == "reply":
                    # リプライを生成
                    new_entry = await self._generate_reply(
                        bot_id,
                        profile,
                        entry,
                        target_affinity,
                    )
                    if new_entry:
                        self.queue_repo.add(new_entry)
                        # 好感度を更新（元投稿者 → リプライした人）
                        self._update_affinity_on_interaction(
                            bot_id, entry.bot_id, "reply"
                        )
                        # 記憶を強化（元投稿者の記憶）
                        self._update_memory_on_feedback(
                            entry.bot_id, entry.content, "reply"
                        )
                        generated += 1
                        print(f"      💬 {profile.name} → {entry.bot_name}")

                elif reaction_type == "reaction":
                    # リアクションを生成
                    new_entry = self._generate_reaction(
                        bot_id,
                        profile,
                        entry,
                    )
                    if new_entry:
                        self.queue_repo.add(new_entry)
                        # 好感度を更新（元投稿者 → リアクションした人）
                        self._update_affinity_on_interaction(
                            bot_id, entry.bot_id, "reaction"
                        )
                        # 記憶を強化（元投稿者の記憶）
                        self._update_memory_on_feedback(
                            entry.bot_id, entry.content, "reaction"
                        )
                        generated += 1
                        print(f"      ❤️  {profile.name} → {entry.bot_name}")

        return generated

    def _already_replied(self, bot_id: int, event_id: str | None) -> bool:
        """既にリプライ済みかチェック"""
        if not event_id:
            return False

        # pending, approved, posted を全てチェック
        for status in [QueueStatus.PENDING, QueueStatus.APPROVED, QueueStatus.POSTED]:
            entries = self.queue_repo.get_all(status)
            for entry in entries:
                if (
                    entry.bot_id == bot_id
                    and entry.reply_to
                    and entry.reply_to.event_id == event_id
                ):
                    return True
        return False

    async def _generate_reply(
        self,
        bot_id: int,
        profile: BotProfile,
        target_entry: QueueEntry,
        affinity: float,
    ) -> QueueEntry | None:
        """リプライを生成"""
        if not self.llm_provider:
            return None

        # リプライ先情報を作成
        reply_to = ReplyTarget(
            resident=f"bot{target_entry.bot_id:03d}",
            event_id=target_entry.event_id or "",
            content=target_entry.content,
        )

        # 関係タイプを取得
        bot_name = f"bot{bot_id:03d}"
        relationship_type = self._get_relationship_type(
            bot_name, f"bot{target_entry.bot_id:03d}"
        )

        # プロンプト生成
        prompt = self.content_strategy.create_reply_prompt(
            profile=profile,
            reply_to=reply_to,
            conversation=None,  # 新規リプライなのでコンテキストなし
            relationship_type=relationship_type,
            affinity=affinity,
        )

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        # 会話コンテキストを作成
        conversation = ConversationContext(
            thread_id=target_entry.event_id or target_entry.id,
            depth=1,
            history=[
                {
                    "author": target_entry.bot_name,
                    "content": target_entry.content,
                    "depth": 0,
                }
            ],
        )

        return QueueEntry(
            bot_id=bot_id,
            bot_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.REPLY,
            reply_to=reply_to,
            conversation=conversation,
        )

    def _generate_reaction(
        self,
        bot_id: int,
        profile: BotProfile,
        target_entry: QueueEntry,
    ) -> QueueEntry | None:
        """リアクションを生成"""
        # 性格に応じた絵文字を選択
        personality_type = self._get_personality_type(profile)
        emoji = self.interaction_manager.select_reaction_emoji(
            target_entry.content, personality_type
        )

        reply_to = ReplyTarget(
            resident=f"bot{target_entry.bot_id:03d}",
            event_id=target_entry.event_id or "",
            content="",  # リアクションでは内容不要
        )

        return QueueEntry(
            bot_id=bot_id,
            bot_name=profile.name,
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

    def _get_personality_type(self, profile: BotProfile) -> str:
        """プロフィールから性格タイプを推定"""
        # 性格タイプから推定
        personality = profile.personality
        personality_type = personality.type.lower()

        # 性格タイプ名から判定
        if any(w in personality_type for w in ["陽気", "明るい", "楽観"]):
            return "陽気"
        if any(w in personality_type for w in ["クール", "冷静", "論理"]):
            return "クール"
        if any(w in personality_type for w in ["熱血", "情熱", "積極"]):
            return "熱血"
        if any(w in personality_type for w in ["内向", "静か", "控えめ"]):
            return "内気"
        if any(w in personality_type for w in ["のんびり", "ゆったり", "マイペース"]):
            return "のんびり"
        if any(w in personality_type for w in ["真面目", "誠実", "堅実"]):
            return "真面目"

        # traitsからも判定
        traits = [t.lower() for t in personality.traits]
        if any("陽気" in t or "明るい" in t for t in traits):
            return "陽気"
        if any("クール" in t or "冷静" in t for t in traits):
            return "クール"

        return "普通"

    def _update_affinity_on_interaction(
        self,
        from_bot_id: int,
        to_bot_id: int,
        interaction_type: str,
    ) -> None:
        """
        相互作用発生時に好感度を更新

        Args:
            from_bot_id: 反応した側のボットID
            to_bot_id: 元投稿者のボットID（好感度が上がる側）
            interaction_type: "reply" or "reaction"
        """
        # 元投稿者の好感度データを読み込み
        to_bot_name = f"bot{to_bot_id:03d}"
        from_bot_name = f"bot{from_bot_id:03d}"

        affinity = self.relationship_repo.load_affinity(to_bot_name)

        # 好感度を更新
        if interaction_type == "reply":
            delta = AFFINITY_DELTA_REPLY
        elif interaction_type == "reaction":
            delta = AFFINITY_DELTA_REACTION
        else:
            return

        old_value = affinity.get_affinity(from_bot_name)
        new_value = affinity.update_affinity(from_bot_name, delta)

        # 最後の相互作用日時を記録
        affinity.record_interaction(from_bot_name, datetime.now().isoformat())

        # 保存
        self.relationship_repo.save_affinity(affinity)

        # ログ出力（デバッグ用、運用時はコメントアウト可）
        if new_value != old_value:
            print(
                f"         📈 {to_bot_name}の{from_bot_name}への好感度: "
                f"{old_value:.2f} → {new_value:.2f}"
            )

    def _update_memory_on_feedback(
        self,
        bot_id: int,
        original_content: str,
        interaction_type: str,
    ) -> None:
        """
        リプライ/リアクションをもらった時に記憶を強化

        Args:
            bot_id: 元投稿者のボットID（記憶が強化される側）
            original_content: 元投稿の内容
            interaction_type: "reply" or "reaction"
        """
        if not self.memory_repo:
            return

        # 元投稿者の記憶を読み込み
        memory = self.memory_repo.load(bot_id)

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
                if memory.reinforce_short_term(keyword, boost):
                    reinforced = True

        # 元投稿自体も強化
        if memory.reinforce_short_term(original_content[:20], boost):
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

    async def process_reply_chains(self, target_bot_ids: list[int]) -> int:
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

            # リプライ先のボットIDを取得
            target_bot_name = entry.reply_to.resident
            if not target_bot_name.startswith("bot"):
                continue

            try:
                target_bot_id = int(target_bot_name[3:])
            except ValueError:
                continue

            # 処理対象でなければスキップ
            if target_bot_id not in target_bot_ids:
                continue

            if target_bot_id not in self.bots:
                continue

            _, profile, _ = self.bots[target_bot_id]

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
            from_affinity = affinity.get_affinity(f"bot{entry.bot_id:03d}")

            # 会話を続けるか判定
            should_continue = self.interaction_manager.should_continue_conversation(
                from_bot=target_bot_name,
                to_bot=f"bot{entry.bot_id:03d}",
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
                self._update_affinity_on_interaction(
                    target_bot_id, entry.bot_id, "reply"
                )
                # 記憶を強化（リプライを送ってきた人の記憶）
                self._update_memory_on_feedback(
                    entry.bot_id, entry.content, "reply"
                )
                generated += 1
                print(f"      💬 {profile.name} ↩️ {entry.bot_name}")

        return generated

    async def _generate_chain_reply(
        self,
        bot_id: int,
        profile: BotProfile,
        incoming_entry: QueueEntry,
        affinity: float,
    ) -> QueueEntry | None:
        """会話チェーンへの返信を生成"""
        if not self.llm_provider:
            return None

        # 会話コンテキストを更新
        existing_conv = incoming_entry.conversation
        new_depth = (existing_conv.depth + 1) if existing_conv else 1

        new_history = (existing_conv.history.copy() if existing_conv else [])
        new_history.append(
            {
                "author": incoming_entry.bot_name,
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
            resident=f"bot{incoming_entry.bot_id:03d}",
            event_id=incoming_entry.event_id or "",
            content=incoming_entry.content,
        )

        # 関係タイプを取得
        bot_name = f"bot{bot_id:03d}"
        relationship_type = self._get_relationship_type(
            bot_name, f"bot{incoming_entry.bot_id:03d}"
        )

        # プロンプト生成
        prompt = self.content_strategy.create_reply_prompt(
            profile=profile,
            reply_to=reply_to,
            conversation=conversation,
            relationship_type=relationship_type,
            affinity=affinity,
        )

        # LLMで生成
        content = await self.llm_provider.generate(
            prompt, max_length=profile.behavior.post_length_max
        )
        content = self.content_strategy.clean_content(content)

        return QueueEntry(
            bot_id=bot_id,
            bot_name=profile.name,
            content=content,
            status=QueueStatus.PENDING,
            post_type=PostType.REPLY,
            reply_to=reply_to,
            conversation=conversation,
        )

    def process_affinity_decay(self, target_bot_ids: list[int]) -> int:
        """
        好感度の減衰処理を実行（疎遠期間による減衰）

        1週間以上相互作用がない関係について好感度を減衰させる。

        Args:
            target_bot_ids: 処理対象の住人ID一覧

        Returns:
            減衰が発生した関係の数
        """
        decayed_count = 0
        now = datetime.now()
        one_week_ago = now - timedelta(weeks=1)

        for bot_id in target_bot_ids:
            if bot_id not in self.bots:
                continue

            bot_name = f"bot{bot_id:03d}"
            affinity = self.relationship_repo.load_affinity(bot_name)
            updated = False

            # 関係のある住人を取得
            related_members = self.relationship_data.get_related_members(bot_name)

            for target_name in related_members:
                # 最後の相互作用日時を確認
                last_interaction = affinity.get_last_interaction(target_name)

                if last_interaction:
                    try:
                        last_dt = datetime.fromisoformat(last_interaction)
                        if last_dt < one_week_ago:
                            # 1週間以上相互作用がない → 減衰
                            old_value = affinity.get_affinity(target_name)
                            new_value = affinity.update_affinity(
                                target_name, AFFINITY_DECAY_WEEKLY
                            )
                            if new_value != old_value:
                                decayed_count += 1
                                updated = True
                    except ValueError:
                        # パースエラーは無視
                        pass

            # 変更があれば保存
            if updated:
                self.relationship_repo.save_affinity(affinity)

        return decayed_count

    def process_ignored_posts(self, target_bot_ids: list[int]) -> int:
        """
        無視された投稿による好感度減衰を処理

        関係者がいるのに誰からも反応がなかった投稿について、
        投稿者の関係者への好感度を微減させる。

        Args:
            target_bot_ids: 処理対象の住人ID一覧

        Returns:
            減衰が発生した数
        """
        decayed_count = 0

        # 投稿済みエントリーを取得（通常投稿のみ）
        posted_entries = self.queue_repo.get_all(QueueStatus.POSTED)
        normal_posts = [
            e for e in posted_entries
            if e.post_type == PostType.NORMAL and e.bot_id in target_bot_ids
        ]

        for entry in normal_posts:
            if not entry.event_id:
                continue

            bot_name = f"bot{entry.bot_id:03d}"

            # この投稿へのリプライ/リアクションがあるかチェック
            has_reaction = self._has_any_reaction(entry.event_id)

            if has_reaction:
                continue

            # 反応がない場合、関係者への好感度を微減
            related_members = self.relationship_data.get_related_members(bot_name)

            if not related_members:
                continue

            affinity = self.relationship_repo.load_affinity(bot_name)
            updated = False

            for target_name in related_members:
                old_value = affinity.get_affinity(target_name)
                new_value = affinity.update_affinity(target_name, AFFINITY_DELTA_IGNORED)
                if new_value != old_value:
                    decayed_count += 1
                    updated = True

            if updated:
                self.relationship_repo.save_affinity(affinity)

        return decayed_count

    def _has_any_reaction(self, event_id: str) -> bool:
        """指定イベントへの反応（リプライ/リアクション）があるかチェック"""
        for status in [QueueStatus.PENDING, QueueStatus.APPROVED, QueueStatus.POSTED]:
            entries = self.queue_repo.get_all(status)
            for entry in entries:
                if entry.reply_to and entry.reply_to.event_id == event_id:
                    return True
        return False
