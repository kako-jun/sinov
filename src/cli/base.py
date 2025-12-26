"""
CLI共通の初期化関数
"""

from dotenv import load_dotenv

from ..application import BotService
from ..config import Settings
from ..domain import extract_bot_id
from ..infrastructure import (
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


async def init_service(settings: Settings, llm: OllamaProvider) -> BotService:
    """BotServiceを初期化"""
    publisher = NostrPublisher(settings.api_endpoint, dry_run=True)
    profile_repo = ProfileRepository(settings.residents_dir, settings.backend_dir)
    state_repo = StateRepository(settings.residents_dir)
    memory_repo = MemoryRepository(settings.residents_dir)
    queue_repo = QueueRepository(settings.queue_dir)

    service = BotService(
        settings=settings,
        llm_provider=llm,
        publisher=publisher,
        profile_repo=profile_repo,
        state_repo=state_repo,
        memory_repo=memory_repo,
        queue_repo=queue_repo,
    )

    print("Loading bots...")
    await service.load_bots()
    await service.initialize_keys()

    return service


def get_target_pubkey(resident: str) -> str | None:
    """住人名（bot001形式）からpubkeyを取得"""
    from ..domain import BotKey

    bot_id = extract_bot_id(resident)
    if bot_id is None:
        return None

    try:
        target_key = BotKey.from_env(bot_id)
        return target_key.pubkey
    except ValueError:
        return None
