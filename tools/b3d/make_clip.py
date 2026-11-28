# -*- coding: utf-8 -*-
"""scene.py --anim が書き出したコマ（入り i0000.png〜・本題 f0000.png〜）に、題名と手順の表示をのせて mp4 にする。
  python tools/b3d/make_clip.py <コマのフォルダ> <出力.mp4> [--script chi]（1秒のコマ数は、フォルダの fps.txt＝scene.py が書く。無ければ12）
のせるもの（2026-11-12 ユーザーの依頼）:
  0. 入り＝会場を回りこむ絵（scene.py --anim --intro）の上に、動画の題名（「チーの方法」）。3Dの卓の解説動画は、どれもこの入りから始める
  1. 上の帯＝手順の番号の列（済み＝緑・今＝オレンジで大きく・これから＝白い輪）。いま全体のどこかが分かる
  2. 見出し＝「② 開示」＋ひとことの説明（かな書きの読みつき）
  3. 手順が終わるたびに絵を止める（hold）。止めている間に説明を読める。あとで声をのせる長さにもなる
  4. 最後に、手順の一覧のカード
牌を番号つきの輪で囲む印は、のせない（2026-11-12 ユーザーの判断。絵のほうで手をどけて寄るので要らない）。
字は Noto Sans JP（Windows は C:/Windows/Fonts/NotoSansJP-VF.ttf）。ffmpeg は PATH のもの、無ければ imageio-ffmpeg。
"""
import glob, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

FONTS = ["C:/Windows/Fonts/NotoSansJP-VF.ttf", "/usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"]
GREEN, ORANGE, INK, WHITE = "#177083", "#E75620", "#1F2A28", "#FFFFFF"
W, H = 1080, 1920
NUM = "①②③④⑤⑥⑦⑧"

# 台本: 手順ごとに (名前, 読み, 説明, 最初のコマ, 最後のコマ, 止める秒, 囲む牌, 吹き出し)。コマの番号は、1秒12コマで数えた番号（もっと細かく書き出したときは、scaled が番号を読みかえる）
SCRIPTS = {
    "chi": dict(yoko=(3, "横向きの牌は", "上家から＝横向き"), clip=("blue", "上家が切った", ["m6"], "UR"), title="チーの方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「チー」と声に出す。ポンが優先なので一拍おいてから", 0, 6, 2.2, [], "チー"),     # 肩ごしで顔が見えるうちに止める（カメラが動き出す前）
        ("開示", "かいじ", "鳴くのに使う{搭子|ターツ}を倒して、みんなに見せる", 7, 31, 1.6, ["m4", "m5"], ""),          # 止める所は、手がどいて真上から寄ったコマ
        ("回収", "かいしゅう", "{他家|ターチャ}が切った牌を取り、横向きで付ける", 32, 61, 1.4, ["m6"], ""),
        ("副露", "フーロ", "3枚を卓の右端に寄せる。{上家|カミチャ}からは左が横向き", 62, 84, 1.6, ["m6", "m4", "m5"], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 85, 109, 1.4, ["s3"], "", "※鳴いた牌と同じ牌・反対側のスジの牌は切れない（喰い替え）"),     # 形の上で切れない牌（2026-11-16 ユーザーの指定）
    ], tail=(110, 120, 2.4),
    sbeats={3: [(69, "卓の右端に寄せます")]},       # ④は、置いた所で止めて「卓の右端に寄せます」の声で寄せる（2026-11-25 ユーザーの指定）
    kuikae=dict(step=4, at="鳴いた牌と", meld=["m6", "m4", "m5"], side=0, ng=[("m6", "同じ牌", "同じ牌"), ("m3", "反対側のスジ", "反対側のスジ")]),      # 喰い替えの具体例（四萬五萬で六萬をチー）
    pre=dict(head="チーできるとき", marks={"own": ("orange", "搭子", ["m4", "m5"], "UR"), "call": ("blue", "上家が切った", ["m6"], "UL")}, ls=[0, 2, 2, 3], beats=[(2.4, 2)], hold=1.8, concl=True, lines=[
        (0.3, "手牌に {搭子|ターツ} がある", "あと1枚で順子になる2枚"),
        (3.4, "{上家|カミチャ}が{ つながる牌 }を切った → チー"),
        (3.9, "そろうのは {順子|シュンツ}", "数がつながった3枚"),
        (4.4, "上家の捨て牌だけチーできる"),
    ])),
    "pon": dict(yoko=(3, "横向きの牌は", "対面から＝横向き"), clip=("blue", "対面が切った", ["z6"], "UR"), title="ポンの方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「ポン」と声に出す。チーより優先される", 0, 6, 2.2, [], "ポン"),
        ("開示", "かいじ", "鳴くのに使う{対子|トイツ}を倒して、みんなに見せる", 7, 31, 1.6, [], ""),
        ("回収", "かいしゅう", "{他家|ターチャ}が切った牌を取り、横向きで付ける", 32, 61, 1.4, [], ""),
        ("副露", "フーロ", "3枚を卓の右端に寄せる。{対面|トイメン}からは真ん中が横向き", 62, 84, 1.6, [], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 85, 109, 1.4, [], "", "※鳴いた牌と同じ牌は切れない（喰い替え）"),
    ], tail=(110, 120, 2.4),
    sbeats={3: [(69, "卓の右端に寄せます")]},
    kuikae=dict(step=4, at="鳴いた牌と", meld=["z6", "z6", "z6"], side=1, ng=[("z6", "同じ牌", "同じ牌")]),      # 發をポン
    pre=dict(head="ポンできるとき", marks={"own": ("orange", "対子", ["z6", "z6"], "UL"), "call": ("blue", "対面が切った", ["z6"], "UR")}, ls=[0, 2, 2, 3], beats=[(2.4, 2)], hold=1.8, concl=True, lines=[
        (0.3, "手牌に {対子|トイツ} がある", "同じ牌2枚"),
        (3.4, "{他家|ターチャ}が{ 同じ牌 }を切った → ポン"),
        (3.9, "そろうのは {刻子|コーツ}", "同じ牌3枚"),
        (4.4, "だれの捨て牌でもポンできる"),
    ])),
    "kan": dict(disc_hold=(2, 1.2), clip_hide_bub=True, clip=("orange", "ツモ", ["z1"], "UL"), title="暗槓の方法", kicker="ルールとマナーに沿った正しい手順", sub="6つの手順で覚える", steps=[
        ("発声", "はっせい", "「カン」と声に出す。自分の番で、ツモったあとに", 0, 6, 2.2, [], "カン"),
        ("開示", "かいじ", "4枚を表向きに倒して見せ、外側の2枚を裏返す", 7, 47, 1.6, [], ""),
        ("配置", "はいち", "4枚を卓の右端に寄せる", 48, 67, 1.4, [], ""),
        ("カンドラ", "", "ドラ表示牌のとなりを1枚めくる。カンドラが1つ増える", 68, 87, 1.6, [], ""),
        ("嶺上牌", "リンシャンパイ", "王牌の端から、嶺上牌を1枚ツモる", 88, 112, 1.4, [], ""),
        ("打牌", "ダハイ", "アガリ牌でなければ、いらない牌を1枚切る", 113, 135, 1.4, [], ""),
    ], tail=(136, 145, 2.4),
    sbeats={1: [(32, "外側の2枚を裏返します")]},     # ②は表向きに倒した所で止め、「外側の2枚を裏返します」の声で裏返す（2026-11-25 ユーザーの指定）
    pre=dict(head="暗槓できるとき", marks={"own": ("orange", "同じ牌4枚", ["z1", "z1", "z1", "z1"], "UL")}, ls=[0, 0, 1, 1], hold=1.8, concl=True, lines=[
        (0.3, "手牌の中だけで{ 同じ牌4枚 }", "自分でツモってそろえた"),
        (1.6, "そろうのは {槓子|カンツ}", "同じ牌4枚"),
        (2.9, "鳴き扱いにならない", "{門前|メンゼン}のまま"),
        (3.7, "自分でそろえた4枚なら、暗槓できる"),
    ])),
    # ここから下は、scene.py の「台本で動かす場面」（S2T の間の時刻からコマを計算: 間 n の止めるコマ＝(時刻＋n×0.7＋0.58)×12）
    "daiminkan": dict(clip_hide_bub=True, yoko=(3, "横向きの牌は", "下家から＝横向き"), clip=("blue", "下家が切った", ["z5"], "UR"), title="大明槓の方法", kicker="ルールとマナーに沿った正しい手順", sub="7つの手順で覚える", steps=[
        ("発声", "はっせい", "「カン」と声に出す。人が切った牌で4枚目をそろえる", 0, 6, 2.2, [], "カン"),
        ("開示", "かいじ", "手牌の同じ牌3枚を倒して、みんなに見せる", 7, 32, 1.6, [], ""),
        ("回収", "かいしゅう", "{他家|ターチャ}が切った牌を取り、横向きで付ける", 33, 61, 1.4, [], ""),
        ("副露", "フーロ", "4枚を卓の右端に寄せる。{下家|シモチャ}からは右が横向き", 62, 84, 1.6, [], ""),
        ("カンドラ", "", "ドラ表示牌のとなりを1枚めくる。カンドラが1つ増える", 85, 105, 1.6, [], ""),
        ("嶺上牌", "リンシャンパイ", "王牌の端から、嶺上牌を1枚ツモる", 106, 131, 1.4, [], ""),
        ("打牌", "ダハイ", "アガリ牌でなければ、いらない牌を1枚切る", 132, 154, 1.4, [], ""),
    ], tail=(155, 165, 2.4),
    sbeats={3: [(69, "卓の右端に寄せます")]},
    pre=dict(head="大明槓できるとき", marks={"own": ("orange", "暗刻", ["z5", "z5", "z5"], "UL"), "call": ("blue", "下家が切った", ["z5"], "UR"), "own2": ("orange", "暗刻", ["z5", "z5", "z5"], "UL"), "call2": ("blue", "下家が切った", ["z5"], "UR")}, ls=[0, 2, 2, 3, 4], beats=[(2.4, 2)], hold=1.8, concl=True, lines=[
        (0.3, "手牌に {暗刻|アンコ} がある", "同じ牌3枚"),
        (3.4, "{他家|ターチャ}が{ 4枚目 }を切った → カン"),
        (3.9, "そろうのは {槓子|カンツ}", "同じ牌4枚"),
        (4.4, "暗槓と違い、{ 鳴き扱い }になる", "{門前|メンゼン}ではなくなる"),
        (4.9, "だれの捨て牌でも大明槓できる"),
    ])),
    "kakan": dict(disc_hold=(2, 1.2), clip_hide_bub=True, yoko=(1, "横向きで重ねます", "加えた牌"), clip=("orange", "ツモ", ["z7"], "UL"), title="加槓の方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「カン」と声に出す。自分の番で、ツモったあとに", 0, 6, 2.2, [], "カン"),
        ("加槓", "カカン", "ポンした牌の横向きの1枚に、横向きで重ねる", 7, 36, 1.8, [], ""),
        ("カンドラ", "", "ドラ表示牌のとなりを1枚めくる。カンドラが1つ増える", 37, 57, 1.6, [], ""),
        ("嶺上牌", "リンシャンパイ", "王牌の端から、嶺上牌を1枚ツモる", 58, 83, 1.4, [], ""),
        ("打牌", "ダハイ", "アガリ牌でなければ、いらない牌を1枚切る", 84, 106, 1.4, [], ""),
    ], tail=(107, 117, 2.4),
    pre=dict(head="加槓できるとき", ls=[0, 2, 2, 2], beats=[(1.4, 2)], marks={"own": ("orange", "明刻", ["z7", "z7", "z7"], "UR"), "call": ("blue", "4枚目", ["z7"], "UL")}, hold=2.0, concl=True, lines=[
        (0.3, "ポンした {明刻|ミンコ} がある", "人の牌でそろえた同じ牌3枚"),
        (1.6, "自分で{ 4枚目 }を引いた → カン"),
        (2.8, "そろうのは {槓子|カンツ}", "同じ牌4枚"),
        (3.6, "ポンした3枚に足して、加槓できる"),
    ])),
    "riichi": dict(disc_hold=(2, 1.2), clip_hide_bub=True, yoko=(1, "切ります", "リーチの宣言牌", True), clip=("orange", "ツモ", ["s8"], "UL"), title="リーチの方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「リーチ」と声に出す", 0, 6, 2.2, [], "リーチ"),
        ("打牌", "ダハイ", "いらない牌を横向きにして切り、ツモった牌は手牌へ", 7, 42, 1.8, [], ""),
        ("供託", "きょうたく", "1,000点棒を1本、卓の中央に出す（アガった人がもらう）", 43, 80, 1.8, [], ""),
        ("ツモ", "", "全員が打牌したあと、アガリ牌をツモる。「ツモ」でアガリ牌を倒し、手牌も倒す", 81, 146, 1.8, [], "ツモ"),
        ("裏ドラ", "うらドラ", "ドラ表示牌と下の牌を手もとに並べ、下の牌をめくる", 147, 186, 1.8, [], ""),     # 2026-11-25 ユーザーの指定
    ], tail=(187, 195, 2.4), bubw={3: "ツモ、と声に出して"},
    sbeats={3: [(118, "ツモ、と声に"), (127, "そのあと")], 4: [(164, "表に")]},      # 「そのあと」はアガリ牌を倒して右手を戻した所で止める（2026-11-28 ユーザーの指定）      # ツモ牌を見せる → 「ツモ」でアガリ牌だけ倒す → 手牌／2枚を並べて見せる → めくる
    doracard=dict(step=4, at="これが裏ドラです", labels=("表ドラ", "裏ドラ", "めくります"), rows=[("表ドラ", "s4", "s5", (255, 170, 120)), ("裏ドラ", "m6", "m7", (140, 220, 230))]), bubpos={"ツモ": ((700, 800), (150, 230))},
    pre=dict(head="リーチできるとき", marks={"own": ("orange", "待ち", ["p3", "p6"], "UL")}, ls=[0, 1, 1], hold=2.0, concl=True, lines=[
        (0.3, "{門前|メンゼン}である", "ポン・チー・明槓をしていない"),
        (1.6, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (2.8, "1,000点棒を出して、リーチできる"),
    ], note=(3.4, "※持ち点や山の残り枚数の条件は、ルールによって違う"))),     # 環境ごとに違う条件は、ただし書きに（2026-11-14 ユーザーの指定）
    "tsumo": dict(sbeats={2: [(53, "そのあと")]},      # ③ ツモった牌を倒したら止め、「そのあと」で手牌を倒す
                  yaku={3: dict(items=[("メンゼンツモ", "メンゼンツモ", 1), ("タンヤオ", "タンヤオ", 1), ("ドラ1", "ドラ", 1)], fu=("3翻30符", "30符"), pts=("点数は", "1000・2000"))},
                  title="ツモアガリの方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("ツモ", "", "山から1枚ツモる。手牌の中には入れない", 0, 42, 1.6, [], ""),
        ("発声", "はっせい", "アガリ牌なら「ツモ」と声に出す", 43, 49, 2.0, [], "ツモ"),
        ("開示", "かいじ", "ツモった牌を倒して見せ、そのあと手牌を両手で倒す", 50, 68, 2.0, [], ""),
        ("申告", "しんこく", "同卓者に点数を申告する", 69, 75, 2.6, [], "1000・2000"),      # 役やドラの説明はカードに書かない（2026-11-25 ユーザーの指定）
        ("支払い", "しはらい", "ほかの3人が、アガった人に点数を払う", 76, 104, 2.0, [], ""),     # 点数の支払いも見せる（2026-11-16 ユーザーの指定）
    ], tail=(105, 105, 2.4),
    pre=dict(head="ツモアガリできるとき", marks={"own": ("orange", "待ち", ["m7"], "UL")}, ls=[0, 1, 2, 2], hold=2.0, concl=True, lines=[
        (0.3, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (1.6, "自分で{ アガリ牌 }を引いた → ツモ"),
        (2.8, "{役|ヤク}が1つ以上ある", "アガるのに必要な形"),
        (3.6, "自分で引いたアガリ牌で、ツモアガリ"),
    ])),
    "ron": dict(yaku={2: dict(items=[("タンヤオ", "タンヤオ", 1), ("ピンフ", "ピンフ", 1), ("赤1", "赤ドラ", 1)], fu=("3翻30符", "30符"), pts=("点数は", "3900"))},
                clip=("blue", "下家が切った", ["p5r"], "UR"), title="ロンアガリの方法", kicker="ルールとマナーに沿った正しい手順", sub="4つの手順で覚える", steps=[
        ("発声", "はっせい", "他家がアガリ牌を切ったら「ロン」と声に出す", 0, 6, 2.2, [], "ロン"),
        ("開示", "かいじ", "両手で手牌の両端を持って、手牌を倒す", 7, 36, 2.0, [], ""),
        ("申告", "しんこく", "同卓者に点数を申告する", 37, 66, 2.6, [], "3900"),     # 役は言わず点数だけ（2026-11-14 ユーザーの指定）
        ("支払い", "しはらい", "ロンされた人だけが、アガった人に点数を払う", 67, 114, 2.0, [], ""),     # 下家が5,000点棒・自分が1,000点棒と100点棒で返す（2026-11-16 ユーザーの指定）
    ], tail=(115, 120, 2.4),
    pre=dict(head="ロンアガリできるとき", marks={"own": ("orange", "待ち", ["p5", "p8"], "UL"), "call": ("blue", "アガリ牌", ["p5r"], "UR")}, ls=[0, 1, 2, 3], beats=[(2.4, 1)], hold=1.8, concl=True, lines=[
        (0.3, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (3.4, "{他家|ターチャ}が{ アガリ牌 }を切った → ロン"),
        (3.9, "{役|ヤク}が1つ以上ある", "アガるのに必要な形"),
        (4.4, "だれの捨て牌でもロンできる"),
    ])),
    "dahai": dict(title="ツモと打牌の方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[     # 2026-11-16 ユーザーの依頼（初心者向けの3D動画の5）
        ("ツモ", "", "自分の番になったら、山の端から1枚取る", 0, 42, 1.6, [], ""),
        ("打牌", "ダハイ", "いらない牌を1枚、河に表向きで置く", 43, 59, 1.4, [], ""),
        ("河", "かわ", "河は左から6枚ずつ並べ、7枚目から次の段へ", 60, 69, 2.0, [], ""),
        ("理牌", "リーパイ", "ツモった牌を、手牌の並びに入れる", 70, 94, 1.6, [], ""),
        ("ツモ切り", "ツモぎり", "ツモった牌を、そのまま切ることもある", 95, 130, 1.6, [], ""),
    ], tail=(131, 141, 2.4),
    counts={2: ("riv", .3, .15)},      # ③河: 自分の河に「1・2・3…6」を順に出す（2026-11-25 ユーザーの指定「説明は、セリフだけでなく見て分かる演出を」）
    pre=dict(head="自分の番の流れ", top=90, ls=[0, 1, 2, 3, 3], beats=[(2.3, 1), (2.4, 2), (4.7, 3)], hold=2.0, concl=True,
             counts=[("hand", 2.3, .06, 13), ("hand", 3.75, .06, 14), ("hand", 6.65, .06, 13)], lines=[      # 13 → ツモって14 → 切って13 を数える（2026-11-26 ユーザーの指定）      # 前置きの絵（scene.py の pre_pose_dahai）に合わせた時刻
        (0.5, "{上家|カミチャ}が切ったら、自分の番"),
        (1.0, "手牌は13枚"),
        (2.0, "山から1枚{ツモ}って14枚"),
        (3.0, "1枚切って、13枚に戻る"),
        (4.0, "ツモって切る、をくり返す"),
    ])),
    "furiten": dict(title="捨て牌のフリテン", kicker="フリテンは3種類", sub="3種類の1つ目", steps=[
        ("待ち", "まち", "待ちを確かめる。一索・四索・七索の3種類", 24, 24, 2.2, [], ""),
        ("河", "かわ", "自分の河に、待ちの一索がある", 25, 44, 2.2, [], ""),
        ("ロンできない", "", "{他家|ターチャ}が四索を切っても、ロンできない", 45, 74, 2.2, [], "", "※ポン・チーで鳴かれて、河に無くてもフリテン"),
        ("ツモ", "", "自分で引いたアガリ牌なら、ツモアガリできる", 75, 126, 2.2, [], "ツモ"),
    ], tail=(127, 139, 2.4), bubw={3: "アガリ牌なら"}, after_motion=(3,), sbeats={3: [(95, "ます")]},      # 手を戻してツモ牌を見せた所で止め、「ツモ」の吹き出し → 倒す。印は倒し終えて手が離れてから（2026-11-28 ユーザーの指定）      # 牌と手牌を倒して右手を戻しきってから、止めた絵に「ツモ」とツモ牌の印（2026-11-28 ユーザーの指定） bubpos={"ツモ": ((760, 1350), (120, 260))},
    pre=dict(head="捨て牌のフリテン", xtext="待ちが変わるまでロンできない", marks={"own": ("teal", "待ち", ["s1", "s4", "s7"], "UL"), "cut": ("orange", "自分が切った", ["s1"], "LR", 1)}, nudge={"cut": 34}, xat="どの待ちでもロンできません", ls=[0, 0, 0, 1], hold=2.0, concl=True, lines=[
        (0.3, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (1.6, "待ちの牌を1種でも{ 切っている }", "自分の河にある"),
        (2.9, "どの待ちでも{ロン}できない", "ツモはできる"),
        (3.7, "待ちが変わるまで、ロンできない"),
    ])),
    "furiten2": dict(bub_hides=(4,), bub_still=(4,), title="同巡内フリテン", kicker="フリテンは3種類", sub="3種類の2つ目", steps=[
        ("待ち", "まち", "チーしていて、役はタンヤオだけ。一索では役が無い", 24, 24, 2.2, [], ""),
        ("見逃し", "みのがし", "{下家|シモチャ}の一索は、役が無いのでロンできない", 25, 50, 2.2, [], ""),
        ("ロンできない", "", "{対面|トイメン}の四索は役があるが、ロンできない", 51, 75, 2.2, [], ""),
        ("打牌", "ダハイ", "自分が打牌すると、フリテンがなくなる", 76, 131, 2.2, [], "", "※番が飛ばされても、自分が打牌するまでは続く"),
        ("ロンできる", "", "このあとの七索なら、ロンできる", 132, 186, 2.2, [], "ロン"),
    ], tail=(187, 193, 2.4),
    sbeats={3: [(107, "いらないので")], 4: [(159, "アガれます")]}, bubpos={"ロン": ((760, 1350), (120, 260))},      # 「ロン」と言ってから手牌を倒す（2026-11-25 ユーザーの指定）
    pre=dict(head="同巡内フリテン", marks={"own": ("teal", "待ち", ["s1", "s4", "s7"], "UL"), "miss": ("blue", "見逃し", ["s1"], "UR", 1)}, xat="どの待ちでもロンできません", xtext="次の自分の打牌までロンできない", ls=[0, 0, 0, 1], hold=2.0, concl=True, lines=[
        (0.3, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (1.6, "アガリ牌が出たのに{ 見逃した }", "役が無いときも"),
        (2.9, "どの待ちでも{ロン}できない", "ツモはできる"),
        (3.7, "次に自分が打牌するまで、ロンできない"),
    ])),
    "furiten3": dict(title="リーチ後のフリテン", kicker="フリテンは3種類", sub="3種類の3つ目", steps=[
        ("待ち", "まち", "リーチをしている。一索・四索・七索待ち", 24, 24, 2.2, [], ""),
        ("見逃し", "みのがし", "タンヤオがつく四索・七索を待って、一索を見逃す", 25, 50, 2.2, [], ""),
        ("打牌", "ダハイ", "自分が打牌しても、フリテンのまま", 51, 112, 2.2, [], ""),
        ("ロンできない", "", "{上家|カミチャ}が四索を切っても、ロンできない", 113, 153, 2.2, [], ""),
        ("ツモ", "", "自分で引いたアガリ牌なら、ツモアガリできる", 154, 208, 2.2, [], "ツモ"),
    ], tail=(209, 217, 2.4), bubw={4: "アガリ牌なら"}, after_motion=(4,), sbeats={4: [(175, "ます")]},      # 捨て牌のフリテンと同じ      # 手牌を倒して右手を戻しきってから「ツモ」とツモ牌の印（捨て牌のフリテンと同じ） bubpos={"ツモ": ((760, 1350), (120, 260))},
    pre=dict(head="リーチ後のフリテン", marks={"riichi": ("orange", "リーチ", [], "LR", 0), "bou": ("orange", "", [], "", 0), "own": ("teal", "待ち", ["s1", "s4", "s7"], "UL"), "miss": ("blue", "見逃し", ["s1"], "UR", 1)}, xat="どの待ちでもロンできません", xtext="この局はもうロンできない", ls=[0, 0, 0, 1], hold=2.0, concl=True, lines=[
        (0.3, "{リーチ}をしている", "待ちを変えられない"),
        (1.6, "アガリ牌が出たのに{ 見逃した }"),
        (2.9, "どの待ちでも{ロン}できない", "ツモはできる"),
        (3.7, "その局が終わるまで、ロンできない"),
    ])),
    "ryukyoku": dict(title="流局のしかた", kicker="ルールとマナーに沿った正しい手順", sub="4つの手順で覚える", steps=[
        ("流局", "りゅうきょく", "アガリが出ないまま、この局はおしまい", 0, 6, 2.2, [], ""),     # 前置きのカードと同じことを言わない（2026-11-14 ユーザーの指定）
        ("テンパイ", "", "あと1枚でアガれる人は、両手で手牌を倒して見せる。{東家|トンチャ}から順に", 7, 36, 2.0, [], ""),     # 流局のテンパイ・ノーテンは声に出さない（2026-11-14 ユーザーの指定）
        ("ノーテン", "", "テンパイでない人は、両手で手牌を伏せる", 37, 86, 2.0, [], ""),
        ("点棒", "てんぼう", "ノーテンの人がテンパイの人へ払う（場に3,000点）", 87, 122, 2.2, [], ""),
    ], tail=(123, 134, 2.4), cards={3: "bappu2"}, order=dict(steps=(1, 2), at="東家", c=(540, 1036, 300, 280), labels=["東家", "南家", "西家", "北家"]),      # 手牌を倒す順（反時計回り。2026-11-28 ユーザーの指定）     # ④は、声の文ごとにノーテン罰符の例を切りかえる（2026-11-25 ユーザーの指定）
    sbeats={3: [(92, "ノーテンの2人が")]},       # 点棒は「ノーテンの2人が」の声で払う
    pre=dict(head="流局になるとき", ls=[0, 1, 2, 2], beats=[(1.0, 1), (3.8, 2)], hold=2.0, concl=True,
             marks={"haitei": ("orange", "海底牌", [], "UL"), "houtei": ("blue", "河底牌", [], "UL"), "wanpai": ("green", "王牌 14枚", [], "UR")}, lines=[
        (0.3, "最後の{海底牌|ハイテイハイ}をツモった", "山の最後の1枚"),
        (1.6, "切った{河底牌|ホウテイハイ}にロンがない", "最後の捨て牌"),
        (2.9, "残りは{王牌|ワンパイ}14枚だけ", "ツモれない牌"),
        (3.7, "ツモ番がなくなり、流局"),
    ], note=(4.2, "※流局＝アガリ以外で局が終わること。この流局を荒牌平局という"))),     # 2026-11-14 ユーザーの指定
}

_fc = {}
def font(size, wght=900):
    k = (size, wght)
    if k in _fc: return _fc[k]
    for f in FONTS:
        if os.path.exists(f):
            ft = ImageFont.truetype(f, size)
            try: ft.set_variation_by_axes([wght])
            except Exception: pass
            _fc[k] = ft; return ft
    raise SystemExit("Noto Sans JP が見つからない: " + " / ".join(FONTS))

def text_c(d, cx, cy, tx, ft, fill, stroke=None, sw=0):
    l, t, r, b = d.textbbox((0, 0), tx, font=ft, stroke_width=sw)
    d.text((cx - (r - l) / 2 - l, cy - (b - t) / 2 - t), tx, font=ft, fill=fill, stroke_width=sw, stroke_fill=stroke)

def rail(d, steps, cur, done_all=False):
    """上の帯。番号の丸を線でつなぐ。cur=今の手順（0始まり）"""
    n = len(steps); x0, x1, y = 130, W - 130, 150; slot = (x1 - x0) / max(1, n - 1)
    d.rounded_rectangle((40, 60, W - 40, 290), radius=48, fill=(12, 20, 22, 205))
    for i in range(n - 1):
        xa = x0 + (x1 - x0) * i / (n - 1); xb = x0 + (x1 - x0) * (i + 1) / (n - 1)
        d.line((xa, y, xb, y), fill=GREEN if (i < cur or done_all) else (255, 255, 255, 90), width=8)
    for i, s in enumerate(steps):
        x = x0 + (x1 - x0) * i / (n - 1)
        now = (i == cur and not done_all); done = i < cur or done_all
        r = 52 if now else 38
        if now: d.ellipse((x - r - 8, y - r - 8, x + r + 8, y + r + 8), fill=(231, 86, 32, 90))
        d.ellipse((x - r, y - r, x + r, y + r), fill=ORANGE if now else (GREEN if done else (12, 20, 22, 255)), outline=WHITE if not (now or done) else None, width=4)
        text_c(d, x, y - 2, str(i + 1), font(60 if now else 42), WHITE)
        lf = fit(d, s[0], 40 if now else 34, slot - 16, 900 if now else 700); lw = d.textlength(s[0], font=lf)      # となりの名前とくっつかない大きさに（大明槓の7手順）
        text_c(d, max(72 + lw / 2, min(W - 72 - lw / 2, x)), y + 92, s[0], lf, WHITE if (now or done) else (255, 255, 255, 150))

def headline(d, i, s, k):
    """見出しと説明。k=出てからの進み（0〜1）で少し下から入る"""
    dy = int((1 - min(1, k * 4)) * 30)
    y = 330 + dy
    NT = s[8] if len(s) > 8 else ""      # 注意書き（例: 喰い替え）。説明の下に、オレンジの字で1行
    TOPY[0] = 330 + (326 if NT else 258) + 62 * s[2].count("\n") + 20
    d.rounded_rectangle((40, y, W - 40, y + (326 if NT else 258) + 62 * s[2].count("\n")), radius=44, fill=(255, 255, 255, 240))
    d.ellipse((76, y + 34, 76 + 104, y + 34 + 104), fill=ORANGE)
    text_c(d, 76 + 52, y + 34 + 50, str(i + 1), font(72), WHITE)
    fn = fit(d, s[0], 88, W - 80 - 204 - d.textlength(s[1], font=font(38, 700)) - 30)
    d.text((204, y + 22 + (88 - fn.size) // 2), s[0], font=fn, fill=INK)
    l, t, r, b = d.textbbox((204, y + 22 + (88 - fn.size) // 2), s[0], font=fn)
    d.text((r + 22, y + 74), s[1], font=font(38, 700), fill=GREEN)
    for n, ln in enumerate(s[2].split("\n")):
        ft = fit(d, ln, 40, W - 80 - 72, 800)
        ruby_draw(d, 76, y + 168 + 62 * n + (20 if any(r for p, r, t in ruby_parts(ln)) else 0), ln, ft, INK, 28, rfill=GREEN)
    if NT: ruby_draw(d, 76, y + 256 + 62 * s[2].count("\n"), NT, fit(d, NT, 36, W - 80 - 72, 800), ORANGE, 24)

def title_card(d, sc, t, dur):
    """入りの題名。少し遅れて下から入り、本題に入る直前に消える"""
    k = min(1, max(0, (t - .5) * 3)); out = min(1, max(0, (dur - t) * 4)); a = k * out
    if a <= 0: return
    A = lambda v: int(v * a)
    y = 230 + int((1 - k) * 40)      # 上に置く（真ん中だと卓と選手が隠れる）
    tr = any(r for p, r, t_ in ruby_parts(sc["title"]))
    # 題名と小見出しのあいだが空きすぎていた（2026-11-26 ユーザーの指摘・全動画）。カードの高さは中身に合わせ、小見出しは題名のすぐ下に少し大きく
    TY = 252 if tr else 222; SY = TY + 132; CH = SY + 74
    d.rounded_rectangle((70, y, W - 70, y + CH), radius=60, fill=(12, 20, 22, A(215)))
    # 左上に小さく、まじゃすこのマーク（2026-11-16 ユーザーの指定。締めと同じアイコン）。帯は「ルールとマナーに沿った正しい手順」（ルールやマナーに沿った方法だと示す）
    ic = _app_icon(78)
    if a < 1: ic = ic.copy(); ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
    d._image.alpha_composite(ic, (104, y + 44))
    kt = sc.get("kicker", ""); ft = fit(d, kt, 42, W - 2 * 200 - 64, 800)
    kw = d.textlength(kt, font=ft) + 64
    d.rounded_rectangle((W / 2 - kw / 2, y + 44, W / 2 + kw / 2, y + 44 + 78), radius=39, fill=(231, 86, 32, A(255)))
    text_c(d, W / 2, y + 44 + 37, kt, ft, (255, 255, 255, A(255)))
    ruby_c(d, W / 2, y + TY, sc["title"], fit(d, sc["title"], 132 if tr else 140, W - 140 - 90), (255, 255, 255, A(255)), 44)     # 長い題名（ロンアガリの方法）は、カードに入るまで小さく
    ruby_c(d, W / 2, y + SY, sc.get("sub", ""), font(52, 700), (255, 255, 255, A(225)), 22)
    text_c(d, W / 2, 1790, "majasco.jp", font(40, 800), (255, 255, 255, A(200)))

def _app_icon(sz):
    """まじゃすこのアイコン（角丸）"""
    k = ("i", sz)
    if k not in _icon:
        fav = Image.open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "favicon.png")).convert("RGBA").resize((sz, sz), Image.LANCZOS)
        m = Image.new("L", (sz, sz), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, sz, sz), radius=int(sz * .23), fill=255)
        fav.putalpha(Image.composite(fav.getchannel("A"), m, m)); _icon[k] = fav
    return _icon[k]
_icon = {}

def _rich(d, x, y, tx, size, maxw):
    """確認のカードの1行。{語|ルビ} と {語} は用語（緑の太字。ルビは字の上に小さく）。幅に入るまで字を小さくする"""
    import re as _re
    parts = [(m[0], None, None) if m[0] else (None, m[1], m[2] or None) for m in _re.findall(r"([^{}]+)|\{([^|}]+)(?:\|([^}]+))?\}", tx)]
    while True:
        f, fk = font(size, 800), font(size, 900)
        w = sum(d.textlength(p[0], font=f) if p[0] else d.textlength(p[1], font=fk) for p in parts)
        if w <= maxw or size <= 24: break
        size -= 1
    for plain, term, rb in parts:
        if plain: d.text((x, y), plain, font=f, fill=INK); x += d.textlength(plain, font=f); continue
        d.text((x, y), term, font=fk, fill=GREEN); tw = d.textlength(term, font=fk)
        if rb:
            rf = font(27, 800); d.text((x + tw / 2 - d.textlength(rb, font=rf) / 2, y - 31), rb, font=rf, fill=GREEN)
        x += tw
    return x


# ルビ（2026-11-14 ユーザーの指定「暗槓とかにルビを振って」）。画面に出す字（題名の下・見出しの説明・確認カード・字幕）で、この語には上に小さく読みを付ける。
# 読みはサイトの記事のルビ（tools/add_ruby.py の READ）と同じ
RUBY = {"暗槓": "アンカン", "大明槓": "ダイミンカン", "加槓": "カカン", "明槓": "ミンカン", "槍槓": "チャンカン", "嶺上牌": "リンシャンパイ", "王牌": "ワンパイ",
        "門前": "メンゼン", "供託": "キョウタク", "喰い替え": "クイカエ", "連荘": "レンチャン", "荒牌平局": "ホワンパイピンチュー", "罰符": "バップ", "海底牌": "ハイテイハイ", "河底牌": "ホウテイハイ"}
# 字幕で、動画ごとに最初に出る所だけ読みを付ける語（2026-11-24 ユーザーの了承。毎回付けるとうるさい）。first_ruby(name) が EXTRA（字幕の文→付ける語）を作る
RUBY_FIRST = {"搭子": "ターツ", "対子": "トイツ", "他家": "ターチャ", "上家": "カミチャ", "対面": "トイメン", "下家": "シモチャ", "東家": "トンチャ", "打牌": "ダハイ"}
EXTRA = {}
def first_ruby(name):
    import narration
    seen = set(); EXTRA.clear()
    for seg, tx in narration.lines(name):
        if not (seg.startswith("step") or seg == "tail"): continue
        for u in sub_units(tx):
            new = {w: r for w, r in RUBY_FIRST.items() if w in u and w not in seen}
            seen |= set(new)
            if new: EXTRA[u] = new
def ruby_parts(tx):
    """文 → [(字, 読み or None, 用語か)]。{語|読み}・{語} は用語（確認カードの緑の字）。ふつうの字の中の RUBY の語にも読みを付ける"""
    import re as _re
    out = []; RB = {**RUBY, **EXTRA.get(tx, {})}
    for m in _re.findall(r"([^{}]+)|\{\s*([^|}]+?)\s*(?:\|([^}]+))?\}", tx):
        if m[0]:
            pat = "(" + "|".join(sorted(map(_re.escape, RB), key=len, reverse=True)) + ")"
            for piece in _re.split(pat, m[0]):
                if piece: out.append((piece, RB.get(piece), False))
        else: out.append((m[1], m[2] or RUBY.get(m[1]), True))
    return out
def ruby_w(d, tx, ft, fk=None):
    return sum(d.textlength(p, font=(fk if (t and fk) else ft)) for p, r, t in ruby_parts(tx))
def ruby_draw(d, x, y, tx, ft, fill, rsize=22, fk=None, tfill=None, rfill=None):
    """左上 (x, y) から書く。読みは字の上に（y から rsize+6 だけ上）。書き終えた右の x を返す"""
    for p, r, t in ruby_parts(tx):
        f = fk if (t and fk) else ft; c = (tfill if (t and tfill) else fill)
        d.text((x, y), p, font=f, fill=c); w = d.textlength(p, font=f)
        if r:
            rf = font(rsize, 800); rw = d.textlength(r, font=rf)
            if rw > w + 8:      # 読みが字より長いときは、字の幅に収まるまで小さく
                rf = font(max(14, int(rsize * (w + 8) / rw)), 800); rw = d.textlength(r, font=rf)
            l_, t_, r_, b_ = d.textbbox((x, y), p, font=f)
            # 読みの字の「下のふち」を、漢字の上のふちから RUBY_GAP だけ上に置く（字の高さで測る。前は字の大きさで置いていて、読みが漢字にかぶった。2026-11-24 ユーザーの指摘）
            rb = d.textbbox((0, 0), r, font=rf)
            d.text((x + w / 2 - rw / 2, t_ - RUBY_GAP - rb[3]), r, font=rf, fill=rfill or c)
        x += w
    return x
RUBY_GAP = 5      # 読みと漢字のすき間（px）


def ruby_c(d, cx, cy, tx, ft, fill, rsize=22, rfill=None):
    """真ん中 (cx, cy) にそろえて書く（text_c のルビつき版）"""
    import re as _re
    plain = "".join(p for p, r, t in ruby_parts(tx))
    l, t, r, b = d.textbbox((0, 0), plain, font=ft)
    ruby_draw(d, cx - (r - l) / 2 - l, cy - (b - t) / 2 - t, tx, ft, fill, rsize, rfill=rfill)
def fit(d, tx, size, maxw, wght=900):
    """幅 maxw に入るまで字を小さくした font（題名・見出しのはみ出し止め。2026-11-14 ユーザーの指摘）"""
    while ruby_w(d, tx, font(size, wght)) > maxw and size > 24: size -= 2
    return font(size, wght)


CARD_BORDER = ((231, 86, 32), 8)     # 確認カードの枠（色, 太さ）＝オレンジ8px（2026-11-14 ユーザーの判断。None＝枠なし）
def pre_card(d, pre, t):
    """前置き（①の前）。下に置く（手牌は画面の真ん中）。説明の行が時間で1行ずつ増える。
    行は (時刻, 文) か (時刻, 文, 用語の説明)。文の {語|ルビ} は用語。説明は行の右に灰色で「＝同じ牌2枚」のように（2026-11-14 ユーザーの指定: 具体の牌の例はやめて抽象で。難しい用語には簡単な説明。最後の1行は緑の帯＝全部の動画）"""
    k = min(1, t * 4); RH = 92; CB = pre.get("concl"); CH = 96
    NT = pre.get("note"); NH = (92 if any(r for p, r, t_ in ruby_parts(NT[1])) else 56) if NT else 0      # ただし書き（緑の帯の下に、小さな灰色の字。ルビがあるときは高く）
    HO = 42 if any(r for p, r, t_ in ruby_parts(pre["head"])) else 0      # 題名にルビがあるときは、上の枠から離す
    hgt = 146 + RH * (len(pre["lines"]) - (1 if CB else 0)) + (CH + 50 if CB else 18) + NH + HO
    y = (pre["top"] if pre.get("top") else H - 80 - hgt) + int((1 - k) * 30)      # top: 画面の上に置く（ツモと打牌は手牌が画面の下寄りになる画角なので）
    TOPY[0] = (pre["top"] + hgt + 20) if pre.get("top") else 610      # 札はカードの下に
    d.rounded_rectangle((40, y, W - 40, y + hgt), radius=44, fill=(255, 255, 255, int(242 * k)))
    if CARD_BORDER:      # カードの枠（色, 太さ）
        c_, w_ = CARD_BORDER; d.rounded_rectangle((40, y, W - 40, y + hgt), radius=44, outline=c_ + (int(255 * k),), width=w_)
    yc, y = y, y + HO; ft = font(46, 800); lw = d.textlength("確認", font=ft) + 60
    d.rounded_rectangle((76, y + 36, 76 + lw, y + 36 + 76), radius=38, fill=ORANGE)
    text_c(d, 76 + lw / 2, y + 36 + 36, "確認", ft, WHITE)
    hf = fit(d, pre["head"], 76, W - 40 - 36 - (76 + lw + 24))
    ruby_draw(d, 76 + lw + 24, y + 26 + (76 - hf.size) // 2, pre["head"], hf, INK, 36, rfill=GREEN)
    for n, ln in enumerate([ln for ln in pre["lines"] if t >= ln[0]]):
        yy = y + 146 + 26 + n * RH; ex = ln[2] if len(ln) > 2 else None
        if CB and n == len(pre["lines"]) - 1:      # 結論の1行は、緑の帯に白い字（2026-11-14 ユーザーの判断・案B）
            by = yy + 6; d.rounded_rectangle((70, by, W - 70, by + CH), radius=22, fill=GREEN)
            bt = "".join(p for p, r, t in ruby_parts(ln[1])); hr = any(r for p, r, t in ruby_parts(ln[1]))
            ruby_c(d, W / 2, by + CH / 2 - 2 + (14 if hr else 0), ln[1].replace("{ ", "{").replace(" }", "}"), fit(d, bt, 46 if hr else 48, W - 180), WHITE, 27); continue
        d.ellipse((80, yy + 14, 102, yy + 36), fill=GREEN)
        exw = (22 + ruby_w(d, "＝" + ex, font(32, 800))) if ex else 0
        x = _rich(d, 122, yy, ln[1], 42, W - 60 - 122 - exw)
        if ex:
            x += 22; ruby_draw(d, x, yy + 9, "＝" + ex, font(32, 800), (95, 110, 106), 23)
    if NT and t >= NT[0]:
        ruby_c(d, W / 2, yc + hgt - 40, NT[1], fit(d, NT[1], 32, W - 140, 800), (95, 110, 106), 23)

BAPPU = [(4, "点数は動かない", ""), (3, "ノーテン1人が、3人に1,000点ずつ", "−3,000 → ＋1,000×3"), (2, "ノーテン2人が、1,500点ずつ", "−1,500×2 → ＋1,500×2"),
         (1, "ノーテン3人が、1,000点ずつ", "−1,000×3 → ＋3,000"), (0, "点数は動かない", "")]
def bappu_card(d, k, now=2):
    """流局のノーテン罰符の早見表（2026-11-18 ユーザーの指定: テンパイ0〜4人の全部のパターンを、わかりやすく）。
    行＝テンパイの人数。左に4人の丸（緑＝テンパイ・灰＝ノーテン）、右に払い方。now＝この動画の場面（テンパイ2人）の行をオレンジで囲む。
    置き場所は見出し（〜y580）と字幕（y1500〜）のあいだ"""
    a = min(1, k * 4); A = lambda v: int(v * a); y0 = 640 + int((1 - min(1, k * 4)) * 30); RH = 136
    d.rounded_rectangle((40, y0, W - 40, y0 + 126 + RH * 5 + 24), radius=44, fill=(255, 255, 255, A(244)))
    d.rounded_rectangle((40, y0, W - 40, y0 + 126 + RH * 5 + 24), radius=44, outline=(231, 86, 32, A(255)), width=8)
    ruby_c(d, W / 2, y0 + 74, "{ノーテン罰符|ノーテンバップ}＝場に3,000点", font(50), (31, 42, 40, A(255)), 22)
    for n, (tp, tx, sub) in enumerate(BAPPU):
        y = y0 + 126 + n * RH
        if tp == now:
            d.rounded_rectangle((64, y + 6, W - 64, y + RH - 6), radius=26, fill=(255, 239, 228, A(255)), outline=(231, 86, 32, A(255)), width=6)
            d.rounded_rectangle((W - 64 - 132, y - 14, W - 64 - 8, y + 30), radius=22, fill=(231, 86, 32, A(255)))
            text_c(d, W - 64 - 70, y + 7, "この動画", font(28), (255, 255, 255, A(255)))
        elif n: d.line((90, y, W - 90, y), fill=(213, 226, 223, A(255)), width=3)
        text_c(d, 150, y + RH / 2 - 26, f"テンパイ", font(28, 800), (95, 110, 106, A(255)))
        text_c(d, 150, y + RH / 2 + 18, f"{tp}人", font(54), (23, 112, 131, A(255)))
        for j in range(4):      # 4人の丸
            cx = 262 + j * 50; cy = y + RH / 2; on = j < tp
            d.ellipse((cx - 19, cy - 19, cx + 19, cy + 19), fill=(23, 112, 131, A(255)) if on else (255, 255, 255, A(255)), outline=(23, 112, 131, A(255)) if on else (180, 192, 189, A(255)), width=4)
        x = 480; ft = fit(d, tx, 40, W - 90 - x, 900)
        d.text((x, y + (RH / 2 - 28 if sub else RH / 2 - 24)), tx, font=ft, fill=(31, 42, 40, A(255)))
        if sub: d.text((x, y + RH / 2 + 16), sub, font=font(28, 700), fill=(95, 110, 106, A(255)))


BAPPU2 = [("ノーテン罰符", None, "ノーテンの人が、テンパイの人へ払う"), ("ノーテンの2人が", {0, 3}, "ノーテン2人が、1,500点ずつ払う"),
          ("テンパイが1人なら", {0}, "ノーテン3人が、1,000点ずつ払う"), ("テンパイが3人なら", {0, 2, 3}, "ノーテン1人が、3人に1,000点ずつ払う"),
          ("全員テンパイか", "all", "全員同じなら、点数は動かない")]
SEATP = {0: (0, 1), 1: (1, 0), 2: (0, -1), 3: (-1, 0)}; SEATN = {0: "自分", 1: "下家", 2: "対面", 3: "上家"}
def bappu_phases(subs):
    """④の声の、例を切りかえる時刻（その手順が出てからの秒）"""
    out = []
    for w, ten, tx in BAPPU2:
        s_ = say_at(subs, w)
        if s_ is not None: out.append((.25 + s_ - .1, ten, tx))
    return out
def bappu_live(d, t, ph):
    """ノーテン罰符の例のカード（2026-11-25 ユーザーの指定「話しているセリフに合わせてカードの表示を変える」）。
    左に卓の図（4人の丸: 緑＝テンパイ・白＝ノーテン、矢印＝払う向き）、右に人数と払い方。声の文が変わるたびに、図と文が入れかわる"""
    cur = [p for p in ph if t >= p[0]]
    if not cur: return
    t0, ten, tx = cur[-1]; k = min(1, (t - ph[0][0]) * 4); a = min(1, (t - t0) * 5); A = lambda v, q=1: int(v * q)
    if len(ph) > 1 and ph[1][0] <= t < ph[1][0] + 1.9:      # 下家 → 自分の1,500点を3Dで映しているあいだは、カードを下げる（2026-11-25 ユーザーの指定）
        return
    if len(ph) > 1 and t >= ph[1][0] + 1.9 and cur[-1] is ph[1]: a = min(1, (t - ph[1][0] - 1.9) * 5)
    y0 = 1060 + int((1 - k) * 30); h = 420
    d.rounded_rectangle((40, y0, W - 40, y0 + h), radius=40, fill=(255, 255, 255, A(246, k)), outline=(231, 86, 32, A(255, k)), width=7)
    ruby_c(d, W / 2, y0 + 84, "{ノーテン罰符|ノーテンバップ}＝場に3,000点", font(46), (31, 42, 40, A(255, k)), 22)      # ルビとカードの上のふちのあいだをあける
    if ten == "all": ten = set(range(4)) if int(t * 1.25) % 2 == 0 else set()      # 全員テンパイ ⇄ 全員ノーテン を交互に
    cx, cy, R = 230, y0 + 268, 92
    d.rounded_rectangle((cx - R + 18, cy - R + 18, cx + R - 18, cy + R - 18), radius=18, fill=(228, 243, 236, A(255, a)))
    if ten is not None:
        pays = []
        nt = [s_ for s_ in range(4) if s_ not in ten]
        if len(ten) == 2: pays = [(1, 0), (2, 3)]      # この動画の場面（下家→自分・対面→上家）
        elif len(ten) in (1, 3): pays = [(n_, t_) for n_ in nt for t_ in ten]
        for g, r_ in pays:      # 払う向きの矢印
            (gx, gy), (rx, ry) = SEATP[g], SEATP[r_]
            x1, y1, x2, y2 = cx + gx * R, cy + gy * R, cx + rx * R, cy + ry * R
            import math as _m
            L = _m.hypot(x2 - x1, y2 - y1); ux, uy = (x2 - x1) / L, (y2 - y1) / L
            x1, y1, x2, y2 = x1 + ux * 36, y1 + uy * 36, x2 - ux * 40, y2 - uy * 40
            d.line((x1, y1, x2, y2), fill=(231, 86, 32, A(120, a)), width=6)
            d.polygon([(x2 + ux * 14, y2 + uy * 14), (x2 - ux * 10 - uy * 14, y2 - uy * 10 + ux * 14), (x2 - ux * 10 + uy * 14, y2 - uy * 10 - ux * 14)], fill=(231, 86, 32, A(255, a)))
            u_ = ((t - t0) * .9) % 1.0      # 点棒が、払う人から受け取る人へ、矢印にそってすべる（くり返し）
            px_, py_ = x1 + (x2 - x1) * u_, y1 + (y2 - y1) * u_; ang = _m.atan2(uy, ux)
            sw, shh = 26, 7; pts = [(-sw, -shh), (sw, -shh), (sw, shh), (-sw, shh)]
            pts = [(px_ + p_[0] * _m.cos(ang) - p_[1] * _m.sin(ang), py_ + p_[0] * _m.sin(ang) + p_[1] * _m.cos(ang)) for p_ in pts]
            d.polygon(pts, fill=(255, 255, 255, A(255, a)), outline=(31, 42, 40, A(255, a)))
            d.ellipse((px_ - 4, py_ - 4, px_ + 4, py_ + 4), fill=(201, 47, 66, A(255, a)))
    for s_ in range(4):
        px, py = cx + SEATP[s_][0] * R, cy + SEATP[s_][1] * R; on = ten is not None and s_ in ten
        d.ellipse((px - 30, py - 30, px + 30, py + 30), fill=(23, 112, 131, A(255, a)) if on else (255, 255, 255, A(255, a)), outline=(23, 112, 131, A(255, a)) if on else (170, 182, 179, A(255, a)), width=5)
        text_c(d, px, py - 2, SEATN[s_][:1], font(28), (255, 255, 255, A(255, a)) if on else (120, 132, 129, A(255, a)))
    x = 420
    if ten is not None:
        text_c(d, x + 100, y0 + 178, "テンパイ", font(30, 800), (95, 110, 106, A(255, a)))
        n_ = len(ten); text_c(d, x + 100, y0 + 238, f"{n_}人", font(70), (23, 112, 131, A(255, a)))
    tx_x = x if ten is None else x + 200; aw = W - 80 - tx_x; rows = [tx]
    if d.textlength(tx, font=font(38, 900)) > aw:      # 長い文は「、」で2行に
        c_ = tx.find("、") + 1 or len(tx) // 2; rows = [tx[:c_], tx[c_:]]
    ft = fit(d, max(rows, key=lambda r_: d.textlength(r_, font=font(38, 900))), 38, aw, 900)
    for j, r_ in enumerate(rows): d.text((tx_x, y0 + 268 - 28 * len(rows) + j * 56), r_, font=ft, fill=(31, 42, 40, A(255, a)))


_bub = {}
# 吹き出しの場所（2026-11-14 ユーザーの指定「口や顔あたりから出るように。対面の顔が隠れないように」）:
#   ①発声のカメラ（肩ごし・どの動画も同じ画角）では、手前の選手の頭が左（x 0〜350・y 480〜960）、対面の顔が上の真ん中（x 600〜900・y 470〜800）。
#   吹き出しは頭の右下（卓の左手前の上）に置き、しっぽを左上へ＝手前の選手の顔の前（頭の右のふち）へ向ける。対面の顔・見出しのカードにかからない
BUB_C = (640, 1045)          # 吹き出しの真ん中（2026-11-14 ユーザーの指定: 右へ。ふちが手前の選手の頭にかからない所＝しっぽの先だけが頭のふちに触れる）
BUB_TIP = (-330, -125)       # しっぽの先（真ん中からのずれ。手前の選手の顔の前を指す）
BUB_POS = {"3900": ((560, 1110), (-60, 300)), "400・700": ((560, 1110), (-60, 300)), "500・1000": ((560, 1110), (-60, 300)), "1000・2000": ((560, 1290), (-60, 300)), "ツモ": ((700, 1330), (110, 300))}     # ツモの②は牌に寄った画角。ツモった牌にかからないよう下から     # 言葉ごとの吹き出しの場所（真ん中, しっぽの向き）。無ければ BUB_FACE に向けて置く
# しっぽはできるだけ短く（2026-11-14 ユーザーの指定）。しっぽの長さ＝ふちから TAIL_L。肩ごしの画角では、しっぽの先を手前の選手の顔の前（BUB_FACE）に合わせ、
# 吹き出しの本体はそこから BUB_TIP の向きの逆へ置く（前の真ん中 BUB_C から先を指す形と同じ向き）
TAIL_L = 46
BUB_FACE = (445, 905)      # 手前の選手の頭の右のふち（顔の前）。吹き出しの本体は頭にかけない
# 肩ごしの吹き出しは、左のふちを固定（BUB_L）して、言葉が長いほど右へのばす。しっぽは左のはしから、左上の顔の前へ短く出す（2026-11-15 ユーザーの判断・案C）。
# しっぽの出っぱり（ふちから先まで）は「3900」と同じ約45px（2026-11-14 ユーザーの指定「ポンもリーチも、しっぽの長さと左をそろえる」）
BUB_L, BUB_Y = 383, 990      # 吹き出しの左のふちの x・真ん中の y（案Cから少し左へ。2026-11-15 ユーザーの指定）
BUB_U = (-.85, -.53)         # しっぽの向き（左上）
def _bub_geom(tx, w, h):
    """吹き出しの真ん中と、しっぽの付け根・先（真ん中からのずれ）"""
    import math as _m
    if tx in BUB_POS:
        c, v = BUB_POS[tx]
        L_ = _m.hypot(*v); dx, dy = v[0] / L_, v[1] / L_
        t = min((w / 2) / max(abs(dx), 1e-6), (h / 2) / max(abs(dy), 1e-6))      # 真ん中からふちまで（その向きで）
        tip = (dx * (t + TAIL_L), dy * (t + TAIL_L))
        ang = _m.atan2(dy, dx); base = (_m.cos(ang) * (w / 2 - 70), _m.sin(ang) * (h / 2 - 30))
        return c, base, tip
    c = (BUB_L + w / 2, BUB_Y)
    base = (40 - w / 2, -10)                                # 左のはしの少し内がわ
    k = (45 + 40) / -BUB_U[0]                               # 左のはしから約45px 出す
    tip = (base[0] + BUB_U[0] * k, base[1] + BUB_U[1] * k)
    return c, base, tip
def bubble(d, tx, k):
    """発声の吹き出し。オレンジの地を、しっぽまで白い枠でぐるりと囲む（2026-11-13 ユーザーの指定。これから使う吹き出しもすべて）。
    ふちがぎざぎざにならないように、3倍の大きさで「白い形 → 少し小さいオレンジの形」を描いてから縮める"""
    a = min(1, k * 5); sc_ = .8 + .2 * a
    if tx not in _bub:
        Q = 3; ft = font(96 * Q); tmp = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        w = max(400, tmp.textlength("「" + tx + "」", font=font(96)) + 100); h = 160; B = 9; pad = 240
        im = Image.new("RGBA", (int((w + pad * 2) * Q), int((h + pad * 2) * Q)), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        X = lambda v: (v + pad) * Q
        _, base, tip = _bub_geom(tx, w, h)
        cx, cy = w / 2, h / 2; tx_, ty_ = cx + tip[0], cy + tip[1]
        import math as _m
        bx, by_ = cx + base[0], cy + base[1]      # しっぽの付け根（ふちの少し内がわ）
        ang = _m.atan2(ty_ - by_, tx_ - bx); nx, ny = -_m.sin(ang), _m.cos(ang)
        # オレンジの形（丸い四角＋しっぽ）を1枚の型にして、白い枠はその型を同じ幅だけ外へ太らせて作る。
        # （前は白い形とオレンジの形を別々に描いていて、細長いしっぽの下のふちだけ白が付かなかった＝2026-11-14 確かめて直した）
        half = 34; R = B * Q
        tri = [(X(bx + nx * half), X(by_ + ny * half)), (X(bx - nx * half), X(by_ - ny * half)), (X(tx_), X(ty_))]
        m = Image.new("L", im.size, 0); dm = ImageDraw.Draw(m)
        dm.rounded_rectangle((X(0), X(0), X(w), X(h)), radius=h / 2 * Q, fill=255); dm.polygon(tri, fill=255)
        wm = Image.new("L", im.size, 0); dw = ImageDraw.Draw(wm)      # 白い枠＝型をどこも同じ幅 R だけ外へ（角は丸く）
        dw.rounded_rectangle((X(0) - R, X(0) - R, X(w) + R, X(h) + R), radius=h / 2 * Q + R, fill=255); dw.polygon(tri, fill=255)
        dw.line(tri + [tri[0]], fill=255, width=2 * R, joint="curve")
        for px, py in tri: dw.ellipse((px - R, py - R, px + R, py + R), fill=255)
        im.paste((255, 255, 255, 255), (0, 0), wm); im.paste((231, 86, 32, 255), (0, 0), m)
        l, t, r, b_ = dr.textbbox((0, 0), "「" + tx + "」", font=ft)
        dr.text((X(cx) - (r - l) / 2 - l, X(cy) - 4 * Q - (b_ - t) / 2 - t), "「" + tx + "」", font=ft, fill=(255, 255, 255, 255))
        _bub[tx] = (im.resize((im.width // Q, im.height // Q), Image.LANCZOS), w, h, pad, _bub_geom(tx, w, h)[0])
    im, w, h, pad, c_ = _bub[tx]
    if sc_ < .999: im = im.resize((max(1, int(im.width * sc_)), max(1, int(im.height * sc_))), Image.LANCZOS)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    d._image.alpha_composite(im, (int(c_[0] - (w / 2 + pad) * sc_), int(c_[1] - (h / 2 + pad) * sc_)))

# ---- 囲みと札（2026-11-24 ユーザーの指定: 説明の動画は卓全体を映し、大事な所を囲む）----
# 手順ごとに (囲む牌の名前＝marks.json, 色, 札の言葉, 札に大きく出す牌, 札の場所)。札の場所: UL・UR＝上の左右／LL・LR＝下の左右／LM・RM＝左右の中ほど。言葉が空なら囲みだけ
MKC = {"teal": (23, 112, 131), "orange": (231, 86, 32), "blue": (66, 97, 170), "red": (201, 47, 66), "green": (22, 138, 80)}
WAIT_ = ("hand5", "teal", "待ち", ["s1", "s4", "s7"], "LL")
MARKS = {
    "furiten": [[], [("fu7", "orange", "自分が切った", ["s1"], "LR")], [("called", "red", "ロンできない", ["s4"], "UL"), ("fu7", "orange", "自分が切った", ["s1"], "LR", "自分の河に")],
                [("fu7", "orange", "", [], ""), ("next", "green", "ツモはできる", ["s4"], "LR", "ツモアガリできます")]],      # 手を引いてから（リーチ後のフリテンと同じ）
    "furiten2": [[("meld", "orange", "チーした牌", ["m2", "m3", "m4"], "RM")], [("o1", "blue", "見逃し", ["s1"], "UR")], [("o1", "blue", "見逃し", ["s1"], "UR"), ("o2", "red", "ロンできない", ["s4"], "UL")],
                 [("next", "orange", "自分が打牌", ["z2"], "LM")], [("o4", "green", "ロンできる", ["s7"], "UR")]],
    "furiten3": [[("rk", "orange", "リーチ", [], "LR"), ("bou", "orange", "", [], "")], [("o1", "blue", "見逃し", ["s1"], "UR")], [("next", "orange", "自分が打牌", ["p9"], "LR")],      # ③は手牌に寄った画角で一索が映らないので、見逃しは出さない（2026-11-28 ユーザーの指定）
                 [("o1", "blue", "見逃し", ["s1"], "UR"), ("o6", "red", "ロンできない", ["s4"], "UL")], [("next2", "green", "ツモはできる", ["s7"], "LR", "ツモアガリできます")]],      # ⑤の「ツモはできる」は手を引いてから（手がかかったまま出ていた）
}
_tim = {}
def _tile_img(code, h):
    """札・カードの牌の絵。3Dの牌そのもの（scene.py --tileimgs で書き出した tiles3d/。2026-11-25 ユーザーの指定「平面ののっぺりした牌でなく、3D動画の牌の感じで」・全動画）"""
    k = (code, h)
    if k not in _tim:
        here_ = os.path.dirname(os.path.abspath(__file__))
        fp = next((q for q in (os.path.join(here_, "tiles3d", code + ".png"), os.path.join(here_, "tiles", code + ".png")) if os.path.exists(q)), None)
        if fp: im = Image.open(fp).convert("RGBA"); _tim[k] = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        else: _tim[k] = tile_img(code, round(h * 3 / 4), h)
    return _tim[k]
MK_T0 = {}; POPS = []      # 囲みが出た時刻（ぽこんと出す）・出た瞬間（音を鳴らす）
def _ease_pop(k):
    """0→1 で、少し行きすぎて戻る（ぽこん）"""
    import math as _m
    return 1 + .18 * _m.sin(_m.pi * min(1, k)) * (1 - min(1, k)) * 2 if k < 1 else 1.0
CUR = [None]
TOPY = [610]      # 札を置ける一番上（見出しのカードの下。注意書きのある手順はカードが高いので下げる＝2026-11-27 札がカードに隠れた）
def _ring_pad(b):
    """囲みのすきまと線の太さ（牌の大きさに合わせる。小さい牌は細く・すきまも小さく）"""
    m = min(b[2] - b[0], b[3] - b[1])
    return max(5, min(22, m * .16)), int(max(4, min(9, m * .12)))
MK_NUDGE = {}
def draw_marks(d, marks, here, xon=True, now=None, key=""):
    """大事な牌を目立たせる（2026-11-25 ユーザーの指定「枠よりウィットに富んだ・見ていて面白い表現を」）:
    まわりを少し暗くして、その牌にスポットライト（丸く明るいまま）＋色の輪 → 札（色のラベルと3Dの牌。白いカードは敷かない）から、はずむ矢印で指す。
    出るときは、ぽこんとはずむ（MK_T0）＋「ポン」（POPS）"""
    from PIL import ImageFilter
    todo = [m for m in marks if m[0] in here]; kk_ = {}
    for nm, col, tx, codes, pos in todo:
        if now is not None:
            t0 = MK_T0.setdefault((key, nm), now)
            if t0 == now: POPS.append(now)
            kk_[nm] = min(1.0, (now - t0) / .3)
        else: kk_[nm] = 1.0
    if not todo: return
    # スポットライト: 牌のまわりを丸く残して、ほかを暗く（ふちはぼかす）
    im = CUR[0]
    if im is not None:
        sc_ = 4; m = Image.new("L", (W // sc_, H // sc_), int(255 * .42 * max(kk_.values())))
        dm = ImageDraw.Draw(m)
        for nm, col, tx, codes, pos in todo:
            x0, y0, x1, y1 = here[nm]; pd, lw = _ring_pad(here[nm]); e = pd + lw + 6
            dm.rounded_rectangle(((x0 - e) / sc_, (y0 - e) / sc_, (x1 + e) / sc_, (y1 + e) / sc_), radius=min(x1 - x0, y1 - y0) / 2 / sc_ + e / sc_, fill=0)
        m = m.filter(ImageFilter.GaussianBlur(5)).resize((W, H), Image.BILINEAR)
        im.paste(Image.new("RGBA", (W, H), (8, 14, 18, 255)), (0, 0), m)
    tnow = now or 0.0; box = {}
    for nm, col, tx, codes, pos in todo:
        if not tx: continue
        TH = 118; ims = [_tile_img(c, TH) for c in codes]; f = font(44)
        w = max(d.textlength(tx, font=f) + 64, sum(i.width + 8 for i in ims) + 8); h = 76 + (TH + 14 if ims else 0)
        # 札は、その牌のすぐ近くに置く（上 → 下 → 右 → 左の順に、見出し・字幕・ほかの札や牌に重ならない所）。矢印は短く（2026-11-25 ユーザーの指摘「矢印の始まりと終わりの位置が適切か」）
        x0, y0, x1, y1 = here[nm]; cx = (x0 + x1) / 2; cy = (y0 + y1) / 2; G = 70
        cand = [(cx - w / 2, y0 - G - h), (cx - w / 2, y1 + G), (x1 + G, cy - h / 2), (x0 - G - w, cy - h / 2)]
        taken = [b[:4] for b in box.values()] + [(here[m[0]][0] - 10, here[m[0]][1] - 10, here[m[0]][2] - here[m[0]][0] + 20, here[m[0]][3] - here[m[0]][1] + 20) for m in todo]
        hit = lambda x, y: any(x < bx + bw and bx < x + w and y < by + bh and by < y + h for bx, by, bw, bh in taken)
        best = None
        for x, y in cand:
            x = min(max(x, 20), W - 20 - w); y = min(max(y, TOPY[0]), 1290 - h)
            if not hit(x, y): best = (x, y); break
        if best is None: x, y = min(max(cand[0][0], 20), W - 20 - w), min(max(cand[0][1], TOPY[0]), 1290 - h)
        else: x, y = best
        if nm in MK_NUDGE:      # 札を牌のすぐ左へ。右のふちが短い矢印の根もと（河にかかってもよい＝2026-11-28 ユーザーの指定「矢印のすぐ左まで」）
            pd_, lw_ = _ring_pad(here[nm]); x = x0 - pd_ - lw_ - MK_NUDGE[nm] - w
        box[nm] = (x, y, w, h, ims, f)
    import math as _m
    for nm, col, tx, codes, pos in todo:      # 輪 → 矢印
        c = MKC[col]; x0, y0, x1, y1 = here[nm]; k = kk_[nm]; a = int(255 * min(1, k * 2.5))
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2; pd, lw = _ring_pad(here[nm]); ep = _ease_pop(k)
        rx, ry = ((x1 - x0) / 2 + pd) * ep, ((y1 - y0) / 2 + pd) * ep; rr = min(rx, ry)
        # 牌の面に沿った角丸の囲み（楕円だと、小さい河の牌でとなりの牌まで入った＝2026-11-27 ユーザーの指摘）。線は牌の外がわに
        d.rounded_rectangle((cx - rx - lw / 2 - 3, cy - ry - lw / 2 - 3, cx + rx + lw / 2 + 3, cy + ry + lw / 2 + 3), radius=rr + lw / 2 + 3, outline=(255, 255, 255, a), width=lw + 6)
        d.rounded_rectangle((cx - rx, cy - ry, cx + rx, cy + ry), radius=rr, outline=c + (a,), width=lw)
        if col == "red" and xon:      # ロンできない牌には大きな×。「ロンできません」を言い終えてから
            r_ = max(rx, ry) * .8
            for sg in (1, -1):
                d.line((cx - r_, cy - r_ * sg, cx + r_, cy + r_ * sg), fill=(255, 255, 255, 255), width=24)
                d.line((cx - r_, cy - r_ * sg, cx + r_, cy + r_ * sg), fill=c + (255,), width=13)
        if nm in box and k > .3:      # 札から牌へ、はずむ矢印
            x, y, w, h, ims, f = box[nm]; bx, by = min(max(cx, x + 30), x + w - 30), min(max(cy, y + 20), y + h - 20)      # 札のふちの、牌にいちばん近い所から
            if nm in MK_NUDGE: bx, by = x + w + 4, cy      # 寄せた札は、右のふちから横に短く
            if y + h < cy: by = y + h + 6
            elif y > cy: by = y - 6
            elif x + w < cx: bx = x + w + 6
            else: bx = x - 6
            L = _m.hypot(cx - bx, cy - by) or 1; ux, uy = (cx - bx) / L, (cy - by) / L
            if L < max(rx, ry) + (0 if nm in MK_NUDGE else 40): continue      # 寄せた札は、短くても矢印を残す      # 札が牌のすぐとなりなら、矢印はいらない
            ex, ey = cx - ux * (max(rx, ry) + 16), cy - uy * (max(rx, ry) + 16)
            bob = 10 * _m.sin(tnow * 7)      # 先がぴょこぴょこ動く
            ex, ey = ex - ux * bob, ey - uy * bob
            d.line((bx, by, ex, ey), fill=(255, 255, 255, a), width=18); d.line((bx, by, ex, ey), fill=c + (a,), width=10)
            hx, hy = -uy, ux
            d.polygon([(ex + ux * 26, ey + uy * 26), (ex - ux * 6 + hx * 22, ey - uy * 6 + hy * 22), (ex - ux * 6 - hx * 22, ey - uy * 6 - hy * 22)], fill=c + (a,), outline=(255, 255, 255, a))
    for nm, (x, y, w, h, ims, f) in box.items():      # 札: 色のラベル＋3Dの牌（白いカードは敷かない）
        col, tx = next((m[1], m[2]) for m in todo if m[0] == nm); c = MKC[col]; k = kk_[nm]
        if k < .3: continue
        sc_ = _ease_pop((k - .3) / .7); a = int(255 * min(1, (k - .3) * 4))
        lw = d.textlength(tx, font=f) + 56; lx = x + (w - lw) / 2; ly = y
        d.rounded_rectangle((lx - 4, ly - 4 + (1 - sc_) * 20, lx + lw + 4, ly + 66 + (1 - sc_) * 20), radius=36, fill=(255, 255, 255, a))
        d.rounded_rectangle((lx, ly + (1 - sc_) * 20, lx + lw, ly + 62 + (1 - sc_) * 20), radius=32, fill=c + (a,))
        text_c(d, lx + lw / 2, ly + 30 + (1 - sc_) * 20, tx, f, (255, 255, 255, a))
        xx = x + w / 2 - (sum(i.width + 8 for i in ims) - 8) / 2
        if nm in MK_NUDGE: xx = x + w - (sum(i.width + 8 for i in ims) - 8)      # 寄せた札は、牌の絵も右（矢印の側）にそろえる
        for j_, i in enumerate(ims):
            i2 = i.resize((max(1, int(i.width * sc_)), max(1, int(i.height * sc_))), Image.LANCZOS) if sc_ != 1 else i
            if a < 255: i2 = i2.copy(); i2.putalpha(i2.getchannel("A").point(lambda v: int(v * a / 255)))
            hop = int(18 * max(0.0, _m.sin(2 * _m.pi * (tnow * 1.3 - j_ * .14)))) if tx == "待ち" else 0      # 待ちの牌は、ぽこぽこ順に跳ねる
            sh = Image.new("RGBA", i2.size, (0, 0, 0, 0)); sh.putalpha(i2.getchannel("A").point(lambda v: int(v * .35)))
            d._image.alpha_composite(sh, (int(xx + 6), int(y + 76 + 8))); d._image.alpha_composite(i2, (int(xx), int(y + 76 - hop)))
            xx += i.width + 8

def summary(d, sc, k):
    a = int(240 * min(1, k * 3))
    n = len(sc["steps"]); y0 = 520 if n <= 5 else 420; RH = min(118, (1400 - y0 - 150) // n)      # 下の字幕（1490〜）に重ならない（2026-11-25 大明槓の7つで重なった）
    d.rounded_rectangle((90, y0, W - 90, y0 + 150 + n * RH), radius=50, fill=(255, 255, 255, a))
    st = sc["title"] + (f"（{sc['sub']}）" if sc.get("sub", "").endswith("編") else "")
    ruby_c(d, W / 2, y0 + (90 if any(r for p, r, t_ in ruby_parts(st)) else 78), st, fit(d, st, 66, W - 260), (23, 112, 131, min(255, a + 15)), 32)
    for i, s in enumerate(sc["steps"]):
        y = y0 + 150 + i * RH
        d.ellipse((150, y, 150 + 84, y + 84), fill=(231, 86, 32, min(255, a + 15)))
        text_c(d, 192, y + 40, str(i + 1), font(56), WHITE)
        d.text((264, y - 6), s[0], font=font(66), fill=INK)
        d.text((264 + d.textlength(s[0], font=font(66)) + 20, y + 22), s[1], font=font(34, 700), fill=GREEN)

OUTRO_LINE = ("麻雀のスコア記録は", "まじゃすこ で")     # 締めの文言（2026-11-12 ユーザーの判断。どの3D動画も同じ）
def outro_card(im, t, dur):
    """締め: 会場へ引いていく絵を少しずつ暗くし、ロゴ・名前・文言・majasco.jp を順に出す（案A）"""
    dark = min(1, t / 1.2) * .6      # 字が読めるように、会場の絵を暗くする
    if dark > 0: im.alpha_composite(Image.new("RGBA", (W, H), (0, 0, 0, int(255 * dark))))
    k = lambda a: max(0.0, min(1.0, (t - a) / .35))
    if "i" not in _icon:
        fav = Image.open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "assets", "favicon.png")).convert("RGBA").resize((220, 220), Image.LANCZOS)
        m = Image.new("L", (220, 220), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 220, 220), radius=50, fill=255)
        fav.putalpha(Image.composite(fav.getchannel("A"), m, m)); _icon["i"] = fav
    a1 = k(.7)
    if a1 > 0:
        ic = _icon["i"].copy(); ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a1)))
        im.alpha_composite(ic, ((W - 220) // 2, 560 + int((1 - a1) * 30)))
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    A = lambda a, v=255: (255, 255, 255, int(v * a))
    if a1 > 0: text_c(d, W / 2, 880, "まじゃすこ", font(110), A(a1))
    a2 = k(1.1)
    if a2 > 0:
        text_c(d, W / 2, 1020, OUTRO_LINE[0], font(56, 800), A(a2, 240)); text_c(d, W / 2, 1100, OUTRO_LINE[1], font(56, 800), A(a2, 240))
    a3 = k(1.5)
    if a3 > 0:
        d.rounded_rectangle((W / 2 - 230, 1210, W / 2 + 230, 1310), radius=50, fill=(231, 86, 32, int(255 * a3)))
        text_c(d, W / 2, 1258, "majasco.jp", font(54), A(a3))
    im.alpha_composite(ov)


SUB_MIN = 38      # 字幕の字の、いちばん小さい大きさ（1行に入れるために小さくしてよい所まで）
SUB_FIT = 44      # 字幕の1枚を詰めるときの字の大きさ
def sub_units(tx):
    """字幕に出す単位（1枚＝1行）。「。」ごとに機械的には切らない（2026-11-18 ユーザーの指定「長くなっていたらいい感じの場所で区切る」）:
    1. 字を42にすれば1行に入る文は分けない。長い文は「、」の所で、1行に入る長さに分ける（「チー、と声に出します」の「、と」では分けない）
    2. 「最後に、」のような短すぎる切れはしは、字を SUB_MIN まで小さくして、となりと1枚に
    3. 短い文は、文がまるごと入るときだけ前の1枚に足す（「〜します。ポンが優先なので、」のように、次の文の頭だけが前の1枚に残らない）"""
    import re as _re
    dd = ImageDraw.Draw(Image.new("RGBA", (8, 8))); fF = font(SUB_FIT, 800); fM = font(SUB_MIN, 800); maxw = W - 2 * 90
    wd = lambda x, f=fF: dd.textlength(x, font=f)
    pieces = []      # (文, 文のまるごとか)
    for sen in [x for x in _re.findall(r"[^。]+。?", tx) if x.strip()]:
        if wd(sen, font(42, 800)) <= maxw: pieces.append((sen, True)); continue      # 少し小さい字で1行に入る文は、分けない
        parts = _re.findall(r"(?:[^、]|、(?=と))+、?", sen); cur = []; chunks = []
        for part in parts:
            if cur and wd("".join(cur) + part) > maxw: chunks.append("".join(cur)); cur = [part]
            else: cur.append(part)
        if cur: chunks.append("".join(cur))
        k = 0
        while k < len(chunks) - 1:      # 短すぎる切れはしは、小さい字でとなりと1枚に
            if (wd(chunks[k]) < maxw * .35 or wd(chunks[k + 1]) < maxw * .35) and wd(chunks[k] + chunks[k + 1], fM) <= maxw:
                chunks[k:k + 2] = [chunks[k] + chunks[k + 1]]
            else: k += 1
        pieces += [(c, len(chunks) == 1) for c in chunks]
    out = []
    for c, whole in pieces:
        if out and whole and out[-1].endswith("。") and wd(out[-1] + c) <= maxw: out[-1] += c
        else: out.append(c)
    return out

def sub_at(d, units, t):
    """時刻 t（声が出てからの秒）に出す1文"""
    for a_, b_, sen in units:
        if t < b_ or (a_, b_, sen) == units[-1]:
            subtitle(d, sen, t - a_); return

def sub_rows(d, tx):
    """字幕の1枚を、字の大きさと行に分ける（subtitle と tools/b3d/subs_dump.py が使う）"""
    ft = font(46, 800); maxw = W - 2 * 90
    rows = [tx]
    while d.textlength(tx, font=ft) > maxw and ft.size > SUB_MIN: ft = font(ft.size - 2, 800)      # まず字を小さくして1行に
    if d.textlength(tx, font=ft) > maxw:      # 2行に分けるときは、真ん中にいちばん近い「、」「。」の後ろで切る（字の途中で折ると読みにくい）
        cuts = ([k + 1 for k, ch in enumerate(tx[:-1]) if ch in "、。"]
                or [k + 1 for k, ch in enumerate(tx[:-1]) if ch in "にをはがで" and tx[k + 1] not in "、。"]      # 「、」が無い文は助詞の後ろで（「ボ／ーナス」と語の途中で折れた。2026-11-18）
                or [len(tx) // 2])
        c = min(cuts, key=lambda k: abs(k - len(tx) / 2)); rows = [tx[:c], tx[c:]]
        if max(d.textlength(r_, font=ft) for r_ in rows) > maxw:      # 2行に入らない長い文は、「、」「。」の所で3行に（喰い替えの説明で、はみ出した）
            best = None
            for c1 in cuts:
                for c2 in cuts:
                    if c2 <= c1: continue
                    rs = [tx[:c1], tx[c1:c2], tx[c2:]]; w_ = max(d.textlength(r_, font=ft) for r_ in rs)
                    if best is None or w_ < best[0]: best = (w_, rs)
            if best: rows = best[1]
        while max(d.textlength(r_, font=ft) for r_ in rows) > maxw and ft.size > 34: ft = font(ft.size - 2, 800)
    return rows, ft


def subtitle(d, tx, k):
    """声の字幕（画面の下3分の1）。暗い四角い帯に白い字・2行まで"""
    a = int(235 * min(1, k * 6)); rows, ft = sub_rows(d, tx)
    # 暗い帯に白い字（前と同じ色・同じ透け方）。角だけ丸めない（2026-11-13 ユーザーの指定「変えるのは角丸を四角角にするだけ」。白いカードにしたのは行きすぎだった）
    # 帯の縦幅は、読みがあっても無くても同じ（2026-11-24 ユーザーの指定「読みがあるときだけ上が広すぎる」）。読みは帯の上の余白に入れる。
    # 2行で2行目に読みがあるときだけ、行の間を読みの分あける
    hr2 = len(rows) > 1 and any(r for p, r, t in ruby_parts(rows[1])); LH = 82 if hr2 else 64
    PAD = 34      # 帯の上下の余白（23 → 34。2026-11-24 ユーザーの指定「上と下を少しだけ広げる」）
    h = 2 * PAD + 64 + LH * (len(rows) - 1); y = 1560 - h // 2
    d.rectangle((50, y, W - 50, y + h), fill=(12, 20, 22, int(a * .86)))
    for n, r_ in enumerate(rows): ruby_c(d, W / 2, y + PAD + 32 + n * LH, r_, ft, (255, 255, 255, a), 24)


def draw_count(d, ps, t, t0, dt, nmax=None, chip=True):
    """牌の上に「1・2・3…」の丸を順に出す（ps＝牌の場所 [x, 上のふち] の並び・t0 から dt 秒おきに1つずつ）。
    数え終わったら「N枚」の札。14枚目はチカチカ（2026-11-26 ユーザーの指定）"""
    ps = ps[:nmax] if nmax else ps
    for k, (x, y) in enumerate(ps):
        a = (t - t0 - k * dt) / .12
        if a <= 0: break
        a = min(1, a); r = 24; cy = y - 34 - int((1 - a) * 14)
        blink = k == 13 and int((t - t0) * 6) % 2 == 0
        col = (255, 200, 40) if blink else (231, 86, 32)
        d.ellipse((x - r, cy - r, x + r, cy + r), fill=col + (int(255 * a),), outline=(255, 255, 255, int(255 * a)), width=4)
        text_c(d, x, cy - 1, str(k + 1), font(30), (255, 255, 255, int(255 * a)))
    if chip and ps and t >= t0 + len(ps) * dt:
        k = min(1, (t - t0 - len(ps) * dt) / .25); s_ = _ease_pop(k); x, y = ps[-1]
        lab = f"{len(ps)}枚"; f_ = font(int(60 * s_), 900); w_ = d.textlength(lab, font=f_) + 50
        cx = min(max(sum(p[0] for p in ps) / len(ps), w_ / 2 + 30), W - w_ / 2 - 30); cy = min(p[1] for p in ps) - 130
        d.rounded_rectangle((cx - w_ / 2, cy - 48 * s_, cx + w_ / 2, cy + 48 * s_), radius=40, fill=(255, 200, 40) if len(ps) == 14 else (23, 112, 131), outline=(255, 255, 255), width=5)
        text_c(d, cx, cy - 3, lab, f_, (31, 42, 40) if len(ps) == 14 else (255, 255, 255))

def order_ring(im, t, od):
    """手牌を倒す順の矢印（2026-11-28 ユーザーの指定）: 画面の9時（東家）→6時（南家）→3時（西家）→12時（北家）へ、反時計回りの円の矢印。
    t＝出してからの秒。番号つきの札が順に出て、矢印がのびる"""
    import math as _m
    cx, cy, rx, ry = od["c"]; k = max(0.0, min(1.0, t / 1.4)); Q = 3
    lay = Image.new("RGBA", (W * Q, H * Q), (0, 0, 0, 0)); dl = ImageDraw.Draw(lay); col = (231, 86, 32); gap = 24
    for i, (a0, a1) in enumerate([(180, 90), (90, 0), (0, -90)]):
        f = max(0.0, min(1.0, k * 3 - i))
        if f <= 0: break
        st = a0 - gap; en = st - (a0 - a1 - 2 * gap) * f
        pts = [(cx + rx * _m.cos(_m.radians(a)), cy + ry * _m.sin(_m.radians(a))) for a in [st + (en - st) * j / 40 for j in range(41)]]
        P = [(x * Q, y * Q) for x, y in pts]
        dl.line(P, fill=(255, 255, 255, 255), width=26 * Q, joint="curve"); dl.line(P, fill=col + (255,), width=14 * Q, joint="curve")
        if f > .15:
            (x1, y1), (x2, y2) = pts[-2], pts[-1]; an = _m.atan2(y2 - y1, x2 - x1); L = 46; Wd = 30
            tip = (x2 + _m.cos(an) * L * .55, y2 + _m.sin(an) * L * .55)
            b1 = (x2 - _m.cos(an) * L * .45 + _m.cos(an + _m.pi / 2) * Wd, y2 - _m.sin(an) * L * .45 + _m.sin(an + _m.pi / 2) * Wd)
            b2 = (x2 - _m.cos(an) * L * .45 - _m.cos(an + _m.pi / 2) * Wd, y2 - _m.sin(an) * L * .45 - _m.sin(an + _m.pi / 2) * Wd)
            tri = [(q[0] * Q, q[1] * Q) for q in (tip, b1, b2)]
            dl.polygon(tri, fill=(255, 255, 255, 255)); dl.line(tri + [tri[0]], fill=(255, 255, 255, 255), width=12 * Q); dl.polygon(tri, fill=col + (255,))
    lay = lay.resize((W, H), Image.LANCZOS); im.alpha_composite(lay)
    d = ImageDraw.Draw(im)
    for i, (ang, tx) in enumerate(zip((180, 90, 0, 270), od["labels"])):
        a = max(0.0, min(1.0, (k * 3 + .35 - i) / .35))
        if a <= 0: break
        s_ = _ease_pop(a); x = cx + rx * _m.cos(_m.radians(ang)); y = cy + ry * _m.sin(_m.radians(ang))
        ft = font(int(38 * s_)); r = 27 * s_; w = d.textlength(tx, font=ft); Wp = 2 * r + 10 * s_ + w + 22 * s_; Hp = 64 * s_; x0 = x - Wp / 2; y0 = y - Hp / 2
        d.rounded_rectangle((x0 - 5, y0 - 5, x0 + Wp + 5, y0 + Hp + 5), radius=Hp / 2 + 5, fill=(255, 255, 255, 255))
        d.rounded_rectangle((x0, y0, x0 + Wp, y0 + Hp), radius=Hp / 2, fill=(23, 112, 131, 255))
        d.ellipse((x0 + 5 * s_, y0 + 5 * s_, x0 + 5 * s_ + 2 * r, y0 + 5 * s_ + 2 * r), fill=col + (255,))
        text_c(d, x0 + 5 * s_ + r, y0 + 5 * s_ + r, str(i + 1), font(int(36 * s_)), WHITE)
        text_c(d, x0 + 2 * r + 16 * s_ + w / 2, y0 + Hp / 2, tx, ft, WHITE)

def next_dora(c):
    """表示牌 → ドラ（数牌は次の数・9の次は1。風は東南西北・三元は白發中の順に回る）"""
    if c[0] == "z":
        n = int(c[1]); return "z" + str((n % 4) + 1 if n <= 4 else ((n - 5 + 1) % 3) + 5)
    return c[0] + str(int(c[1]) % 9 + 1)

def blink_mark(d, b, t, tx="横向き"):
    """鳴いた牌（横向き）を点滅させる（2026-11-28 ユーザーの指定「文面だけだとわかりにくい。もらった牌を点滅させたり、囲った丸を点滅させたり」）。
    牌に明るい色を重ねて点滅＋輪も点滅、上に札（札は点滅させない）"""
    import math as _m
    if t < 0: return
    k = min(1, t / .3); s_ = _ease_pop(k); bl = .5 + .5 * _m.cos(2 * _m.pi * 1.6 * t)      # 1秒に1.6回
    pad, lw = _ring_pad(b); pad += 4; col = (231, 86, 32)
    x0, y0, x1, y1 = b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad
    d.rounded_rectangle((b[0], b[1], b[2], b[3]), radius=8, fill=(255, 200, 90, int(120 * bl * k)))
    d.rounded_rectangle((x0, y0, x1, y1), radius=pad + 8, outline=(255, 255, 255, int(255 * (.35 + .65 * bl) * k)), width=lw + 6)
    d.rounded_rectangle((x0, y0, x1, y1), radius=pad + 8, outline=col + (int(255 * (.35 + .65 * bl) * k),), width=lw + 2)
    ft = font(int(36 * s_)); w = d.textlength(tx, font=ft) + 40 * s_; h = 62 * s_; cx = (x0 + x1) / 2; yb = y0 - 18
    d.rounded_rectangle((cx - w / 2, yb - h, cx + w / 2, yb), radius=h / 2, fill=col + (255,), outline=(255, 255, 255, 255), width=4)
    text_c(d, cx, yb - h / 2, tx, ft, WHITE)
    d.polygon([(cx - 13, yb - 2), (cx + 13, yb - 2), (cx, yb + 15)], fill=col + (255,))

def kandora_marks(d, bx, t_new, now, labels=("元ドラ", "新ドラ"), t_old=0.0):
    """④カンドラ: 牌の上に「元ドラ表示牌」「新ドラ表示牌」の札（6枚切りの数字と同じ見せ方。2026-11-28 ユーザーの指定）"""
    for key, tx, col, t0 in (("dora", labels[0], (23, 112, 131), t_old), ("kandora", labels[1], (231, 86, 32), t_new)):
        b = bx.get(key)
        if not b or now < t0: continue
        k = min(1, (now - t0) / .3); s_ = _ease_pop(k); x = (b[0] + b[2]) / 2; y = b[1] - 16
        ft = font(int(34 * s_)); w = d.textlength(tx, font=ft) + 34 * s_; h = 58 * s_
        lx = x
        if bx.get("kandora") and now >= t_new:      # 2つ並ぶときは、札を左右に開く（となり同士の牌なので、真上だと重なる）。矢じりは牌の真上のまま
            other = bx["kandora"] if key == "dora" else bx["dora"]; sd = -1 if x < (other[0] + other[2]) / 2 else 1
            lx = x + sd * (w / 2 - 20)
        d.rounded_rectangle((lx - w / 2, y - h, lx + w / 2, y), radius=h / 2, fill=col + (255,), outline=(255, 255, 255, 255), width=4)
        text_c(d, lx, y - h / 2, tx, ft, WHITE)
        d.polygon([(x - 12, y - 2), (x + 12, y - 2), (x, y + 14)], fill=col + (255,))

def sfx_events(sc, name, seq, fps, bub_at={}, subs_={}):
    """効果音を鳴らす時刻（秒）と音。画面の出来事（手順・吹き出し・カード）と、牌の当たる瞬間（sfx.TILE_EVENTS）"""
    import sfx
    ev = []; first = {}
    for n, (f, i, t, held) in enumerate(seq):
        sec = n / fps
        if n == 0 or i != seq[n - 1][1]:          # 場面が変わった瞬間
            # 画面の出来事で鳴らすのは、発声の吹き出しと、手順の切りかえ（2026-11-24 ユーザーの指定で足した。琴の「ポロン」）。箇条書き・まとめでは鳴らさない
            if i >= 0 and sc["steps"][i][7]: ev.append((sec + bub_at.get(f"step{i + 1}", .25), "pop"))
            if i >= 0: ev.append((sec, "kstep"))
            if i == 0 and isinstance(f, str) and os.path.basename(f).startswith("d"): ev.append((sec + 1.3, "clack"))      # 他家の打牌（scene.py の DISC_T）
            if i == -4:       # 前置き: 鳴くのに使う手牌が動いた瞬間と、他家がその牌を切った瞬間に「ポンッ」（sfx.PRE_EVENTS）
                am = sc["pre"].get("amap")
                for t_, snd in sfx.PRE_EVENTS.get(name, []): ev.append((sec + (next((k / fps for k, x in enumerate(am) if x >= t_), t_) if am else t_), snd))
                for (k_, a_, cd, nmx), ct_ in zip(sc["pre"].get("counts", []), sc["pre"].get("cts", [])):      # 数える丸が出るたびに小さな音
                    ev += [(sec + ct_ + k * cd, "tick") for k in range(nmx)]
            if i >= 0 and sc.get("cards", {}).get(i) == "bappu2" and f"step{i + 1}" in subs_:      # 例が切りかわるたびに「ポン」
                ev += [(sec + p[0], "pop") for p in bappu_phases(subs_[f"step{i + 1}"])]
            yk_ = sc.get("yaku", {}).get(i)
            if i >= 0 and yk_ and f"step{i + 1}" in subs_:      # 役が出るたびに「ポン」・点数で「チャイム」
                for w_, l_, h_ in yk_["items"]:
                    a_ = say_at(subs_[f"step{i + 1}"], w_)
                    if a_ is not None: ev.append((sec + .25 + a_, "pop"))
                for key_, snd_ in (("fu", "pop"), ("pts", "chime")):
                    a_ = say_at(subs_[f"step{i + 1}"], yk_[key_][0])
                    if a_ is not None: ev.append((sec + .25 + a_, snd_))
            kk_ = sc.get("kuikae")
            if i >= 0 and kk_ and kk_["step"] == i and f"step{i + 1}" in subs_:      # 喰い替えの牌がぽこんと出るたびに
                for c_, l_, wd_ in kk_["ng"]:
                    w_ = say_at(subs_[f"step{i + 1}"], wd_)
                    if w_ is not None: ev.append((sec + .25 + w_, "pop"))
            if i >= 0 and i in sc.get("counts", {}):
                _, c0, cd = sc["counts"][i]; ev += [(sec + c0 + k * cd, "tick") for k in range(6)]
        if i >= 0 and not held and not isinstance(f, str): first.setdefault(f, sec)
    for t, snd in sfx.TILE_EVENTS.get(name, []):
        fr = sfx.frame_of(name, t, fps)
        if fr in first: ev.append((first[fr], snd))
    return ev


def say_end(subs, word):
    """言葉 word を言い終える時刻（声が出てからの秒）"""
    for t0, t1, sen in subs:
        if word in sen: return t0 + (t1 - t0) * (sen.index(word) + len(word)) / max(1, len(sen))
    return None


def say_at(subs, word):
    """字幕の文の並び (出す, 消す, 文) から、言葉 word を言い始める時刻（声が出てからの秒）。文の中の位置は字の数で割りふる"""
    for t0, t1, sen in subs:
        if word in sen: return t0 + (t1 - t0) * sen.index(word) / max(1, len(sen))
    return None


def tile_img(code, w, h):
    """牌の表の絵（scene.py と同じ make_tile_tex.py の絵）"""
    k = (code, w, h)
    if k not in _tiles:
        if not os.path.isdir(TEX[0]):
            TEX[0] = tempfile.mkdtemp(); subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "make_tile_tex.py"), TEX[0]], check=True)
        _tiles[k] = Image.open(os.path.join(TEX[0], code + ".png")).convert("RGBA").resize((w, h), Image.LANCZOS)
    return _tiles[k]
_tiles = {}; TEX = [""]


FU_HAND = ["m2", "m3", "m4", "m8", "m8", "p5", "p6", "p7", "s2", "s3", "s4", "s5", "s6"]      # フリテンの3本の手牌（scene.py と同じ）
def hand_strip(d, name, a=1.0):
    """自分の手牌を牌の絵で、字幕の上に帯で出す（2026-11-25 ユーザーの指定「手牌と自分の河を両方見せる」。卓は上から映すので、立てた手牌の表は見えない）。
    待ちを作る5枚（二〜六索）は緑の下線、右に「待ち」と一索・四索・七索"""
    hand = FU_HAND[3:] if name == "furiten2" else FU_HAND; meld = ["m2", "m3", "m4"] if name == "furiten2" else []
    TH = 84; ims = [_tile_img(c, TH) for c in hand]; tw = ims[0].width
    mw = sum(_tile_img(c, TH).width + 2 for c in meld) + (TH - tw if meld else 0) + (16 if meld else 0)
    ww = len(ims) * (tw + 2) + mw; x0 = (W - ww) / 2; y0 = 1362; A = lambda v: int(v * a)
    d.rounded_rectangle((x0 - 22, y0 - 54, x0 + ww + 22, y0 + TH + 18), radius=24, fill=(12, 20, 22, A(200)))
    d.text((x0 - 4, y0 - 48), "自分の手牌", font=font(30, 800), fill=(140, 220, 230, A(255)))
    wt = [_tile_img(c, 40) for c in ("s1", "s4", "s7")]; wx = x0 + ww - sum(i.width + 4 for i in wt)
    d.text((wx - 70, y0 - 48), "待ち", font=font(30, 800), fill=(140, 220, 230, A(255)))
    x = x0
    for k, im in enumerate(ims):
        if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        d._image.alpha_composite(im, (int(x), int(y0)))
        if k >= len(ims) - 5: d.rectangle((x, y0 + TH + 4, x + tw, y0 + TH + 10), fill=(120, 210, 225, A(255)))
        x += tw + 2
    if meld:
        x += 16
        for k, c in enumerate(meld):
            im = _tile_img(c, TH)
            if k == 0: im = im.rotate(90, expand=True)
            if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            d._image.alpha_composite(im, (int(x), int(y0 + TH - im.height))); x += im.width + 2
    for im in wt:
        d._image.alpha_composite(im, (int(wx), int(y0 - 48))); wx += im.width + 4


def x_badge(d, t, tx="ロンできない"):
    """「ロンできない」の大きな×（前置きのカードの上）"""
    a = min(1, t * 5); sc_ = .7 + .3 * min(1, t * 5); cx, cy, r = W / 2, 300, int(120 * sc_)      # 画面の上（卓や札にかからない）
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(255, 255, 255, int(235 * a)), outline=(201, 47, 66, int(255 * a)), width=12)
    for sg in (1, -1): d.line((cx - r * .55, cy - r * .55 * sg, cx + r * .55, cy + r * .55 * sg), fill=(201, 47, 66, int(255 * a)), width=26)
    tw = d.textlength(tx, font=font(48)) + 60
    d.rounded_rectangle((cx - tw / 2, cy + r + 18, cx + tw / 2, cy + r + 86), radius=34, fill=(201, 47, 66, int(255 * a)))      # かんたんな説明（2026-11-26 ユーザーの指定）
    text_c(d, cx, cy + r + 50, tx, font(48), (255, 255, 255, int(255 * a)))


PTS_RON = {20: [None, None, None, None], 30: ["1000", "2000", "3900", "7700"], 40: ["1300", "2600", "5200", "8000"], 50: ["1600", "3200", "6400", "8000"], 60: ["2000", "3900", "7700", "8000"]}
PTS_TSUMO = {20: [None, "400・700", "700・1300", "1300・2600"], 30: ["300・500", "500・1000", "1000・2000", "2000・3900"], 40: ["400・700", "700・1300", "1300・2600", "2000・4000"],
             50: ["400・800", "800・1600", "1600・3200", "2000・4000"], 60: ["500・1000", "1000・2000", "2000・3900", "2000・4000"]}      # 子のアガリ（0本場）。ツモは「子の払い・親の払い」
def yaku_board(d, t, yk, subs):
    """申告（2026-11-26 ユーザーの指定）: 声に合わせて役が1つずつ出て翻が増える → 「3翻30符」→ 子の点数表（1〜4翻・20〜60符）で
    3翻30符のマスを光らせ、点数が出る。発声の吹き出しが出たら消す（make_clip.py が呼ばない）"""
    import math as _m
    x0, y0 = 46, 660; ph = []
    for w, lab, han in yk["items"]:
        ws = say_at(subs, w)
        if ws is not None: ph.append((.25 + ws, lab, han))
    if not ph or t < ph[0][0]: return
    a0 = min(1, (t - ph[0][0]) * 4)
    tot = sum(h for t_, l, h in ph if t >= t_); last = max(t_ for t_, l, h in ph if t >= t_)
    PW = 520; PH = 104 + 86 * len(ph)
    d.rounded_rectangle((x0, y0, x0 + PW, y0 + PH), radius=34, fill=(12, 20, 22, int(210 * a0)))
    d.text((x0 + 30, y0 + 22), "役", font=font(44, 900), fill=(255, 255, 255, int(255 * a0)))
    k = min(1, (t - last) / .35); s_ = _ease_pop(k) * (1.2 - .2 * k)      # 翻の数（増えるたびに、ぽこんと大きく）。板の中に収める
    r = 38 * s_; cx, cy = x0 + PW - 64, y0 + 54
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(231, 86, 32, 255), outline=(255, 255, 255, 255), width=4)
    text_c(d, cx, cy - 3, f"{tot}翻", font(int(32 * s_), 900), (255, 255, 255, 255))
    for n, (t_, lab, han) in enumerate(ph):
        if t < t_: break
        k = min(1, (t - t_) / .3); yy = y0 + 104 + n * 86; xx = x0 + 26 - (1 - k) * 80; a = int(255 * k)
        d.rounded_rectangle((xx, yy, xx + 330, yy + 70), radius=35, fill=(255, 255, 255, a))
        text_c(d, xx + 165, yy + 33, lab, font(38, 900), (23, 112, 131, a))
        d.rounded_rectangle((xx + 346, yy + 8, xx + 446, yy + 62), radius=27, fill=(231, 86, 32, a))
        text_c(d, xx + 396, yy + 33, f"+{han}翻", font(30, 900), (255, 255, 255, a))
    # 「3翻30符」→ 点数表
    wf = say_at(subs, yk["fu"][0])
    if wf is None or t < .25 + wf: return
    kf = min(1, (t - .25 - wf) / .3)
    fu = int(yk["fu"][1].replace("符", "")); tsumo = "・" in yk["pts"][1]; TB = PTS_TSUMO if tsumo else PTS_RON
    cx_, cy_ = x0 + PW + 24, y0 + 30      # 板の右に「3翻 30符」
    lab_ = f"{tot}翻 {fu}符"; lw = d.textlength(lab_, font=font(44, 900)) + 50
    d.rounded_rectangle((cx_, cy_, cx_ + lw, cy_ + 76), radius=38, fill=(255, 255, 255, int(255 * kf)), outline=(231, 86, 32, int(255 * kf)), width=6)
    text_c(d, cx_ + lw / 2, cy_ + 36, lab_, font(44, 900), (231, 86, 32, int(255 * kf)))
    ty = y0 + PH + 24; tx0 = 46; CW0 = 120; CW = (W - 92 - CW0) / 4; RH = 62
    TT_ = 50      # 表の題の行
    d.rounded_rectangle((tx0, ty, W - 46, ty + TT_ + RH * 6 + 16), radius=28, fill=(255, 255, 255, int(240 * kf)))
    hdr = "子のツモ（子・親の払い）" if tsumo else "子のロン"
    d.text((tx0 + 20, ty + 12), hdr, font=font(30, 900), fill=(23, 112, 131, int(255 * kf)))
    ty += TT_
    for c in range(4): text_c(d, tx0 + CW0 + CW * (c + .5), ty + 16 + RH * .5, f"{c + 1}翻", font(32, 900), (23, 112, 131, int(255 * kf)))
    wp = say_at(subs, yk["pts"][0]); hot = wp is not None and t >= .25 + wp
    for rI, f_ in enumerate((20, 30, 40, 50, 60)):
        yy = ty + 16 + RH * (rI + 1)
        text_c(d, tx0 + CW0 / 2, yy + RH / 2, f"{f_}符", font(32, 900), (23, 112, 131, int(255 * kf)))
        for c in range(4):
            v = TB[f_][c]; xx = tx0 + CW0 + CW * c
            on = (f_ == fu and c + 1 == tot)
            if on and hot:      # 3翻30符のマスを光らせる
                pk = .5 + .5 * _m.sin((t - .25 - wp) * 10)
                d.rounded_rectangle((xx + 4, yy + 4, xx + CW - 4, yy + RH - 4), radius=16, fill=(231, 86, 32, int(255 * kf)), outline=(255, 210, 120, int(255 * pk)), width=6)
            elif (f_ == fu or c + 1 == tot) and kf >= 1:      # 行と列をうすく
                d.rectangle((xx + 4, yy + 4, xx + CW - 4, yy + RH - 4), fill=(255, 236, 222, 255))
            text_c(d, xx + CW / 2, yy + RH / 2, v or "—", font(26 if tsumo else 32, 900), (255, 255, 255, 255) if on and hot else (40, 50, 50, int(255 * kf)))

def dora_card(d, t, dc):
    """表示牌 → ドラ を見せる図（2026-11-26 ユーザーの指定「表示牌→表ドラ、表示牌→裏ドラが目で見てわかるように」）。行ごとに、ぽこんと出る"""
    a = min(1, t * 4); y0 = dc.get("y", 650); h = 360; A = lambda v: int(v * a)
    d.rounded_rectangle((60, y0, W - 60, y0 + h), radius=40, fill=(12, 20, 22, A(205)), outline=(231, 86, 32, A(255)), width=6)
    th = 112
    for n, (lab, ind, dora, col) in enumerate(dc["rows"]):
        k = (t - n * .6) / .3
        if k <= 0: continue
        k = min(1, k); s_ = _ease_pop(k); yy = y0 + 40 + n * 160
        text_c(d, 175, yy + th / 2, lab, font(40, 900), col + (int(255 * k),))
        im = _tile_img(ind, int(th * s_)); d._image.alpha_composite(im, (300, int(yy + (th - im.height) / 2)))
        text_c(d, 300 + im.width / 2, yy + th + 18, "表示牌", font(26, 800), (220, 230, 230, int(255 * k)))
        ax = 300 + im.width + 30
        d.line((ax, yy + th / 2, ax + 120, yy + th / 2), fill=col + (int(255 * k),), width=10)
        d.polygon([(ax + 140, yy + th / 2), (ax + 112, yy + th / 2 - 20), (ax + 112, yy + th / 2 + 20)], fill=col + (int(255 * k),))
        im2 = _tile_img(dora, int(th * s_)); d._image.alpha_composite(im2, (int(ax + 170), int(yy + (th - im2.height) / 2)))
        text_c(d, ax + 170 + im2.width / 2, yy + th + 18, "ドラ", font(26, 800), col + (int(255 * k),))


def kuikae_card(d, kk, t, subs):
    """喰い替えの具体例（2026-11-25 ユーザーの指定）。「鳴いた牌と…」と話し始めたらカード（鳴いた形）→ 声に合わせて、切れない牌が1枚ずつ、ぽこんと出る"""
    a = min(1, t * 4); A = lambda v: int(v * a); y = kk.get("y", max(650, TOPY[0])) + int((1 - a) * 24); h = 540      # 鳴いた牌と重ならない高さ（動画ごとに y。チーは鳴いた牌が画面の上なので下へ）
    d.rounded_rectangle((60, y, W - 60, y + h), radius=44, fill=(12, 20, 22, A(200)), outline=(231, 86, 32, A(255)), width=6)
    d.rounded_rectangle((W / 2 - 190, y + 34, W / 2 + 190, y + 98), radius=32, fill=(231, 86, 32, A(255)))      # 見出しはカードの中（ルビがカードの外に出ていた。2026-11-26 ユーザーの指摘）
    ruby_c(d, W / 2, y + 68, "{喰い替え|くいかえ}の例", font(40, 800), (255, 255, 255, A(255)), 22)
    th = 118
    text_c(d, 200, y + 175, "鳴いた形", font(38, 800), (140, 220, 230, A(255)))
    x = 330
    for n, c in enumerate(kk["meld"]):
        im = _tile_img(c, th)
        if n == kk.get("side"): im = im.rotate(90, expand=True)
        if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        d._image.alpha_composite(im, (int(x), int(y + 115 + (th - im.size[1])))); x += im.size[0] + 8
    d.line((110, y + 268, W - 110, y + 268), fill=(255, 255, 255, A(60)), width=3)
    text_c(d, 200, y + 395, "切れない", font(38, 800), (255, 120, 120, A(255)))
    x = 330
    for c, lab, wd in kk["ng"]:
        ws = say_at(subs, wd)
        k = 1.0 if ws is None else (t + kk["_t0"] - (.25 + ws)) / .3
        if k <= 0: continue
        s_ = _ease_pop(min(1, k)); im = _tile_img(c, int(th * s_))
        yy = y + 315 + (th - im.height) / 2; d._image.alpha_composite(im, (int(x + (int(th * .75) - im.width) / 2), int(yy)))
        cx, cy = x + th * .375, y + 315 + th / 2
        if k > .6:      # 牌の右上に、赤い丸の×（牌の絵は隠さない）
            bx, by, r = x + th * .75 - 6, y + 315 + 4, 26
            d.ellipse((bx - r - 4, by - r - 4, bx + r + 4, by + r + 4), fill=(255, 255, 255, 255)); d.ellipse((bx - r, by - r, bx + r, by + r), fill=(201, 47, 66, 255))
            for sg in (1, -1): d.line((bx - 11, by - 11 * sg, bx + 11, by + 11 * sg), fill=(255, 255, 255, 255), width=7)
        text_c(d, cx, y + 315 + th + 36, lab, font(32, 800), (235, 240, 240, 255))
        x += max(int(th * .75), int(d.textlength(lab, font=font(32, 800)))) + 70


def scaled(sc, fps):
    """台本のコマの番号（1秒12コマ）→ 書き出したコマの番号。手順の終わりの時刻はそのまま、次の手順はその次のコマから"""
    k = fps / 12
    if fps == 12: return sc
    end = lambda n: int(round(n * k)); beg = lambda n: end(n - 1) + 1 if n else 0
    st = [s[:3] + (end(s[3]) if s[3] == s[4] else beg(s[3]), end(s[4])) + s[5:] for s in sc["steps"]]
    sb = {i: [(end(f), w) for f, w in v] for i, v in sc.get("sbeats", {}).items()}
    return dict(sc, steps=st, tail=(beg(sc["tail"][0]), end(sc["tail"][1]), sc["tail"][2]), sbeats=sb)


BUB_GAP = .7      # 吹き出しが出てから次のセリフまでの間（秒）。86BPMの1拍（2026-11-24 ユーザーの指定「一拍あける」）


def main():
    a = sys.argv[1:]
    fpt = os.path.join(a[0], "fps.txt"); fps = int(a[a.index("--fps") + 1]) if "--fps" in a else int(open(fpt).read()) if os.path.exists(fpt) else 12
    mkp = os.path.join(a[0], "marks.json"); MK = json.load(open(mkp)) if os.path.exists(mkp) else []      # 囲む牌の場所（scene.py が作る）
    cp_ = os.path.join(a[0], "count.json"); CNT = json.load(open(cp_)) if os.path.exists(cp_) else []      # 数える丸の場所（ツモと打牌）
    pp_ = os.path.join(a[0], "pcount.json"); PCNT = json.load(open(pp_)) if os.path.exists(pp_) else []
    pm_ = os.path.join(a[0], "pmarks.json"); PMK = json.load(open(pm_)) if os.path.exists(pm_) else []
    dm_ = os.path.join(a[0], "dmarks.json"); DMK = json.load(open(dm_)) if os.path.exists(dm_) else []
    ck_ = os.path.join(a[0], "callmk.json"); CMK = json.load(open(ck_)) if os.path.exists(ck_) else None      # 鳴いた牌（横向き）の場所
    dk_ = os.path.join(a[0], "doramk.json"); DRK = json.load(open(dk_)) if os.path.exists(dk_) else None      # カンの元ドラ・新ドラの場所      # ①の前の絵（他家が切る・自分がツモる）で囲む牌
    name = a[a.index("--script") + 1] if "--script" in a else "chi"
    sc = scaled(SCRIPTS[name], fps)
    BUB_POS.update(sc.get("bubpos", {}))      # 動画ごとの吹き出しの場所（同巡内フリテンの「ロン」は上からの画角）
    # 声（2026-11-13〜）: --voice を付けると、narration.py の台本を VOICEVOX で読ませて入れる。手順ごとの止める長さは、声が言い終わるまでのばす
    VO = {}; BUB_AT = {}; SUBS = {}; PRE_S = []      # PRE_S＝前置きの声の、文ごとの始まり（声が出てからの秒）     # BUB_AT＝手順ごとの、吹き出しを出す時刻（その手順が出てからの秒）・SUBS＝字幕の1文ずつの (出す, 消す, 文)
    if "--voice" in a:
        import wave, narration
        vtmp = tempfile.mkdtemp(); first_ruby(name)
        for seg, tx in narration.lines(name):
            wp = os.path.join(vtmp, seg + ".wav"); narration.synth(tx, wp)
            with wave.open(wp) as wf: VO[seg] = (wp, wf.getnframes() / wf.getframerate(), tx, wf.getframerate())
            key = next((k_ for k_ in ("声に出します。", "申告します。") if k_ in tx), None)
            gap_at = None
            if seg.startswith("step") and key:     # 吹き出しは「〇〇と声に出します。」「〇〇と申告します。」を言い終わってから（2026-11-14 ユーザーの指定・全部の動画の決まり）
                wb = os.path.join(vtmp, seg + "_b.wav"); narration.synth(tx[:tx.index(key) + len(key)], wb)
                with wave.open(wb) as wf: BUB_AT[seg] = .25 + wf.getnframes() / wf.getframerate() + .05
                rest = tx[tx.index(key) + len(key):].strip()
                if rest:      # 吹き出しが出たら一拍おいてから次のセリフ（2026-11-24 ユーザーの指定）。前半の声＋無音 BUB_GAP 秒＋残りの声 に作り直す
                    wr = os.path.join(vtmp, seg + "_r.wav"); narration.synth(rest, wr)
                    with wave.open(wb) as a_, wave.open(wr) as b_:
                        sr_ = a_.getframerate(); pa, pb = a_.readframes(a_.getnframes()), b_.readframes(b_.getnframes())
                    gap_at = len(pa) / 2 / sr_
                    with wave.open(wp, "wb") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr_); wf.writeframes(pa + b"\0\0" * int(BUB_GAP * sr_) + pb)
                    VO[seg] = (wp, (len(pa) + len(pb)) / 2 / sr_ + BUB_GAP, tx, sr_)
            if seg == "pre":     # 前置きの文ごとの時刻（カードの行と絵を、声に合わせる。2026-11-25 ユーザーの指定「セリフと映像を合わせる」）
                import re as _re2; us = []
                for j, sen in enumerate([x for x in _re2.split("(?<=。)", tx) if x]):
                    wu = os.path.join(vtmp, f"pre_s{j}.wav"); narration.synth(sen, wu)
                    with wave.open(wu) as wf: us.append(wf.getnframes() / wf.getframerate())
                k_ = VO[seg][1] / max(1e-6, sum(us)); acc = 0.0; PRE_S.clear()
                for du in us: PRE_S.append(acc * k_); acc += du
            if seg.startswith("step") or seg == "tail":     # 字幕は1文ずつ出す（2026-11-16 ユーザーの指定）。文ごとに声の長さを測って、出す時刻を決める
                units = []
                for j, sen in enumerate(sub_units(tx)):
                    wu = os.path.join(vtmp, f"{seg}_u{j}.wav"); narration.synth(sen, wu)
                    with wave.open(wu) as wf: units.append((sen, wf.getnframes() / wf.getframerate()))
                spoken = VO[seg][1] - (BUB_GAP if gap_at is not None else 0)
                sc_ = spoken / max(1e-6, sum(u[1] for u in units)); t_ = 0.0; SUBS[seg] = []
                for sen, du in units:
                    if gap_at is not None and t_ >= gap_at - .15: t_ += BUB_GAP; gap_at = None      # 一拍の間のぶん、後ろの字幕をずらす
                    SUBS[seg].append((t_, t_ + du * sc_, sen)); t_ += du * sc_
    for i_, w_ in SCRIPTS[name].get("bubw", {}).items():      # 吹き出しを、その言葉を言い終えた時に（フリテンの「ツモ」）
        e_ = say_end(SUBS.get(f"step{i_ + 1}", []), w_)
        if e_ is not None: BUB_AT[f"step{i_ + 1}"] = .25 + e_
    need = lambda seg, pad=.35: (VO[seg][1] + pad) if seg in VO else 0.0
    starts = {}      # 声を鳴らし始める時刻（秒）
    src, out = a[0], a[1]; TEX[0] = os.path.join(os.path.dirname(os.path.abspath(src)), "tex")
    frames = sorted(glob.glob(os.path.join(src, "f[0-9]*.png")))
    assert frames, "コマが無い: " + src
    intro = sorted(glob.glob(os.path.join(src, "i[0-9]*.png")))
    disc = sorted(glob.glob(os.path.join(src, "d[0-9]*.png")))
    if disc and sc["steps"][0][7]:      # ①の前の絵の上の吹き出し。他家が切る絵（自分の真後ろから）＝手牌の上・自分がツモる絵（右うしろから）＝自分の選手（左下）の頭の右
        BUB_POS[sc["steps"][0][7]] = ((420, 1230), (-140, 300)) if name in ("kan", "kakan", "riichi") else ((690, 1120), (90, 300))
    # 出すコマの並び: (元のコマ, 手順, その手順が出てからの秒, 止めているか)
    seq = []
    starts["intro"] = .5
    for n, fp in enumerate(intro + [intro[-1]] * max(0, int((need("intro") + .5) * fps) - len(intro)) if intro else []): seq.append((fp, -2, n / fps, False))
    pre = sorted(glob.glob(os.path.join(src, "p[0-9]*.png")))       # 前置き（scene.py --anim --pre）。手牌を映して、なぜ鳴けるかを見せる
    if pre and sc.get("pre"):
        starts["pre"] = len(seq) / fps + .6
        pc = sc["pre"]
        if PRE_S and pc.get("ls"):
            # カードの行は、その行の文が始まる時に出す（同じ文に2行あれば、少しずらす）。絵は beats（絵の時刻, 文）で、その文が始まるまで止めて待つ
            so = lambda j: .6 + PRE_S[min(j, len(PRE_S) - 1)]
            seen = {}; nl = []
            for ln, j in zip(pc["lines"], pc["ls"]):
                k = seen.get(j, 0); seen[j] = k + 1; nl.append((so(j) + .15 + .9 * k,) + tuple(ln[1:]))
            pc = dict(pc, lines=nl)
            if pc.get("note"): pc["note"] = (nl[-1][0] + .9,) + tuple(pc["note"][1:])
            if pc.get("xat"):      # 「どの待ちでもロンできません」と言うときに×
                import re as _re3; sens = [x for x in _re3.split("(?<=。)", VO["pre"][2]) if x]
                for j, sen in enumerate(sens):
                    if pc["xat"] in sen:
                        nx_ = PRE_S[j + 1] if j + 1 < len(PRE_S) else VO["pre"][1]
                        pc["x_t"] = .6 + PRE_S[j] + (nx_ - PRE_S[j]) * (sen.index(pc["xat"]) + len(pc["xat"])) / len(sen); break      # 言い終わってから×（2026-11-25 ユーザーの指定）
            if pc.get("count"): pc["count"] = (pc["count"][0], nl[pc.get("count_line", 2)][0] + .4, pc["count"][2])
            sc = dict(sc, pre=pc)
            beats = [(0.0, 0.0)] + [(a_, so(j)) for a_, j in pc.get("beats", [])]
            AD = len(pre) / fps; amap = []; total = max(beats[-1][1] + AD - beats[-1][0], .6 + VO["pre"][1] + .6, nl[-1][0] + pc["hold"])
            for n in range(int(total * fps)):
                u = n / fps; a_ = AD
                for (a0, o0), nxt in zip(beats, beats[1:] + [(AD, 1e9)]):
                    if u < nxt[1]: a_ = min(a0 + max(0, u - o0), nxt[0]); break
                seq.append((pre[min(len(pre) - 1, int(round(a_ * fps)))], -4, u, False)); amap.append(a_)
            sc["pre"]["amap"] = amap      # 出す時刻ごとの、前置きの絵の時刻（効果音を絵に合わせる）
            if pc.get("counts"): sc["pre"]["cts"] = [next((k / fps for k, x in enumerate(amap) if x >= c_[1] - 1e-6), 0.0) for c_ in pc["counts"]]
        else:
            for n, fp in enumerate(pre + [pre[-1]] * max(int(sc["pre"]["hold"] * fps), int((need("pre") + .6) * fps) - len(pre))): seq.append((fp, -4, n / fps, False))
    for i, s in enumerate(sc["steps"]):
        t = 0.0; starts[f"step{i + 1}"] = len(seq) / fps + .25
        # 発声と、①（流局など）の手順は、最初のコマで止めたまま見せる（2026-11-14 ユーザーの指定「①で画角が少しでも動くのはいらない。止めた絵で説明」）。
        # 次の手順は、止めたコマのすぐ後から動かす（止めた所から先のコマを飛ばすと、絵が飛ぶ）。ツモアガリの①ツモは、山から取る動きそのものなので止めない
        frozen = s[0] == "発声" or (i == 0 and s[0] != "ツモ")
        a0 = sc["steps"][i - 1][3] + 1 if i and (sc["steps"][i - 1][0] == "発声" or (i == 1 and sc["steps"][0][0] != "ツモ")) else s[3]
        fr = [s[3]] * (s[4] - s[3] + 1) if frozen else list(range(a0, s[4] + 1))
        hf = s[3] if frozen else s[4]
        if i == 0 and disc:
            fr = list(disc); hf = disc[-1]
            dh_ = sc.get("disc_hold")      # (止めるコマ, 秒)。「山から1枚」を長く見せる（リーチ。2026-11-28 ユーザーの指定）
            if dh_: fr = fr[:dh_[0] + 1] + [fr[dh_[0]]] * int(dh_[1] * fps) + fr[dh_[0] + 1:]      # 他家が切ってから発声する（scene.py --disc）。止めるのも、切った牌が河にある絵
        for bf, wd in sc.get("sbeats", {}).get(i, []):      # 声のその言葉が出るまで、コマ bf で止めて待つ（前から順に。前の止めの分も時刻に入る）
            ws = say_at(SUBS.get(f"step{i + 1}", []), wd)
            if ws is not None and bf in fr:
                k_ = fr.index(bf); fr = fr[:k_ + 1] + [bf] * max(0, int((.25 + ws - .1) * fps) - (k_ + 1)) + fr[k_ + 1:]
        for f in fr: seq.append((f, i, t, False)); t += 1 / fps
        nd = max(need(f"step{i + 1}") + .25, (BUB_AT.get(f"step{i + 1}", .25) + 1.8) if s[7] else 0)     # 吹き出しが出てから1.8秒は見せる（1秒では一瞬で消えて見えた）
        for _ in range(max(int(s[5] * fps), int(nd * fps) - len(fr))): seq.append((hf, i, t, True)); t += 1 / fps
    f0, f1, hold = sc["tail"]; t = 0.0; starts["tail"] = len(seq) / fps + .9
    for f in range(f0, f1 + 1): seq.append((f, -1, t, False)); t += 1 / fps
    for _ in range(max(int(hold * fps), int((need("tail") + .9) * fps) - (f1 - f0 + 1))): seq.append((f1, -1, t, True)); t += 1 / fps
    starts["outro"] = len(seq) / fps + 1.2
    outro = sorted(glob.glob(os.path.join(src, "o[0-9]*.png")))      # 締め（scene.py --anim --outro）。最後のコマで2秒止める
    odur = (len(outro) + 2 * fps) / fps
    for n, fp in enumerate(outro + [outro[-1]] * (2 * fps) if outro else []): seq.append((fp, -3, n / fps, False))
    HOLD_T = {}
    for f_, i_, t_, h_ in seq:
        if h_ and i_ >= 0: HOLD_T.setdefault(i_, t_)
    tmp = tempfile.mkdtemp(); cache = {}; fade = None; cache_prev = None; card_t0 = {}; hold_n = 0
    for n, (f, i, t, held) in enumerate(seq):
        if f not in cache:
            cache.clear(); cache[f] = Image.open(f if isinstance(f, str) else frames[min(f, len(frames) - 1)]).convert("RGBA").resize((W, H), Image.LANCZOS)
        im = cache[f].copy(); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        # 前置きの前後は、絵を重ねてつなぐ（カメラは選手の目に飛ぶので、動かすと体の中を通る）
        # ①へは重ねずに切りかえる（重ねると、カメラが少し動いたように見える。2026-11-14 ユーザーの指摘「①で画角が少し動く」）
        if n and i != seq[n - 1][1] and i == -4: fade = [cache_prev, 0]
        if fade and fade[1] < int(.5 * fps):      # 0.5秒かけて重ねる
            fade[1] += 1; u = fade[1] / (int(.5 * fps) + 1); im = Image.blend(fade[0], im, u * u * (3 - 2 * u))
        cache_prev = cache[f]
        CUR[0] = im      # 囲みの外を暗くする（draw_marks）ため、いまの絵
        if i == -4:
            pre_card(d, sc["pre"], t)
            MK_NUDGE.clear(); MK_NUDGE.update(sc["pre"].get("nudge", {}) if i == -4 else {})
            if sc["pre"].get("marks") and PMK:      # 使う手牌と、人が切った牌を囲む（2026-11-25 ユーザーの指定）
                pi = min(int(os.path.basename(f)[1:5]), len(PMK) - 1) if isinstance(f, str) else 0
                here_ = {k_: b_ for k_, b_ in PMK[pi].items() if b_[3] < 1240}      # カードの所（下）に入った牌は囲まない（カメラが動いて、カードに重なった）
                pl_ = sc["pre"].get("lines", [])      # 5つ目＝カードのその行が出てから
                mk_ = [(k_,) + tuple(v_[:4]) for k_, v_ in sc["pre"]["marks"].items() if len(v_) < 5 or (v_[4] < len(pl_) and t >= pl_[v_[4]][0])]
                draw_marks(d, mk_, here_, now=n / fps, key="pre")
            if sc["pre"].get("x_t") is not None and t >= sc["pre"]["x_t"]: x_badge(d, t - sc["pre"]["x_t"], sc["pre"].get("xtext", "ロンできない"))      # 札の上に重ねる
            if sc["pre"].get("counts") and PCNT and sc["pre"].get("cts"):      # いちばん新しく始まった数え（前置きの絵の時刻 → 出す時刻）
                pi = min(int(os.path.basename(f)[1:5]), len(PCNT) - 1) if isinstance(f, str) else 0
                cur_ = [(c_, ct_) for c_, ct_ in zip(sc["pre"]["counts"], sc["pre"]["cts"]) if t >= ct_]
                if cur_:
                    (key, a_, cd, nmx), ct_ = cur_[-1]
                    if len(PCNT[pi][key]) == nmx: draw_count(d, PCNT[pi][key], t, ct_, cd, nmx)      # 枚数が変わったら（14枚から1枚切ったら）、その数えは消す。次の数えは手を戻してから
        elif i == -3:
            outro_card(im, t, odur)
        elif i == -2:
            title_card(d, sc, t, sum(1 for q in seq if q[1] == -2) / fps)      # 入りの声が長いときも、入りが終わるまで題名を出し続ける（前は入りの絵の長さ4秒で消えた。2026-11-25 ユーザーの指摘）
        elif i >= 0:
            s = sc["steps"][i]
            if name in MARKS:
                assert MK, "marks.json が無い（scene.py を動かすと、コマと同じフォルダにできる）"
                xe = say_end(SUBS.get(f"step{i + 1}", []), "ロンできません")
                ms_ = []
                for m_ in MARKS[name][i]:      # 6つ目＝その言葉を言い始めてから出す
                    if len(m_) > 5:
                        w_ = say_at(SUBS.get(f"step{i + 1}", []), m_[5])
                        if w_ is not None and t < .25 + w_: continue
                        if i in sc.get("after_motion", ()) and t < HOLD_T.get(i, 0) + .15: continue
                    if i in sc.get("bub_hides", ()) and s[7] and t > BUB_AT.get(f"step{i + 1}", .25): continue      # 吹き出しが出たら印は消す
                    ms_.append(m_[:5])
                draw_marks(d, ms_, MK[min(f, len(MK) - 1)], xe is None or t >= .25 + xe, now=n / fps, key=f"s{i}")
            rail(d, sc["steps"], i); headline(d, i, s, t)
            if i == 0 and DMK and sc.get("clip") and isinstance(f, str) and os.path.basename(f).startswith("d") and not (sc.get("clip_hide_bub") and s[7] and t > BUB_AT.get("step1", .25)):      # 吹き出しが出たらツモ牌の印は消す（リーチ）      # 切られた牌・ツモった牌に印
                di = min(int(os.path.basename(f)[1:5]), len(DMK) - 1)
                draw_marks(d, [("tile",) + tuple(sc["clip"]), ("src", "orange", "山から1枚", [], "UR")], DMK[di], now=n / fps, key="clip")
            if name.startswith("furiten") and i < len(sc["steps"]) - 1 and i not in {"furiten2": (3,), "furiten3": (2,)}.get(name, ()): hand_strip(d, name)      # 卓の手牌を映す手順では、帯は出さない      # 最後の手順（ツモ・ロン）は卓の手牌を映すので、帯は消す
            bt = BUB_AT.get(f"step{i + 1}", .25)
            bd_ = sc.get("bubdur", {}).get(i)      # 吹き出しを出しておく秒（ほかの動画は手順が1.8秒ほどで終わって消える。同巡内フリテン⑤は手順が長いので、同じ長さで消す＝2026-11-28 ユーザーの指定）
            still_ = i in sc.get("bub_still", ()) and any(f_ > bf_ for bf_, w_ in sc.get("sbeats", {}).get(i, []) for f_ in [f] if not isinstance(f, str))      # 止めた絵から動き始めたら消す（画角が変わる＝2026-11-28 ユーザーの指定）
            if s[7] and t > bt and (bd_ is None or t < bt + bd_) and not still_: bubble(d, s[7], t - bt)
            if i in sc.get("counts", {}) and CNT:
                key, c0, cd = sc["counts"][i]; draw_count(d, CNT[min(f, len(CNT) - 1)][key], t, c0, cd, 6, chip=False)      # 河は1段目の6枚まで（7枚目の丸と「7枚」の札は出さない＝2026-11-27 ユーザーの指定）
            if sc.get("cards", {}).get(i) == "bappu2" and f"step{i + 1}" in SUBS:
                bappu_live(d, t, bappu_phases(SUBS[f"step{i + 1}"]))
            if sc.get("cards", {}).get(i) == "bappu" and held:      # 手順の動きが終わって止めているあいだに、早見表を出す
                card_t0.setdefault(i, t); bappu_card(d, t - card_t0[i])
            yk_ = sc.get("yoko")
            if CMK and yk_ and yk_[0] == i and f"step{i + 1}" in SUBS and not isinstance(f, str):      # 右端に寄せたあと「横向きの牌は…」で、鳴いた牌を点滅
                w_ = say_at(SUBS[f"step{i + 1}"], yk_[1])
                if w_ is not None:
                    t0_ = max(.25 + w_, HOLD_T.get(i, 0) + .15) if len(yk_) > 3 and yk_[3] else .25 + w_      # 4つ目が真なら、動きが止まってから（リーチの宣言牌は、置いて手を戻してから＝2026-11-28）
                    blink_mark(d, CMK[min(f, len(CMK) - 1)], t - t0_, yk_[2])
            if DRK and s[0] == "裏ドラ" and f"step{i + 1}" in SUBS and not isinstance(f, str):      # 表ドラ・裏ドラの札（カンの元ドラ・新ドラと同じ。2026-11-28 ユーザーの指定）
                bx_ = DRK["frames"][min(f, len(DRK["frames"]) - 1)]
                w1 = say_end(SUBS[f"step{i + 1}"], "めくります") or 3.0; w0 = say_end(SUBS[f"step{i + 1}"], "並べます") or 1.5
                kandora_marks(d, bx_, .25 + w1, t, labels=("表ドラ", "裏ドラ"), t_old=.25 + w1)      # 表ドラ・裏ドラの札は同時に（2026-11-28 ユーザーの指定）
            if DRK and s[0] == "カンドラ" and f"step{i + 1}" in SUBS and not isinstance(f, str):
                bx_ = DRK["frames"][min(f, len(DRK["frames"]) - 1)]
                w1 = say_end(SUBS[f"step{i + 1}"], "めくります") or 1.5; w2 = say_at(SUBS[f"step{i + 1}"], "カンドラが") or 2.0
                kandora_marks(d, bx_, .25 + w1, t, t_old=.25 + w1)      # 元ドラ・新ドラの札は同時に（リーチの表ドラ・裏ドラとそろえる＝2026-11-28 ユーザーの指定）
                if t >= .25 + w2:      # 表示牌 → ドラ のカード（3Dの牌）。王牌と重ならない側に
                    yb = min(v[1] for v in (bx_["dora"], bx_.get("kandora") or bx_["dora"]))
                    dora_card(d, t - .25 - w2, dict(y=(1100 if yb < 900 else 640), rows=[("元ドラ", DRK["dora"], next_dora(DRK["dora"]), (140, 220, 230)), ("新ドラ", DRK["kandora"], next_dora(DRK["kandora"]), (255, 170, 120))]))
            dc_ = sc.get("doracard")
            if dc_ and dc_["step"] == i and f"step{i + 1}" in SUBS:
                ws_ = say_end(SUBS[f"step{i + 1}"], dc_["at"])
                if ws_ is not None and t >= .25 + ws_: dora_card(d, t - .25 - ws_, dc_)
            if i in sc.get("yaku", {}) and f"step{i + 1}" in SUBS and not (s[7] and t > BUB_AT.get(f"step{i + 1}", .25)): yaku_board(d, t, sc["yaku"][i], SUBS[f"step{i + 1}"])      # 吹き出しが出たら消す（重ならないように切りかえる）
            od_ = sc.get("order")
            if od_ and i in od_["steps"] and "step%d" % (od_["steps"][0] + 1) in SUBS:
                ws_ = say_at(SUBS["step%d" % (od_["steps"][0] + 1)], od_["at"])
                if ws_ is not None:
                    t_ = (t - .25 - ws_) if i == od_["steps"][0] else 99
                    if t_ >= 0: order_ring(ov, t_, od_)
            kk = sc.get("kuikae")
            if kk and kk["step"] == i and f"step{i + 1}" in SUBS:
                ws = say_at(SUBS[f"step{i + 1}"], kk["at"])
                if ws is not None and t >= .25 + ws - .1:
                    kk = dict(kk, _t0=.25 + ws - .1); kuikae_card(d, kk, t - kk["_t0"], SUBS[f"step{i + 1}"])
            if f"step{i + 1}" in VO and .25 <= t <= .25 + VO[f"step{i + 1}"][1] + .3: sub_at(d, SUBS[f"step{i + 1}"], t - .25)
        else:
            rail(d, sc["steps"], len(sc["steps"]), done_all=True)
            if t > .9: summary(d, sc, t - .9)
            if "tail" in VO and .9 <= t <= .9 + VO["tail"][1] + .3: sub_at(d, SUBS["tail"], t - .9)
        Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(tmp, f"f{n:04d}.png"))
    ff = shutil.which("ffmpeg")
    if not ff:
        import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
    if VO:      # 声を1本の音にまとめて入れる
        import wave, array
        sr = next(iter(VO.values()))[3]; total = int((len(seq) / fps + .5) * sr); buf = array.array("h", [0]) * total
        for seg, (wp, dur, tx, _) in VO.items():
            with wave.open(wp) as wf: pcm = array.array("h", wf.readframes(wf.getnframes()))
            o = int(starts[seg] * sr)
            for k_ in range(min(len(pcm), total - o)): buf[o + k_] = max(-32768, min(32767, buf[o + k_] + pcm[k_]))
        if "--sfx" in a:     # 効果音（2026-11-14〜・sfx.py）。声の下に、牌の当たる音・吹き出し・手順の音などを足す
            import numpy as np, sfx
            ev = sfx_events(sc, name, seq, fps, BUB_AT, SUBS) + [(t_, "pop") for t_ in POPS]      # 囲みが出るたびに「ポン」
            fx = sfx.render(ev, len(seq) / fps, sr)[:total]
            v = np.frombuffer(buf.tobytes(), dtype=np.int16).astype(float) / 32768
            m = v + fx[:len(v)] * .8
            m = m / max(1.0, np.abs(m).max() / .98)
            buf = array.array("h", (m * 32767).astype(np.int16).tobytes())
        if "--music" in a:     # 音楽（2026-11-24〜・music.py の和モダン）: 入りの琴・BGM・締めのジングル＋余韻
            import numpy as np, music
            v = np.frombuffer(buf.tobytes(), dtype=np.int16).astype(float) / 32768
            m, sr = music.score(v, sr, bgm_from=2.8, outro_at=max(0, len(seq) / fps - len(music.PACKS["wa"]("outro")) / music.SR - .1))
            buf = array.array("h", (np.clip(m, -1, 1) * 32767).astype(np.int16).tobytes())
        mix = os.path.join(tmp, "voice.wav")
        with wave.open(mix, "wb") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(buf.tobytes())
        subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"), "-i", mix,
                        "-r", str(max(24, fps)), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
        shutil.rmtree(vtmp)
    else:
        subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"),
                        "-r", str(max(24, fps)), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    shutil.rmtree(tmp); print("ok", out, len(seq), "コマ", round(len(seq) / fps, 1), "秒")

if __name__ == "__main__":
    main()
