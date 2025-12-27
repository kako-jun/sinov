#!/usr/bin/env python3
"""
Window Color生成スクリプト

約85人のNPCにMYPACE独自機能のWindow Colorを設定。
性格タイプと興味分野に基づいて一貫性のあるカラーテーマを付与。
全キャラがユニークな色を持つ。
"""

import random
from pathlib import Path

import yaml


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """HEXカラーをRGBタプルに変換"""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """RGBをHEXカラーに変換"""
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def adjust_color(hex_color: str, offset: int) -> str:
    """色を微調整（明度を少し変える程度、色相は維持）"""
    r, g, b = hex_to_rgb(hex_color)
    # オフセットに基づいて各成分を微調整（-30 ~ +30程度）
    adjustment = (offset % 61) - 30  # -30 to +30
    r = max(0, min(255, r + adjustment))
    g = max(0, min(255, g + adjustment + (offset % 11) - 5))
    b = max(0, min(255, b + adjustment + (offset % 7) - 3))
    return rgb_to_hex(r, g, b)


# =============================================================================
# カテゴリ別ベースカラー（各カテゴリに複数のベース色）
# =============================================================================

CATEGORY_BASE_COLORS = {
    "blue": [
        "#4A90D9",
        "#5B9BD5",
        "#2C3E50",
        "#1E90FF",
        "#00CED1",
        "#4169E1",
        "#87CEEB",
        "#6495ED",
    ],
    "purple": [
        "#9370DB",
        "#8B008B",
        "#BA55D3",
        "#DDA0DD",
        "#E6E6FA",
        "#FF69B4",
        "#DA70D6",
        "#9932CC",
    ],
    "warm": [
        "#FF8C00",
        "#FF6347",
        "#FF7F50",
        "#FFA500",
        "#FFD700",
        "#DC143C",
        "#CD853F",
        "#F4A460",
    ],
    "green": [
        "#3CB371",
        "#228B22",
        "#32CD32",
        "#20B2AA",
        "#98FB98",
        "#90EE90",
        "#2E8B57",
        "#66CDAA",
    ],
    "neon": [
        "#00FFFF",
        "#FF00FF",
        "#39FF14",
        "#FF073A",
        "#FF6EC7",
        "#FFFF00",
        "#7FFF00",
        "#00FF7F",
    ],
    "metallic": [
        "#DAA520",
        "#8B4513",
        "#A0522D",
        "#DEB887",
        "#C0C0C0",
        "#B8860B",
        "#CD7F32",
        "#D2691E",
    ],
    "gray": [
        "#708090",
        "#696969",
        "#778899",
        "#36454F",
        "#A9A9A9",
        "#808080",
        "#C0C0C0",
        "#D3D3D3",
    ],
}

# パターンタイプ
PATTERN_TYPES = [
    "solid",  # 4角同色
    "gradient_v",  # 上下グラデーション
    "bottom_only",  # 下角のみ
    "diagonal",  # 対角線
    "left_side",  # 左側のみ
    "right_side",  # 右側のみ
    "top_only",  # 上角のみ
    "gradient_h",  # 左右グラデーション
]

# 国旗モチーフ（5人用）- これは固定色
FLAG_PALETTES = {
    "italy": {
        "top_left": "#009246",
        "top_right": "#CE2B37",
        "bottom_left": "#009246",
        "bottom_right": "#CE2B37",
    },
    "france": {
        "top_left": "#0055A4",
        "top_right": "#EF4135",
        "bottom_left": "#0055A4",
        "bottom_right": "#EF4135",
    },
    "germany": {
        "top_left": "#000000",
        "top_right": "#DD0000",
        "bottom_left": "#FFCC00",
        "bottom_right": "#FFCC00",
    },
    "sweden": {
        "top_left": "#006AA7",
        "top_right": "#FECC00",
        "bottom_left": "#FECC00",
        "bottom_right": "#006AA7",
    },
    "brazil": {
        "top_left": "#009B3A",
        "top_right": "#FFDF00",
        "bottom_left": "#FFDF00",
        "bottom_right": "#009B3A",
    },
}

# 使用済み色の組み合わせを追跡
used_color_combinations: set[str] = set()


def generate_unique_palette(category: str, npc_id: int, attempt: int = 0) -> dict:
    """ユニークなカラーパレットを生成"""
    base_colors = CATEGORY_BASE_COLORS.get(category, CATEGORY_BASE_COLORS["blue"])

    # IDとattemptに基づいてベース色とパターンを選択
    random.seed(npc_id * 17 + attempt * 31)

    base_idx = (npc_id + attempt) % len(base_colors)
    base_color = base_colors[base_idx]

    # 第2色（グラデーション用）
    second_idx = (npc_id + attempt + 3) % len(base_colors)
    second_color = base_colors[second_idx]
    if second_color == base_color:
        second_idx = (second_idx + 1) % len(base_colors)
        second_color = base_colors[second_idx]

    # NPCごとに色を微調整してユニーク化
    offset = (npc_id * 7 + attempt * 13) % 30 - 15  # -15 ~ +15
    color1 = adjust_color(base_color, offset)
    color2 = adjust_color(second_color, offset + 5)

    # パターン選択
    pattern_idx = (npc_id + attempt) % len(PATTERN_TYPES)
    pattern = PATTERN_TYPES[pattern_idx]

    # パターンに応じてパレット生成
    if pattern == "solid":
        palette = {
            "top_left": color1,
            "top_right": color1,
            "bottom_left": color1,
            "bottom_right": color1,
        }
    elif pattern == "gradient_v":
        palette = {
            "top_left": color1,
            "top_right": color1,
            "bottom_left": color2,
            "bottom_right": color2,
        }
    elif pattern == "bottom_only":
        palette = {
            "top_left": None,
            "top_right": None,
            "bottom_left": color1,
            "bottom_right": color1,
        }
    elif pattern == "diagonal":
        palette = {
            "top_left": color1,
            "top_right": None,
            "bottom_left": None,
            "bottom_right": color1,
        }
    elif pattern == "left_side":
        palette = {
            "top_left": color1,
            "top_right": None,
            "bottom_left": color1,
            "bottom_right": None,
        }
    elif pattern == "right_side":
        palette = {
            "top_left": None,
            "top_right": color1,
            "bottom_left": None,
            "bottom_right": color1,
        }
    elif pattern == "top_only":
        palette = {
            "top_left": color1,
            "top_right": color1,
            "bottom_left": None,
            "bottom_right": None,
        }
    elif pattern == "gradient_h":
        palette = {
            "top_left": color1,
            "top_right": color2,
            "bottom_left": color1,
            "bottom_right": color2,
        }
    else:
        palette = {
            "top_left": color1,
            "top_right": color1,
            "bottom_left": color1,
            "bottom_right": color1,
        }

    return palette


def get_palette_signature(palette: dict) -> str:
    """パレットのシグネチャ（重複チェック用）"""
    parts = [
        palette.get("top_left") or "None",
        palette.get("top_right") or "None",
        palette.get("bottom_left") or "None",
        palette.get("bottom_right") or "None",
    ]
    return "|".join(parts)


def get_unique_palette(category: str, npc_id: int) -> dict:
    """重複しないユニークなパレットを取得"""
    for attempt in range(100):  # 最大100回試行
        palette = generate_unique_palette(category, npc_id, attempt)
        signature = get_palette_signature(palette)

        if signature not in used_color_combinations:
            used_color_combinations.add(signature)
            return palette

    # 万が一重複が避けられない場合は微調整
    palette = generate_unique_palette(category, npc_id, npc_id * 100)
    # 強制的にユニーク化
    if palette.get("top_left"):
        palette["top_left"] = adjust_color(palette["top_left"], npc_id)
    return palette


# =============================================================================
# NPCカテゴリ判定
# =============================================================================


def get_npc_category(profile: dict) -> str:
    """NPCの興味・性格からカテゴリを判定"""
    topics = profile.get("interests", {}).get("topics", [])
    topics_str = " ".join(topics).lower()

    personality_type = profile.get("personality", {}).get("type", "")

    # 映像/アニメーション系
    if any(
        kw in topics_str
        for kw in ["motion", "映像", "after effects", "アニメーション", "mv", "動画"]
    ):
        return "neon"

    # 音楽系
    if any(
        kw in topics_str
        for kw in ["dtm", "作曲", "音楽", "シンセ", "bgm", "edm", "daw", "ボカロ", "vocaloid"]
    ):
        return "purple"

    # 3D/CG系
    if any(kw in topics_str for kw in ["blender", "3d", "unity", "unreal", "cg", "モデリング"]):
        return "metallic"

    # ゲーム開発系
    if any(kw in topics_str for kw in ["ゲーム", "game", "godot", "rpg", "インディー"]):
        return "green"

    # イラスト/デザイン系
    if any(
        kw in topics_str
        for kw in ["イラスト", "絵", "デザイン", "ui", "ux", "figma", "photoshop", "clip"]
    ):
        return "warm"

    # プログラマー系
    if any(
        kw in topics_str
        for kw in [
            "web",
            "typescript",
            "python",
            "rust",
            "react",
            "開発",
            "プログラ",
            "コード",
            "api",
        ]
    ):
        return "blue"

    # 性格ベース
    if personality_type == "クール":
        return "gray"

    # デフォルトは青
    return "blue"


# =============================================================================
# ファイル操作
# =============================================================================


def get_all_npc_dirs() -> list[Path]:
    """全NPCディレクトリを取得（residents + backend）"""
    base = Path(__file__).parent.parent / "npcs"
    dirs = []

    residents_dir = base / "residents"
    if residents_dir.exists():
        dirs.extend(sorted(residents_dir.iterdir()))

    backend_dir = base / "backend"
    if backend_dir.exists():
        dirs.extend(sorted(backend_dir.iterdir()))

    return [d for d in dirs if d.is_dir() and d.name.startswith("npc")]


def load_profile(profile_path: Path) -> dict | None:
    """profile.yamlを読み込み"""
    if not profile_path.exists():
        return None
    with open(profile_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def update_profile_yaml(profile_path: Path, window_color: dict | None) -> bool:
    """profile.yamlにwindow_colorを追加/更新"""
    if not profile_path.exists():
        return False

    with open(profile_path, encoding="utf-8") as f:
        content = f.read()

    data = yaml.safe_load(content)

    if window_color:
        # Noneを除いた有効なカラーのみ設定
        color_data = {k: v for k, v in window_color.items() if v is not None}
        if color_data:
            data["window_color"] = color_data
        elif "window_color" in data:
            del data["window_color"]
    elif "window_color" in data:
        del data["window_color"]

    with open(profile_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return True


# =============================================================================
# メイン処理
# =============================================================================


def main():
    print("🎨 Window Color Generator (Unique Colors)")
    print("=" * 60)

    npc_dirs = get_all_npc_dirs()
    print(f"Found {len(npc_dirs)} NPCs total")

    # バックエンド（reporter/reviewer）を除外
    resident_dirs = [d for d in npc_dirs if "backend" not in str(d)]
    backend_dirs = [d for d in npc_dirs if "backend" in str(d)]

    print(f"  Residents: {len(resident_dirs)}")
    print(f"  Backend (excluded): {len(backend_dirs)}")

    # 国旗モチーフ5人を選択
    flag_npc_ids = {5, 15, 25, 45, 75}
    flag_countries = list(FLAG_PALETTES.keys())

    # 色なし15人を選択（ランダムに、国旗モチーフを除外）
    random.seed(42)
    available_ids = [i for i in range(1, len(resident_dirs) + 1) if i not in flag_npc_ids]
    no_color_ids = set(random.sample(available_ids, 15))

    print(f"\n  No color: {sorted(no_color_ids)}")
    print(f"  Flag motif: {sorted(flag_npc_ids)}")
    print()

    updated = 0
    skipped = 0
    categories_count: dict[str, int] = {}

    # 国旗パレットを使用済みに追加
    for country, palette in FLAG_PALETTES.items():
        used_color_combinations.add(get_palette_signature(palette))

    for npc_dir in npc_dirs:
        npc_name = npc_dir.name
        npc_id = int(npc_name.replace("npc", ""))
        profile_path = npc_dir / "profile.yaml"

        # バックエンドは除外
        if "backend" in str(npc_dir):
            print(f"  ⏭️  {npc_name}: skipped (backend)")
            skipped += 1
            continue

        # 色なし対象
        if npc_id in no_color_ids:
            # 既存のwindow_colorを削除
            update_profile_yaml(profile_path, None)
            print(f"  ⏭️  {npc_name}: skipped (no color)")
            skipped += 1
            continue

        profile = load_profile(profile_path)
        if not profile:
            print(f"  ❌ {npc_name}: profile not found")
            skipped += 1
            continue

        # 国旗モチーフ
        if npc_id in flag_npc_ids:
            country_idx = sorted(flag_npc_ids).index(npc_id)
            country = flag_countries[country_idx]
            color = FLAG_PALETTES[country]
            category = f"flag:{country}"
        else:
            # カテゴリ判定してユニークパレット取得
            category = get_npc_category(profile)
            color = get_unique_palette(category, npc_id)

        categories_count[category] = categories_count.get(category, 0) + 1

        if update_profile_yaml(profile_path, color):
            color_values = [v for v in color.values() if v]
            color_preview = ", ".join(color_values[:2])
            if len(color_values) > 2:
                color_preview += f" (+{len(color_values) - 2})"
            print(f"  ✅ {npc_name} [{category}]: {color_preview}")
            updated += 1
        else:
            skipped += 1

    print()
    print("=" * 60)
    print(f"✅ Updated: {updated}")
    print(f"⏭️  Skipped: {skipped}")
    print(f"🎨 Unique color combinations: {len(used_color_combinations)}")
    print()
    print("📊 Category distribution:")
    for cat, count in sorted(categories_count.items()):
        print(f"   {cat}: {count}")


if __name__ == "__main__":
    main()
