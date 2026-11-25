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
    "chi": dict(title="チーの方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「チー」と声に出す。ポンが優先なので一拍おいてから", 0, 6, 2.2, [], "チー"),     # 肩ごしで顔が見えるうちに止める（カメラが動き出す前）
        ("開示", "かいじ", "鳴くのに使う{搭子|ターツ}を倒して、みんなに見せる", 7, 31, 1.6, ["m4", "m5"], ""),          # 止める所は、手がどいて真上から寄ったコマ
        ("回収", "かいしゅう", "{他家|ターチャ}が切った牌を取ってくる", 32, 61, 1.4, ["m6"], ""),
        ("副露", "フーロ", "取った牌を左に横向きで付け、卓の右端に寄せる", 62, 84, 1.6, ["m6", "m4", "m5"], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 85, 109, 1.4, ["s3"], "", "※鳴いた牌と同じ牌・反対側のスジの牌は切れない（喰い替え）"),     # 形の上で切れない牌（2026-11-16 ユーザーの指定）
    ], tail=(110, 120, 2.4),
    sbeats={3: [(67, "卓の右端に寄せます")]},       # ④は、置いた所で止めて「卓の右端に寄せます」の声で寄せる（2026-11-25 ユーザーの指定）
    kuikae=dict(step=4, at="切れません", meld=["m6", "m4", "m5"], side=0, ng=[("m6", "同じ牌"), ("m3", "反対側のスジ")]),      # 喰い替えの具体例（四萬五萬で六萬をチー）
    pre=dict(head="チーできるとき", marks={"own": ("orange", "ターツ", ["m4", "m5"], "UR"), "call": ("blue", "上家が切った", ["m6"], "UL")}, ls=[0, 2, 2, 3], beats=[(2.4, 2)], hold=1.8, concl=True, lines=[
        (0.3, "手牌に {搭子|ターツ} がある", "あと1枚で順子になる2枚"),
        (3.4, "{上家|カミチャ}が{ つながる牌 }を切った → チー"),
        (3.9, "そろうのは {順子|シュンツ}", "数がつながった3枚"),
        (4.4, "上家の捨て牌だけチーできる"),
    ])),
    "pon": dict(title="ポンの方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「ポン」と声に出す。チーより優先される", 0, 6, 2.2, [], "ポン"),
        ("開示", "かいじ", "鳴くのに使う{対子|トイツ}を倒して、みんなに見せる", 7, 31, 1.6, [], ""),
        ("回収", "かいしゅう", "{他家|ターチャ}が切った牌を取ってくる", 32, 61, 1.4, [], ""),
        ("副露", "フーロ", "{対面|トイメン}から鳴いたら真ん中に横向きで付け、右端に寄せる", 62, 84, 1.6, [], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 85, 109, 1.4, [], "", "※鳴いた牌と同じ牌は切れない（喰い替え）"),
    ], tail=(110, 120, 2.4),
    sbeats={3: [(67, "卓の右端に寄せます")]},
    kuikae=dict(step=4, at="切れません", meld=["z6", "z6", "z6"], side=1, ng=[("z6", "同じ牌")]),      # 發をポン
    pre=dict(head="ポンできるとき", marks={"own": ("orange", "トイツ", ["z6", "z6"], "UL"), "call": ("blue", "対面が切った", ["z6"], "UR")}, ls=[0, 2, 2, 3], beats=[(2.4, 2)], hold=1.8, concl=True, lines=[
        (0.3, "手牌に {対子|トイツ} がある", "同じ牌2枚"),
        (3.4, "{他家|ターチャ}が{ 同じ牌 }を切った → ポン"),
        (3.9, "そろうのは {刻子|コーツ}", "同じ牌3枚"),
        (4.4, "だれの捨て牌でもポンできる"),
    ])),
    "kan": dict(title="暗槓の方法", kicker="ルールとマナーに沿った正しい手順", sub="6つの手順で覚える", steps=[
        ("発声", "はっせい", "「カン」と声に出す。自分の番で、ツモったあとに", 0, 6, 2.2, [], "カン"),
        ("開示", "かいじ", "4枚を表向きに倒して見せ、外側の2枚を裏返す", 7, 47, 1.6, [], ""),
        ("配置", "はいち", "4枚を卓の右端に寄せる", 48, 67, 1.4, [], ""),
        ("カンドラ", "", "ドラ表示牌のとなりを1枚めくる。カンドラが1つ増える", 68, 87, 1.6, [], ""),
        ("嶺上牌", "リンシャンパイ", "王牌の端から、嶺上牌を1枚ツモる", 88, 112, 1.4, [], ""),
        ("打牌", "ダハイ", "アガリ牌でなければ、いらない牌を1枚切る", 113, 132, 1.4, [], ""),
    ], tail=(133, 142, 2.4),
    sbeats={1: [(32, "外側の2枚を裏返します")]},     # ②は表向きに倒した所で止め、「外側の2枚を裏返します」の声で裏返す（2026-11-25 ユーザーの指定）
    pre=dict(head="暗槓できるとき", ls=[0, 0, 1, 1], hold=1.8, concl=True, lines=[
        (0.3, "手牌の中だけで{ 同じ牌4枚 }", "自分でツモってそろえた"),
        (1.6, "そろうのは {槓子|カンツ}", "同じ牌4枚"),
        (2.9, "鳴き扱いにならない", "{門前|メンゼン}のまま"),
        (3.7, "自分でそろえた4枚なら、暗槓できる"),
    ])),
    # ここから下は、scene.py の「台本で動かす場面」（S2T の間の時刻からコマを計算: 間 n の止めるコマ＝(時刻＋n×0.7＋0.58)×12）
    "daiminkan": dict(title="大明槓の方法", kicker="ルールとマナーに沿った正しい手順", sub="7つの手順で覚える", steps=[
        ("発声", "はっせい", "「カン」と声に出す。人が切った牌で4枚目をそろえる", 0, 6, 2.2, [], "カン"),
        ("開示", "かいじ", "手牌の同じ牌3枚を倒して、みんなに見せる", 7, 32, 1.6, [], ""),
        ("回収", "かいしゅう", "{他家|ターチャ}が切った牌を取ってくる", 33, 61, 1.4, [], ""),
        ("副露", "フーロ", "{下家|シモチャ}から鳴いたら右に横向きで付け、右端に寄せる", 62, 84, 1.6, [], ""),
        ("カンドラ", "", "ドラ表示牌のとなりを1枚めくる。カンドラが1つ増える", 85, 105, 1.6, [], ""),
        ("嶺上牌", "リンシャンパイ", "王牌の端から、嶺上牌を1枚ツモる", 106, 131, 1.4, [], ""),
        ("打牌", "ダハイ", "アガリ牌でなければ、いらない牌を1枚切る", 132, 154, 1.4, [], ""),
    ], tail=(155, 165, 2.4),
    sbeats={3: [(67, "卓の右端に寄せます")]},
    pre=dict(head="大明槓できるとき", marks={"own": ("orange", "アンコ", ["z5", "z5", "z5"], "UL"), "call": ("blue", "下家が切った", ["z5"], "UR")}, ls=[0, 2, 2, 3, 4], beats=[(2.4, 2)], hold=1.8, concl=True, lines=[
        (0.3, "手牌に {暗刻|アンコ} がある", "同じ牌3枚"),
        (3.4, "{他家|ターチャ}が{ 4枚目 }を切った → カン"),
        (3.9, "そろうのは {槓子|カンツ}", "同じ牌4枚"),
        (4.4, "暗槓と違い、{ 鳴き扱い }になる", "{門前|メンゼン}ではなくなる"),
        (4.9, "だれの捨て牌でも大明槓できる"),
    ])),
    "kakan": dict(title="加槓の方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「カン」と声に出す。自分の番で、ツモったあとに", 0, 6, 2.2, [], "カン"),
        ("加槓", "カカン", "ポンした牌の横向きの1枚に、横向きで重ねる", 7, 36, 1.8, [], ""),
        ("カンドラ", "", "ドラ表示牌のとなりを1枚めくる。カンドラが1つ増える", 37, 57, 1.6, [], ""),
        ("嶺上牌", "リンシャンパイ", "王牌の端から、嶺上牌を1枚ツモる", 58, 83, 1.4, [], ""),
        ("打牌", "ダハイ", "アガリ牌でなければ、いらない牌を1枚切る", 84, 106, 1.4, [], ""),
    ], tail=(107, 117, 2.4),
    pre=dict(head="加槓できるとき", ls=[0, 2, 2, 2], beats=[(1.4, 2)], marks={"own": ("orange", "ミンコ", ["z7", "z7", "z7"], "UR"), "call": ("blue", "4枚目", ["z7"], "UL")}, hold=2.0, concl=True, lines=[
        (0.3, "ポンした {明刻|ミンコ} がある", "人の牌でそろえた同じ牌3枚"),
        (1.6, "自分で{ 4枚目 }を引いた → カン"),
        (2.8, "そろうのは {槓子|カンツ}", "同じ牌4枚"),
        (3.6, "ポンした3枚に足して、加槓できる"),
    ])),
    "riichi": dict(title="リーチの方法", kicker="ルールとマナーに沿った正しい手順", sub="3つの手順で覚える", steps=[
        ("発声", "はっせい", "「リーチ」と声に出す", 0, 6, 2.2, [], "リーチ"),
        ("打牌", "ダハイ", "いらない牌を、横向きにして切る", 7, 42, 1.8, [], ""),
        ("供託", "きょうたく", "1,000点棒を1本、卓の中央に出す（アガった人がもらう）", 43, 80, 1.8, [], ""),     # 「待つ」の手順はやめた（2026-11-14 ユーザーの判断）
    ], tail=(81, 93, 2.4),
    pre=dict(head="リーチできるとき", ls=[0, 1, 1], hold=2.0, concl=True, lines=[
        (0.3, "{門前|メンゼン}である", "ポン・チー・明槓をしていない"),
        (1.6, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (2.8, "1,000点棒を出して、リーチできる"),
    ], note=(3.4, "※持ち点や山の残り枚数の条件は、ルールによって違う"))),     # 環境ごとに違う条件は、ただし書きに（2026-11-14 ユーザーの指定）
    "tsumo": dict(title="ツモアガリの方法", kicker="ルールとマナーに沿った正しい手順", sub="5つの手順で覚える", steps=[
        ("ツモ", "", "山から取ったアガリ牌を、手牌の横に置く。手牌には入れない", 0, 42, 1.6, [], ""),
        ("発声", "はっせい", "「ツモ」と声に出す", 43, 49, 2.0, [], "ツモ"),
        ("開示", "かいじ", "両手で手牌の両端を持って、手牌を倒す", 50, 68, 2.0, [], ""),
        ("申告", "しんこく", "点数だけを言う\nメンゼンツモ・タンヤオ・ドラ1＝子の3翻30符", 69, 75, 2.6, [], "1000・2000", "※ドラ表示牌が三萬なので、ドラは四萬。手牌に1枚でドラ1"),     # ドラ表示牌を見せる（画角は scene.py の DV。2026-11-18 ユーザーの指定）     # 役は言わず点数だけ・両手で倒す（2026-11-14 ユーザーの指定。ロンと同じ）。500・1000のアガリ（2026-11-16）
        ("支払い", "しはらい", "親は2,000点、子は1,000点ずつ、アガった人に払う", 76, 104, 2.0, [], ""),     # 点数の支払いも見せる（2026-11-16 ユーザーの指定）
    ], tail=(105, 105, 2.4),
    pre=dict(head="ツモアガリできるとき", ls=[0, 1, 2, 2], hold=2.0, concl=True, lines=[
        (0.3, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (1.6, "自分で{ アガリ牌 }を引いた → ツモ"),
        (2.8, "{役|ヤク}が1つ以上ある", "アガるのに必要な形"),
        (3.6, "自分で引いたアガリ牌で、ツモアガリ"),
    ])),
    "ron": dict(title="ロンアガリの方法", kicker="ルールとマナーに沿った正しい手順", sub="4つの手順で覚える", steps=[
        ("発声", "はっせい", "「ロン」と声に出す。ポン・チーより優先される", 0, 6, 2.2, [], "ロン"),
        ("開示", "かいじ", "両手で手牌の両端を持って、手牌を倒す", 7, 36, 2.0, [], ""),
        ("申告", "しんこく", "点数だけを言う\nタンヤオ・ピンフ・赤1＝子の3翻30符で3,900点", 37, 66, 2.6, [], "3900"),     # 役は言わず点数だけ（2026-11-14 ユーザーの指定）
        ("支払い", "しはらい", "{下家|シモチャ}が5,000点棒で払い、おつりの1,100点を返す", 67, 114, 2.0, [], ""),     # 下家が5,000点棒・自分が1,000点棒と100点棒で返す（2026-11-16 ユーザーの指定）
    ], tail=(115, 120, 2.4),
    pre=dict(head="ロンアガリできるとき", marks={"own": ("orange", "待ちの形", ["p6", "p7"], "UL"), "call": ("blue", "アガリ牌", ["p5r"], "UR")}, ls=[0, 1, 2, 3], beats=[(2.4, 1)], hold=1.8, concl=True, lines=[
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
    counts={2: ("riv", .3, .3)},      # ③河: 自分の河に「1・2・3…7」を順に出す（2026-11-25 ユーザーの指定「説明は、セリフだけでなく見て分かる演出を」）
    pre=dict(head="自分の番の流れ", ls=[0, 1, 2, 2], beats=[(3.1, 1), (5.9, 2)], hold=2.0, concl=True, count=("hand", 6.6, .2), lines=[      # 前置きの絵（scene.py の pre_pose_dahai）に合わせた時刻
        (0.5, "{上家|カミチャ}が切ったら、自分の番"),
        (3.1, "1枚{ツモ}って、1枚切る"),
        (6.2, "手牌はいつも13枚", "切ったあと"),
        (9.2, "ツモって切る、をくり返す"),
    ])),
    "furiten": dict(title="捨て牌のフリテン", kicker="フリテンは3種類", sub="3種類の1つめ", steps=[
        ("待ち", "まち", "待ちを確かめる。一索・四索・七索の3種類", 24, 24, 2.2, [], ""),
        ("河", "かわ", "自分の河に、待ちの一索がある", 25, 44, 2.2, [], ""),
        ("ロンできない", "", "{他家|ターチャ}が四索を切っても、ロンできない", 45, 74, 2.2, [], "", "※ポン・チーで鳴かれて、河に無くてもフリテン"),
        ("ツモ", "", "自分で引いたアガリ牌なら、ツモアガリできる", 75, 116, 2.2, [], ""),
    ], tail=(117, 126, 2.4),
    pre=dict(head="捨て牌のフリテン", ls=[0, 0, 0, 1], hold=2.0, concl=True, lines=[
        (0.3, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (1.6, "待ちの牌を1種でも{ 切っている }", "自分の河にある"),
        (2.9, "どの待ちでも{ロン}できない", "ツモはできる"),
        (3.7, "待ちが変わるまで、ロンできない"),
    ])),
    "furiten2": dict(title="同巡内フリテン", kicker="フリテンは3種類", sub="3種類の2つめ", steps=[
        ("待ち", "まち", "チーしていて、役はタンヤオだけ。一索では役が無い", 24, 24, 2.2, [], ""),
        ("見逃し", "みのがし", "{下家|シモチャ}の一索は、役が無いのでロンできない", 25, 50, 2.2, [], ""),
        ("ロンできない", "", "{対面|トイメン}の四索は役があるが、ロンできない", 51, 75, 2.2, [], ""),
        ("打牌", "ダハイ", "自分が打牌すると、フリテンがなくなる", 76, 131, 2.2, [], "", "※番が飛ばされても、自分が打牌するまでは続く"),
        ("ロンできる", "", "このあとの七索なら、ロンできる", 132, 156, 2.2, [], ""),
    ], tail=(157, 167, 2.4),
    pre=dict(head="同巡内フリテン", ls=[0, 0, 0, 1], hold=2.0, concl=True, lines=[
        (0.3, "{聴牌|テンパイ}している", "あと1枚でアガれる形"),
        (1.6, "アガリ牌が出たのに{ 見逃した }", "役が無いときも"),
        (2.9, "どの待ちでも{ロン}できない", "ツモはできる"),
        (3.7, "次に自分が打牌するまで、ロンできない"),
    ])),
    "furiten3": dict(title="リーチ後のフリテン", kicker="フリテンは3種類", sub="3種類の3つめ", steps=[
        ("待ち", "まち", "リーチをしている。一索・四索・七索待ち", 24, 24, 2.2, [], ""),
        ("見逃し", "みのがし", "タンヤオがつく四索・七索を待って、一索を見逃す", 25, 50, 2.2, [], ""),
        ("打牌", "ダハイ", "自分が打牌しても、フリテンのまま", 51, 112, 2.2, [], ""),
        ("ロンできない", "", "{上家|カミチャ}が四索を切っても、ロンできない", 113, 153, 2.2, [], ""),
        ("ツモ", "", "自分で引いたアガリ牌なら、ツモアガリできる", 154, 200, 2.2, [], ""),
    ], tail=(201, 210, 2.4),
    pre=dict(head="リーチ後のフリテン", ls=[0, 0, 0, 1], hold=2.0, concl=True, lines=[
        (0.3, "{リーチ}をしている", "待ちを変えられない"),
        (1.6, "アガリ牌が出たのに{ 見逃した }"),
        (2.9, "どの待ちでも{ロン}できない", "ツモはできる"),
        (3.7, "その局が終わるまで、ロンできない"),
    ])),
    "ryukyoku": dict(title="流局のしかた", kicker="ルールとマナーに沿った正しい手順", sub="4つの手順で覚える", steps=[
        ("流局", "りゅうきょく", "アガリが出ないまま、この局はおしまい", 0, 6, 2.2, [], ""),     # 前置きのカードと同じことを言わない（2026-11-14 ユーザーの指定）
        ("テンパイ", "", "あと1枚でアガれる人は、両手で手牌を倒して見せる", 7, 36, 2.0, [], ""),     # 流局のテンパイ・ノーテンは声に出さない（2026-11-14 ユーザーの指定）
        ("ノーテン", "", "テンパイなら倒し、ノーテンなら両手で伏せる。{東家|トンチャ}から順に", 37, 86, 2.0, [], ""),
        ("点棒", "てんぼう", "ノーテンの人がテンパイの人へ払う（場に3,000点）", 87, 113, 2.2, [], ""),
    ], tail=(114, 125, 2.4), cards={3: "bappu"},     # ④の止めているあいだに、ノーテン罰符の早見表（テンパイ0〜4人。2026-11-18 ユーザーの指定）
    pre=dict(head="流局になるとき", ls=[0, 1, 2, 2], hold=2.0, concl=True, lines=[
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
    d.rounded_rectangle((70, y, W - 70, y + 440), radius=60, fill=(12, 20, 22, A(215)))
    # 左上に小さく、まじゃすこのマーク（2026-11-16 ユーザーの指定。締めと同じアイコン）。帯は「ルールとマナーに沿った正しい手順」（ルールやマナーに沿った方法だと示す）
    ic = _app_icon(78)
    if a < 1: ic = ic.copy(); ic.putalpha(ic.getchannel("A").point(lambda v: int(v * a)))
    d._image.alpha_composite(ic, (104, y + 44))
    kt = sc.get("kicker", ""); ft = fit(d, kt, 42, W - 2 * 200 - 64, 800)
    kw = d.textlength(kt, font=ft) + 64
    d.rounded_rectangle((W / 2 - kw / 2, y + 44, W / 2 + kw / 2, y + 44 + 78), radius=39, fill=(231, 86, 32, A(255)))
    text_c(d, W / 2, y + 44 + 37, kt, ft, (255, 255, 255, A(255)))
    tr = any(r for p, r, t_ in ruby_parts(sc["title"]))
    ruby_c(d, W / 2, y + (252 if tr else 222), sc["title"], fit(d, sc["title"], 132 if tr else 140, W - 140 - 90), (255, 255, 255, A(255)), 44)     # 長い題名（ロンアガリの方法）は、カードに入るまで小さく
    ruby_c(d, W / 2, y + 384, sc.get("sub", ""), font(48, 700), (255, 255, 255, A(220)), 22)
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
    y = H - 80 - hgt + int((1 - k) * 30)
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


_bub = {}
# 吹き出しの場所（2026-11-14 ユーザーの指定「口や顔あたりから出るように。対面の顔が隠れないように」）:
#   ①発声のカメラ（肩ごし・どの動画も同じ画角）では、手前の選手の頭が左（x 0〜350・y 480〜960）、対面の顔が上の真ん中（x 600〜900・y 470〜800）。
#   吹き出しは頭の右下（卓の左手前の上）に置き、しっぽを左上へ＝手前の選手の顔の前（頭の右のふち）へ向ける。対面の顔・見出しのカードにかからない
BUB_C = (640, 1045)          # 吹き出しの真ん中（2026-11-14 ユーザーの指定: 右へ。ふちが手前の選手の頭にかからない所＝しっぽの先だけが頭のふちに触れる）
BUB_TIP = (-330, -125)       # しっぽの先（真ん中からのずれ。手前の選手の顔の前を指す）
BUB_POS = {"3900": ((560, 1110), (-60, 300)), "400・700": ((560, 1110), (-60, 300)), "500・1000": ((560, 1110), (-60, 300)), "1000・2000": ((560, 1110), (-60, 300)), "ツモ": ((600, 1250), (-60, 300))}     # ツモの②は牌に寄った画角。ツモった牌にかからないよう下から     # 言葉ごとの吹き出しの場所（真ん中, しっぽの向き）。無ければ BUB_FACE に向けて置く
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
    "furiten": [[WAIT_], [WAIT_, ("fu7", "orange", "自分が切った", ["s1"], "LR")], [WAIT_, ("fu7", "orange", "自分が切った", ["s1"], "LR"), ("called", "red", "ロンできない", ["s4"], "UL")],
                [("fu7", "orange", "", [], ""), ("next", "green", "ツモはできる", ["s4"], "LR")]],
    "furiten2": [[WAIT_, ("meld", "orange", "チーした牌", ["m2", "m3", "m4"], "RM")], [WAIT_, ("o1", "blue", "見逃し", ["s1"], "UR")], [WAIT_, ("o1", "blue", "見逃し", ["s1"], "UR"), ("o2", "red", "ロンできない", ["s4"], "UL")],
                 [WAIT_, ("next", "orange", "自分が打牌", ["z2"], "LM")], [WAIT_, ("o4", "green", "ロンできる", ["s7"], "UR")]],
    "furiten3": [[WAIT_, ("rk", "orange", "リーチ", ["m1"], "LR"), ("bou", "orange", "", [], "")], [WAIT_, ("o1", "blue", "見逃し", ["s1"], "UR")], [WAIT_, ("o1", "blue", "見逃し", ["s1"], "UR"), ("next", "orange", "自分が打牌", ["p9"], "LR")],
                 [WAIT_, ("o1", "blue", "見逃し", ["s1"], "UR"), ("o6", "red", "ロンできない", ["s4"], "UL")], [("o1", "blue", "", [], ""), ("next2", "green", "ツモはできる", ["s7"], "LR")]],
}
_tim = {}
def _tile_img(code, h):
    k = (code, h)
    if k not in _tim:
        fp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tiles", code + ".png")
        if os.path.exists(fp): im = Image.open(fp).convert("RGBA"); _tim[k] = im.resize((round(im.width * h / im.height), h), Image.LANCZOS)
        else: _tim[k] = tile_img(code, round(h * 3 / 4), h)      # tiles/ に無い牌は、3Dの牌の絵（make_tile_tex.py）
    return _tim[k]
def draw_marks(d, marks, here):
    """囲み（白いふち＋色の線）と、牌の絵つきの札・つなぐ線。here＝このコマの牌の場所（まだ切られていない牌は無い）"""
    todo = [m for m in marks if m[0] in here]; box = {}
    for nm, col, tx, codes, pos in todo:
        if not tx: continue
        TH = 104; ims = [_tile_img(c, TH) for c in codes]; f = font(40)
        w = max(d.textlength(tx, font=f), sum(i.width + 6 for i in ims)) + 44; h = 74 + TH + 18
        x, y = {"UL": (24, 690), "UR": (W - 24 - w, 690), "LL": (24, 1296), "LR": (W - 24 - w, 1296), "RM": (W - 24 - w, 1060), "LM": (24, 1050)}[pos]
        box[nm] = (x, y, w, h, ims, f)
    for nm, col, tx, codes, pos in todo:      # 線 → 囲み → 札の順に重ねる
        c = MKC[col]; x0, y0, x1, y1 = here[nm]; P_ = 9
        if nm in box:
            x, y, w, h, ims, f = box[nm]; ax = min(max((x0 + x1) / 2, x + 30), x + w - 30); ay = y + h if y + h < y0 else (y if y > y1 else y + h / 2)
            if ay == y + h / 2: ax = x + w if x + w < x0 else x
            tx_, ty_ = min(max(ax, x0 - P_), x1 + P_), min(max(ay, y0 - P_), y1 + P_)
            d.line((ax, ay, tx_, ty_), fill=(255, 255, 255, 255), width=14); d.line((ax, ay, tx_, ty_), fill=c + (255,), width=8)
        d.rounded_rectangle((x0 - P_ - 4, y0 - P_ - 4, x1 + P_ + 4, y1 + P_ + 4), radius=16, outline=(255, 255, 255, 255), width=14)
        d.rounded_rectangle((x0 - P_, y0 - P_, x1 + P_, y1 + P_), radius=13, outline=c + (255,), width=7)
    for nm, (x, y, w, h, ims, f) in box.items():
        col, tx = next((m[1], m[2]) for m in todo if m[0] == nm); c = MKC[col]
        d.rounded_rectangle((x, y, x + w, y + h), radius=24, fill=(255, 255, 255, 250), outline=c + (255,), width=7)
        d.rounded_rectangle((x, y, x + w, y + 66), radius=24, fill=c + (255,)); d.rectangle((x, y + 36, x + w, y + 66), fill=c + (255,))
        text_c(d, x + w / 2, y + 32, tx, f, WHITE)
        xx = x + w / 2 - (sum(i.width + 6 for i in ims) - 6) / 2
        for i in ims: d._image.alpha_composite(i, (int(xx), int(y + 78))); xx += i.width + 6

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


def draw_count(d, ps, t, t0, dt, nmax=None):
    """牌の上に「1・2・3…」の丸を順に出す（ps＝牌の場所 [x, 上のふち] の並び・t0 から dt 秒おきに1つずつ）"""
    for k, (x, y) in enumerate(ps[:nmax] if nmax else ps):
        a = (t - t0 - k * dt) / .12
        if a <= 0: break
        a = min(1, a); r = 24; cy = y - 34 - int((1 - a) * 14)
        d.ellipse((x - r, cy - r, x + r, cy + r), fill=(231, 86, 32, int(255 * a)), outline=(255, 255, 255, int(255 * a)), width=4)
        text_c(d, x, cy - 1, str(k + 1), font(30), (255, 255, 255, int(255 * a)))


def sfx_events(sc, name, seq, fps, bub_at={}):
    """効果音を鳴らす時刻（秒）と音。画面の出来事（手順・吹き出し・カード）と、牌の当たる瞬間（sfx.TILE_EVENTS）"""
    import sfx
    ev = []; first = {}
    for n, (f, i, t, held) in enumerate(seq):
        sec = n / fps
        if n == 0 or i != seq[n - 1][1]:          # 場面が変わった瞬間
            # 画面の出来事で鳴らすのは、発声の吹き出しと、手順の切りかえ（2026-11-24 ユーザーの指定で足した。琴の「ポロン」）。箇条書き・まとめでは鳴らさない
            if i >= 0 and sc["steps"][i][7]: ev.append((sec + bub_at.get(f"step{i + 1}", .25), "pop"))
            if i >= 0: ev.append((sec, "kstep"))
            if i == -4:       # 前置き: 鳴くのに使う手牌が動いた瞬間と、他家がその牌を切った瞬間に「ポンッ」（sfx.PRE_EVENTS）
                am = sc["pre"].get("amap")
                for t_, snd in sfx.PRE_EVENTS.get(name, []): ev.append((sec + (next((k / fps for k, x in enumerate(am) if x >= t_), t_) if am else t_), snd))
                if sc["pre"].get("count"):      # 数える丸が出るたびに小さな音
                    _, c0, cd = sc["pre"]["count"]; ev += [(sec + c0 + k * cd, "tick") for k in range(13)]
            if i >= 0 and i in sc.get("counts", {}):
                _, c0, cd = sc["counts"][i]; ev += [(sec + c0 + k * cd, "tick") for k in range(7)]
        if i >= 0 and not held and not isinstance(f, str): first.setdefault(f, sec)
    for t, snd in sfx.TILE_EVENTS.get(name, []):
        fr = sfx.frame_of(name, t, fps)
        if fr in first: ev.append((first[fr], snd))
    return ev


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


def kuikae_card(d, kk, t):
    """喰い替えの具体例（2026-11-25 ユーザーの指定「具体的に画面で見せる」）。鳴いた形と、そのあと切れない牌に×"""
    a = min(1, t * 4); A = lambda v: int(v * a); y = 930 + int((1 - a) * 24); h = 470
    d.rounded_rectangle((60, y, W - 60, y + h), radius=40, fill=(255, 255, 255, A(245)), outline=(231, 86, 32, A(255)), width=6)
    text_c(d, W / 2, y + 52, "喰い替えの例", font(44, 800), (231, 86, 32, A(255)))
    tw, th = 74, 99
    def row(codes, x0, yy, side=None):
        x = x0
        for n, c in enumerate(codes):
            im = _tile_img(c, th)
            if n == side: im = im.rotate(90, expand=True)
            if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
            d._image.alpha_composite(im, (int(x), int(yy + (th - im.size[1]))))
            x += im.size[0] + 6
        return x
    text_c(d, 210, y + 170, "鳴いた形", font(36, 800), (23, 112, 131, A(255)))
    meld = kk["meld"]; mw = sum(tw + 6 for _ in meld) + (th - tw)
    row(meld, 330, y + 120, side=kk.get("side"))
    text_c(d, 210, y + 330, "切れない", font(36, 800), (201, 47, 66, A(255)))
    x = 330
    for c, lab in kk["ng"]:
        im = _tile_img(c, th)
        if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        yy = y + 262; d._image.alpha_composite(im, (x, yy))
        cx, cy = x + tw / 2, yy + th / 2; r = 34
        for s_ in (1, -1): d.line((cx - r, cy - r * s_, cx + r, cy + r * s_), fill=(201, 47, 66, A(235)), width=10)
        text_c(d, cx, yy + th + 32, lab, font(30, 800), (80, 90, 92, A(255)))
        x += max(tw, int(d.textlength(lab, font=font(30, 800)))) + 60


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
    name = a[a.index("--script") + 1] if "--script" in a else "chi"
    sc = scaled(SCRIPTS[name], fps)
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
    need = lambda seg, pad=.35: (VO[seg][1] + pad) if seg in VO else 0.0
    starts = {}      # 声を鳴らし始める時刻（秒）
    src, out = a[0], a[1]; TEX[0] = os.path.join(os.path.dirname(os.path.abspath(src)), "tex")
    frames = sorted(glob.glob(os.path.join(src, "f[0-9]*.png")))
    assert frames, "コマが無い: " + src
    intro = sorted(glob.glob(os.path.join(src, "i[0-9]*.png")))
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
        else:
            for n, fp in enumerate(pre + [pre[-1]] * max(int(sc["pre"]["hold"] * fps), int((need("pre") + .6) * fps) - len(pre))): seq.append((fp, -4, n / fps, False))
    for i, s in enumerate(sc["steps"]):
        t = 0.0; starts[f"step{i + 1}"] = len(seq) / fps + .25
        # 発声と、①（流局など）の手順は、最初のコマで止めたまま見せる（2026-11-14 ユーザーの指定「①で画角が少しでも動くのはいらない。止めた絵で説明」）。
        # 次の手順は、止めたコマのすぐ後から動かす（止めた所から先のコマを飛ばすと、絵が飛ぶ）。ツモアガリの①ツモは、山から取る動きそのものなので止めない
        frozen = s[0] == "発声" or (i == 0 and s[0] != "ツモ")
        a0 = sc["steps"][i - 1][3] + 1 if i and (sc["steps"][i - 1][0] == "発声" or (i == 1 and sc["steps"][0][0] != "ツモ")) else s[3]
        fr = [s[3]] * (s[4] - s[3] + 1) if frozen else list(range(a0, s[4] + 1))
        for bf, wd in reversed(sc.get("sbeats", {}).get(i, [])):      # 声のその言葉が出るまで、コマ bf で止めて待つ
            ws = say_at(SUBS.get(f"step{i + 1}", []), wd)
            if ws is not None and bf in fr:
                k_ = fr.index(bf); fr = fr[:k_ + 1] + [bf] * max(0, int((.25 + ws - .1) * fps) - (k_ + 1)) + fr[k_ + 1:]
        for f in fr: seq.append((f, i, t, False)); t += 1 / fps
        nd = max(need(f"step{i + 1}") + .25, (BUB_AT.get(f"step{i + 1}", .25) + 1.8) if s[7] else 0)     # 吹き出しが出てから1.8秒は見せる（1秒では一瞬で消えて見えた）
        for _ in range(max(int(s[5] * fps), int(nd * fps) - len(fr))): seq.append((s[3] if frozen else s[4], i, t, True)); t += 1 / fps
    f0, f1, hold = sc["tail"]; t = 0.0; starts["tail"] = len(seq) / fps + .9
    for f in range(f0, f1 + 1): seq.append((f, -1, t, False)); t += 1 / fps
    for _ in range(max(int(hold * fps), int((need("tail") + .9) * fps) - (f1 - f0 + 1))): seq.append((f1, -1, t, True)); t += 1 / fps
    starts["outro"] = len(seq) / fps + 1.2
    outro = sorted(glob.glob(os.path.join(src, "o[0-9]*.png")))      # 締め（scene.py --anim --outro）。最後のコマで2秒止める
    odur = (len(outro) + 2 * fps) / fps
    for n, fp in enumerate(outro + [outro[-1]] * (2 * fps) if outro else []): seq.append((fp, -3, n / fps, False))
    tmp = tempfile.mkdtemp(); cache = {}; fade = None; cache_prev = None; card_t0 = {}
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
        if i == -4:
            pre_card(d, sc["pre"], t)
            if sc["pre"].get("marks") and PMK:      # 使う手牌と、人が切った牌を囲む（2026-11-25 ユーザーの指定）
                pi = min(int(os.path.basename(f)[1:5]), len(PMK) - 1) if isinstance(f, str) else 0
                draw_marks(d, [(k_,) + tuple(v_) for k_, v_ in sc["pre"]["marks"].items()], PMK[pi])
            if sc["pre"].get("count") and PCNT:
                key, c0, cd = sc["pre"]["count"]; pi = min(int(os.path.basename(f)[1:5]), len(PCNT) - 1) if isinstance(f, str) else 0
                draw_count(d, PCNT[pi][key], t, c0, cd, 13)
        elif i == -3:
            outro_card(im, t, odur)
        elif i == -2:
            title_card(d, sc, t, sum(1 for q in seq if q[1] == -2) / fps)      # 入りの声が長いときも、入りが終わるまで題名を出し続ける（前は入りの絵の長さ4秒で消えた。2026-11-25 ユーザーの指摘）
        elif i >= 0:
            s = sc["steps"][i]
            if name in MARKS:
                assert MK, "marks.json が無い（scene.py を動かすと、コマと同じフォルダにできる）"
                draw_marks(d, MARKS[name][i], MK[min(f, len(MK) - 1)])
            rail(d, sc["steps"], i); headline(d, i, s, t)
            bt = BUB_AT.get(f"step{i + 1}", .25)
            if s[7] and t > bt: bubble(d, s[7], t - bt)
            if i in sc.get("counts", {}) and CNT:
                key, c0, cd = sc["counts"][i]; draw_count(d, CNT[min(f, len(CNT) - 1)][key], t, c0, cd, 7)
            if sc.get("cards", {}).get(i) == "bappu" and held:      # 手順の動きが終わって止めているあいだに、早見表を出す
                card_t0.setdefault(i, t); bappu_card(d, t - card_t0[i])
            kk = sc.get("kuikae")
            if kk and kk["step"] == i and f"step{i + 1}" in SUBS:
                ws = say_at(SUBS[f"step{i + 1}"], kk["at"])
                if ws is not None and t >= .25 + ws - .3: kuikae_card(d, kk, t - (.25 + ws - .3))
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
            ev = sfx_events(sc, name, seq, fps, BUB_AT)
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
