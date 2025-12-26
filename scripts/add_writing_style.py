#!/usr/bin/env python3
"""
プロファイルにwriting_styleフィールドを追加するスクリプト

文章スタイル設定:
- typo_rate: 誤字率（0.0〜0.1）
- line_break: 改行スタイル（none, minimal, sentence, paragraph）
- punctuation: 句読点スタイル（full, comma_only, period_only, none）
- quirks: 文章の癖リスト
"""

import random
from pathlib import Path

import yaml

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
RESIDENTS_DIR = PROJECT_ROOT / "bots" / "residents"

# 性格タイプごとの改行スタイル傾向
PERSONALITY_LINE_BREAK = {
    "陰キャ": ["none"],  # 改行なしで一気に書く
    "内向的": ["none", "minimal"],
    "静か": ["minimal"],
    "控えめ": ["minimal"],
    "おとなしい": ["minimal", "none"],
    "活発": ["sentence", "paragraph"],
    "元気": ["sentence", "paragraph"],
    "明るい": ["sentence", "minimal"],
    "社交的": ["sentence", "minimal"],
    "熱血": ["paragraph"],
    "マイペース": ["minimal"],
    "のんびり": ["paragraph"],  # 段落で区切る
}

# 文体ごとの句読点スタイル傾向
STYLE_PUNCTUATION = {
    "young": ["none", "comma_only"],  # 若者は句読点少なめ
    "2ch": ["none"],  # 2ch風は句読点使わない
    "otaku": ["full", "comma_only"],
    "polite": ["full"],  # 丁寧語は句読点しっかり
    "terse": ["none", "comma_only"],  # 簡潔は句読点少なめ
    "ojisan": ["full"],  # おじさんは句読点使う
    "normal": ["full", "comma_only"],
}

# 文体ごとの癖傾向
STYLE_QUIRKS = {
    "young": ["w_heavy", "abbreviation"],
    "2ch": ["w_heavy", "kusa"],
    "otaku": ["ellipsis_heavy", "exclamation_heavy"],
    "polite": ["suffix_ne"],
    "terse": [],
    "ojisan": ["exclamation_heavy", "tilde_heavy"],
    "normal": [],
}

# 職業ごとの追加癖
OCCUPATION_QUIRKS = {
    "エンジニア": ["parentheses", "arrow"],  # 補足や流れの説明が多い
    "プログラマー": ["parentheses", "arrow"],
    "ライター": ["parentheses"],
    "デザイナー": ["katakana_english"],  # カタカナ英語多い
    "VTuber": ["tilde_heavy", "exclamation_heavy"],
    "DTMer": ["katakana_english"],
    "学生": ["w_heavy", "abbreviation"],
}


def get_line_break_style(personality_traits: list, personality_type: str) -> str:
    """性格から改行スタイルを決定"""
    # 性格特性をチェック
    for trait in personality_traits:
        for key, styles in PERSONALITY_LINE_BREAK.items():
            if key in trait:
                return random.choice(styles)

    # 性格タイプをチェック
    for key, styles in PERSONALITY_LINE_BREAK.items():
        if key in personality_type:
            return random.choice(styles)

    # デフォルト
    return random.choice(["minimal", "sentence"])


def get_punctuation_style(style: str) -> str:
    """文体から句読点スタイルを決定"""
    styles = STYLE_PUNCTUATION.get(style, ["full"])
    return random.choice(styles)


def get_quirks(style: str, occupation: str) -> list:
    """文体と職業から癖を決定"""
    quirks = set()

    # 文体ベースの癖
    style_q = STYLE_QUIRKS.get(style, [])
    if style_q:
        # 0〜2個選択
        num = random.randint(0, min(2, len(style_q)))
        quirks.update(random.sample(style_q, num))

    # 職業ベースの癖
    for occ_key, occ_quirks in OCCUPATION_QUIRKS.items():
        if occ_key in occupation:
            # 0〜1個追加
            if occ_quirks and random.random() < 0.5:
                quirks.add(random.choice(occ_quirks))
            break

    return list(quirks)


def get_typo_rate(personality_type: str, occupation: str) -> float:
    """誤字率を決定"""
    # 基本は0（誤字なし）
    base = 0.0

    # 性格による調整
    if "慌ただしい" in personality_type or "せっかち" in personality_type:
        base = 0.02
    elif "のんびり" in personality_type or "マイペース" in personality_type:
        base = 0.01

    # 職業による調整（ライターや編集者は誤字少ない）
    if "ライター" in occupation or "小説家" in occupation or "編集" in occupation:
        base = 0.0
    elif "学生" in occupation:
        base = max(base, 0.01)

    # ランダム要素
    if random.random() < 0.2:  # 20%の人は少し誤字
        base = max(base, 0.01)

    return round(base, 2)


def update_profile(profile_path: Path) -> bool:
    """プロファイルにwriting_styleを追加"""
    with open(profile_path, encoding="utf-8") as f:
        content = f.read()

    # 既に更新済みの場合はスキップ
    if "writing_style:" in content:
        return False

    with open(profile_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    personality = data.get("personality", {})
    background = data.get("background", {})
    style = data.get("style", "normal")

    personality_type = personality.get("type", "普通")
    personality_traits = personality.get("traits", [])
    occupation = background.get("occupation", "")

    # writing_styleを生成
    typo_rate = get_typo_rate(personality_type, occupation)
    line_break = get_line_break_style(personality_traits, personality_type)
    punctuation = get_punctuation_style(style)
    quirks = get_quirks(style, occupation)

    # 末尾に新しいフィールドを追加
    additions = """
# 文章スタイル設定
writing_style:
"""
    additions += f"  typo_rate: {typo_rate}\n"
    additions += f"  line_break: {line_break}\n"
    additions += f"  punctuation: {punctuation}\n"

    if quirks:
        additions += "  quirks:\n"
        for q in quirks:
            additions += f"    - {q}\n"
    else:
        additions += "  quirks: []\n"

    # ファイルに追記
    with open(profile_path, "a", encoding="utf-8") as f:
        f.write(additions)

    print(f"  Updated: {profile_path.name}")
    print(f"    typo_rate: {typo_rate}, line_break: {line_break}, punctuation: {punctuation}")
    if quirks:
        print(f"    quirks: {quirks}")

    return True


def main():
    """メイン処理"""
    print("Adding writing_style to profiles...")
    print()

    updated = 0
    skipped = 0

    for bot_dir in sorted(RESIDENTS_DIR.iterdir()):
        if not bot_dir.is_dir():
            continue

        profile_path = bot_dir / "profile.yaml"
        if not profile_path.exists():
            continue

        if update_profile(profile_path):
            updated += 1
        else:
            skipped += 1

    print()
    print(f"Done! Updated: {updated}, Skipped: {skipped}")


if __name__ == "__main__":
    main()
