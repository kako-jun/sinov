"""
メインエントリーポイント
"""
import asyncio
import os
from pathlib import Path

from dotenv import load_dotenv

from .bot_manager import BotManager
from .llm import LLMClient


async def main() -> None:
    # 環境変数読み込み（.env + .env.keys）
    load_dotenv()  # .env
    load_dotenv(".env.keys")  # .env.keys（ボットの鍵）
    
    # 設定
    profiles_dir = Path("bots/profiles")
    states_file = Path("bots/states.json")
    
    api_endpoint = os.getenv("API_ENDPOINT", "http://localhost:8787")
    dry_run = os.getenv("DRY_RUN", "false").lower() == "true"
    
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
    
    # LLMクライアント初期化（オプション）
    llm_client = None
    try:
        llm = LLMClient(ollama_host, ollama_model)
        if llm.is_available():
            llm_client = llm
            print(f"✅ Ollama is available (model: {ollama_model})")
        else:
            print("⚠️  Ollama is not available, using simple content generation")
    except Exception as e:
        print(f"⚠️  Could not connect to Ollama: {e}")
        print("Using simple content generation instead")
    
    if dry_run:
        print("\n🔍 DRY RUN MODE: Posts will not be sent to the API\n")
    
    # ボットマネージャー初期化
    manager = BotManager(
        profiles_dir=profiles_dir,
        states_file=states_file,
        api_endpoint=api_endpoint,
        relays=[],  # APIが内部でリレーに接続するため不要
        llm_client=llm_client,
        dry_run=dry_run,
    )
    
    # ボット読み込み
    await manager.load_bots()
    
    # Nostr署名鍵初期化
    await manager.initialize_keys()
    
    # メインループ開始（1分ごとにチェック）
    await manager.run_forever(check_interval=60)


if __name__ == "__main__":
    asyncio.run(main())
