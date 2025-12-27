"""
スケジューリングロジック
"""

import random
from datetime import datetime

from .models import NpcProfile, NpcState


class Scheduler:
    """NPC投稿のスケジューリング"""

    @staticmethod
    def get_activity_probability(hour: int, profile: NpcProfile, state: NpcState) -> float:
        """時間帯と状態に基づく活動確率を計算

        Args:
            hour: 時間（0-23）
            profile: NPCプロフィール
            state: NPC状態

        Returns:
            活動確率（0.0-1.0）
        """
        behavior = profile.behavior

        # hourly_weightが設定されていればそれを使用、なければデフォルト0.5
        base = behavior.hourly_weight.get(hour, 0.5)

        # chronotype補正
        if behavior.chronotype == "lark":
            # 朝型：午前中（5-12時）の確率を上げる
            if 5 <= hour < 12:
                base *= 1.3
            elif hour >= 22 or hour < 5:
                base *= 0.5
        elif behavior.chronotype == "owl":
            # 夜型：夜間（20-4時）の確率を上げる
            if hour >= 20 or hour < 4:
                base *= 1.3
            elif 5 <= hour < 12:
                base *= 0.5

        # 状態による補正
        # 疲労が高いと活動確率が下がる
        base *= 1.0 - state.fatigue * 0.5

        # メンタルが低いと活動確率が下がる
        if state.mental_health < 0.4:
            base *= 0.5

        # エネルギーが低いと活動確率が下がる
        base *= 0.5 + state.energy * 0.5

        return min(max(base, 0.0), 1.0)

    @staticmethod
    def should_post_now(profile: NpcProfile, state: NpcState) -> bool:
        """このNPCが今投稿すべきかを判定"""
        now = datetime.now()
        current_time = int(now.timestamp())
        current_hour = now.hour
        current_weekday = now.weekday()  # 0=月曜, 6=日曜

        # 活動曜日かチェック
        if hasattr(profile.behavior, "active_days") and profile.behavior.active_days:
            if current_weekday not in profile.behavior.active_days:
                return False

        # 活動時間帯かチェック
        if current_hour not in profile.behavior.active_hours:
            return False

        # hourly_weightが設定されている場合は確率的に判定
        if profile.behavior.hourly_weight:
            probability = Scheduler.get_activity_probability(current_hour, profile, state)
            if random.random() > probability:
                return False

        # 次回投稿時刻が未設定または過去の場合は投稿
        if state.next_post_time == 0 or current_time >= state.next_post_time:
            return True

        return False

    @staticmethod
    def calculate_next_post_time(profile: NpcProfile) -> int:
        """次回投稿時刻を計算"""
        # 1日の投稿頻度から平均間隔を計算（秒）
        avg_interval = 86400 / profile.behavior.post_frequency

        # ばらつきを考慮した実際の間隔
        variance = profile.behavior.post_frequency_variance
        actual_interval = avg_interval * random.uniform(1 - variance, 1 + variance)

        current_time = int(datetime.now().timestamp())
        next_time = current_time + int(actual_interval)

        return next_time
