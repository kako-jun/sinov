"""ドメイン層（ビジネスロジック）"""

# --- アクティビティログ ---
from .activity_log import (
    ActivityLogger,
    DailyLog,
    LogEntry,
    LogEventType,
    ParameterChange,
)

# --- コンテンツ生成 ---
from .content import ContentStrategy

# --- イベント ---
from .events import EventCalendar, SeasonalEvent

# --- 相互作用 ---
from .interaction import InteractionManager

# --- 記憶 ---
from .memory import AcquiredMemory, NpcMemory, SeriesState, ShortTermMemory

# --- モデル（Enum・型定義） ---
from .models import (
    Background,
    Behavior,
    HabitType,
    Interests,
    LineBreakStyle,
    NpcKey,
    NpcProfile,
    NpcState,
    Personality,
    PersonalityTraits,
    Prompts,
    PunctuationStyle,
    Social,
    StyleType,
    TickState,
    WritingQuirk,
    WritingStyle,
)

# --- ニュース ---
from .news import BulletinBoard, NewsItem, ReporterConfig

# --- ユーティリティ ---
from .npc_utils import extract_npc_id, format_npc_name

# --- 性格分析 ---
from .personality import PersonalityAnalyzer

# --- キュー ---
from .queue import (
    ConversationContext,
    MumbleAbout,
    PostType,
    QueueEntry,
    QueueStatus,
    ReplyTarget,
)

# --- 関係性 ---
from .relationships import (
    Affinity,
    Group,
    GroupInteraction,
    Pair,
    PairInteraction,
    RelationshipData,
    RelationshipType,
    Stalker,
    StalkerBehavior,
    StalkerReaction,
    StalkerTarget,
)

# --- スケジューラ ---
from .scheduler import Scheduler

# --- テキスト処理 ---
from .text_processor import TextProcessor

__all__ = [
    # ユーティリティ
    "format_npc_name",
    "extract_npc_id",
    "PersonalityAnalyzer",
    # モデル - 基本型
    "NpcKey",
    "Personality",
    "PersonalityTraits",
    "Interests",
    "Behavior",
    "Social",
    "Background",
    "NpcProfile",
    "NpcState",
    "TickState",
    # モデル - Enum
    "StyleType",
    "HabitType",
    "LineBreakStyle",
    "PunctuationStyle",
    "WritingQuirk",
    "WritingStyle",
    "Prompts",
    # 記憶
    "ShortTermMemory",
    "AcquiredMemory",
    "SeriesState",
    "NpcMemory",
    # スケジューラ・コンテンツ
    "Scheduler",
    "ContentStrategy",
    # イベント
    "SeasonalEvent",
    "EventCalendar",
    # 相互作用
    "InteractionManager",
    # ニュース
    "NewsItem",
    "BulletinBoard",
    "ReporterConfig",
    # キュー
    "QueueEntry",
    "QueueStatus",
    "PostType",
    "ReplyTarget",
    "ConversationContext",
    "MumbleAbout",
    # 関係性
    "RelationshipType",
    "GroupInteraction",
    "Group",
    "PairInteraction",
    "Pair",
    "StalkerReaction",
    "StalkerTarget",
    "StalkerBehavior",
    "Stalker",
    "Affinity",
    "RelationshipData",
    # アクティビティログ
    "LogEventType",
    "ParameterChange",
    "LogEntry",
    "DailyLog",
    "ActivityLogger",
    # テキスト処理
    "TextProcessor",
]
