"""
NPC ID関連のユーティリティ
"""


def format_npc_name(npc_id: int) -> str:
    """
    NPC IDを標準フォーマットに変換

    Args:
        npc_id: NPC ID（例: 1）

    Returns:
        フォーマットされた名前（例: "npc001"）
    """
    return f"npc{npc_id:03d}"


def extract_npc_id(npc_name: str) -> int | None:
    """
    NPC名からIDを抽出

    Args:
        npc_name: NPC名（例: "npc001" または "1"）

    Returns:
        NPC ID（例: 1）、パース失敗時はNone
    """
    if npc_name.startswith("npc"):
        try:
            return int(npc_name[3:])
        except ValueError:
            return None
    try:
        return int(npc_name)
    except ValueError:
        return None
