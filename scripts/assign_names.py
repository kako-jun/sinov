#!/usr/bin/env python3
"""NPCに名前を割り当てるスクリプト"""

import re
from pathlib import Path

# NPC番号 → 新しい名前のマッピング（職業・スタイルに合わせて選定）
NAME_MAPPING = {
    1: "code sense",  # フロントエンドエンジニア (normal) - コード系
    2: "nullpo",  # バックエンドエンジニア (terse) - プログラマジョーク
    3: "mcΔt",  # 研究者 (normal) - 数学/物理系
    4: "いちごミルク",  # イラストレーター (otaku) - かわいい系
    5: "寧波",  # 背景イラストレーター (normal) - アーティスティック
    6: "鹿丸",  # 漫画家 (otaku) - 和風
    7: "青原波音",  # UIデザイナー (polite) - 綺麗な名前
    8: "AKIRA2",  # インディーゲーム開発者 (young) - ゲーマー風
    9: "qc",  # サウンドエンジニア (terse) - シンプル
    10: "チョコP",  # ゲーム音楽作曲家 (normal) - P系
    11: "Kokopelli",  # 電子音楽アーティスト (normal) - 音楽神話
    12: "美樹本洋介",  # 小説家 (normal) - 作家っぽい本名
    13: "妹子",  # フリーライター (polite) - 柔らかい
    14: "そあ",  # 詩人 (polite) - 詩的
    15: "ZtoA",  # フルスタックエンジニア (terse) - 技術系
    16: "dustor",  # インフラエンジニア (terse) - 渋い英語
    17: "schooler",  # データアナリスト見習い (normal) - 学習中感
    18: "cyan",  # 3DCGアーティスト (normal) - 色系
    19: "承り太郎",  # テクニカルライター (normal) - 丁寧系
    20: "fobic",  # セキュリティエンジニア (terse) - 警戒系
    21: "キャンキャン界隈",  # VTuber・配信者 (otaku) - 配信者っぽい
    22: "∞man",  # MLエンジニア (normal) - 無限/AI系
    23: "なっす",  # 会社員（趣味でプログラミング） (normal) - カジュアル
    24: "momiji",  # アニメーター (normal) - 和風英語
    25: "Emet-Selch",  # コンセプトアーティスト (normal) - FF14ファン風
    26: "ねぬ",  # ドット絵師 (normal) - シンプルかわいい
    27: "鰤大根駄々子",  # 同人作家 (normal) - 面白い名前
    28: "曽場蒼輝",  # グラフィックデザイナー (polite) - デザイナー本名
    29: "meon",  # フォトグラファー (normal) - 光系
    30: "twist-twist",  # モーショングラフィックスデザイナー (normal) - 動き系
    31: "帆立出汁先輩",  # Webデザイナー (polite) - 先輩キャラ
    32: "ミラー貝入",  # ロゴデザイナー (polite) - 個性的
    33: "りんご宇宙",  # キャラクターデザイナー (polite) - ファンシー
    34: "nemco",  # ボカロP (normal) - ゲーム会社風
    35: "musset",  # 会社員（趣味でDTM） (normal) - 詩人の名前
    36: "crazy shoes",  # バンドマン（ギター） (normal) - ロック
    37: "skyk",  # DJ (normal) - 空系
    38: "よろしくお願いしまぁす",  # 声優・ナレーター (normal) - 挨拶系
    39: "ククルル",  # 歌い手 (normal) - 歌っぽい
    40: "swicca",  # ピアニスト (normal) - 優雅
    41: "田中優美清春香菜",  # ライトノベル作家 (normal) - ラノベっぽい長い名前
    42: "内田かずき",  # シナリオライター (polite) - 本名っぽい
    43: "La Vacca Saturno Saturnita",  # 翻訳家 (normal) - 多言語
    44: "出来杉",  # 編集者 (normal) - 優秀そう
    45: "抹茶チョコバナナ",  # エッセイスト (normal) - 食べ物好き
    46: "やることが…やることが多い",  # ブロガー (normal) - ブロガーあるある
    47: "神無神無",  # 歌人 (normal) - 和歌っぽい
    48: "レモン味おもち",  # 同人小説家 (normal) - お菓子系
    49: "senju punch",  # ゲームプランナー (normal) - 格闘ゲーム風
    50: "locks",  # レベルデザイナー (polite) - ロック/鍵
    51: "costry",  # QAテスター (normal) - コスト意識
    52: "ブラックパックン最強",  # ゲーム実況者 (normal) - 実況者っぽい
    53: "寿司打25000円",  # プロゲーマー (normal) - タイピングゲーム
    54: "shallet hoden",  # ローカライズコーディネーター (normal) - 多言語
    55: "spati",  # 同人ゲーム開発者 (otaku) - 空間系
    56: "フリーサ",  # ノベルゲームシナリオライター (normal) - キャラっぽい
    57: "fleo",  # iOSエンジニア (normal) - モバイル
    58: "lestol",  # Androidエンジニア (normal) - モバイル
    59: "鉄製綿棒",  # 組み込みエンジニア (normal) - ハードウェア感
    60: "wrecky",  # SRE (normal) - 障害対応
    61: "cluuuut",  # DBA (normal) - データ系
    62: "rop dazer",  # DevOpsエンジニア (terse) - 運用系
    63: "kailjute",  # ブロックチェーンエンジニア (terse) - 暗号っぽい
    64: "yuo",  # XRエンジニア (normal) - VR/AR
    65: "剛侠（カンシア）",  # ロボットエンジニア (terse) - 硬派
    66: "H.ONDA",  # CTO (normal) - 創業者風
    67: "lusky taton",  # 大学教授（情報学） (normal) - 学者風
    68: "crazier",  # AI研究者 (normal) - クレイジー研究
    69: "TAM.C",  # 専門学校講師（ゲーム） (normal) - 講師風
    70: "ママス",  # プログラミング教室講師 (normal) - 優しい
    71: "fool SAKAMOT",  # 技術書著者 (normal) - 著者っぽい
    72: "ヘシータ",  # ゲーム研究者 (normal) - 研究者風
    73: "てくじろう",  # 大学生（情報工学科3年） (normal) - 技術系学生
    74: "チーおか",  # 専門学校生（ゲーム科2年） (normal) - 学生風
    75: "ゆきだる魔おとし",  # 専門学校生（アニメ科2年） (normal) - アニメ風
    76: "24",  # 高校生（2年） (normal) - 若い
    77: "まり子ん",  # 会社員（事務職） (normal) - OL風
    78: "将来の夢はお茶",  # 主婦（趣味で小説執筆） (normal) - ほっこり
    79: "ノギムラ",  # 元エンジニア（定年退職） (normal) - 渋い
    80: "令和マロン",  # 会社員（副業でWeb制作） (normal) - 令和感
    81: "ヨンサナイ",  # 転職活動中（元SES） (normal) - 404感
    82: "スマホン",  # フリーランスエンジニア（1年目） (terse) - モバイル
    83: "超能力ピーナッツ",  # VRChat住人（本業は会社員） (normal) - VR感
    84: "ディゴランチン",  # 会社員（TRPG愛好家） (normal) - TRPG風
    85: "クロコダイルマーガリン",  # ボードゲームデザイナー (polite) - ボドゲ風
    86: "あっあっあっ",  # コスプレイヤー（本業は美容師） (normal) - テンション高い
    87: "サーモンEX",  # フィギュア原型師 (normal) - フィギュア風
    88: "ガリ大盛",  # 会社員（趣味でプラモデル） (normal) - 趣味人
    89: "ガリガリ君しょうゆ味",  # 会社員（自作PC愛好家） (normal) - マニアック
    90: "ノイス",  # OSSコントリビューター（本業はエンジニア） (normal) - OSS
    91: "黄金の株",  # エンジニア（技術同人誌サークル代表） (terse) - 代表感
    92: "タピ岡ひろし",  # 技術系YouTuber (normal) - YouTuber風
    93: "ぱちんんこ",  # エンジニア（Vim使い） (normal) - キーボード音
    94: "替え玉",  # 同人イベントスタッフ（本業は会社員） (normal) - サポート
    95: "ドラ食うな",  # 音MAD職人（本業は会社員） (normal) - ネタ系
}

# バックエンドNPC（記者・レビューア）の名前
BACKEND_MAPPING = {
    "reporter_creative": "お肉にはケチャップ派",  # クリエイティブ記者 - 好み主張系
    "reporter_game": "犬バス",  # ゲーム記者 - かわいい系
    "reporter_general": "くさったドリアン",  # 一般記者 - 個性的
    "reporter_tech": "しまうー",  # 技術記者 - ゆるい
    "reporter_trend": "はらたいらPayPay",  # トレンド記者 - 時事ネタ
    "reviewer": "Imposter",  # レビューア - Among Us風
}


def update_npc_name(npc_dir: Path, new_name: str) -> bool:
    """NPCのprofile.yamlの名前を更新"""
    profile_path = npc_dir / "profile.yaml"
    if not profile_path.exists():
        return False

    content = profile_path.read_text(encoding="utf-8")
    # name: "xxx" または name: xxx を置換
    new_content = re.sub(
        r'^(name:\s*)(["\']?).*?\2\s*$', f'\\1"{new_name}"', content, count=1, flags=re.MULTILINE
    )

    if new_content != content:
        profile_path.write_text(new_content, encoding="utf-8")
        return True
    return False


def main():
    # 住人NPCの更新
    residents_dir = Path("npcs/residents")
    print("=== 住人NPC ===")
    for npc_id, new_name in NAME_MAPPING.items():
        npc_dir = residents_dir / f"npc{npc_id:03d}"
        if update_npc_name(npc_dir, new_name):
            print(f"✓ npc{npc_id:03d} → {new_name}")
        else:
            print(f"✗ npc{npc_id:03d} not found or unchanged")

    # バックエンドNPCの更新
    backend_dir = Path("npcs/backend")
    print("\n=== バックエンドNPC ===")
    for npc_name, new_name in BACKEND_MAPPING.items():
        npc_dir = backend_dir / npc_name
        if update_npc_name(npc_dir, new_name):
            print(f"✓ {npc_name} → {new_name}")
        else:
            print(f"✗ {npc_name} not found or unchanged")


if __name__ == "__main__":
    main()
