"""
ボットプロフィールリポジトリ
"""

from pathlib import Path

import yaml

from ...domain.models import BotProfile


class ProfileRepository:
    """YAMLファイルからボットプロフィールを読み込む"""

    def __init__(self, profiles_dir: Path):
        self.profiles_dir = profiles_dir

    def load_all(self) -> list[BotProfile]:
        """全プロフィールを読み込み"""
        profiles: list[BotProfile] = []
        profile_files = sorted(self.profiles_dir.glob("bot*.yaml"))

        if not profile_files:
            print("⚠️  No bot profiles found in bots/profiles/")
            return profiles

        for profile_file in profile_files:
            try:
                profile = self.load(profile_file)
                profiles.append(profile)
            except Exception as e:
                print(f"⚠️  Failed to load {profile_file.name}: {e}, skipping...")
                continue

        return profiles

    def load(self, profile_file: Path) -> BotProfile:
        """単一プロフィールを読み込み"""
        try:
            with open(profile_file) as f:
                data = yaml.safe_load(f)

            # Pydanticでバリデーション
            profile = BotProfile.model_validate(data)
            return profile
        except Exception as e:
            raise ValueError(f"Failed to load profile from {profile_file}: {e}") from e
