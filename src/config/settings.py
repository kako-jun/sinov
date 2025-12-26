"""
アプリケーション設定（環境変数から読み込み）
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class ContentSettings(BaseSettings):
    """投稿コンテンツ生成の設定"""

    # 文脈継続の確率（前回投稿の続きを書く）
    context_continuation_probability: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="前回投稿の続きを書く確率",
    )

    # 共有ニュース参照の確率
    news_reference_probability: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="共有ニュースを参照する確率",
    )

    # 連作開始の確率
    series_start_probability: float = Field(
        default=0.2,
        ge=0.0,
        le=1.0,
        description="連作つぶやきを開始する確率",
    )

    # 興味の進化（何投稿ごとに新トピック発見）
    evolution_interval: int = Field(
        default=10,
        gt=0,
        description="新しいトピックを発見する投稿間隔",
    )

    # LLM生成のリトライ回数
    llm_retry_count: int = Field(
        default=3,
        gt=0,
        description="LLM生成失敗時のリトライ回数",
    )

    # 重複防止で参照する過去投稿数
    history_check_count: int = Field(
        default=5,
        ge=0,
        description="重複チェックで参照する過去投稿数",
    )

    # 保持する投稿履歴の最大件数
    max_history_size: int = Field(
        default=20,
        gt=0,
        description="保持する投稿履歴の最大件数",
    )


class AffinitySettings(BaseSettings):
    """好感度・親密度・気分の設定"""

    # 好感度変動値
    delta_reply: float = Field(
        default=0.05,
        description="リプライをもらった時の好感度上昇",
    )
    delta_reaction: float = Field(
        default=0.02,
        description="リアクションをもらった時の好感度上昇",
    )
    delta_ignored: float = Field(
        default=-0.01,
        description="無視された時の好感度減少",
    )
    decay_weekly: float = Field(
        default=-0.02,
        description="疎遠期間の週次減衰",
    )

    # 親密度変動値（相互作用するほど知り合いになる）
    familiarity_reply: float = Field(
        default=0.03,
        description="リプライ時の親密度上昇",
    )
    familiarity_reaction: float = Field(
        default=0.01,
        description="リアクション時の親密度上昇",
    )

    # 気分変動値（反応をもらうと嬉しい）
    mood_reply: float = Field(
        default=0.1,
        description="リプライをもらった時の気分上昇",
    )
    mood_reaction: float = Field(
        default=0.05,
        description="リアクションをもらった時の気分上昇",
    )
    mood_ignored: float = Field(
        default=-0.03,
        description="無視された時の気分減少",
    )
    mood_decay: float = Field(
        default=-0.01,
        description="時間経過による気分の中立化（0に向かう）",
    )


class MemorySettings(BaseSettings):
    """記憶の設定"""

    # 短期記憶の最大件数
    max_short_term: int = Field(
        default=20,
        gt=0,
        description="短期記憶の最大保持件数",
    )

    # 長期記憶の最大件数
    max_long_term: int = Field(
        default=50,
        gt=0,
        description="長期記憶の最大保持件数",
    )

    # 長期記憶昇格の閾値
    promotion_threshold: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="短期→長期記憶昇格の強度閾値",
    )

    # アクティブな興味の強度閾値
    active_interests_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="アクティブな興味と判定する強度閾値",
    )


class Settings(BaseSettings):
    """アプリケーション全体の設定"""

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # パス設定（住人ごとのフォルダ）
    residents_dir: Path = Field(
        default=Path("npcs/residents"),
        description="住人フォルダのルートディレクトリ",
    )
    backend_dir: Path = Field(
        default=Path("npcs/backend"),
        description="裏方NPCフォルダのルートディレクトリ",
    )

    # パス設定（共有データ）
    data_dir: Path = Field(
        default=Path("npcs/data"),
        description="共有データのディレクトリ",
    )
    queue_dir: Path = Field(
        default=Path("npcs/data/queue"),
        description="キューファイルのディレクトリ",
    )
    tick_state_file: Path = Field(
        default=Path("npcs/data/tick_state.json"),
        description="tick状態ファイルのパス",
    )
    relationships_dir: Path = Field(
        default=Path("npcs/data/relationships"),
        description="関係性ファイルのディレクトリ",
    )
    bulletin_dir: Path = Field(
        default=Path("npcs/data/bulletin_board"),
        description="掲示板ディレクトリ",
    )

    # API設定
    api_endpoint: str = Field(
        default="http://localhost:8787",
        description="MYPACE APIエンドポイント",
    )

    # 実行モード
    dry_run: bool = Field(
        default=False,
        description="Dry runモード（投稿しない）",
    )

    # LLM設定
    ollama_host: str = Field(
        default="http://localhost:11434",
        description="OllamaホストURL",
    )
    ollama_model: str = Field(
        default="llama3.2:3b",
        description="使用するOllamaモデル",
    )

    # コンテンツ設定
    content: ContentSettings = Field(default_factory=ContentSettings)

    # 好感度設定
    affinity: AffinitySettings = Field(default_factory=AffinitySettings)

    # 記憶設定
    memory: MemorySettings = Field(default_factory=MemorySettings)

    # 新しいトピック候補プール
    topic_pool: list[str] = Field(
        default=[
            "機械学習",
            "Webデザイン",
            "データベース",
            "セキュリティ",
            "クラウド",
            "Docker",
            "Kubernetes",
            "CI/CD",
            "アジャイル開発",
            "オープンソース",
            "ブロックチェーン",
        ],
        description="興味進化時の新トピック候補",
    )
