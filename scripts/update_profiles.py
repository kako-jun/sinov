#!/usr/bin/env python3
"""
プロファイルに新しいフィールド（traits_detail, style, habits, prompts）を追加するスクリプト
"""

import random
from pathlib import Path

import yaml

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
RESIDENTS_DIR = PROJECT_ROOT / "bots" / "residents"

# 職業ごとのスタイル傾向
OCCUPATION_STYLES = {
    "イラストレーター": ["otaku", "normal", "enthusiastic"],
    "漫画家": ["otaku", "normal"],
    "デザイナー": ["normal", "polite"],
    "小説家": ["normal", "polite"],
    "ライター": ["normal", "polite"],
    "詩人": ["normal", "polite"],
    "作曲家": ["normal", "otaku"],
    "DTMer": ["normal", "young"],
    "サウンドエンジニア": ["normal", "terse"],
    "ゲーム開発者": ["normal", "otaku", "young"],
    "プログラマー": ["normal", "terse"],
    "エンジニア": ["normal", "terse"],
    "学生": ["young", "normal"],
    "VTuber": ["otaku", "young", "enthusiastic"],
}

# 職業ごとの習慣傾向
OCCUPATION_HABITS = {
    "イラストレーター": ["wip_poster", "emoji_heavy"],
    "漫画家": ["wip_poster"],
    "デザイナー": ["tip_sharer", "wip_poster"],
    "小説家": ["self_deprecating"],
    "ライター": ["tip_sharer", "news_summarizer"],
    "ゲーム開発者": ["wip_poster", "tip_sharer"],
    "プログラマー": ["tip_sharer"],
    "エンジニア": ["tip_sharer", "news_summarizer"],
    "学生": ["question_asker"],
    "VTuber": ["emoji_heavy", "enthusiastic"],
}

# 職業ごとのプロンプト
OCCUPATION_PROMPTS = {
    "イラストレーター": {
        "positive": ["絵の話が多い", "色彩や構図について語る", "制作過程をつぶやく"],
        "negative": ["他人の絵を批判しない", "締め切りの愚痴ばかりにならない"],
    },
    "漫画家": {
        "positive": ["漫画制作について語る", "ストーリーやキャラについて語る"],
        "negative": ["ネタバレを書かない", "他作品を貶さない"],
    },
    "小説家": {
        "positive": ["執筆について語る", "言葉選びにこだわりがある"],
        "negative": ["他人の作品を批判しない"],
    },
    "ゲーム開発者": {
        "positive": ["ゲーム開発について語る", "技術的な話題を共有する"],
        "negative": ["特定のプラットフォームを批判しない"],
    },
    "エンジニア": {
        "positive": ["技術的な発見を共有する", "学びを共有する"],
        "negative": ["技術マウントを取らない", "他の技術を批判しない"],
    },
}


def generate_traits_detail(personality_type: str, emotional_range: int) -> dict:
    """性格タイプと感情表現幅から詳細な性格パラメータを生成"""

    # ベース値
    base = 0.5

    # 感情表現幅から調整
    expressiveness = emotional_range / 10

    # 性格タイプから調整
    type_adjustments = {
        "陽気": {
            "optimism": 0.3,
            "sociability": 0.2,
            "activeness": 0.2,
        },
        "クール": {
            "optimism": -0.1,
            "sociability": -0.2,
            "expressiveness": -0.3,
        },
        "真面目": {
            "persistence": 0.2,
            "intelligence": 0.1,
        },
        "穏やか": {
            "sensitivity": 0.2,
            "optimism": 0.1,
        },
        "内向的": {
            "sociability": -0.3,
            "sensitivity": 0.2,
        },
        "情熱的": {
            "activeness": 0.3,
            "expressiveness": 0.2,
            "optimism": 0.2,
        },
    }

    traits = {
        "activeness": base + random.uniform(-0.2, 0.2),
        "curiosity": base + random.uniform(-0.2, 0.2),
        "sociability": base + random.uniform(-0.2, 0.2),
        "sensitivity": base + random.uniform(-0.2, 0.2),
        "optimism": base + random.uniform(-0.2, 0.2),
        "creativity": base + random.uniform(-0.2, 0.2),
        "persistence": base + random.uniform(-0.2, 0.2),
        "expressiveness": expressiveness,
        "expertise": base + random.uniform(-0.2, 0.2),
        "intelligence": base + random.uniform(-0.2, 0.2),
        "feedback_sensitivity": base + random.uniform(-0.2, 0.2),
    }

    # 性格タイプによる調整を適用
    adjustments = type_adjustments.get(personality_type, {})
    for key, adj in adjustments.items():
        if key in traits:
            traits[key] += adj

    # 0.0〜1.0の範囲にクランプ
    for key in traits:
        traits[key] = round(max(0.0, min(1.0, traits[key])), 1)

    return traits


def get_style_for_occupation(occupation: str) -> str:
    """職業からスタイルを決定"""
    for occ_key, styles in OCCUPATION_STYLES.items():
        if occ_key in occupation:
            return random.choice(styles)
    return "normal"


def get_habits_for_occupation(occupation: str) -> list:
    """職業から習慣を決定"""
    for occ_key, habits in OCCUPATION_HABITS.items():
        if occ_key in occupation:
            # 0〜2個の習慣をランダムに選択
            num = random.randint(0, min(2, len(habits)))
            return random.sample(habits, num)
    return []


def get_prompts_for_occupation(occupation: str) -> dict:
    """職業からプロンプトを取得"""
    for occ_key, prompts in OCCUPATION_PROMPTS.items():
        if occ_key in occupation:
            return prompts
    return {"positive": [], "negative": []}


def update_profile(profile_path: Path) -> bool:
    """プロファイルを更新"""
    with open(profile_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # 既に更新済みの場合はスキップ
    if "traits_detail" in data:
        return False

    npc_id = data["id"]
    name = data["name"]
    personality = data.get("personality", {})
    background = data.get("background", {})

    personality_type = personality.get("type", "普通")
    emotional_range = personality.get("emotional_range", 5)
    occupation = background.get("occupation", "")

    # 新しいフィールドを生成
    traits_detail = generate_traits_detail(personality_type, emotional_range)
    style = get_style_for_occupation(occupation)
    habits = get_habits_for_occupation(occupation)
    prompts = get_prompts_for_occupation(occupation)

    # YAMLに追加（コメント付きで手動追加）
    # 元のYAMLを読み込み、末尾に追加
    with open(profile_path, encoding="utf-8") as f:
        content = f.read()

    # 末尾に新しいフィールドを追加
    additions = f"""
# 詳細な性格パラメータ（0.0〜1.0）
traits_detail:
  activeness: {traits_detail['activeness']}
  curiosity: {traits_detail['curiosity']}
  sociability: {traits_detail['sociability']}
  sensitivity: {traits_detail['sensitivity']}
  optimism: {traits_detail['optimism']}
  creativity: {traits_detail['creativity']}
  persistence: {traits_detail['persistence']}
  expressiveness: {traits_detail['expressiveness']}
  expertise: {traits_detail['expertise']}
  intelligence: {traits_detail['intelligence']}
  feedback_sensitivity: {traits_detail['feedback_sensitivity']}

# 文体スタイル
style: {style}
"""

    if habits:
        additions += f"""
# 特殊な習慣
habits:
"""
        for h in habits:
            additions += f"  - {h}\n"
    else:
        additions += """
# 特殊な習慣
habits: []
"""

    if prompts["positive"] or prompts["negative"]:
        additions += """
# 個人プロンプト
prompts:
"""
        if prompts["positive"]:
            additions += "  positive:\n"
            for p in prompts["positive"]:
                additions += f'    - "{p}"\n'
        if prompts["negative"]:
            additions += "  negative:\n"
            for p in prompts["negative"]:
                additions += f'    - "{p}"\n'

    # 書き込み
    with open(profile_path, "w", encoding="utf-8") as f:
        f.write(content.rstrip() + "\n" + additions)

    print(f"  Updated: bot{npc_id:03d} ({name}) - style={style}, habits={habits}")
    return True


def main():
    """メイン処理"""
    print("Updating profiles with new fields...")

    updated = 0
    skipped = 0

    for resident_dir in sorted(RESIDENTS_DIR.iterdir()):
        if not resident_dir.is_dir() or not resident_dir.name.startswith("bot"):
            continue

        profile_path = resident_dir / "profile.yaml"
        if not profile_path.exists():
            continue

        if update_profile(profile_path):
            updated += 1
        else:
            skipped += 1

    print(f"\nDone! Updated: {updated}, Skipped (already updated): {skipped}")


if __name__ == "__main__":
    main()
