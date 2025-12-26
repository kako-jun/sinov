"""
CLI共通の初期化関数
"""

from dotenv import load_dotenv

from ..application import NpcService
from ..config import Settings
from ..domain import extract_npc_id
from ..infrastructure import (
    LogRepository,
    MemoryRepository,
    NostrPublisher,
    OllamaProvider,
    ProfileRepository,
    QueueRepository,
    StateRepository,
)


def init_env() -> Settings:
    """環境変数とSettingsを初期化"""
    load_dotenv()
    load_dotenv(".env.keys")
    return Settings()


def init_llm(settings: Settings) -> OllamaProvider | None:
    """LLMプロバイダーを初期化"""
    print("Initializing LLM...")
    try:
        llm = OllamaProvider(settings.ollama_host, settings.ollama_model)
        if not llm.is_available():
            print("⚠️  Ollama is not available")
            return None
        print(f"  Model: {settings.ollama_model}")
        return llm
    except Exception as e:
        print(f"⚠️  Could not connect to Ollama: {e}")
        return None


async def init_service(settings: Settings, llm: OllamaProvider) -> NpcService:
    """NpcServiceを初期化"""
    publisher = NostrPublisher(settings.api_endpoint, dry_run=True)
    profile_repo = ProfileRepository(settings.residents_dir, settings.backend_dir)
    state_repo = StateRepository(settings.residents_dir)
    memory_repo = MemoryRepository(settings.residents_dir)
    queue_repo = QueueRepository(settings.queue_dir)
    log_repo = LogRepository(str(settings.residents_dir))

    service = NpcService(
        settings=settings,
        llm_provider=llm,
        publisher=publisher,
        profile_repo=profile_repo,
        state_repo=state_repo,
        memory_repo=memory_repo,
        queue_repo=queue_repo,
        log_repo=log_repo,
    )

    print("Loading NPCs...")
    await service.load_bots()
    await service.initialize_keys()

    return service


def get_target_pubkey(resident: str) -> str | None:
    """住人名（npc001形式）からpubkeyを取得"""
    from ..domain import NpcKey

    npc_id = extract_npc_id(resident)
    if npc_id is None:
        return None

    try:
        target_key = NpcKey.from_env(npc_id)
        return target_key.pubkey
    except ValueError:
        return None
