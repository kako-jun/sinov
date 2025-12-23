#!/usr/bin/env python
"""
ニュース収集スクリプト
定期的に実行してbots/shared_news.jsonに最新ニュースを保存
"""
import json
from datetime import datetime
from pathlib import Path


def collect_tech_news() -> list[str]:
    """テクノロジーニュースを収集（現在はダミー実装）"""
    # TODO: 実際のニュースAPI（例: Hacker News API, Reddit API など）から取得
    # 現在はサンプルデータ
    sample_news = [
        "Python 3.13のベータ版がリリース、パフォーマンス改善が目玉",
        "新しいJavaScriptフレームワークが注目を集めている",
        "量子コンピュータの商用化が加速",
        "AIチップ市場が急成長、NVIDIAが独走",
        "Rustの採用企業が増加中",
        "Webアセンブリが新しい標準として定着",
        "クラウドネイティブ技術の導入が進む",
        "エッジコンピューティングの重要性が高まる",
        "5G通信でIoTデバイスが爆発的に増加",
        "サイバーセキュリティ対策がますます重要に"
    ]
    
    # ランダムに5件選択
    import random
    return random.sample(sample_news, min(5, len(sample_news)))


def save_shared_news(news_items: list[str]) -> None:
    """共有ニュースを保存"""
    news_file = Path("bots/shared_news.json")
    news_file.parent.mkdir(parents=True, exist_ok=True)
    
    data = {
        "updated_at": datetime.now().isoformat(),
        "news": news_items
    }
    
    with open(news_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(news_items)} news items to {news_file}")


def main():
    """メイン処理"""
    print("📰 Collecting tech news...")
    news_items = collect_tech_news()
    
    print(f"Found {len(news_items)} news items:")
    for i, item in enumerate(news_items, 1):
        print(f"  {i}. {item}")
    
    save_shared_news(news_items)


if __name__ == "__main__":
    main()
