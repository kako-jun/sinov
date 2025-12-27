#!/usr/bin/env python3
"""IT系NPCのMarkdown/コードブロック設定を更新するスクリプト"""

import re
from pathlib import Path

# IT系の職業キーワード
IT_OCCUPATIONS = [
    "エンジニア",
    "プログラマー",
    "開発者",
    "デベロッパー",
    "SRE",
    "DBA",
    "CTO",
    "研究者",
    "データ",
    "ML",
    "AI",
    "インフラ",
    "DevOps",
    "ブロックチェーン",
    "セキュリティ",
]

# コードブロックを使いそうな職業
CODE_BLOCK_OCCUPATIONS = [
    "エンジニア",
    "プログラマー",
    "開発者",
    "デベロッパー",
    "SRE",
    "DevOps",
    "ブロックチェーン",
    "組み込み",
]


def is_it_occupation(occupation: str) -> bool:
    """IT系の職業かどうか判定"""
    return any(keyword in occupation for keyword in IT_OCCUPATIONS)


def should_use_code_blocks(occupation: str) -> bool:
    """コードブロックを使う職業かどうか判定"""
    return any(keyword in occupation for keyword in CODE_BLOCK_OCCUPATIONS)


def update_profile(profile_path: Path) -> tuple[bool, bool]:
    """プロフィールのMarkdown設定を更新

    Returns:
        (markdown_updated, code_blocks_updated)
    """
    content = profile_path.read_text(encoding="utf-8")

    # 職業を抽出
    occupation_match = re.search(r'occupation:\s*"([^"]+)"', content)
    if not occupation_match:
        return False, False

    occupation = occupation_match.group(1)
    markdown_updated = False
    code_blocks_updated = False

    # IT系ならuse_markdown: trueに
    if is_it_occupation(occupation):
        if "use_markdown: false" in content:
            content = content.replace("use_markdown: false", "use_markdown: true")
            markdown_updated = True

    # コードブロック使う職業ならuse_code_blocks: trueに
    if should_use_code_blocks(occupation):
        if "use_code_blocks: false" in content:
            content = content.replace("use_code_blocks: false", "use_code_blocks: true")
            code_blocks_updated = True

    if markdown_updated or code_blocks_updated:
        profile_path.write_text(content, encoding="utf-8")

    return markdown_updated, code_blocks_updated


def main():
    residents_dir = Path("npcs/residents")
    markdown_count = 0
    code_blocks_count = 0

    print("=== IT系NPCのMarkdown/コードブロック設定を更新 ===\n")

    for npc_dir in sorted(residents_dir.iterdir()):
        if not npc_dir.is_dir():
            continue

        profile_path = npc_dir / "profile.yaml"
        if not profile_path.exists():
            continue

        md_updated, cb_updated = update_profile(profile_path)

        if md_updated or cb_updated:
            # 職業を取得して表示
            content = profile_path.read_text(encoding="utf-8")
            name_match = re.search(r'name:\s*"([^"]+)"', content)
            occ_match = re.search(r'occupation:\s*"([^"]+)"', content)
            name = name_match.group(1) if name_match else npc_dir.name
            occupation = occ_match.group(1) if occ_match else "?"

            updates = []
            if md_updated:
                updates.append("markdown")
                markdown_count += 1
            if cb_updated:
                updates.append("code_blocks")
                code_blocks_count += 1

            print(f"✓ {name} ({occupation}): {', '.join(updates)}")

    print(f"\n合計: markdown={markdown_count}, code_blocks={code_blocks_count}")


if __name__ == "__main__":
    main()
