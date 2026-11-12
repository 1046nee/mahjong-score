# -*- coding: utf-8 -*-
"""用語シリーズの作り直し（2026-11-10 ユーザーの指示）。80語を1語1本 → カテゴリごとの12本（gy-01〜12）。
卓・山・河・手牌・点棒の絵をその場で組み、動きで説明する。2〜9は特に丁寧に（ユーザーの指示）。
古い g-01〜80 は DROP で外す。
"""
from video_topics import esc, head, stage, hook, tile, article_end
import video_topics3  # noqa: data-anim / data-nums を先に足す
import make_short as ms

TOPICS = {}
DROP = [f"g-{i:02d}" for i in range(1, 81)]
G_END = (["ほかの言葉も、", "まじゃすこの記事で。"], article_end("blog-mahjong-yougo", "80語は記事で"))

ms.CSS += """
.tb { position: relative; width: 860px; height: 860px; margin: 0 auto; background: #2E7D5B; border-radius: 46px; box-shadow: inset 0 0 0 16px #24664A, 0 20px 50px rgba(16,40,36,.2); overflow: hidden; }
.tb .side { position: absolute; inset: 0; }
.tb .ab { position: absolute; }
.tb .ab img { display: block; }
.tb .lab { position: absolute; font-size: 36px; font-weight: 900; color: #fff; background: rgba(0,0,0,.35); border-radius: 14px; padding: 4px 16px; white-space: nowrap; }
.tb .ctr { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; font-weight: 900; }
.hl { position: absolute; border: 7px solid #E75620; border-radius: 12px; box-shadow: 0 0 0 4px rgba(231,86,32,.25); }
.term { display: inline-flex; align-items: baseline; gap: 18px; background: #fff; border-radius: 26px; padding: 14px 34px; box-shadow: 0 14px 34px rgba(16,40,36,.14); }
.term b { font-size: 76px; font-weight: 900; color: #1F2A28; }
.term span { font-size: 44px; font-weight: 900; color: #E75620; }
.stk { position: relative; display: inline-block; width: 340px; height: 30px; background: #FAFAF6; border: 2px solid #A79E87; border-radius: 15px; margin: 6px 0; }
.stk i { position: absolute; top: 50%; width: 12px; height: 12px; margin-top: -6px; border-radius: 50%; }
.cnt { display: inline-block; font-size: 40px; font-weight: 900; color: #fff; background: #1F2A28; border-radius: 999px; padding: 6px 24px; }
.pl { position: absolute; font-size: 40px; font-weight: 900; padding: 8px 20px; border-radius: 16px; background: #fff; color: #1F2A28; white-space: nowrap; }
.pl.me { background: #E75620; color: #fff; }
.tiles { display: flex; gap: 3px; justify-content: center; align-items: flex-end; }
.tiles img { display: block; }
"""

# ---------------- 部品 ----------------
def T(c, w):
    return tile(c, round(w * 1.4) if "yoko" in c else w)

def tiles(cs, w=60, gap=3, hl=(), hlc="#E75620", dim=()):
    out = ""
    for i, c in enumerate(cs):
        st = f"outline:6px solid {hlc};outline-offset:2px;border-radius:8px;" if i in hl else ""
        if i in dim: st += "opacity:.3;"
        out += f'<span style="display:inline-block;{st}">{T(c, w)}</span>'
    return f'<div class="tiles" style="gap:{gap}px">{out}</div>'

def term(kj, ym):
    return f'<div class="mid"><span class="term"><b>{esc(kj)}</b><span>{esc(ym)}</span></span></div>'

def term2(k1, y1, k2, y2):
    """言葉2つを横に並べる（1行に収まる大きさ）"""
    one = lambda k, y: f'<span class="term" style="padding:12px 24px"><b style="font-size:58px">{esc(k)}</b><span style="font-size:34px">{esc(y)}</span></span>'
    return f'<div class="mid" style="display:flex;gap:18px;justify-content:center;white-space:nowrap">{one(k1, y1)}{one(k2, y2)}</div>'

def note(tx):
    return f'<div class="note">{tx}</div>'

def stick(kind):
    """点棒（自作の絵）。kind = 100 / 1000 / 5000 / 10000"""
    if kind == 100:
        dots = "".join(f'<i style="left:{70 + k * 28}px;background:#1F2A28;width:9px;height:9px;margin-top:-4.5px"></i>' for k in range(8))
    elif kind == 1000:
        dots = '<i style="left:164px;background:#C62828"></i>'
    elif kind == 5000:
        dots = "".join(f'<i style="left:{x}px;background:{c}"></i>' for x, c in ((120, "#1F2A28"), (164, "#C62828"), (208, "#1F2A28")))
    else:
        dots = "".join(f'<i style="left:{x}px;background:{c}"></i>' for x, c in ((100, "#1F2A28"), (132, "#1F2A28"), (164, "#C62828"), (196, "#1F2A28"), (228, "#1F2A28")))
    return f'<span class="stk">{dots}</span>'

def sc(title, *parts, top_term=None):
    """場面。parts = [(ずれ, 上の位置, HTML) or (ずれ, 上の位置, HTML, 動き)]"""
    def mk(a, b):
        els = [head(a, b, title)]
        for p in parts:
            d, t, h = p[:3]
            els.append(stage(a + d, b, h, top=t, anim=p[3] if len(p) > 3 else "up"))
        return els
    return mk

# ---- 卓（上から見た図）。下＝自分 ----
TBW = 860
WALL_Y = 672  # 山の位置。17幢×28px の半分（238）より中心（430）から離す＝4辺の山が角で重ならない（2026-11-11）
def _side(rot, inner):
    return f'<div class="side" style="transform:rotate({rot}deg)">{inner}</div>'

def wall_row(n=17, w=28, y=WALL_Y, hl=(), hlc="#E75620", up=(), dim=(), cls=""):
    """自分の前の山（2段）。上から見るので1幢＝裏の牌1枚で描く。hl は橙の枠、up は表を向けた牌 {番号: 牌}"""
    x0 = (TBW - n * w) // 2
    out = ""
    for k in range(n):
        c = up.get(k, "back") if isinstance(up, dict) else "back"
        st = "opacity:.25;" if k in dim else ""
        out += f'<div class="ab {cls}" style="left:{x0 + k * w}px;top:{y}px;{st}">{tile(c, w - 2)}</div>'
    if hl:
        a_, b_ = min(hl), max(hl)
        out += f'<div class="hl" style="left:{x0 + a_ * w - 8}px;top:{y - 8}px;width:{(b_ - a_ + 1) * w + 10}px;height:{round((w - 2) * 89 / 62) + 14}px"></div>'
    return out

def table(sides=None, center="", extra=""):
    """sides = {0: 下（自分）, 90: 左, 180: 上, 270: 右} の中身（自分の向きで書く）"""
    inner = "".join(_side(r, h) for r, h in (sides or {}).items())
    return f'<div class="tb">{inner}<div class="ctr">{center}</div>{extra}</div>'

def walls(**kw):
    return {r: wall_row(**kw) for r in (0, 90, 180, 270)}

def river(cs, w=40, y=470, per=6):
    x0 = (TBW - per * w) // 2
    out = ""
    for i, c in enumerate(cs):
        out += f'<div class="ab" style="left:{x0 + (i % per) * w}px;top:{y + (i // per) * round(w * 1.45)}px">{T(c, w - 2)}</div>'
    return out

# ======================= 1 牌の種類 =======================
def gy01():
    vis = tiles(["m1", "p5", "s9", "z1", "z5", "z7"], 120)
    allt = [f"{k}{i}" for k in "mps" for i in range(1, 10)] + [f"z{i}" for i in range(1, 8)]
    yao = [i for i, c in enumerate(allt) if c[0] == "z" or c[1] in "19"]
    rows = lambda hl, dim: "".join(tiles(allt[r * 9:(r + 1) * 9] if r < 3 else allt[27:], 86, hl=[i - r * 9 for i in hl if r * 9 <= i < (r + 1) * 9] if r < 3 else [i - 27 for i in hl if i >= 27],
                                         dim=[i - r * 9 for i in dim if r * 9 <= i < (r + 1) * 9] if r < 3 else [i - 27 for i in dim if i >= 27]) + '<div style="height:18px"></div>' for r in range(4))
    return [(["麻雀の牌の呼び方、", "全部言える？", "8つの言葉で整理します。"], hook("麻雀用語", "牌の呼び方\n8つ", vis, g=False)),
            (["数字の書いてある牌が、数牌。", "萬子・筒子・索子の3種類に、", "1から9まであります。"],
             sc("数牌", (.2, 330, term("数牌", "シューパイ")), (.6, 500, "".join(tiles([f"{k}{i}" for i in range(1, 10)], 90) + '<div style="height:20px"></div>' for k in "mps")))),
            (["数字のない牌が、字牌。", "東南西北の4つが風牌、", "白・發・中の3つが三元牌です。"],
             sc("字牌", (.2, 330, term("字牌", "ジハイ")), (.6, 520, '<div class="mid"><p class="lbl">風牌（フォンパイ）</p></div>' + tiles(["z1", "z2", "z3", "z4"], 130)),
                (1.4, 860, '<div class="mid"><p class="lbl">三元牌（サンゲンパイ）</p></div>' + tiles(["z5", "z6", "z7"], 130)))),
            (["一と九と字牌をまとめて、", "么九牌と呼びます。", "国士無双やチャンタで使う牌です。"],
             sc("么九牌", (.2, 330, term("么九牌", "ヤオチューハイ")), (.6, 500, rows(yao, [])))),
            (["反対に、二から八の数牌が、", "中張牌。", "タンヤオはこの牌だけで作ります。"],
             sc("中張牌", (.2, 330, term("中張牌", "チュンチャンパイ")), (.6, 500, rows([i for i in range(34) if i not in yao], yao)))),
            (["風牌のうち、", "その場の風が場風牌、", "自分の席の風が自風牌。", "どちらも3枚で1翻です。"],
             sc("場風牌と自風牌", (.2, 330, '<div class="mid">' + term("圏風牌", "チャンフォンパイ") + '<div style="height:16px"></div>' + term("門風牌", "メンフォンパイ") + "</div>"),
                (.9, 640, note("東場なら<b>東</b>が場風牌<br>南家なら<b>南</b>が自風牌<br>ふつうは「場風」「自風」と呼ぶ")))),
            G_END]
TOPICS["gy-01"] = gy01

# ======================= 2 打つ前の準備 =======================
def gy02():
    import random
    rnd = random.Random(7)
    vis = table(walls(), center='<div style="font-size:44px">山ができるまで</div>')
    def shuffle(a, b):
        out = ""
        for k in range(36):
            x0, y0 = rnd.randint(150, 650), rnd.randint(150, 650)
            x1, y1 = rnd.randint(150, 650), rnd.randint(150, 650)
            r0, r1 = rnd.randint(0, 180), rnd.randint(180, 540)
            out += (f'<div class="ab" data-anim="{a + .4},{b - .3},left,{x0},{x1},px;{a + .4},{b - .3},top,{y0},{y1},px;{a + .4},{b - .3},rotate,{r0},{r1},deg" '
                    f'style="left:{x0}px;top:{y0}px">{tile("back", 46)}</div>')
        return [head(a, b, "洗牌"), stage(a + .1, b, term("洗牌", "シーパイ"), top=300), stage(a + .3, b, table(extra=out), top=460)]
    def build(a, b):
        sides = {}
        for r in (0, 90, 180, 270):
            row = ""
            x0 = (TBW - 17 * 28) // 2
            for k in range(17):
                t0 = a + .5 + k * .08
                row += f'<div class="ab" data-in="{t0:.2f}" data-a="pop" style="left:{x0 + k * 28}px;top:{WALL_Y}px">{tile("back", 26)}</div>'
            sides[r] = row
        return [head(a, b, "砌牌 → 壁牌"), stage(a + .1, b, term2("砌牌", "チーパイ", "壁牌", "ピーパイ"), top=300),
                stage(a + .3, b, table(sides, center='<div style="font-size:40px">2段に積んで<br>17幢ずつ</div>'), top=460)]
    def dou(a, b):
        sides = walls()
        sides[0] = wall_row(hl=(8,))
        return [head(a, b, "幢"), stage(a + .1, b, term("幢", "トン"), top=300), stage(a + .3, b, table(sides, center='<div style="font-size:40px">上下2枚で<br><b style="color:#FFD27A">1幢</b></div>'), top=460),
                stage(a + 1.2, b, note("1人の前に<b>17幢</b>＝34枚。4人で<b>136枚</b>"), top=1340)]
    def kaimon(a, b):
        sides = walls()
        sides[270] = wall_row(hl=(10,), dim=())
        dice = '<div style="display:flex;gap:16px;justify-content:center">' + tile("d3", 70) + tile("d4", 70) + "</div><div style='font-size:36px;margin-top:10px'>3＋4＝7</div>"
        return [head(a, b, "開門"), stage(a + .1, b, term("開門", "カイメン"), top=300), stage(a + .3, b, table(sides, center=dice), top=460),
                stage(a + 1.2, b, note("出た目で<b>山を割る場所</b>が決まる"), top=1340)]
    def haipai(a, b):
        hand_ = ["m1", "m4", "p9", "z2", "s3", "m7", "z5", "p2", "s8", "m9", "p6", "s3", "z7"]
        steps = '<div class="mid" style="display:flex;gap:16px;justify-content:center">' + "".join(
            f'<span class="cnt" data-in="{a + .6 + i * .7:.1f}" data-a="pop">{t}</span>' for i, t in enumerate(["4枚", "4枚", "4枚", "1枚"])) + "</div>"
        return [head(a, b, "配牌"), stage(a + .1, b, term("配牌", "ハイパイ"), top=300), stage(a + .3, b, steps, top=480),
                stage(a + 3.4, b, tiles(hand_, 64), top=640, anim="fade"), stage(a + 3.8, b, note("4枚ずつ3回、最後に1枚。<b>13枚</b>で始まる<br>（親は14枚）"), top=860)]
    def wanpai(a, b):
        sides = walls()
        sides[0] = wall_row(hl=tuple(range(0, 7)), up={2: "p3"})   # ドラ表示牌は嶺上牌（0・1）のとなり＝時計回りに5幢目（2026-11-13 ユーザーの指摘。前は4で、時計回りに3幢目になっていた）
        return [head(a, b, "王牌"), stage(a + .1, b, term("王牌", "ワンパイ"), top=300),
                stage(a + .3, b, table(sides, center='<div style="font-size:36px">山の最後の<br><b style="color:#FFD27A">7幢＝14枚</b>は<br>ツモらない</div>'), top=460),
                stage(a + 1.4, b, note("表を向けた牌が<b>ドラ表示牌</b>"), top=1340)]
    def rinshan(a, b):
        sides = walls()
        sides[0] = wall_row(hl=(0, 1), up={2: "p3"})
        return [head(a, b, "嶺上牌"), stage(a + .1, b, term("嶺上牌", "リンシャンパイ"), top=300),
                stage(a + .3, b, table(sides, center='<div style="font-size:36px">カンをしたら<br>王牌の<b style="color:#FFD27A">端から</b><br>1枚もらう</div>'), top=460),
                stage(a + 1.4, b, note("この牌であがると<b>嶺上開花</b>（1翻）"), top=1340)]
    def ripai(a, b):
        mess = ["s3", "m7", "z2", "p6", "m1", "s8", "p2", "z5", "m4", "s3", "p9", "m9", "z7"]
        order = sorted(range(13), key=lambda i: ("mpsz".index(mess[i][0]), mess[i][1:]))
        w, gap = 66, 4
        x0 = (960 - 13 * (w + gap)) // 2
        out = ""
        for i, c in enumerate(mess):
            to = order.index(i)
            out += (f'<div class="ab" style="position:absolute;top:0;left:{x0 + i * (w + gap)}px" data-anim="{a + 1.0},{a + 2.4},left,{x0 + i * (w + gap)},{x0 + to * (w + gap)},px">{tile(c, w)}</div>')
        box = f'<div style="position:relative;height:110px">{out}</div>'
        return [head(a, b, "理牌"), stage(a + .1, b, term("理牌", "リーパイ"), top=300), stage(a + .3, b, box, top=560),
                stage(a + 2.6, b, note("配られた牌を、<b>種類と数字の順</b>に並べかえる"), top=760)]
    return [(["麻雀の準備、", "言葉で言える？", "山ができるまでを順に見ます。"], hook("麻雀用語", "山ができるまで\nの9語", vis, g=False)),
            (["まず、全部の牌を裏にして", "かき混ぜます。", "これが洗牌です。"], shuffle),
            (["混ぜた牌を、2段に積んで、", "自分の前に山を作ります。", "積むことが砌牌、", "できた山が壁牌です。"], build),
            (["上下2枚の1組を、", "幢と数えます。", "1人の前に17幢、", "4人で136枚になります。"], dou),
            (["サイコロを振って、", "出た目で、", "どこから取るかを決めます。", "これが開門です。"], kaimon),
            (["割ったところから、", "4枚ずつ3回、", "最後に1枚取って13枚。", "これが配牌です。"], haipai),
            (["山の最後の7幢、", "14枚は王牌。", "ここはツモらずに残しておき、", "ドラ表示牌をめくります。"], wanpai),
            (["カンをしたときは、", "王牌の端から1枚もらいます。", "これが嶺上牌です。"], rinshan),
            (["最後に、配られた牌を", "見やすく並べかえます。", "これが理牌。", "これで準備完了です。"], ripai),
            G_END]
TOPICS["gy-02"] = gy02

# ======================= 3 席と親の呼び方 =======================
def seat_table(me="東", hl=(), labels=None, chicha=False):
    pos = {"下": (330, 740), "右": (640, 380), "上": (330, 40), "左": (0, 380)}
    order = ["下", "右", "上", "左"]
    winds = ["東", "南", "西", "北"]
    k0 = winds.index(me)
    out = ""
    for i, p in enumerate(order):
        w = winds[(k0 + i) % 4]
        x, y = pos[p]
        lab = (labels or {}).get(p, f"{w}家").replace("（", "<br>（")
        cls = "pl me" if p == "下" else "pl"
        st = "outline:6px solid #E75620;" if p in hl else ""
        out += f'<div class="{cls}" style="left:{x + 20}px;top:{y}px;text-align:center;line-height:1.25;{st}">{lab}</div>'
    cm = f'<div class="ab" style="left:{350}px;top:{660}px">{tile("chicha", 150)}</div>' if chicha else ""
    return f'<div class="tb" style="height:860px">{out}{cm}<div class="ctr" style="font-size:40px">上から見た卓</div></div>'

def gy03():
    vis = seat_table("東")
    return [(["上家、下家、対面。", "どの席のことか分かる？", "席と親の呼び方を整理します。"], hook("麻雀用語", "席の呼び方\n9語", vis, g=False)),
            (["半荘の最初の親が、起家です。", "起家の前には、", "起家マークを置きます。"],
             sc("起家", (.1, 300, term("起家", "チーチャ")), (.3, 460, seat_table("東", hl=("下",), labels={"下": "起家（最初の親）"}, chicha=True)))),
            (["親の正式な呼び方が荘家、", "子は散家です。", "親は点数が1.5倍になります。"],
             sc("荘家と散家", (.1, 300, term2("荘家", "チャンチャ", "散家", "サンチャ")),
                (.3, 460, seat_table("東", labels={"下": "荘家（親）", "右": "散家", "上": "散家", "左": "散家"})))),
            (["親が東家で、", "そこから右回りに、", "南家、西家、北家です。"],
             sc("東家・南家・西家・北家", (.3, 330, seat_table("東", labels={"下": "東家（親）", "右": "南家", "上": "西家", "左": "北家"})),
                (1.2, 1230, note("親の右どなりが<b>南家</b>、その次が<b>西家</b>")))),
            (["自分から見て、", "左の人が上家、", "右の人が下家、", "正面の人が対面です。"],
             sc("上家・下家・対面", (.3, 330, seat_table("東", labels={"下": "あなた", "右": "下家（シモチャ）", "上": "対面（トイメン）", "左": "上家（カミチャ）"}, hl=("左", "右", "上"))),
                (1.4, 1230, note("チーができるのは<b>上家</b>の捨てた牌だけ")))),
            (["自分のことを自家、", "ほかの3人をまとめて", "他家と呼びます。"],
             sc("自家と他家", (.1, 300, term2("自家", "ジチャ", "他家", "ターチャ")),
                (.3, 460, seat_table("東", labels={"下": "自家", "右": "他家", "上": "他家", "左": "他家"})))),
            G_END]
TOPICS["gy-03"] = gy03

# ======================= 4 点棒と局の進み方 =======================
def kyoku_flow(items, a, step=.7):
    out = ""
    for i, (tx, c) in enumerate(items):
        out += f'<span class="cnt" data-in="{a + .5 + i * step:.2f}" data-a="pop" style="background:{c};margin:8px">{tx}</span>'
        if i < len(items) - 1:
            out += f'<span data-in="{a + .5 + i * step + .3:.2f}" style="font-size:46px;font-weight:900;color:#5F6E6B">→</span>'
    return f'<div class="mid" style="line-height:2.4">{out}</div>'

def gy04():
    vis = '<div class="vcard mid">' + stick(10000) + "<br>" + stick(5000) + "<br>" + stick(1000) + "<br>" + stick(100) + "</div>"
    def haikyu(a, b):
        rows = [(10000, 1, "10,000点"), (5000, 2, "5,000点 × 2"), (1000, 4, "1,000点 × 4"), (100, 10, "100点 × 10")]
        out = "".join(f'<div data-in="{a + .5 + i * .5:.1f}" data-a="left" style="display:flex;align-items:center;gap:20px;margin:6px 0">{stick(k)}<span class="yk" style="font-size:40px;font-weight:900">{t}</span></div>' for i, (k, n, t) in enumerate(rows))
        return [head(a, b, "配給原点"), stage(a + .1, b, term("配給原点", "はいきゅうげんてん"), top=300),
                stage(a + .3, b, f'<div class="vcard">{out}</div>', top=460), stage(a + 2.8, b, note("最初に配られる持ち点。ふつう<b>25,000点</b>"), top=1010)]
    def renchan(a, b):
        return [head(a, b, "連荘"), stage(a + .1, b, term("連荘", "レンチャン"), top=300),
                stage(a + .3, b, kyoku_flow([("東1局", "#177083"), ("親があがる", "#E75620"), ("東1局 1本場", "#177083")], a), top=520),
                stage(a + 2.6, b, note("親があがるか、流局で親がテンパイなら<br><b>同じ人がもう1回親</b>"), top=860)]
    def rinchan(a, b):
        return [head(a, b, "輪荘"), stage(a + .1, b, term("輪荘", "ロンチャン"), top=300),
                stage(a + .3, b, kyoku_flow([("東1局", "#177083"), ("子があがる", "#5F6E6B"), ("東2局", "#177083")], a), top=520),
                stage(a + 2.6, b, note("親が<b>右どなりへ</b>うつる"), top=860)]
    def honba(a, b):
        sticks = "".join(f'<div data-in="{a + .8 + i * .6:.1f}" data-a="pop">{stick(100)}</div>' for i in range(3))
        return [head(a, b, "本場と積み棒"), stage(a + .1, b, term2("本場", "ほんば", "積み棒", "つみぼう"), top=300),
                stage(a + .3, b, f'<div class="vcard mid"><div class="cnt" style="margin-bottom:14px">3本場</div>{sticks}</div>', top=460),
                stage(a + 2.8, b, note("連荘や流局のたびに100点棒を1本。<br>あがった人は<b>1本につき300点</b>多くもらう"), top=980)]
    def kyotaku(a, b):
        tb_ = table(walls(), center=f'<div data-in="{a + .8}" data-a="pop">{stick(1000)}</div><div style="font-size:36px;margin-top:10px">リーチ棒</div>')
        return [head(a, b, "供託"), stage(a + .1, b, term("供託", "きょうたく"), top=300), stage(a + .3, b, tb_, top=460),
                stage(a + 1.6, b, note("場に出したリーチ棒。<b>次にあがった人</b>がもらう"), top=1340)]
    def hako(a, b):
        return [head(a, b, "ハコ"), stage(a + .1, b, term("箱", "ハコ"), top=300),
                stage(a + .3, b, f'<div class="vcard mid"><div class="big" data-nums="{a + .6},{a + 2.2},8000,-3000,0" data-post="点" data-color>8,000点</div></div>', top=500),
                stage(a + 2.4, b, note("持ち点が0より少なくなること。<br>そこで終わる（<b>トビ</b>）かは、打つ前に決める"), top=860)]
    return [(["麻雀の点棒、", "何本もらうか知ってる？", "局の進み方とあわせて説明します。"], hook("麻雀用語", "点棒と\n局の進み方", vis, g=False)),
            (["最初に配られる持ち点が、", "配給原点。", "25,000点なら、", "1万点が1本、5千点が2本、", "千点が4本、百点が10本です。"], haikyu),
            (["親があがると、", "同じ人がもう1回親をします。", "これが連荘です。"], renchan),
            (["子があがると、", "親は右どなりへ移ります。", "これが輪荘です。"], rinchan),
            (["連荘のたびに、", "百点棒を1本ずつ置きます。", "これが積み棒で、", "その数が本場。", "1本につき300点がプラスされます。"], honba),
            (["リーチのときに出した千点棒は、", "場に残ります。", "これが供託で、", "次にあがった人がもらいます。"], kyotaku),
            (["持ち点が0より少なくなるのが、", "ハコ。", "そこで終わるかは、", "打つ前に決めておきましょう。"], hako),
            G_END]
TOPICS["gy-04"] = gy04

# ======================= 5 1巡の動き =======================
H13 = ["m2", "m3", "m4", "p5", "p6", "p7", "s3", "s4", "s5", "m6", "m7", "z1", "z1"]
def hand_line(cs, w=62, extra=None, extra_hl=False):
    h = tiles(cs, w)
    if extra:
        h = h.replace('</div>', f'<span style="display:inline-block;margin-left:22px;{"outline:6px solid #E75620;outline-offset:2px;border-radius:8px" if extra_hl else ""}">{T(extra, w)}</span></div>', 1)
    return h

def gy05():
    vis = hand_line(H13, 60, "m8", True)
    def mouda(a, b):
        tb_ = table({0: wall_row(), 90: wall_row(), 180: wall_row(), 270: wall_row()},
                    extra=(f'<div class="ab" style="left:{(TBW - 28) // 2 + 28 * 3}px;top:{WALL_Y}px" data-anim="{a + .6},{a + 1.4},top,{WALL_Y},820,px;{a + .6},{a + 1.4},opacity,1,0,">{tile("back", 26)}</div>'
                           f'<div class="ab" data-in="{a + 2.0}" data-a="pop" style="left:{(TBW - 6 * 40) // 2}px;top:470px">{tile("s9", 38)}</div>'))
        return [head(a, b, "摸打"), stage(a + .1, b, term("摸打", "モウダ"), top=300), stage(a + .3, b, tb_, top=460),
                stage(a + 1.0, b, note("<b>1枚引いて（ツモ）</b>→<b>1枚捨てる（打牌）</b>のくり返し"), top=1340)]
    def tsumo(a, b):
        return [head(a, b, "自摸"), stage(a + .1, b, term("自摸", "ツモ"), top=300), stage(a + .3, b, hand_line(H13, 60), top=520),
                stage(a + 1.0, b, '<div class="mid">' + tile("m8", 80) + '<div class="cnt" style="margin-top:10px">山から1枚</div></div>', top=700, anim="pop"),
                stage(a + 1.8, b, note("引いた牌であがると<b>ツモあがり</b>"), top=1000)]
    def dahai(a, b):
        return [head(a, b, "打牌"), stage(a + .1, b, term("打牌", "ダハイ"), top=300), stage(a + .3, b, hand_line(H13[:12] + ["m8"], 60), top=520),
                stage(a + 1.0, b, '<div class="mid">' + tile("z1", 80) + '<div class="cnt" style="margin-top:10px">河へ捨てる</div></div>', top=700, anim="pop"),
                stage(a + 1.8, b, note("捨てた牌が並ぶ場所が<b>河（ホー）</b>"), top=1000)]
    def hora(a, b):
        return [head(a, b, "和了と栄和"), stage(a + .1, b, term2("和了", "ホーラ", "栄和", "ロンホー"), top=300),
                stage(a + .3, b, hand_line(H13, 58, "m8", True), top=500),
                stage(a + 1.0, b, '<div class="vcard">' + vt2([("和了（あがり）", "形が完成すること"), ("自摸和（ツモ）", "自分で引いてあがる"), ("栄和（ロン）", "人の捨て牌であがる")]) + "</div>", top=700)]
    def touhai(a, b):
        return [head(a, b, "倒牌"), stage(a + .1, b, term("倒牌", "トウハイ"), top=300),
                stage(a + .3, b, f'<div data-anim="{a + .6},{a + 1.4},rotate,-80,0,deg" style="transform-origin:bottom">{hand_line(H13, 58, "m8", True)}</div>', top=520),
                stage(a + 1.6, b, note("あがったら<b>手牌を倒して</b>みんなに見せる"), top=800)]
    def haitei(a, b):
        sides = {r: wall_row(dim=tuple(range(0, 17))) for r in (90, 180, 270)}
        sides[0] = wall_row(dim=tuple(range(1, 17)), hl=(0,))
        tb_ = table(sides, center='<div style="font-size:36px">山の<br><b style="color:#FFD27A">最後の1枚</b></div>')
        return [head(a, b, "海底牌と河底牌"), stage(a + .1, b, '<div class="mid">' + term("海底牌", "ハイテイハイ") + "</div>", top=300), stage(a + .3, b, tb_, top=460),
                stage(a + 1.4, b, note("最後のツモ＝<b>海底牌</b>、最後の捨て牌＝<b>河底牌</b><br>これであがると1翻（海底・河底）"), top=1330)]
    return [(["ツモ、ロン、ダハイ。", "1巡の動きを、", "言葉で説明できる？"], hook("麻雀用語", "1巡の動き\n8語", vis, g=False)),
            (["麻雀は、1枚引いて1枚捨てる、", "のくり返し。", "これを摸打と言います。"], mouda),
            (["山から1枚引くのが、", "ツモ。", "引いた牌であがるのも、", "ツモと言います。"], tsumo),
            (["手牌から1枚を", "河に捨てるのが、打牌です。"], dahai),
            (["形が完成することが和了。", "自分で引けばツモ、", "人の捨て牌ならロン。", "ロンの正式な言い方が栄和です。"], hora),
            (["あがったら、", "手牌を倒してみんなに見せます。", "これが倒牌です。"], touhai),
            (["山の最後の1枚が海底牌、", "最後の捨て牌が河底牌。", "これであがると1翻つきます。"], haitei),
            G_END]
TOPICS["gy-05"] = gy05

def vt2(rows):
    return '<table class="vt">' + "".join(f'<tr><td style="color:#E75620">{esc(l)}</td><td class="r">{esc(r)}</td></tr>' for l, r in rows) + "</table>"

# ======================= 6 鳴き =======================
def meld_demo(title, kj, ym, from_, before, meld, say, a, b, desc):
    """from_ = 誰の捨て牌か。before = 手の牌、meld = 鳴いた形（横向きの牌つき）"""
    return [head(a, b, title), stage(a + .1, b, term(kj, ym), top=300),
            stage(a + .3, b, f'<div class="mid"><span class="cnt" style="background:#5F6E6B">{from_}</span></div>', top=470),
            stage(a + .6, b, tiles(before, 100), top=560),
            stage(a + 1.4, b, f'<div class="mid"><span class="ans">{say}</span></div>', top=730, anim="pop"),
            stage(a + 2.0, b, tiles(meld, 104), top=900, anim="pop"),
            stage(a + 2.6, b, note(desc), top=1110)]

def gy06():
    vis = tiles(["m4-yoko", "m5", "m6"], 110) + '<div style="height:20px"></div>' + tiles(["p5", "p5-yoko", "p5"], 110)
    return [(["チー、ポン、カン。", "違いと、横に倒す牌の意味、", "分かる？"], hook("麻雀用語", "鳴きの8語", vis, g=False)),
            (["人の捨てた牌をもらって、", "組を作ることを、副露。", "ふつうは、鳴くと言います。"],
             sc("副露", (.1, 300, term("副露", "フーロ")), (.5, 500, note("人の捨て牌をもらって<b>組を作る</b>こと。<br>もらった牌は<b>横に倒して</b>、誰からもらったか分かるようにする")))),
            (["チーは、左の人、上家の牌で、", "順番の組を作ること。", "上家の牌しかチーできません。"],
             lambda a, b: meld_demo("チー", "吃", "チー", "上家が四萬を捨てた", ["m5", "m6"], ["m4-yoko", "m5", "m6"], "チー！", a, b, "左の人からもらったので<b>左の牌を横に</b>")),
            (["ポンは、誰の牌でもOK。", "同じ牌3枚の組を作ります。", "対面からなら、真ん中を倒します。"],
             lambda a, b: meld_demo("ポン", "碰", "ポン", "対面が五筒を捨てた", ["p5", "p5"], ["p5", "p5-yoko", "p5"], "ポン！", a, b, "正面からもらったので<b>真ん中を横に</b>")),
            (["カンは、同じ牌4枚の組。", "持っている3枚に、", "人の捨てた4枚目をもらうのが、", "大明槓です。"],
             lambda a, b: meld_demo("大明槓", "大明槓", "ダイミンカン", "下家が中を捨てた", ["z7", "z7", "z7"], ["z7", "z7", "z7", "z7-yoko"], "カン！", a, b, "右の人からなので<b>右の牌を横に</b>。王牌から1枚補う")),
            (["自分で4枚そろえたら、", "暗槓。", "両はしを裏にして置きます。", "門前のままです。"],
             sc("暗槓", (.1, 300, term("暗槓", "アンカン")), (.4, 480, tiles(["z1", "z1", "z1"], 80) + '<div style="height:14px"></div>' + tiles(["z1"], 80, hl=(0,))),
                (1.4, 720, tiles(["back", "z1", "z1", "back"], 90), "pop"), (2.0, 920, note("両はしを裏に。<b>鳴いたことにならない</b>")))),
            (["ポンした組に、", "自分で引いた4枚目を足すのが、", "加槓です。"],
             sc("加槓", (.1, 300, term("加槓", "カカン")), (.4, 500, tiles(["z6", "z6-yoko", "z6"], 84)),
                (1.2, 640, f'<div class="mid">{tile("z6", 80)}<div class="cnt" style="margin-top:8px">自分で引いた</div></div>', "pop"),
                (2.0, 860, '<div class="tiles" style="align-items:flex-end">' + T("z6", 84) + '<span style="display:inline-flex;flex-direction:column;gap:2px">' + T("z6-yoko", 84) + T("z6-yoko", 84) + "</span>" + T("z6", 84) + "</div>", "pop"),
                (2.6, 1080, note("横にした牌の上に<b>重ねる</b>")))),
            (["その加槓の牌で、", "ほかの人がロンできるのが搶槓。", "1翻の役です。"],
             sc("搶槓", (.1, 300, term("搶槓", "チャンカン")), (.5, 500, note("加槓で出した<b>4枚目</b>が<br>ほかの人の<b>あがり牌</b>だったら")),
                (1.4, 760, f'<div class="mid"><span class="ans">ロン！</span></div>', "pop"), (2.0, 940, note("カンは成立せず、<b>搶槓で1翻</b>")))),
            G_END]
TOPICS["gy-06"] = gy06

# ======================= 7 テンパイまわり =======================
TEN = ["m2", "m3", "m4", "p5", "p6", "p7", "s3", "s4", "s5", "m6", "m7", "z1", "z1"]
def gy07():
    vis = tiles(TEN, 58) + '<div class="mid" style="margin-top:20px">' + tile("m5", 80) + tile("m8", 80) + "</div>"
    return [(["テンパイ、ノーテン、フリテン。", "正しく説明できる？"], hook("麻雀用語", "テンパイまわり\n6語", vis, g=False)),
            (["鳴いていない状態が、門前。", "リーチやピンフなど、", "門前でしかつかない役があります。"],
             sc("門前", (.1, 300, term("門前", "メンゼン")), (.4, 480, tiles(TEN, 58)), (1.0, 680, note("鳴いていない＝<b>門前</b>")))),
            (["あと1枚であがれる状態が、", "テンパイ。", "この手は、五萬か八萬であがれます。"],
             sc("聴牌", (.1, 300, term("聴牌", "テンパイ")), (.4, 480, tiles(TEN, 58, hl=(9, 10))),
                (1.2, 660, '<div class="mid">' + tile("m5", 90) + tile("m8", 90) + '<div class="cnt" style="margin-top:10px">待ち</div></div>', "pop"))),
            (["テンパイしていないのがノーテン。", "流局のときに、", "点を払うことになります。"],
             sc("不聴", (.1, 300, term("不聴", "ノーテン")), (.4, 480, tiles(["m1", "m4", "m8", "p2", "p6", "p9", "s1", "s5", "z2", "z3", "z5", "z6", "z7"], 58)),
                (1.0, 680, note("あと2枚以上必要＝<b>ノーテン</b>")))),
            (["役がなくても、", "形がテンパイなら形式テンパイ。", "流局のときは、テンパイあつかいです。"],
             sc("形式聴牌", (.1, 300, term("形式聴牌", "けいしきテンパイ")), (.5, 500, note("役がなくてあがれない手でも、<br>形がテンパイなら<b>流局でテンパイと言える</b>")))),
            (["テンパイして宣言するのが、", "リーチ。", "千点を場に出して、1翻つきます。"],
             sc("立直", (.1, 300, term("立直", "リーチ")), (.4, 480, f'<div class="vcard mid">{stick(1000)}<div class="yk" style="font-size:40px;font-weight:900">1,000点を出して宣言</div></div>'))),
            (["自分の河に、", "あがり牌が捨ててあると、", "フリテン。", "ロンはできず、ツモならOKです。"],
             sc("振聴", (.1, 300, term("振聴", "フリテン")), (.4, 470, tiles(TEN, 54, hl=(9, 10))),
                (1.0, 640, '<div class="mid"><div class="cnt">自分の河</div></div>' + tiles(["z3", "p1", "m8", "s9", "z6"], 64, hl=(2,), hlc="#C62828")),
                (1.8, 900, '<div class="mid"><span class="ng" style="font-size:44px">ロン ×</span>　<span class="ok" style="font-size:44px">ツモ ○</span></div>'),
                (2.4, 1040, note("八萬を自分で捨てているので<b>ロンできない</b>")))),
            G_END]
TOPICS["gy-07"] = gy07

# ======================= 8 流局 =======================
def gy08():
    vis = table({r: wall_row(dim=tuple(range(17))) for r in (0, 90, 180, 270)}, center='<div style="font-size:48px">誰もあがらず…</div>')
    def kouhai(a, b):
        sides = {r: f'<div data-anim="{a + .5},{a + 2.0},opacity,1,.15,">{wall_row()}</div>' for r in (0, 90, 180, 270)}
        return [head(a, b, "流局と荒牌平局"), stage(a + .1, b, '<div class="mid">' + term("流局", "りゅうきょく") + "</div>", top=300),
                stage(a + .3, b, table(sides, center='<div style="font-size:40px">山がなくなって<br>誰もあがれない</div>'), top=460),
                stage(a + 2.0, b, note("山が尽きて終わる＝<b>荒牌平局</b>（ホワンパイピンチュー）"), top=1340)]
    def bappu(a, b):
        return [head(a, b, "不聴罰符"), stage(a + .1, b, term("不聴罰符", "ノーテンばっぷ"), top=300),
                stage(a + .3, b, '<div class="vcard">' + vt2([("テンパイ1人", "+3,000／−1,000×3"), ("テンパイ2人", "+1,500×2／−1,500×2"),
                                                         ("テンパイ3人", "+1,000×3／−3,000"), ("全員か0人", "動かない")]).replace("<td", "<td style=\"white-space:nowrap;font-size:40px\"", 99) + "</div>", top=460),
                stage(a + 2.0, b, note("ノーテンの人が、テンパイの人に<b>合わせて3,000点</b>を払う"), top=1020)]
    def kyushu(a, b):
        h = ["m1", "m9", "p1", "p9", "s1", "z1", "z2", "z5", "z7", "m4", "p6", "s7", "s3", "m5"]
        return [head(a, b, "九種九牌"), stage(a + .1, b, term("九種九牌", "キュウシュキュウハイ"), top=300),
                stage(a + .3, b, tiles(h, 58, hl=tuple(range(9))), top=500),
                stage(a + 1.2, b, note("最初の手に<b>么九牌が9種類</b>以上。<br>最初のツモのあと、宣言すれば流局にできる"), top=700)]
    def sufon(a, b):
        rv = "".join(f'<div class="ab" data-in="{a + .5 + i * .5:.1f}" data-a="pop" style="left:{x}px;top:{y}px">{tile("z1", 56)}</div>' for i, (x, y) in enumerate(((402, 560), (560, 402), (402, 220), (240, 402))))
        return [head(a, b, "四風連打"), stage(a + .1, b, term("四風連打", "スーフーレンダ"), top=300), stage(a + .3, b, table(extra=rv), top=460),
                stage(a + 2.6, b, note("最初の1巡で、4人が<b>同じ風牌</b>を捨てたら流局"), top=1340)]
    def suucha(a, b):
        rv = "".join(f'<div class="ab" data-in="{a + .5 + i * .5:.1f}" data-a="pop" style="left:{x}px;top:{y}px;transform:rotate({r}deg)">{stick(1000)}</div>'
                     for i, (x, y, r) in enumerate(((260, 600, 0), (440, 415, 90), (260, 230, 0), (80, 415, 90))))
        return [head(a, b, "四家立直"), stage(a + .1, b, term("四家立直", "スーチャリーチ"), top=300), stage(a + .3, b, table(extra=rv), top=460),
                stage(a + 2.6, b, note("<b>4人全員</b>がリーチしたら流局"), top=1340)]
    def sukai(a, b):
        return [head(a, b, "四開槓"), stage(a + .1, b, term("四開槓", "スーカイカン"), top=300),
                stage(a + .3, b, note("<b>2人以上</b>で合わせて4回カンしたら流局<br>（1人で4回なら四槓子の役満をねらえる）"), top=500),
                stage(a + 1.2, b, tiles(["z1", "z1", "z1", "z1-yoko"], 70) + '<div style="height:14px"></div>' + tiles(["back", "p5", "p5", "back"], 70), top=780)]
    def sancha(a, b):
        return [head(a, b, "三家和"), stage(a + .1, b, term("三家和", "サンチャホー"), top=300),
                stage(a + .3, b, '<div class="mid">' + "".join(f'<span class="ans" data-in="{a + .5 + i * .4:.1f}" data-a="pop" style="margin:8px;font-size:56px">ロン！</span>' for i in range(3)) + "</div>", top=520),
                stage(a + 1.8, b, note("1枚の捨て牌に<b>3人が同時にロン</b>したら流局<br>（ルールによっては頭ハネ）"), top=800)]
    return [(["誰もあがらずに終わる、流局。", "途中で終わるパターンも", "全部見ていきます。"], hook("麻雀用語", "流局の8語", vis, g=False)),
            (["あがりがないまま", "局が終わるのが流局。", "山がなくなって終わるのが、", "荒牌平局です。"], kouhai),
            (["流局したら、", "ノーテンの人がテンパイの人に、", "合わせて3,000点を払います。", "これがノーテン罰符です。"], bappu),
            (["ここからは途中で流れるパターン。", "最初の手に、", "一・九・字牌が9種類あれば、", "九種九牌で流せます。"], kyushu),
            (["最初の1巡で、", "4人が同じ風牌を捨てると、", "四風連打で流局です。"], sufon),
            (["4人全員がリーチすると、", "四家立直で流局。"], suucha),
            (["2人以上で、", "合わせて4回カンすると、", "四開槓で流局です。"], sukai),
            (["1枚に3人がロンすると、", "三家和。", "途中流局があるかは、", "打つ前に決めておきましょう。"], sancha),
            G_END]
TOPICS["gy-08"] = gy08

# ======================= 9 反則 =======================
def gy09():
    vis = '<div class="mid"><span class="ans" style="background:#C62828;font-size:90px">チョンボ</span></div>'
    return [(["チョンボになるのは、どんなとき？", "反則の4語です。"], hook("麻雀用語", "反則の4語", vis, g=False)),
            (["あがっていないのに", "ロンと言ってしまうなど、", "ルール違反がチョンボ。", "正式には錯和と言います。"],
             sc("錯和（チョンボ）", (.1, 300, term("錯和", "チョンボ")), (.4, 480, tiles(TEN, 56)),
                (1.0, 660, '<div class="mid"><span class="ans">ロン！</span>　' + tile("m9", 90) + "</div>", "pop"),
                (1.8, 880, note("待ちは五萬・八萬なのに九萬でロン → <b>チョンボ</b><br>罰符はふつう<b>満貫を払う</b>")))),
            (["手牌が1枚多いのが多牌。", "14枚あるのに、", "捨て忘れたときなどに起きます。"],
             sc("多牌", (.1, 300, term("多牌", "ターハイ")), (.4, 480, tiles(TEN + ["s9"], 56, hl=(13,), hlc="#C62828")),
                (1.2, 680, '<div class="mid"><span class="cnt" style="background:#C62828">14枚</span></div>'), (1.6, 820, note("13枚のはずが<b>14枚</b>。あがれなくなる")))),
            (["反対に、1枚少ないのが少牌。", "どちらも、その局はあがれません。"],
             sc("少牌", (.1, 300, term("少牌", "ショウハイ")), (.4, 480, tiles(TEN[:12], 58)), (1.2, 680, note("13枚のはずが<b>12枚</b>。あがれなくなる")))),
            (["包は、役満を確定させる牌を", "鳴かせた人が、責任を持つ決まり。", "白と發をポンしている人に、", "中を鳴かせたら、責任払いです。"],
             sc("包（パオ）", (.1, 300, term("包", "パオ")), (.4, 480, tiles(["z5", "z5-yoko", "z5"], 70) + '<div style="height:12px"></div>' + tiles(["z6-yoko", "z6", "z6"], 70)),
                (1.4, 760, '<div class="mid"><span class="cnt" style="background:#C62828">中を捨てる</span>　' + tile("z7", 80) + "</div>", "pop"),
                (2.2, 960, note("大三元が確定 → 中を捨てた人が<b>責任払い</b>")))),
            G_END]
TOPICS["gy-09"] = gy09

# ======================= 10 手の形 =======================
HAND = [("o", ["m2", "m3", "m4"]), ("g", ["p6", "p6", "p6"]), ("o", ["s3", "s4", "s5"]), ("o", ["m6", "m7", "m8"]), ("b", ["z1", "z1"])]
def grp(groups, w=60):
    col = {"o": "#E75620", "g": "#177083", "b": "#4261AA", "": "transparent"}
    return '<div class="tiles" style="gap:14px">' + "".join(f'<span style="display:inline-flex;gap:2px;padding-bottom:10px;border-bottom:10px solid {col[c]}">' + "".join(T(t, w) for t in ts) + "</span>" for c, ts in groups) + "</div>"

def gy10():
    vis = grp(HAND, 58)
    return [(["メンツ、ジャントウ、ターツ。", "あがりの形の言葉を", "まとめて覚えます。"], hook("麻雀用語", "手の形の7語", vis, g=False)),
            (["あがりの形は、", "3枚の組が4つと、", "2枚の組が1つ。", "3枚の組が面子です。"],
             sc("面子", (.1, 300, term("面子", "メンツ")), (.4, 480, grp(HAND, 60)), (1.2, 700, note("<b>3枚の組×4</b>＋<b>2枚×1</b>＝14枚")))),
            (["面子は2種類。", "順番に並んだ組が順子、", "同じ牌3枚が刻子です。"],
             sc("順子と刻子", (.1, 300, term2("順子", "シュンツ", "刻子", "コーツ")),
                (.4, 480, tiles(["p4", "p5", "p6"], 100)), (.9, 650, tiles(["s7", "s7", "s7"], 100)),
                (1.4, 840, note("順子＝<b>連続した3枚</b>　刻子＝<b>同じ3枚</b><br>字牌は順子にならない")))),
            (["同じ牌4枚でカンした組が、", "槓子です。"],
             sc("槓子", (.1, 300, term("槓子", "カンツ")), (.4, 500, tiles(["z1", "z1", "z1", "z1"], 110)))),
            (["2枚の組のうち、", "あがりに必要な1組が雀頭。", "同じ牌2枚の組は対子と言います。"],
             sc("雀頭と対子", (.1, 300, term2("雀頭", "ジャントウ", "対子", "トイツ")),
                (.4, 480, grp(HAND, 60).replace("#4261AA", "#4261AA")), (1.2, 700, note("あがりに使う2枚＝<b>雀頭</b><br>同じ2枚の組＝<b>対子</b>（雀頭の候補）")))),
            (["あと1枚で順子になる、", "2枚の組が搭子です。"],
             sc("搭子", (.1, 300, term("搭子", "ターツ")), (.4, 500, tiles(["s4", "s5"], 110) + '<div style="height:20px"></div>' + tiles(["m3", "m5"], 110)),
                (1.2, 860, note("4・5なら3か6、3・5なら4で<b>順子になる</b>")))),
            G_END]
TOPICS["gy-10"] = gy10

# ======================= 11 待ちの形 =======================
def wait(kj, ym, have, waits, desc):
    def mk(a, b):
        return [head(a, b, kj), stage(a + .1, b, term(kj, ym), top=300), stage(a + .4, b, tiles(have, 110), top=480),
                stage(a + 1.1, b, '<div class="mid"><div class="cnt" style="margin-bottom:12px">待ち</div>' + "".join(f'<span style="display:inline-block;margin:0 10px;outline:7px solid #E75620;outline-offset:3px;border-radius:10px">{tile(w, 100)}</span>' for w in waits) + "</div>", top=700, anim="pop"),
                stage(a + 1.8, b, note(desc), top=1010)]
    return mk

def gy11():
    vis = tiles(["s4", "s5"], 120) + '<div class="mid" style="margin-top:18px">' + tile("s3", 90) + tile("s6", 90) + "</div>"
    return [(["リャンメン、カンチャン、ペンチャン。", "待ちの形を5つ、", "絵で覚えましょう。"], hook("麻雀用語", "待ちの形\n5つ", vis, g=False)),
            (["四と五のように、", "両側どちらでもいい形が両面。", "三と六の2種類、最大8枚待ちです。"], wait("両面", "リャンメン", ["s4", "s5"], ["s3", "s6"], "両側どちらでも。<b>いちばん良い待ち</b>")),
            (["四と六のように、", "間の1枚を待つのが嵌張。", "五の1種類だけです。"], wait("嵌張", "カンチャン", ["m4", "m6"], ["m5"], "<b>間の1枚</b>だけ")),
            (["一二、八九のように、", "片側しかないのが辺張。", "三か七の1種類です。"], wait("辺張", "ペンチャン", ["p1", "p2"], ["p3"], "一二は<b>三</b>、八九は<b>七</b>だけ")),
            (["雀頭の1枚を待つのが単騎。", "待ちは自由に選べます。"], wait("単騎", "タンキ", ["z1"], ["z1"], "雀頭の<b>1枚</b>を待つ")),
            (["対子2組の、", "どちらかが刻子になれば", "あがれる形がシャンポンです。"], wait("双碰", "シャンポン", ["m2", "m2", "s8", "s8"], ["m2", "s8"], "どちらかが<b>3枚目</b>になればあがり")),
            G_END]
TOPICS["gy-11"] = gy11

# ======================= 12 点数のもと =======================
def gy12():
    vis = '<div class="mid"><span class="term"><b>30符</b><span>4翻</span></span></div>'
    return [(["符と翻、", "何が違うか分かる？"], hook("麻雀用語", "符と翻", vis, g=False)),
            (["翻は、役やドラで増える、", "点数の段階です。", "リーチで1翻、ドラ1枚で1翻。"],
             sc("翻", (.1, 300, term("飜", "ハン")), (.4, 480, '<div class="vcard">' + vt2([("リーチ", "1翻"), ("ドラ1枚", "1翻"), ("ホンイツ", "3翻")]) + "</div>"),
                (1.4, 900, note("1翻ふえると、点数は<b>ほぼ2倍</b>")))),
            (["符は、手の形で決まる", "点数の基礎です。", "刻子や待ちの形で増えます。"],
             sc("符", (.1, 300, term("符", "フ")), (.4, 480, '<div class="vcard">' + vt2([("あがり", "20符"), ("門前でロン", "＋10符"), ("中張牌の暗刻", "＋4符")]) + "</div>"),
                (1.4, 900, note("ふつうは<b>30符か40符</b>になることが多い")))),
            (["符と翻の組み合わせで、", "点数が決まります。", "点数の計算は記事で", "表にしています。"],
             sc("組み合わせで点数", (.3, 380, '<div class="vcard">' + vt2([("30符1翻", "1,000点"), ("30符2翻", "2,000点"), ("30符3翻", "3,900点"), ("30符4翻", "7,700点")]) + "</div>"))),
            G_END]
TOPICS["gy-12"] = gy12
