"""
サービスファクトリ

各サービスのインスタンス化と依存関係の解決を担当
"""

from ..config import Settings
from ..domain import ContentStrategy
from ..infrastructure import (
    LLMProvider,
    LogRepository,
    MemoryRepository,
    ProfileRepository,
    QueueRepository,
    RelationshipRepository,
    StateRepository,
    TickStateRepository,
)
from .external_reaction_service import ExternalReactionService
from .interaction_service import InteractionService
from .npc_service import NpcService


class ServiceFactory:
    """サービスのインスタンス化を担当するファクトリ"""

    def __init__(
        self,
        settings: Settings,
        llm_provider: LLMProvider | None = None,
    ):
        self.settings = settings
        self.llm_provider = llm_provider

        # リポジトリの初期化
        self._profile_repo: ProfileRepository | None = None
        self._state_repo: StateRepository | None = None
        self._memory_repo: MemoryRepository | None = None
        self._queue_repo: QueueRepository | None = None
        self._log_repo: LogRepository | None = None
        self._relationship_repo: RelationshipRepository | None = None
        self._tick_state_repo: TickStateRepository | None = None

        # サービスのキャッシュ
        self._npc_service: NpcService | None = None
        self._content_strategy: ContentStrategy | None = None

    @property
    def profile_repo(self) -> ProfileRepository:
        """ProfileRepositoryを取得（遅延初期化）"""
        if self._profile_repo is None:
            self._profile_repo = ProfileRepository(
                self.settings.residents_dir,
                backend_dir=self.settings.backend_dir,
            )
        return self._profile_repo

    @property
    def state_repo(self) -> StateRepository:
        """StateRepositoryを取得（遅延初期化）"""
        if self._state_repo is None:
            self._state_repo = StateRepository(self.settings.residents_dir)
        return self._state_repo

    @property
    def memory_repo(self) -> MemoryRepository:
        """MemoryRepositoryを取得（遅延初期化）"""
        if self._memory_repo is None:
            self._memory_repo = MemoryRepository(self.settings.residents_dir)
        return self._memory_repo

    @property
    def queue_repo(self) -> QueueRepository:
        """QueueRepositoryを取得（遅延初期化）"""
        if self._queue_repo is None:
            self._queue_repo = QueueRepository(self.settings.queue_dir)
        return self._queue_repo

    @property
    def log_repo(self) -> LogRepository:
        """LogRepositoryを取得（遅延初期化）"""
        if self._log_repo is None:
            self._log_repo = LogRepository(str(self.settings.residents_dir))
        return self._log_repo

    @property
    def relationship_repo(self) -> RelationshipRepository:
        """RelationshipRepositoryを取得（遅延初期化）"""
        if self._relationship_repo is None:
            self._relationship_repo = RelationshipRepository(self.settings.relationships_dir)
        return self._relationship_repo

    @property
    def tick_state_repo(self) -> TickStateRepository:
        """TickStateRepositoryを取得（遅延初期化）"""
        if self._tick_state_repo is None:
            self._tick_state_repo = TickStateRepository(self.settings.tick_state_file)
        return self._tick_state_repo

    @property
    def content_strategy(self) -> ContentStrategy:
        """ContentStrategyを取得（遅延初期化）"""
        if self._content_strategy is None:
            self._content_strategy = ContentStrategy(self.settings.content)
        return self._content_strategy

    async def create_npc_service(self) -> NpcService:
        """NpcServiceを作成して初期化"""
        from ..infrastructure.nostr import NostrPublisher

        publisher = NostrPublisher(self.settings.api_endpoint)

        service = NpcService(
            settings=self.settings,
            llm_provider=self.llm_provider,
            publisher=publisher,
            profile_repo=self.profile_repo,
            state_repo=self.state_repo,
            memory_repo=self.memory_repo,
            queue_repo=self.queue_repo,
            log_repo=self.log_repo,
        )

        await service.load_bots()
        await service.initialize_keys()

        self._npc_service = service
        return service

    def create_interaction_service(self, npc_service: NpcService) -> InteractionService:
        """InteractionServiceを作成"""
        return InteractionService(
            llm_provider=self.llm_provider,
            queue_repo=self.queue_repo,
            relationship_repo=self.relationship_repo,
            content_strategy=npc_service.content_strategy,
            npcs=npc_service.npcs,
            memory_repo=self.memory_repo,
            affinity_settings=self.settings.affinity,
            profile_repo=self.profile_repo,
            log_repo=self.log_repo,
        )

    def create_external_reaction_service(self, npc_service: NpcService) -> ExternalReactionService:
        """ExternalReactionServiceを作成"""
        return ExternalReactionService(
            llm_provider=self.llm_provider,
            queue_repo=self.queue_repo,
            content_strategy=npc_service.content_strategy,
            npcs=npc_service.npcs,
            log_repo=self.log_repo,
        )
