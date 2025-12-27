"""
制作物システムのドメインロジック
"""

import random
from datetime import datetime

from .models import PROGRESS_MESSAGES, CreativeWork, NpcProfile

# 進捗変化量
PROGRESS_DELTA = {
    "working": 0.02,  # 通常作業
    "focused": 0.05,  # 集中して作業（focus > 0.7）
    "breakthrough": 0.10,  # ブレイクスルー（低確率）
}

# 進捗更新確率（投稿時）
PROGRESS_UPDATE_PROBABILITY = 0.3


class CreativeWorksManager:
    """制作物の進捗管理"""

    @staticmethod
    def update_progress(
        profile: NpcProfile,
        focus: float = 0.5,
    ) -> tuple[CreativeWork | None, bool]:
        """
        投稿時に制作物の進捗を更新

        Args:
            profile: NPCプロフィール
            focus: 現在の集中度

        Returns:
            (更新された作品, 完成したかどうか)
        """
        if not profile.creative_works or not profile.creative_works.current:
            return None, False

        # 確率で進捗更新
        if random.random() > PROGRESS_UPDATE_PROBABILITY:
            return None, False

        # 最初の進行中作品を更新
        work = profile.creative_works.current[0]

        # 進捗変化量を決定
        if random.random() < 0.05:  # 5%でブレイクスルー
            delta = PROGRESS_DELTA["breakthrough"]
        elif focus > 0.7:
            delta = PROGRESS_DELTA["focused"]
        else:
            delta = PROGRESS_DELTA["working"]

        work.progress = min(1.0, work.progress + delta)

        # 完成チェック
        completed = False
        if work.progress >= 1.0:
            work.status = "completed"
            work.completed_at = datetime.now()
            work.progress = 1.0
            completed = True

            # current から completed に移動
            profile.creative_works.current.remove(work)
            profile.creative_works.completed.append(work)

            # planned から次の作品を current に移動
            if profile.creative_works.planned:
                next_work = profile.creative_works.planned.pop(0)
                next_work.status = "in_progress"
                next_work.started_at = datetime.now()
                next_work.progress = 0.0
                profile.creative_works.current.append(next_work)

        return work, completed

    @staticmethod
    def get_progress_message(work: CreativeWork) -> str | None:
        """
        進捗に応じた発言テンプレートを取得

        Args:
            work: 制作物

        Returns:
            発言テンプレート（{name}, {progress_pct}を含む場合あり）
        """
        progress = work.progress

        for (low, high), templates in PROGRESS_MESSAGES.items():
            if low <= progress < high:
                template = random.choice(templates)
                return template.format(
                    name=work.name,
                    progress_pct=int(progress * 100),
                )

        # 完成時
        if progress >= 1.0:
            return f"{work.name}、完成した！"

        return None

    @staticmethod
    def get_current_work_context(profile: NpcProfile) -> str | None:
        """
        現在の制作物情報をプロンプト用のコンテキストとして取得

        Args:
            profile: NPCプロフィール

        Returns:
            コンテキスト文字列
        """
        if not profile.creative_works or not profile.creative_works.current:
            return None

        work = profile.creative_works.current[0]
        progress_pct = int(work.progress * 100)

        context = f"現在「{work.name}」（{work.type}）を制作中（進捗: {progress_pct}%）"
        if work.current_task:
            context += f"。今は{work.current_task}に取り組んでいる"

        return context

    @staticmethod
    def create_completion_memory(work: CreativeWork) -> dict:
        """
        完成時に長期記憶に追加するデータを生成

        Args:
            work: 完成した制作物

        Returns:
            記憶データ
        """
        return {
            "content": f"「{work.name}」を完成させた",
            "type": "achievement",
            "work_id": work.id,
            "work_type": work.type,
            "completed_at": work.completed_at.isoformat() if work.completed_at else None,
        }
