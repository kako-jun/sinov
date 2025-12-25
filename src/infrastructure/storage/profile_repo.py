"""
ボットプロフィールリポジトリ
"""

from pathlib import Path

import yaml

from ...domain.bot_utils import format_bot_name
from ...domain.models import BotProfile


class ProfileRepository:
    """住人フォルダからボットプロフィールを読み込む"""

    def __init__(self, residents_dir: Path, backend_dir: Path | None = None):
        self.residents_dir = residents_dir
        self.backend_dir = backend_dir

    def load_all(self) -> list[BotProfile]:
        """全住人のプロフィールを読み込み"""
        profiles: list[BotProfile] = []

        if not self.residents_dir.exists():
            print(f"⚠️  Residents directory not found: {self.residents_dir}")
            return profiles

        # bot001, bot002, ... の順でソート
        resident_dirs = sorted(
            [d for d in self.residents_dir.iterdir() if d.is_dir() and d.name.startswith("bot")],
            key=lambda d: d.name
        )

        if not resident_dirs:
            print(f"⚠️  No resident folders found in {self.residents_dir}")
            return profiles

        for resident_dir in resident_dirs:
            profile_file = resident_dir / "profile.yaml"
            if not profile_file.exists():
                print(f"⚠️  No profile.yaml in {resident_dir.name}, skipping...")
                continue

            try:
                profile = self.load(profile_file)
                profiles.append(profile)
            except Exception as e:
                print(f"⚠️  Failed to load {resident_dir.name}: {e}, skipping...")
                continue

        return profiles

    def load(self, profile_file: Path) -> BotProfile:
        """単一プロフィールを読み込み"""
        try:
            with open(profile_file) as f:
                data = yaml.safe_load(f)

            profile = BotProfile.model_validate(data)
            return profile
        except Exception as e:
            raise ValueError(f"Failed to load profile from {profile_file}: {e}") from e

    def load_by_id(self, bot_id: int) -> BotProfile | None:
        """IDで住人プロフィールを読み込み"""
        resident_dir = self.residents_dir / format_bot_name(bot_id)
        profile_file = resident_dir / "profile.yaml"

        if not profile_file.exists():
            return None

        return self.load(profile_file)

    def get_resident_dir(self, bot_id: int) -> Path:
        """住人のフォルダパスを取得"""
        return self.residents_dir / format_bot_name(bot_id)
