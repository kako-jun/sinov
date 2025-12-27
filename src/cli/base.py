"""
CLI共通の初期化関数
"""

from dotenv import load_dotenv

from ..application import ServiceFactory
from ..config import Settings
from ..domain import NpcKey, extract_npc_id
from ..infrastructure import OllamaProvider


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


def create_factory(settings: Settings, llm: OllamaProvider | None = None) -> ServiceFactory:
    """ServiceFactoryを作成"""
    return ServiceFactory(settings, llm)


def get_target_pubkey(resident: str) -> str | None:
    """住人名（npc001形式）からpubkeyを取得"""
    npc_id = extract_npc_id(resident)
    if npc_id is None:
        return None

    try:
        target_key = NpcKey.from_env(npc_id)
        return target_key.pubkey
    except ValueError:
        return None
