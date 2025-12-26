"""
スケジューリングロジック
"""

import random
from datetime import datetime

from .models import BotProfile, BotState


class Scheduler:
    """NPC投稿のスケジューリング"""

    @staticmethod
    def should_post_now(profile: BotProfile, state: BotState) -> bool:
        """このNPCが今投稿すべきかを判定"""
        current_time = int(datetime.now().timestamp())
        current_hour = datetime.now().hour

        # 活動時間帯かチェック
        if current_hour not in profile.behavior.active_hours:
            return False

        # 次回投稿時刻が未設定または過去の場合は投稿
        if state.next_post_time == 0 or current_time >= state.next_post_time:
            return True

        return False

    @staticmethod
    def calculate_next_post_time(profile: BotProfile) -> int:
        """次回投稿時刻を計算"""
        # 1日の投稿頻度から平均間隔を計算（秒）
        avg_interval = 86400 / profile.behavior.post_frequency

        # ばらつきを考慮した実際の間隔
        variance = profile.behavior.post_frequency_variance
        actual_interval = avg_interval * random.uniform(1 - variance, 1 + variance)

        current_time = int(datetime.now().timestamp())
        next_time = current_time + int(actual_interval)

        return next_time
