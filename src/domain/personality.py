"""
性格分析（プロフィールから性格タイプを推定）
"""

from .models import NpcProfile


class PersonalityAnalyzer:
    """プロフィールから性格タイプを分析"""

    # 性格タイプのキーワードマッピング
    TYPE_KEYWORDS = {
        "陽気": ["陽気", "明るい", "楽観"],
        "クール": ["クール", "冷静", "論理"],
        "熱血": ["熱血", "情熱", "積極"],
        "内気": ["内向", "静か", "控えめ"],
        "のんびり": ["のんびり", "ゆったり", "マイペース"],
        "真面目": ["真面目", "誠実", "堅実"],
    }

    @classmethod
    def classify(cls, profile: NpcProfile) -> str:
        """
        プロフィールから性格タイプを推定

        Args:
            profile: NPCプロフィール

        Returns:
            性格タイプ（陽気, クール, 熱血, 内気, のんびり, 真面目, 普通）
        """
        personality = profile.personality
        personality_type = personality.type.lower()

        # 性格タイプ名から判定
        for type_name, keywords in cls.TYPE_KEYWORDS.items():
            if any(w in personality_type for w in keywords):
                return type_name

        # traitsからも判定
        traits = [t.lower() for t in personality.traits]
        for type_name, keywords in cls.TYPE_KEYWORDS.items():
            if any(any(kw in t for kw in keywords) for t in traits):
                return type_name

        return "普通"

    @classmethod
    def get_emoji_style(cls, personality_type: str) -> str:
        """
        性格タイプに応じた絵文字スタイルを取得

        Args:
            personality_type: 性格タイプ

        Returns:
            絵文字スタイル（positive, cool, varied, simple）
        """
        if personality_type in ["陽気", "熱血"]:
            return "positive"
        elif personality_type in ["クール", "真面目"]:
            return "cool"
        elif personality_type in ["内気", "のんびり"]:
            return "simple"
        else:
            return "varied"
