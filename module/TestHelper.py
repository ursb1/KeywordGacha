import json

from model.Word import Word

class TestHelper:

    DATA = {
        # "ブルースライム": "蓝史莱姆",
        # "ワイバーン": "双足飞龙",
        # "ミスリル": "秘银",
        # "ポーション": "药水",
        # "ハイポーション": "高级药水",
        # "魔付き": "魔附者",
        "オルディネ": "奥迪涅",
        "イシュラナ": "伊修拉纳",
        "エリルキア": "艾利尔齐亚",
        "ダリヤ": "达莉亚",
        "ロセッティ": "罗塞蒂",
        "ヴォルフレード": "沃尔夫雷德",
        "スカルファロット": "斯卡尔法罗特",
        "ヴォルフ": "沃尔夫",
        "カルロ": "卡洛",
        "イルマ": "伊露玛",
        "ヌヴォラーリ": "努沃拉里",
        "マルチェラ": "马尔切拉",
        "イヴァーノ": "伊凡诺",
        "バドエル": "巴多尔",
        "メルカダンテ": "梅卡丹特",
        "メッツェナ": "梅泽纳",
        "グリーヴ": "格里夫",
        "メーナ": "梅纳",
        "フェルモ": "费尔莫",
        "ガンドルフィ": "甘道夫",
        "バルバラ": "芭芭拉",
        "トビアス": "托比亚斯",
        "オルランド": "奥兰多",
        "エミリヤ": "爱蜜丽雅",
        "タリーニ": "塔利尼",
        "イレネオ": "依勒内欧",
        "レオーネ": "雷欧尼",
        "ジェッダ": "杰达",
        "ガブリエラ": "加布里埃拉",
        "ドミニク": "多明尼克",
        "ケンプフェル": "坎普法",
        "グラート": "格拉特",
        "バルトローネ": "巴托洛内",
        "グリゼルダ": "格里赛达",
        "ランツァ": "兰扎",
        "ジスモンド": "吉斯蒙德",
        "カフィ": "卡菲",
        "ランドルフ": "兰道夫",
        "グッドウィン": "古德温",
        "ドリノ": "多里诺",
        "バーティ": "巴堤",
        "ミロレスタノ": "米洛雷斯塔诺",
        "カジミーリ": "卡西米利",
        "ミロ": "米洛",
        "アルフィオ": "阿尔菲奥",
        "ジオーネ": "吉欧涅",
        "ニコラ": "尼古拉",
        "アストルガ": "阿斯托加",
        "カーク": "卡克",
        "レオナルディ": "莱昂纳多",
        "ジルドファン": "吉得范",
        "ディールス": "迪尔斯",
        "ジルド": "吉得",
        "ベルニージ": "伯尼吉",
        "ドラーツィ": "多拉齐",
        "ウロス": "乌洛斯",
        "ウォーロック": "沃洛克",
        "カルミネ": "卡尔米奈",
        "ザナルディ": "扎纳尔迪",
        "レナート": "雷纳托",
        "ヴァネッサ": "凡妮莎",
        "グイード": "古伊德",
        "ヨナス": "约纳斯",
        "ファビオ": "法比奥",
        "エルード": "艾尔德",
        "ローザリア": "罗莎莉亚",
        "ローザ": "罗莎",
        "グローリア": "哥洛莉亞",
        "オズヴァルド": "奥茲华尔德",
        "ゾーラ": "佐拉",
        "オズ": "奥兹",
        "カテリーナ": "卡捷琳娜",
        "フィオレ": "菲奥雷",
        "エルメリンダ": "埃尔梅琳达",
        "ラウルエーレ": "劳尔艾雷",
        "ラウル": "劳尔",
        "フォルトゥナート": "福尔托纳特",
        "ルイーニ": "路易尼",
        "フォルト": "佛特",
        "ルチア": "露琪亚",
        "ファーノ": "法诺",
        "アウグスト": "奥古斯特",
        "スカルラッティ": "斯卡拉蒂",
        "ジャン": "约翰",
        "タッソ": "塔索",
        "イデアリーナ": "伊蒂亞莉娜",
        "ニコレッティ": "尼可莱蒂",
        "イデア": "伊蒂亚",
        "アルテア": "阿尔蒂亚",
        "ガストーニ": "加斯托尼",
        "トリスターノ": "托里斯塔诺",
        "フロレス": "弗洛雷斯",
        "リーナ": "莉娜",
        "ラウレン": "劳伦",
        "ロレッタ": "罗蕾塔",
        "イリーナ": "伊琳娜",
        "ロアーヌ": "罗安娜",
        "ロレンツ": "洛伦茨",
        "ティルナーラ": "提尔娜拉",
        "ティル": "提尔",
        "ユリシュア": "尤利西亚",
        "モルテード": "摩尔泰德",
        "ユーセフ": "尤瑟夫",
        "ハルダード": "哈尔达多",
        "ナジャー": "纳杰",
        "ラゼフ": "拉泽夫",
        "ファジュル": "法朱尔",
        "ミトナ": "米特纳",
        "メルセラ": "梅尔塞拉",
        "エラルド": "埃拉尔德",
        "レオンツィオ": "莱昂齐奥",
        "ゴッフレード": "高弗雷德",
        "ゴード": "高德",
        "ハディス": "哈迪斯",
        "バルディス": "巴尔迪斯",
        "ドナ": "多娜",
        "セラフィノ": "塞拉芬诺",
        "ベガルタ": "贝加尔塔",
        "ディルディナ": "迪尔迪纳",
        "ベガ": "贝加",
        "モーラ": "莫拉",
        "ピエリナ": "皮耶丽娜",
        "ファビオラ": "法比奧菈",
        "コルンバーノ": "科伦巴诺",
        "ヒューラ": "休拉",
        "ロドヴィーズ": "罗德维兹",
        "カノーヴァ": "卡诺瓦",
        "ロド": "罗德",
        "ユドラス": "尤德拉斯",
        "フェルローネ": "费罗内",
        "ギーシュ": "吉什",
        "ガディス": "加迪斯",
        "ダルドレフ": "达尔德列夫",
        "ダフネ": "达芙妮",
        "フォディス": "福迪斯",
        "シュテファン": "斯特凡",
        "キエザ": "基耶扎",
        "ストルキオス": "斯托尔奇奥斯",
        "アルドリウス": "阿尔德鲁斯",
        "フランドフラン": "弗兰德弗兰",
        "ノワルスール": "诺瓦尔苏尔",
        "ヴェントルジェント": "文特尔金特",
    }

    THRESHOLDS = (
        0.25,
        0.30,
        0.35,
        0.40,
        0.45,
        0.50,
        0.55,
        0.60,
        0.65,
        0.70,
        0.75,
        0.80,
        0.85,
        0.90,
        0.95,
    )

    def check_score_threshold(words: list[Word], path: str) -> None:
        with open(path, "w", encoding = "utf-8") as writer:
            for threshold in TestHelper.THRESHOLDS:
                x = {k for k in TestHelper.DATA.keys()}
                y = {
                    word.surface
                    for word in words if word.score > threshold
                }

                writer.write(f"当置信度阈值设置为 {threshold:.4f} 时：\n")
                writer.write(f"第一个词典独有的键 - {len(x - y)}\n")
                writer.write(f"{x - y}\n")
                writer.write(f"第二个词典独有的键 - {len(y - x)}\n")
                writer.write(f"{y - x}\n")
                writer.write(f"两个字典共有的键 - {len(x & y)}\n")
                writer.write(f"{x & y}\n")
                writer.write("\n")
                writer.write("\n")

    def check_result_duplication(words: list[Word], path: str) -> None:
        with open(path, "w", encoding = "utf-8") as writer:
            x = {k for k in TestHelper.DATA.keys()}
            y = {word.surface for word in words if word.group == "角色"}
            z = {word.surface for word in words if word.group != "角色"}

            writer.write(f"x 独有的键 - {len(x - y - z)}\n")
            writer.write(f"{x - y - z}\n")
            writer.write(f"y 独有的键 - {len(y - x - z)}\n")
            writer.write(f"{y - x - z}\n")
            writer.write(f"xy 共有的键 - {len(x & y)}\n")
            writer.write(f"{x & y}\n")
            writer.write(f"xz 共有的键 - {len(x & z)}\n")
            writer.write(f"{x & z}\n")
            writer.write("\n")
            writer.write("\n")

    def save_surface_analysis_log(words: list[Word], path: str) -> None:
        with open(path, "w", encoding = "utf-8") as writer:
            writer.write(
                json.dumps(
                    [
                        {
                            "request": word.llmrequest_surface_analysis,
                            "response": word.llmresponse_surface_analysis,
                        }
                        for word in words
                    ],
                    indent = 4,
                    ensure_ascii = False,
                )
            )

    def save_context_translate_log(words: list[Word], path: str) -> None:
        with open(path, "w", encoding = "utf-8") as writer:
            writer.write(
                json.dumps(
                    [
                        {
                            "request": word.llmrequest_context_translate,
                            "response": word.llmresponse_context_translate,
                        }
                        for word in words
                    ],
                    indent = 4,
                    ensure_ascii = False,
                )
            )
