"""
ボットID関連のユーティリティ
"""


def format_bot_name(bot_id: int) -> str:
    """
    ボットIDを標準フォーマットに変換

    Args:
        bot_id: ボットID（例: 1）

    Returns:
        フォーマットされた名前（例: "bot001"）
    """
    return f"bot{bot_id:03d}"


def extract_bot_id(bot_name: str) -> int | None:
    """
    ボット名からIDを抽出

    Args:
        bot_name: ボット名（例: "bot001" または "1"）

    Returns:
        ボットID（例: 1）、パース失敗時はNone
    """
    if bot_name.startswith("bot"):
        try:
            return int(bot_name[3:])
        except ValueError:
            return None
    try:
        return int(bot_name)
    except ValueError:
        return None
