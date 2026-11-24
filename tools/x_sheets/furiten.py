import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
import table_art as A      # tools/ は base が sys.path に入れてある
def stick(w=70): return f'<svg viewBox="-1 -1 92 13" style="width:{w}px;vertical-align:middle;display:block">{A.tenbo_color(1000, 0, 0, L=90, H=10)}</svg>'

# 例の手（2026-11-24 ユーザーの指定「一四七索待ち」「タンヤオとピンフの役がある待ち」）。二三四萬・八八萬・五六七筒・二三四五六索 → 一・四・七索待ち（machi3.waits で確認）。
# 四・七索ならタンヤオ・ピンフ、一索だとタンヤオが付かない → 一索を見逃すつじつまが合う。②は二三四萬をチーしたあと（喰いタンだけなので、一索では役が無い）
HAND = "m2 m3 m4 m8 m8 p5 p6 p7 s2 s3 s4 s5 s6"
HAND_CHI = "m8 m8 p5 p6 p7 s2 s3 s4 s5 s6 | y:m2 m3 m4"
wait = "".join(tl(c, 20) for c in "s2 s3 s4 s5 s6".split()) + '<span class="ar">待ち</span>' + tl("s1", 18) + tl("s4", 18) + tl("s7", 18)

# 卓の図（2026-11-24 ユーザーの指定）。自分は下・下家は右・対面は上・上家は左。河は6枚切り（その局の進み方に合わせて5枚の人もいる）。
# 河は席ごとに回して置く（その人から見て左から切った順）。印は牌の角の丸（回さずに立てて読めるようにする）。
# 印: h＝自分が切った待ちの牌（オレンジ）・m＝見逃した牌（青）・x＝ロンできない牌（赤）・r＝リーチの横向きの牌
W, H = 224, 244
SEAT = {"self": (112, 176, 0), "shimo": (186, 104, -90), "toi": (112, 34, 180), "kami": (38, 104, 90)}
MK = {"h": ("切", "#E25A1C"), "m": ("見", "#4261AA"), "x": ("✕", "#C92F42")}
TW = 15      # 河の牌の幅
def river(seat, spec):
    x, y, r = SEAT[seat]; out = ""
    for p in spec.split():
        code, _, mk = p.partition(":")
        if mk == "r":
            out += f'<span class="rt"><img src="{T}/{code}-yoko.svg" style="height:{TW * 69 / 62:.1f}px"></span>'; continue
        bd = f'<i class="bd" style="background:{MK[mk][1]};transform:rotate({-r}deg)">{MK[mk][0]}</i>' if mk else ""
        out += f'<span class="rt {mk}">{tl(code, TW)}{bd}</span>'
    return f'<div class="rv" style="left:{x}px;top:{y}px;transform:translate(-50%,-50%) rotate({r}deg)">{out}</div>'
def hand_html(spec):
    out = ""
    for c in spec.split():
        if c == "|": out += '<span style="width:4px"></span>'
        elif c.startswith("y:"): out += f'<img class="t" src="{T}/{c[2:]}-yoko.svg" style="height:{14 * 69 / 62:.1f}px;align-self:flex-end">'
        else: out += tl(c, 14)
    return out
def taku(no, name, rivers, center, cap, riichi=False, hand=HAND):
    seats = f'<b class="st v" style="left:{W - 8}px;top:104px">下家</b><b class="st" style="left:112px;top:3px">対面</b><b class="st v" style="left:8px;top:104px">上家</b>'
    rb = f'<div class="rb">{stick(54)}</div>' if riichi else ""
    hand = f'<div class="hand">{hand_html(hand)}</div>'
    return (f'<div class="tk"><h3><i>{no}</i>{name}</h3><div class="mat">{seats}{"".join(river(s, v) for s, v in rivers)}{rb}'
            f'<div class="ctr"><div>{center}</div></div>{hand}</div><p class="cap">{cap}</p></div>')
TAKU = [
    # 下家の6枚目でロンできない（自分・下家は6枚、対面・上家は5枚）
    taku("1", "捨て牌のフリテン", [("self", "z1 m9 s1:h p1 z5 m1"), ("shimo", "z4 p9 m1 z3 m9 s4:x"), ("toi", "m1 z6 p9 s9 p2"), ("kami", "s9 z3 m9 p3 z7")],
         "四索・七索<br>が出ても<b>ロン✕</b>", '自分の河に<b class="o">一索</b>がある。<br>一・四・七索待ちなので、<br><b>四索・七索でもロンできない</b>'),
    # 下家の6枚目の四索を見逃し → 自分の番の前の対面の一索もロンできない（上家は5枚）
    taku("2", "同巡内フリテン", [("self", "z1 m9 p1 z5 m1 p9"), ("shimo", "z4 p9 m1 z3 m9 s1:m"), ("toi", "m1 z6 p9 s9 p2 s4:x"), ("kami", "s9 z3 m9 p3 z7")],
         "自分が<br>打牌するまで<b>ロン✕</b>", 'チーしていて、一索では役が無い。<br>下家の<b class="b">一索を見逃した</b>ので、<br>自分が打牌するまで<b>四索もロン✕</b>', hand=HAND_CHI),
    # 自分は5枚目でリーチ → 下家の5枚目の四索を見逃し → 自分が6枚目を切ったあとの上家の一索もロンできない
    taku("3", "リーチ後のフリテン", [("self", "z1 m9 p1 z5 m1:r p9"), ("shimo", "z4 p9 m1 z3 s1:m m9"), ("toi", "m1 z6 p9 s9 p2 s8"), ("kami", "s9 z3 m9 p3 z7 s4:x")],
         "この局は<br>ずっと<b>ロン✕</b>", 'リーチのあと、タンヤオの付く<br>四・七索を待って<b class="b">一索を見逃した</b>。<br>この局はもう<b>四索でもロンできない</b>', riichi=True),
]
LEG = "".join(f'<span><i class="bd" style="background:{c};position:static">{t}</i>{lab}</span>' for (t, c), lab in zip(MK.values(), ["自分が切った待ちの牌", "見逃した牌", "ロンできない牌"]))
ROWS = [
 ("捨て牌の<br>フリテン", "ステハイ", '自分の河に<b class="o">待ちの牌</b>がある<small>ポン・チーで鳴かれた牌もふくむ</small>', "✕", "○", '待ちが変わるまで<small>（その待ちのあいだずっと）</small>'),
 ("同巡内<br>フリテン", "ドウジュンナイ", 'アガリ牌が出たのに<b class="o">見逃した</b>', "✕", "○", '次に<b class="k">自分が打牌</b>するまで<small>ポン・チーで自分の番が飛んでも続く</small>'),
 ("リーチ後の<br>フリテン", "リーチゴ", '<b class="o">リーチのあと</b>に見逃した', "✕", "○", '<b class="o">その局が終わるまで</b>'),
]
rows = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="tx">{c}</td><td class="mk ng">{e}</td><td class="mk ok">{f}</td><td class="tx">{g}</td></tr>' for a, b, c, e, f, g in ROWS)
body = f"""
<div class="bar" style="margin-top:0">卓で見る、3つのフリテン<small>例は一・四・七索待ち（四・七索ならタンヤオ・ピンフ）　{wait}</small></div>
<div class="tks">{"".join(TAKU)}<div class="leg">{LEG}<span class="hn">いちばん手前は自分の手牌</span></div></div>
<div class="warn">
<p><b>捨て牌のフリテン</b>　自分が切った牌が<b>ポン・チーで鳴かれる</b>と、河から無くなるので見逃しやすい。<br>鳴かれた牌も自分の捨て牌なので、フリテンになる。</p>
<p><b>同巡内フリテン</b>　見逃してから<b>次に自分が打牌するまで</b>はロンできない。自分が新しく打牌したあとなら、ロンできる。<br>間に<b>ポン・チーが入って自分の番が飛ばされても</b>、自分が打牌するまでは続く。</p></div>
<div class="bar">まとめ</div>
<table><colgroup><col style="width:104px"><col><col style="width:56px"><col style="width:56px"><col style="width:216px"></colgroup>
<thead><tr><th>種類</th><th>なるとき</th><th>ロン</th><th>ツモ</th><th>ロンできないのは</th></tr></thead><tbody>{rows}</tbody></table>
<div class="tip"><b>待ちが2種類以上のとき</b>　どれか1種でも自分の河にあれば、<b>どの待ちでもロンできない</b>。<br>（一・四・七索待ちで一索を切っていたら、四索・七索でもロンできない）<br>
<b>どれも、ツモアガリはできる</b>　フリテンで止まるのはロンだけ。</div>
<p class="note">役が無くてロンできなかったときも、見逃したのと同じ扱い（同巡内フリテン）。フリテンのままロンすると<b>チョンボ</b>になるのがふつう。<br>フリテンの決まりは、Mリーグも雀魂も同じ</p>"""
css = f"""td.tx {{ font-size: 12.5px; }} td.tx small {{ display: block; font-size: 10.5px; color: #6B7A77; }}
td.mk {{ text-align: center; font-size: 26px; font-weight: 900; }} td.ng {{ color: #C92F42; }} td.ok {{ color: #177083; }} .ar {{ font-size: 10.5px; font-weight: 800; color: #DDF0EC; margin: 0 4px; }}
.bar img.t {{ vertical-align: -6px; }} tbody tr {{ height: 52px; }} .b {{ color: #4261AA; font-weight: 900; }}
.tks {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background: #fff; border: 2px solid #177083; border-top: 0; padding: 10px 10px 8px; }}
.tk h3 {{ display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 900; margin-bottom: 5px; }}
.tk h3 i {{ font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 50%; background: #177083; color: #fff; font-size: 12px; }}
.mat {{ position: relative; width: {W}px; height: {H}px; margin: 0 auto; background: #2F7A62; border-radius: 10px; box-shadow: inset 0 0 0 3px #245F4C; }}
.rv {{ position: absolute; display: flex; gap: 1px; align-items: flex-end; white-space: nowrap; }}
.rt {{ position: relative; display: inline-flex; }} .rt img {{ display: block; }}
.rt.h img {{ outline: 2.5px solid #F07A3C; border-radius: 2px; }} .rt.m img {{ outline: 2.5px solid #6E9BF5; border-radius: 2px; }} .rt.x img {{ outline: 2.5px solid #FF5A6E; border-radius: 2px; }}
i.bd {{ position: absolute; top: -7px; right: -7px; width: 15px; height: 15px; border-radius: 50%; font-style: normal; font-size: 9.5px; font-weight: 900; color: #fff; display: inline-flex; align-items: center; justify-content: center; box-shadow: 0 0 0 1.5px #fff; z-index: 3; }}
.st {{ position: absolute; transform: translate(-50%, 0); font-size: 10px; font-weight: 900; color: #CFE8DF; }} .st.v {{ writing-mode: vertical-rl; transform: translate(-50%, -50%); }}
.ctr {{ position: absolute; left: 112px; top: 100px; transform: translate(-50%, -50%); width: 70px; height: 62px; border-radius: 8px; background: #F4F8F6; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 10px; font-weight: 800; line-height: 1.3; color: #33403D; }}
.ctr b {{ display: block; color: #C92F42; font-size: 13px; }}
.rb {{ position: absolute; left: 112px; top: 146px; transform: translate(-50%, -50%); }}
.hand {{ position: absolute; left: 50%; bottom: 6px; transform: translateX(-50%); display: flex; gap: 0; white-space: nowrap; }}
.cap {{ font-size: 11.5px; font-weight: 700; line-height: 1.5; margin-top: 6px; color: #33403D; }} .cap b {{ font-weight: 900; color: #C92F42; }} .cap b.o {{ color: #E25A1C; }} .cap b.b {{ color: #4261AA; }}
.leg {{ grid-column: 1 / -1; display: flex; gap: 14px; align-items: center; font-size: 11px; font-weight: 800; color: #4F5C5A; border-top: 1px dashed #C5D6D2; padding-top: 6px; }}
.leg span {{ display: inline-flex; align-items: center; gap: 4px; }} .leg .hn {{ margin-left: auto; }}
.warn {{ margin-top: 8px; border: 1.5px solid #C92F42; border-radius: 6px; padding: 6px 10px; background: #FFF3F4; font-size: 11.5px; font-weight: 700; line-height: 1.55; }}
.warn p + p {{ margin-top: 3px; }} .warn b {{ color: #C92F42; }}"""
render(page("フリテンの3種類", "ロンできないのは、どんなときか", "ロンは<b>✕</b><br><span>ツモは○</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "furiten")
