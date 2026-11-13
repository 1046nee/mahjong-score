# -*- coding: utf-8 -*-
"""scene.py --anim が書き出したコマ（入り i0000.png〜・本題 f0000.png〜）に、題名と手順の表示をのせて mp4 にする。
  python tools/b3d/make_clip.py <コマのフォルダ> <出力.mp4> [--fps 12] [--script chi]
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

# 台本: 手順ごとに (名前, 読み, 説明, 最初のコマ, 最後のコマ, 止める秒, 囲む牌, 吹き出し)。コマは scene.py の anim_pose の区切り（12fps）
SCRIPTS = {
    "chi": dict(title="チーの方法", kicker="麻雀の所作", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「チー」と声に出す。ポンが優先なので一拍おいてから", 0, 6, 2.2, [], "チー"),     # 肩ごしで顔が見えるうちに止める（カメラが動き出す前）
        ("開示", "かいじ", "鳴くのに使うターツを倒して、みんなに見せる", 7, 31, 1.6, ["m4", "m5"], ""),          # 止める所は、手がどいて真上から寄ったコマ
        ("回収", "かいしゅう", "他家（ターチャ）が切った牌を取ってくる", 32, 61, 1.4, ["m6"], ""),
        ("副露", "フーロ", "取った牌を横向きにして付け、卓の右に寄せる", 62, 84, 1.6, ["m6", "m4", "m5"], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 85, 105, 1.4, ["s3"], ""),
    ], tail=(106, 120, 2.4),
    pre=dict(head="チーできるとき", hold=1.8, lines=[
        (0.3, "手牌に 四萬・五萬 がある"),
        (1.6, "六萬が来れば 四五六 の順子になる"),
        (3.4, "上家（左の人）が 六萬 を切った → チーできる"),
        (3.9, "チーは上家の捨て牌だけ。ポンは同じ牌2枚で、だれの捨て牌でもできる"),
    ])),
    "pon": dict(title="ポンの方法", kicker="麻雀の所作", sub="5つの手順で覚える", steps=[
        ("発声", "はっせい", "「ポン」と声に出す。チーより優先される", 0, 6, 2.2, [], "ポン"),
        ("開示", "かいじ", "鳴くのに使う対子（トイツ）を倒して、みんなに見せる", 7, 31, 1.6, [], ""),
        ("回収", "かいしゅう", "他家（ターチャ）が切った牌を取ってくる", 32, 61, 1.4, [], ""),
        ("副露", "フーロ", "取った牌を横向きに。対面から鳴いたら真ん中に置く", 62, 84, 1.6, [], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 85, 105, 1.4, [], ""),
    ], tail=(106, 120, 2.4),
    pre=dict(head="ポンできるとき", hold=1.8, lines=[
        (0.3, "手牌に対子（同じ牌が2枚）がある"),
        (3.4, "他家がもう1枚同じ牌を切った → ポンできる"),
        (3.9, "ポンは、だれの捨て牌でもできる"),
        (4.4, "副露の横向きの牌の位置で、だれから鳴いたかわかる"),
    ])),
    "kan": dict(title="カンの方法", kicker="麻雀の所作", sub="暗槓（アンカン）編", steps=[
        ("発声", "はっせい", "「カン」と声に出す。自分の番で、ツモったあとに", 0, 6, 2.2, [], "カン"),
        ("開示", "かいじ", "同じ牌4枚を倒す。暗槓は外側の2枚を伏せる", 7, 33, 1.6, [], ""),
        ("副露", "フーロ", "4枚を卓の右に寄せる", 34, 57, 1.4, [], ""),
        ("カンドラ", "カンドラ", "ドラ表示牌のとなりを1枚めくる", 58, 79, 1.6, [], ""),
        ("嶺上牌", "リンシャンハイ", "王牌の端から1枚取ってくる", 80, 104, 1.4, [], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 105, 124, 1.4, [], ""),
    ], tail=(125, 134, 2.4),
    pre=dict(head="カンできるとき", hold=1.8, lines=[
        (0.3, "手牌に 東 が4枚そろった"),
        (1.6, "同じ牌4枚 → 自分の番なら 暗槓（アンカン）できる"),
        (3.0, "人が切った牌で4枚目をそろえるのは 大明槓（ダイミンカン）"),
    ])),
    # ここから下は、scene.py の「台本で動かす場面」（S2T の間の時刻からコマを計算: 間 n の止めるコマ＝(時刻＋n×0.7＋0.58)×12）
    "daiminkan": dict(title="カンの方法", kicker="麻雀の所作", sub="大明槓（ダイミンカン）編", steps=[
        ("発声", "はっせい", "「カン」と声に出す。人が切った牌で4枚目をそろえる", 0, 6, 2.2, [], "カン"),
        ("開示", "かいじ", "手牌の同じ牌3枚を倒して、みんなに見せる", 7, 32, 1.6, [], ""),
        ("回収", "かいしゅう", "他家（ターチャ）が切った牌を取ってくる", 33, 61, 1.4, [], ""),
        ("副露", "フーロ", "取った牌を横向きに。下家から鳴いたら右に置く", 62, 84, 1.6, [], ""),
        ("カンドラ", "カンドラ", "ドラ表示牌のとなりを1枚めくる", 85, 105, 1.6, [], ""),
        ("嶺上牌", "リンシャンハイ", "王牌の端から1枚取ってくる", 106, 131, 1.4, [], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 132, 150, 1.4, [], ""),
    ], tail=(151, 165, 2.4),
    pre=dict(head="大明槓できるとき", hold=1.8, lines=[
        (0.3, "手牌に 白 が3枚（暗刻）ある"),
        (1.6, "4枚目が出れば、カンできる"),
        (3.4, "下家（右の人）が 白 を切った → 大明槓できる"),
        (3.9, "だれの捨て牌でもできる。鳴くので、門前ではなくなる"),
    ])),
    "kakan": dict(title="カンの方法", kicker="麻雀の所作", sub="加槓（カカン）編", steps=[
        ("発声", "はっせい", "「カン」と声に出す。自分の番で、ツモったあとに", 0, 6, 2.2, [], "カン"),
        ("加槓", "カカン", "ポンした牌の横向きの1枚に、横向きで重ねる", 7, 36, 1.8, [], ""),
        ("カンドラ", "カンドラ", "ドラ表示牌のとなりを1枚めくる", 37, 57, 1.6, [], ""),
        ("嶺上牌", "リンシャンハイ", "王牌の端から1枚取ってくる", 58, 83, 1.4, [], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 84, 102, 1.4, [], ""),
    ], tail=(103, 117, 2.4),
    pre=dict(head="加槓できるとき", hold=2.0, lines=[
        (0.3, "中 をポンしている"),
        (1.6, "4枚目の 中 をツモった"),
        (2.8, "ポンした3枚に足して、カンにできる"),
        (3.6, "加えた牌でロンされることがある（槍槓＝チャンカン）"),
    ])),
    "riichi": dict(title="リーチの方法", kicker="麻雀の所作", sub="4つの手順で覚える", steps=[
        ("発声", "はっせい", "「リーチ」と声に出す", 0, 6, 2.2, [], "リーチ"),
        ("打牌", "ダハイ", "いらない牌を、横向きにして切る", 7, 36, 1.8, [], ""),
        ("供託", "きょうたく", "千点棒を1本、卓の中央に出す", 37, 61, 1.8, [], ""),
        ("待つ", "まつ", "あとは手牌を変えられない。あがり牌を待つ", 62, 76, 1.8, [], ""),
    ], tail=(77, 85, 2.4),
    pre=dict(head="リーチできるとき", hold=2.0, lines=[
        (0.3, "鳴いていない（門前＝メンゼン）"),
        (1.6, "あと1枚であがれる形（テンパイ）。ここは 三筒・六筒 待ち"),
        (2.8, "持ち点が1000点以上ある"),
        (3.6, "山にツモれる牌が4枚以上残っている"),
    ])),
    "tsumo": dict(title="ツモあがりの方法", kicker="麻雀の所作", sub="4つの手順で覚える", steps=[
        ("ツモ", "ツモ", "山から取ったあがり牌を、手牌の横に置く。手牌には入れない", 0, 42, 1.6, [], ""),
        ("発声", "はっせい", "「ツモ」と声に出す", 43, 49, 2.0, [], "ツモ"),
        ("開示", "かいじ", "手牌を倒して、みんなに見せる", 50, 68, 2.0, [], ""),
        ("申告", "しんこく", "役と点数を言う「ツモ・平和、400・700」", 69, 71, 2.6, [], ""),
    ], tail=(72, 79, 2.4),
    pre=dict(head="ツモあがりできるとき", hold=2.0, lines=[
        (0.3, "あと1枚であがれる形（テンパイ）"),
        (1.6, "七萬・八萬 があるので、六萬 か 九萬 であがり"),
        (2.8, "自分でその牌を引いたら → ツモあがり"),
        (3.6, "役が1つ以上いる。鳴いていなければ、ツモだけで役になる"),
    ])),
    "ron": dict(title="ロンあがりの方法", kicker="麻雀の所作", sub="4つの手順で覚える", steps=[
        ("発声", "はっせい", "「ロン」と声に出す。ポン・チーより優先される", 0, 6, 2.2, [], "ロン"),
        ("開示", "かいじ", "手牌を倒して、みんなに見せる", 7, 36, 2.0, [], ""),
        ("あがり牌", "あがりはい", "あがり牌は相手の河に置いたまま。取ってこない", 37, 54, 2.0, [], ""),
        ("申告", "しんこく", "役と点数を言う「タンヤオ・平和・三色、7700」", 55, 66, 2.6, [], ""),
    ], tail=(67, 73, 2.4),
    pre=dict(head="ロンあがりできるとき", hold=1.8, lines=[
        (0.3, "あと1枚であがれる形（テンパイ）。六筒・七筒 がある"),
        (1.6, "五筒 か 八筒 が出れば、あがり"),
        (3.4, "下家（右の人）が 八筒 を切った → ロンできる"),
        (3.9, "役が1つ以上いる。自分が捨てた牌が待ちにあると、ロンできない（フリテン）"),
    ])),
    "ryukyoku": dict(title="流局のしかた", kicker="麻雀の所作", sub="4つの手順で覚える", steps=[
        ("流局", "りゅうきょく", "だれもあがらずに、山の牌がなくなった", 0, 6, 2.2, [], ""),
        ("テンパイ", "テンパイ", "あと1枚であがれる人は「テンパイ」と言って手牌を倒す", 7, 36, 2.0, [], "テンパイ"),
        ("ノーテン", "ノーテン", "親から順に。テンパイでない人は「ノーテン」と言って伏せる", 37, 86, 2.0, [], ""),
        ("点棒", "てんぼう", "ノーテンの人がテンパイの人へ払う（場に3000点）", 87, 113, 2.2, [], ""),
    ], tail=(114, 125, 2.4),
    pre=dict(head="流局になるとき", hold=2.0, lines=[
        (0.3, "手牌は 六索・七索 で、五索 か 八索 待ち（テンパイ）"),
        (1.6, "あがり牌が出ないまま、最後の牌が切られた"),
        (2.9, "山の牌がなくなったら、その局は流局"),
        (3.7, "親がテンパイなら、親をもう一度（連荘）"),
    ])),
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
    n = len(steps); x0, x1, y = 130, W - 130, 150
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
        text_c(d, x, y + 92, s[0], font(40 if now else 34, 900 if now else 700), WHITE if (now or done) else (255, 255, 255, 150))

def headline(d, i, s, k):
    """見出しと説明。k=出てからの進み（0〜1）で少し下から入る"""
    dy = int((1 - min(1, k * 4)) * 30)
    y = 330 + dy
    d.rounded_rectangle((40, y, W - 40, y + 250), radius=44, fill=(255, 255, 255, 240))
    d.ellipse((76, y + 34, 76 + 104, y + 34 + 104), fill=ORANGE)
    text_c(d, 76 + 52, y + 34 + 50, str(i + 1), font(72), WHITE)
    d.text((204, y + 22), s[0], font=font(88), fill=INK)
    l, t, r, b = d.textbbox((204, y + 22), s[0], font=font(88))
    d.text((r + 22, y + 74), s[1], font=font(38, 700), fill=GREEN)
    ft = font(40, 800); tx = s[2]
    while d.textlength(tx, font=ft) > W - 80 - 72 and ft.size > 30: ft = font(ft.size - 2, 800)
    d.text((76, y + 164), tx, font=ft, fill=INK)

def title_card(d, sc, t, dur):
    """入りの題名。少し遅れて下から入り、本題に入る直前に消える"""
    k = min(1, max(0, (t - .5) * 3)); out = min(1, max(0, (dur - t) * 4)); a = k * out
    if a <= 0: return
    A = lambda v: int(v * a)
    y = 230 + int((1 - k) * 40)      # 上に置く（真ん中だと卓と選手が隠れる）
    d.rounded_rectangle((70, y, W - 70, y + 400), radius=60, fill=(12, 20, 22, A(215)))
    kt = sc.get("kicker", ""); ft = font(46, 800)
    kw = d.textlength(kt, font=ft) + 72
    d.rounded_rectangle((W / 2 - kw / 2, y + 44, W / 2 + kw / 2, y + 44 + 78), radius=39, fill=(231, 86, 32, A(255)))
    text_c(d, W / 2, y + 44 + 37, kt, ft, (255, 255, 255, A(255)))
    text_c(d, W / 2, y + 222, sc["title"], font(150), (255, 255, 255, A(255)))
    text_c(d, W / 2, y + 338, sc.get("sub", ""), font(48, 700), (255, 255, 255, A(220)))
    text_c(d, W / 2, 1790, "majasco.jp", font(40, 800), (255, 255, 255, A(200)))

def pre_card(d, pre, t):
    """前置き（①の前）。下に置く（手牌は画面の真ん中）。説明の行が時間で1行ずつ増える"""
    k = min(1, t * 4); y = 1250 + int((1 - k) * 30)
    rows = [tx for (ts, tx) in pre["lines"] if t >= ts]
    d.rounded_rectangle((40, y, W - 40, y + 150 + 92 * len(pre["lines"])), radius=44, fill=(255, 255, 255, int(240 * k)))
    ft = font(46, 800); lw = d.textlength("確認", font=ft) + 60
    d.rounded_rectangle((76, y + 36, 76 + lw, y + 36 + 76), radius=38, fill=ORANGE)
    text_c(d, 76 + lw / 2, y + 36 + 36, "確認", ft, WHITE)
    d.text((76 + lw + 24, y + 22), pre["head"], font=font(76), fill=INK)
    for n, tx in enumerate(rows):
        ft = font(40, 800)
        while d.textlength(tx, font=ft) > W - 80 - 130 and ft.size > 20: ft = font(ft.size - 1, 800)      # カードからはみ出さない（2026-11-13 ユーザーの指摘。前は28で止めていて、長い行が右へはみ出した）
        yy = y + 150 + n * 92
        d.ellipse((80, yy + 14, 80 + 22, yy + 14 + 22), fill=GREEN)
        d.text((120, yy), tx, font=ft, fill=INK if n < len(rows) - 1 or n == 0 else GREEN)

_bub = {}
def bubble(d, tx, k):
    """発声の吹き出し。オレンジの地を、しっぽまで白い枠でぐるりと囲む（2026-11-13 ユーザーの指定「オレンジの吹き出しを白枠で囲うように綺麗に。これから使う吹き出しもすべて」）。
    しっぽだけ枠が無い・ふちがぎざぎざ、にならないように、3倍の大きさで「白い形 → 少し小さいオレンジの形」を描いてから縮める"""
    a = min(1, k * 5); sc_ = .8 + .2 * a
    if tx not in _bub:
        Q = 3; ft = font(96 * Q); tmp = ImageDraw.Draw(Image.new("RGBA", (8, 8)))
        w = max(420, tmp.textlength("「" + tx + "」", font=font(96)) + 110); h = 170; B = 9; pad = 30; tail = 78
        im = Image.new("RGBA", (int((w + pad * 2) * Q), int((h + tail + pad * 2) * Q)), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
        X = lambda v: (v + pad) * Q
        def shape(g, col):      # g＝外へ広げる幅（白い枠は B、オレンジは 0）
            dr.rounded_rectangle((X(-g), X(-g), X(w + g), X(h + g)), radius=(h / 2 + g) * Q, fill=col)
            bx0, bx1, tipx, tipy = w / 2 - 152, w / 2 - 84, w / 2 - 196, h + tail - 6      # しっぽ（左下へ）
            dr.polygon([(X(bx0 - g * 1.5), X(h - 14)), (X(bx1 + g * 1.9), X(h - 14)), (X(tipx - g * 1.25), X(tipy + g * 1.9))], fill=col)
        shape(B, (255, 255, 255, 255)); shape(0, (231, 86, 32, 255))
        l, t, r, b_ = dr.textbbox((0, 0), "「" + tx + "」", font=ft)
        dr.text((X(w / 2) - (r - l) / 2 - l, X(h / 2) - 4 * Q - (b_ - t) / 2 - t), "「" + tx + "」", font=ft, fill=(255, 255, 255, 255))
        _bub[tx] = (im.resize((im.width // Q, im.height // Q), Image.LANCZOS), w, h, pad)
    im, w, h, pad = _bub[tx]
    if sc_ < .999: im = im.resize((max(1, int(im.width * sc_)), max(1, int(im.height * sc_))), Image.LANCZOS)
    if a < 1: im = im.copy(); im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
    cx, cy = W / 2, 1060
    d._image.alpha_composite(im, (int(cx - (w / 2 + pad) * sc_), int(cy - (h / 2 + pad) * sc_)))

def summary(d, sc, k):
    a = int(240 * min(1, k * 3))
    n = len(sc["steps"]); y0 = 520
    d.rounded_rectangle((90, y0, W - 90, y0 + 150 + n * 118), radius=50, fill=(255, 255, 255, a))
    text_c(d, W / 2, y0 + 78, sc["title"], font(66), (23, 112, 131, min(255, a + 15)))
    for i, s in enumerate(sc["steps"]):
        y = y0 + 150 + i * 118
        d.ellipse((150, y, 150 + 84, y + 84), fill=(231, 86, 32, min(255, a + 15)))
        text_c(d, 192, y + 40, str(i + 1), font(56), WHITE)
        d.text((264, y - 6), s[0], font=font(66), fill=INK)
        d.text((264 + d.textlength(s[0], font=font(66)) + 20, y + 22), s[1], font=font(34, 700), fill=GREEN)

OUTRO_LINE = ("麻雀のスコア記録は", "まじゃすこ で")     # 締めの文言（2026-11-12 ユーザーの判断。どの3D動画も同じ）
_icon = {}
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


def subtitle(d, tx, k):
    """声の字幕（画面の下3分の1）。暗い四角い帯に白い字・2行まで"""
    ft = font(46, 800); a = int(235 * min(1, k * 6)); maxw = W - 2 * 90
    rows = [tx]
    if d.textlength(tx, font=ft) > maxw:      # 2行に分けるときは、真ん中にいちばん近い「、」「。」の後ろで切る（字の途中で折ると読みにくい）
        cuts = [k + 1 for k, ch in enumerate(tx[:-1]) if ch in "、。"] or [len(tx) // 2]
        c = min(cuts, key=lambda k: abs(k - len(tx) / 2)); rows = [tx[:c], tx[c:]]
        while max(d.textlength(r_, font=ft) for r_ in rows) > maxw and ft.size > 34: ft = font(ft.size - 2, 800)
    # 暗い帯に白い字（前と同じ色・同じ透け方）。角だけ丸めない（2026-11-13 ユーザーの指定「変えるのは角丸を四角角にするだけ」。白いカードにしたのは行きすぎだった）
    h = 46 + 64 * len(rows); y = 1560 - h // 2
    d.rectangle((50, y, W - 50, y + h), fill=(12, 20, 22, int(a * .86)))
    for n, r_ in enumerate(rows): text_c(d, W / 2, y + 23 + 32 + n * 64, r_, ft, (255, 255, 255, a))


def main():
    a = sys.argv[1:]
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 12
    name = a[a.index("--script") + 1] if "--script" in a else "chi"
    sc = SCRIPTS[name]
    # 声（2026-11-13〜）: --voice を付けると、narration.py の台本を VOICEVOX で読ませて入れる。手順ごとの止める長さは、声が言い終わるまでのばす
    VO = {}
    if "--voice" in a:
        import wave, narration
        vtmp = tempfile.mkdtemp()
        for seg, tx in narration.lines(name):
            wp = os.path.join(vtmp, seg + ".wav"); narration.synth(tx, wp)
            with wave.open(wp) as wf: VO[seg] = (wp, wf.getnframes() / wf.getframerate(), tx, wf.getframerate())
    need = lambda seg, pad=.35: (VO[seg][1] + pad) if seg in VO else 0.0
    starts = {}      # 声を鳴らし始める時刻（秒）
    src, out = a[0], a[1]
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
        for n, fp in enumerate(pre + [pre[-1]] * max(int(sc["pre"]["hold"] * fps), int((need("pre") + .6) * fps) - len(pre))): seq.append((fp, -4, n / fps, False))
    for i, s in enumerate(sc["steps"]):
        t = 0.0; starts[f"step{i + 1}"] = len(seq) / fps + .25
        for f in range(s[3], s[4] + 1): seq.append((f, i, t, False)); t += 1 / fps
        for _ in range(max(int(s[5] * fps), int((need(f"step{i + 1}") + .25) * fps) - (s[4] - s[3] + 1))): seq.append((s[4], i, t, True)); t += 1 / fps
    f0, f1, hold = sc["tail"]; t = 0.0; starts["tail"] = len(seq) / fps + .9
    for f in range(f0, f1 + 1): seq.append((f, -1, t, False)); t += 1 / fps
    for _ in range(max(int(hold * fps), int((need("tail") + .9) * fps) - (f1 - f0 + 1))): seq.append((f1, -1, t, True)); t += 1 / fps
    starts["outro"] = len(seq) / fps + 1.2
    outro = sorted(glob.glob(os.path.join(src, "o[0-9]*.png")))      # 締め（scene.py --anim --outro）。最後のコマで2秒止める
    odur = (len(outro) + 2 * fps) / fps
    for n, fp in enumerate(outro + [outro[-1]] * (2 * fps) if outro else []): seq.append((fp, -3, n / fps, False))
    tmp = tempfile.mkdtemp(); cache = {}; fade = None; cache_prev = None
    for n, (f, i, t, held) in enumerate(seq):
        if f not in cache:
            cache.clear(); cache[f] = Image.open(f if isinstance(f, str) else frames[min(f, len(frames) - 1)]).convert("RGBA").resize((W, H), Image.LANCZOS)
        im = cache[f].copy(); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        # 前置きの前後は、絵を重ねてつなぐ（カメラは選手の目に飛ぶので、動かすと体の中を通る）
        if n and i != seq[n - 1][1] and (i == -4 or seq[n - 1][1] == -4): fade = [cache_prev, 0]
        if fade and fade[1] < 6:
            fade[1] += 1; im = Image.blend(fade[0], im, fade[1] / 7)
        cache_prev = cache[f]
        if i == -4:
            pre_card(d, sc["pre"], t)
        elif i == -3:
            outro_card(im, t, odur)
        elif i == -2:
            title_card(d, sc, t, len(intro) / fps)
        elif i >= 0:
            s = sc["steps"][i]
            rail(d, sc["steps"], i); headline(d, i, s, t)
            if s[7] and t > .25: bubble(d, s[7], t - .25)
            if f"step{i + 1}" in VO and .25 <= t <= .25 + VO[f"step{i + 1}"][1] + .3: subtitle(d, VO[f"step{i + 1}"][2], t - .25)
        else:
            rail(d, sc["steps"], len(sc["steps"]), done_all=True)
            if t > .9: summary(d, sc, t - .9)
            if "tail" in VO and .9 <= t <= .9 + VO["tail"][1] + .3: subtitle(d, VO["tail"][2], t - .9)
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
        mix = os.path.join(tmp, "voice.wav")
        with wave.open(mix, "wb") as wf: wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(sr); wf.writeframes(buf.tobytes())
        subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"), "-i", mix,
                        "-vf", "fps=24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
        shutil.rmtree(vtmp)
    else:
        subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"),
                        "-vf", "fps=24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    shutil.rmtree(tmp); print("ok", out, len(seq), "コマ", round(len(seq) / fps, 1), "秒")

if __name__ == "__main__":
    main()
