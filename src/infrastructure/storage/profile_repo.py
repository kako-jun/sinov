"""
NPCプロフィールリポジトリ
"""

from pathlib import Path

import yaml

from ...domain import NpcProfile, Prompts, format_npc_name


class ProfileRepository:
    """住人フォルダからNPCプロフィールを読み込む"""

    def __init__(
        self,
        residents_dir: Path,
        backend_dir: Path | None = None,
        bots_dir: Path | None = None,
    ):
        self.residents_dir = residents_dir
        self.backend_dir = backend_dir
        self.bots_dir = bots_dir or residents_dir.parent
        self._common_prompts: Prompts | None = None

    def load_common_prompts(self) -> Prompts:
        """共通プロンプトを読み込み（キャッシュあり）"""
        if self._common_prompts is not None:
            return self._common_prompts

        common_file = self.bots_dir / "_common.yaml"
        if not common_file.exists():
            self._common_prompts = Prompts()
            return self._common_prompts

        with open(common_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        self._common_prompts = Prompts(
            positive=data.get("positive", []),
            negative=data.get("negative", []),
        )
        return self._common_prompts

    def get_merged_prompts(self, profile: NpcProfile) -> Prompts:
        """共通プロンプト + 個人プロンプトをマージ"""
        common = self.load_common_prompts()
        personal = profile.prompts or Prompts()

        return Prompts(
            positive=common.positive + personal.positive,
            negative=common.negative + personal.negative,
        )

    def load_all(self, include_backend: bool = True) -> list[NpcProfile]:
        """全住人のプロフィールを読み込み"""
        profiles: list[NpcProfile] = []

        if not self.residents_dir.exists():
            print(f"⚠️  Residents directory not found: {self.residents_dir}")
            return profiles

        # npc001, bot002, ... の順でソート
        resident_dirs = sorted(
            [d for d in self.residents_dir.iterdir() if d.is_dir() and d.name.startswith("npc")],
            key=lambda d: d.name,
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
                # posts: false なら読み込まない（段階的リリース用）
                if not profile.posts:
                    continue
                profiles.append(profile)
            except Exception as e:
                print(f"⚠️  Failed to load {resident_dir.name}: {e}, skipping...")
                continue

        # バックエンドNPC（記者・レビューア）も読み込み
        if include_backend and self.backend_dir and self.backend_dir.exists():
            backend_profiles = self._load_backend_npcs()
            profiles.extend(backend_profiles)

        return profiles

    def _load_backend_npcs(self) -> list[NpcProfile]:
        """バックエンドNPC（記者・レビューア）を読み込み"""
        profiles: list[NpcProfile] = []

        if not self.backend_dir or not self.backend_dir.exists():
            return profiles

        for backend_dir in sorted(self.backend_dir.iterdir()):
            if not backend_dir.is_dir():
                continue

            profile_file = backend_dir / "profile.yaml"
            if not profile_file.exists():
                continue

            try:
                profile = self.load(profile_file)
                # バックエンドNPCとしてマーク
                profile.is_backend = True
                # posts: true のバックエンドNPCのみ読み込み
                if profile.posts:
                    profiles.append(profile)
            except Exception as e:
                print(f"⚠️  Failed to load backend {backend_dir.name}: {e}, skipping...")
                continue

        return profiles

    def load(self, profile_file: Path) -> NpcProfile:
        """単一プロフィールを読み込み"""
        try:
            with open(profile_file) as f:
                data = yaml.safe_load(f)

            profile = NpcProfile.model_validate(data)
            return profile
        except Exception as e:
            raise ValueError(f"Failed to load profile from {profile_file}: {e}") from e

    def load_by_id(self, npc_id: int) -> NpcProfile | None:
        """IDで住人プロフィールを読み込み"""
        resident_dir = self.residents_dir / format_npc_name(npc_id)
        profile_file = resident_dir / "profile.yaml"

        if not profile_file.exists():
            return None

        return self.load(profile_file)

    def get_resident_dir(self, npc_id: int) -> Path:
        """住人のフォルダパスを取得"""
        return self.residents_dir / format_npc_name(npc_id)
