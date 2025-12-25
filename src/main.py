"""
メインエントリーポイント
"""

import asyncio

from dotenv import load_dotenv

from .application import BotService
from .config import Settings
from .infrastructure import (
    NostrPublisher,
    OllamaProvider,
    ProfileRepository,
    StateRepository,
)


async def main() -> None:
    # 環境変数読み込み（.env + .env.keys）
    load_dotenv()  # .env
    load_dotenv(".env.keys")  # .env.keys（ボットの鍵）

    # 設定読み込み
    settings = Settings()

    # LLMプロバイダー初期化
    llm_provider = None
    try:
        llm = OllamaProvider(settings.ollama_host, settings.ollama_model)
        if llm.is_available():
            llm_provider = llm
            print(f"✅ Ollama is available (model: {settings.ollama_model})")
        else:
            print("⚠️  Ollama is not available")
    except Exception as e:
        print(f"⚠️  Could not connect to Ollama: {e}")

    if not llm_provider:
        print("❌ LLM provider is required. Exiting.")
        return

    if settings.dry_run:
        print("\n🔍 DRY RUN MODE: Posts will not be sent to the API\n")

    # 依存関係を構築
    publisher = NostrPublisher(settings.api_endpoint, settings.dry_run)
    profile_repo = ProfileRepository(settings.profiles_dir)
    state_repo = StateRepository(settings.states_file)

    # サービス初期化
    service = BotService(
        settings=settings,
        llm_provider=llm_provider,
        publisher=publisher,
        profile_repo=profile_repo,
        state_repo=state_repo,
    )

    # ボット読み込み
    await service.load_bots()

    # Nostr署名鍵初期化
    await service.initialize_keys()

    # メインループ開始
    await service.run_forever()


if __name__ == "__main__":
    asyncio.run(main())
