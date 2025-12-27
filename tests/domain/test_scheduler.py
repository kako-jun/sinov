"""Scheduler のユニットテスト"""

from datetime import datetime
from unittest.mock import patch

from src.domain import NpcState, Scheduler
from src.domain.models import (
    Background,
    Behavior,
    Interests,
    NpcProfile,
    Personality,
    Social,
)


def create_test_profile(
    active_hours: list[int] | None = None,
    post_frequency: int = 3,
    variance: float = 0.3,
) -> NpcProfile:
    """テスト用プロファイルを作成"""
    return NpcProfile(
        id=1,
        name="test_npc",
        personality=Personality(type="friendly", traits=["明るい"], emotional_range=5),
        interests=Interests(topics=["テスト"], keywords=["テスト"]),
        behavior=Behavior(
            active_hours=active_hours or list(range(9, 23)),
            post_frequency=post_frequency,
            post_frequency_variance=variance,
            post_length_min=20,
            post_length_max=140,
        ),
        social=Social(reply_probability=0.5, repost_probability=0.1, like_probability=0.3),
        background=Background(),
    )


def create_test_state(next_post_time: int = 0) -> NpcState:
    """テスト用状態を作成"""
    return NpcState(
        id=1,
        last_post_time=0,
        next_post_time=next_post_time,
        total_posts=0,
    )


class TestSchedulerShouldPostNow:
    """should_post_now メソッドのテスト"""

    def test_returns_false_outside_active_hours(self) -> None:
        """活動時間外は投稿しない"""
        profile = create_test_profile(active_hours=[10, 11, 12])
        state = create_test_state(next_post_time=0)

        # 午前3時にモック
        mock_dt = datetime(2025, 1, 1, 3, 0, 0)
        with patch("src.domain.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            result = Scheduler.should_post_now(profile, state)
        assert result is False

    def test_returns_true_in_active_hours_with_zero_next_time(self) -> None:
        """活動時間内で next_post_time=0 なら投稿する"""
        profile = create_test_profile(active_hours=[10, 11, 12])
        state = create_test_state(next_post_time=0)

        mock_dt = datetime(2025, 1, 1, 11, 0, 0)
        with patch("src.domain.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            result = Scheduler.should_post_now(profile, state)
        assert result is True

    def test_returns_true_when_past_next_post_time(self) -> None:
        """next_post_time を過ぎていれば投稿する"""
        profile = create_test_profile(active_hours=[10, 11, 12])
        past_time = int(datetime(2025, 1, 1, 10, 0, 0).timestamp())
        state = create_test_state(next_post_time=past_time)

        mock_dt = datetime(2025, 1, 1, 11, 0, 0)  # 1時間後
        with patch("src.domain.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            result = Scheduler.should_post_now(profile, state)
        assert result is True

    def test_returns_false_before_next_post_time(self) -> None:
        """next_post_time 前は投稿しない"""
        profile = create_test_profile(active_hours=[10, 11, 12])
        future_time = int(datetime(2025, 1, 1, 12, 0, 0).timestamp())
        state = create_test_state(next_post_time=future_time)

        mock_dt = datetime(2025, 1, 1, 11, 0, 0)  # 1時間前
        with patch("src.domain.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            result = Scheduler.should_post_now(profile, state)
        assert result is False


class TestSchedulerCalculateNextPostTime:
    """calculate_next_post_time メソッドのテスト"""

    def test_returns_future_timestamp(self) -> None:
        """未来のタイムスタンプを返す"""
        profile = create_test_profile(post_frequency=3.0, variance=0.0)

        mock_dt = datetime(2025, 1, 1, 12, 0, 0)
        current_ts = int(mock_dt.timestamp())

        with patch("src.domain.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            result = Scheduler.calculate_next_post_time(profile)

        assert result > current_ts

    def test_interval_based_on_frequency(self) -> None:
        """頻度に基づいた間隔を計算"""
        # 1日3回 = 8時間間隔 = 28800秒
        profile = create_test_profile(post_frequency=3.0, variance=0.0)

        mock_dt = datetime(2025, 1, 1, 12, 0, 0)
        current_ts = int(mock_dt.timestamp())

        with patch("src.domain.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            import random

            random.seed(42)
            result = Scheduler.calculate_next_post_time(profile)

        expected_interval = 86400 / 3  # 28800秒
        actual_interval = result - current_ts
        assert actual_interval == int(expected_interval)

    def test_variance_affects_interval(self) -> None:
        """variance が間隔に影響する"""
        profile = create_test_profile(post_frequency=3.0, variance=0.5)

        mock_dt = datetime(2025, 1, 1, 12, 0, 0)
        current_ts = int(mock_dt.timestamp())

        results = []
        with patch("src.domain.scheduler.datetime") as mock_datetime:
            mock_datetime.now.return_value = mock_dt
            import random

            for i in range(10):
                random.seed(i)
                result = Scheduler.calculate_next_post_time(profile)
                results.append(result - current_ts)

        # 異なる間隔が生成される
        assert len(set(results)) > 1
