#!/usr/bin/env python3
"""パラメータを統合するスクリプト

統合:
- intelligence → expertise に統合（平均値）して intelligence 削除
- feedback_sensitivity → sensitivity に統合（平均値）して feedback_sensitivity 削除

追加:
- eccentricity（不思議ちゃん度）
- contrarian（逆張り度）
"""

import random
import re
from pathlib import Path

import yaml


def merge_parameters(profile_path: Path) -> bool:
    """パラメータを統合して更新"""
    content = profile_path.read_text(encoding="utf-8")

    # YAMLをパース
    data = yaml.safe_load(content)
    if not data or "traits_detail" not in data:
        return False

    traits = data["traits_detail"]
    modified = False

    # 1. intelligence → expertise に統合
    if "intelligence" in traits and "expertise" in traits:
        old_expertise = traits["expertise"]
        old_intelligence = traits["intelligence"]
        # 平均値を新しいexpertiseに
        new_expertise = round((old_expertise + old_intelligence) / 2, 1)
        traits["expertise"] = new_expertise
        del traits["intelligence"]
        modified = True
        print(f"  expertise: {old_expertise} + intelligence: {old_intelligence} → {new_expertise}")

    # 2. feedback_sensitivity → sensitivity に統合
    if "feedback_sensitivity" in traits and "sensitivity" in traits:
        old_sensitivity = traits["sensitivity"]
        old_feedback = traits["feedback_sensitivity"]
        # 平均値を新しいsensitivityに
        new_sensitivity = round((old_sensitivity + old_feedback) / 2, 1)
        traits["sensitivity"] = new_sensitivity
        del traits["feedback_sensitivity"]
        modified = True
        print(
            f"  sensitivity: {old_sensitivity} + feedback_sensitivity: {old_feedback} → {new_sensitivity}"
        )

    # 3. eccentricity を追加（キャラに合わせて設定）
    if "eccentricity" not in traits:
        # 職業や性格タイプに基づいて値を決定
        occupation = data.get("background", {}).get("occupation", "")
        personality_type = data.get("personality", {}).get("type", "")
        personality_traits = data.get("personality", {}).get("traits", [])

        # 不思議ちゃん度の基準値
        if any(
            word in str(personality_traits) for word in ["哲学", "詩", "夢見", "マイペース", "独特"]
        ):
            eccentricity = round(random.uniform(0.6, 0.9), 1)
        elif personality_type in ["のんびり"]:
            eccentricity = round(random.uniform(0.4, 0.6), 1)
        elif "研究" in occupation or "詩人" in occupation or "アーティスト" in occupation:
            eccentricity = round(random.uniform(0.5, 0.7), 1)
        else:
            eccentricity = round(random.uniform(0.1, 0.4), 1)

        traits["eccentricity"] = eccentricity
        modified = True
        print(f"  eccentricity: {eccentricity} (新規)")

    # 4. contrarian を追加（キャラに合わせて設定）
    if "contrarian" not in traits:
        personality_traits = data.get("personality", {}).get("traits", [])
        style = data.get("style", "normal")

        # 逆張り度の基準値
        if any(word in str(personality_traits) for word in ["皮肉", "批評", "論理", "分析"]):
            contrarian = round(random.uniform(0.5, 0.8), 1)
        elif style in ["terse", "2ch"]:
            contrarian = round(random.uniform(0.4, 0.7), 1)
        elif style in ["polite", "ojisan"]:
            contrarian = round(random.uniform(0.1, 0.3), 1)
        else:
            contrarian = round(random.uniform(0.2, 0.5), 1)

        traits["contrarian"] = contrarian
        modified = True
        print(f"  contrarian: {contrarian} (新規)")

    if modified:
        # traits_detailセクションを再構築
        # 順序を保持するため、正規表現で置換
        new_traits_yaml = "traits_detail:\n"
        param_order = [
            "activeness",
            "curiosity",
            "sociability",
            "sensitivity",
            "optimism",
            "creativity",
            "persistence",
            "expressiveness",
            "expertise",
            "eccentricity",
            "contrarian",
        ]
        for param in param_order:
            if param in traits:
                new_traits_yaml += f"  {param}: {traits[param]}\n"

        # 既存のtraits_detailセクションを置換
        pattern = r"traits_detail:.*?(?=\n[a-z#]|\Z)"
        new_content = re.sub(pattern, new_traits_yaml.rstrip(), content, flags=re.DOTALL)

        profile_path.write_text(new_content, encoding="utf-8")
        return True

    return False


def main():
    random.seed(42)  # 再現性のため

    residents_dir = Path("npcs/residents")
    backend_dir = Path("npcs/backend")

    print("=== 住人NPC ===")
    for npc_dir in sorted(residents_dir.iterdir()):
        if npc_dir.is_dir():
            profile_path = npc_dir / "profile.yaml"
            if profile_path.exists():
                print(f"\n{npc_dir.name}:")
                if merge_parameters(profile_path):
                    print("  ✓ 更新完了")
                else:
                    print("  - スキップ")

    print("\n=== バックエンドNPC ===")
    for npc_dir in sorted(backend_dir.iterdir()):
        if npc_dir.is_dir():
            profile_path = npc_dir / "profile.yaml"
            if profile_path.exists():
                print(f"\n{npc_dir.name}:")
                if merge_parameters(profile_path):
                    print("  ✓ 更新完了")
                else:
                    print("  - スキップ（traits_detailなし）")


if __name__ == "__main__":
    main()
