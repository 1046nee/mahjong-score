import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
import table_art as A      # tools/ は base が sys.path に入れてある
def stick(): return f'<svg viewBox="-1 -1 92 13" style="width:70px;vertical-align:middle">{A.tenbo_color(1000, 0, 0, L=90, H=10)}</svg>'
wait = tl("s5", 22) + tl("s6", 22) + '<span class="ar">待ち</span>' + tl("s4", 18) + tl("s7", 18)

# 卓の図（2026-11-24 ユーザーの指定「卓の画像があった方がわかりやすい」）。自分は下・下家は右・対面は上・上家は左。
# 河は席ごとに回して置く（その人から見て左から切った順）。札は回さずに立てて読めるようにする。
# 印: h＝自分が切った待ちの牌（オレンジの枠）・m＝見逃した牌（青の枠）・x＝ロンできない牌（赤の枠と✕）・r＝リーチの横向きの牌
SEAT = {"self": (112, 182, 0), "shimo": (182, 112, -90), "toi": (112, 42, 180), "kami": (42, 112, 90)}
TAG = {"h": ("切った", "#E25A1C"), "m": ("見逃し", "#4261AA"), "x": ("ロン✕", "#C92F42")}
def river(seat, spec):
    x, y, r = SEAT[seat]; out = ""
    for p in spec.split():
        code, _, mk = p.partition(":")
        if mk == "r":
            out += f'<span class="rt"><img src="{T}/{code}-yoko.svg" style="height:{17 * 69 / 62:.1f}px"></span>'; continue
        # 札は印の牌の先（河の続く向き）に置く。横の席は札の幅が河と直角になるので、近くに置く
        off = 22 if r in (0, 180) else 12
        tag = f'<i class="tga" style="left:calc(100% + {off}px)"><i class="tg" style="background:{TAG[mk][1]};transform:translate(-50%,-50%) rotate({-r}deg)">{TAG[mk][0]}</i></i>' if mk else ""
        out += f'<span class="rt {mk}">{tl(code, 17)}{tag}</span>'
    return f'<div class="rv" style="left:{x}px;top:{y}px;transform:translate(-50%,-50%) rotate({r}deg)">{out}</div>'
def taku(no, name, rivers, center, cap):
    seats = '<b class="st" style="left:112px;top:206px">自分</b><b class="st v" style="left:216px;top:112px">下家</b><b class="st" style="left:112px;top:4px">対面</b><b class="st v" style="left:8px;top:112px">上家</b>'
    return (f'<div class="tk"><h3><i>{no}</i>{name}</h3><div class="mat">{seats}{"".join(river(s, v) for s, v in rivers)}'
            f'<div class="ctr"><div>{center}</div></div></div><p class="cap">{cap}</p></div>')
TAKU = [
    taku("1", "捨て牌のフリテン", [("self", "z1 m9 p1 z5 s7:h"), ("shimo", "z4 p9 m1 s4:x"), ("toi", "m1 z6 p9 s2"), ("kami", "s9 z2 m8 p3")],
         "四索が<br>出ても<b>ロン✕</b>", '自分の河に<b class="o">七索</b>がある。四索・七索待ちなので、<b>四索でもロンできない</b>'),
    taku("2", "同巡内フリテン", [("self", "z1 m9 p1 z5"), ("shimo", "z4 p9 m1 s4:m"), ("toi", "m1 z6 p9 s7:x"), ("kami", "s9 z2 m8")],
         "自分が<br>切るまで<b>ロン✕</b>", '下家の<b class="b">四索を見逃した</b>。自分が切るまでは、対面の七索でもロンできない'),
    taku("3", "リーチ後のフリテン", [("self", "z1 m9 p1:r m2 z7"), ("shimo", "z4 m3 s4:m"), ("toi", "m1 z6 p2 s1"), ("kami", "s9 z2 m6 p8 s7:x")],
         "この局は<br>ずっと<b>ロン✕</b>", 'リーチのあとに<b class="b">四索を見逃した</b>。その局が終わるまで、ロンはできない'),
]
ROWS = [
 ("捨て牌の<br>フリテン", "ステハイ", '自分の河に<b class="o">待ちの牌</b>がある', "✕", "○", '待ちが変わるまで<small>（その待ちのあいだずっと）</small>'),
 ("同巡内<br>フリテン", "ドウジュンナイ", 'アガリ牌が出たのに<b class="o">見逃した</b>', "✕", "○", '次に<b class="k">自分が打牌</b>するまで'),
 ("リーチ後の<br>フリテン", "リーチゴ", '<b class="o">リーチのあと</b>に見逃した', "✕", "○", '<b class="o">その局が終わるまで</b>'),
]
rows = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="tx">{c}</td><td class="mk ng">{e}</td><td class="mk ok">{f}</td><td class="tx">{g}</td></tr>' for a, b, c, e, f, g in ROWS)
body = f"""
<div class="bar" style="margin-top:0">卓で見る、3つのフリテン<small>例は四索・七索の両面待ち　{wait}</small></div>
<div class="tks">{"".join(TAKU)}</div>
<div class="bar">まとめ</div>
<table><colgroup><col style="width:104px"><col><col style="width:62px"><col style="width:62px"><col style="width:200px"></colgroup>
<thead><tr><th>種類</th><th>なるとき</th><th>ロン</th><th>ツモ</th><th>ロンできないのは</th></tr></thead><tbody>{rows}</tbody></table>
<div class="tip"><b>待ちが2種類以上のとき</b>　どれか1種でも自分の河にあれば、<b>どの待ちでもロンできない</b>（四索・七索待ちで七索を切っていたら、四索でもロンできない）。<br>
<b>どれも、ツモアガリはできる</b>　フリテンで止まるのはロンだけ。</div>
<p class="note">役が無くてロンできなかったときも、見逃したのと同じ扱い（同巡内フリテン）。フリテンのままロンすると<b>チョンボ</b>になるのがふつう。フリテンの決まりは、Mリーグも雀魂も同じ</p>"""
css = """td.tx { font-size: 12.5px; } td.tx small { display: block; font-size: 10.5px; color: #6B7A77; }
td.mk { text-align: center; font-size: 26px; font-weight: 900; } td.ng { color: #C92F42; } td.ok { color: #177083; } .ar { font-size: 10.5px; font-weight: 800; color: #DDF0EC; margin: 0 4px; }
.bar img.t { vertical-align: -6px; } tbody tr { height: 50px; } .b { color: #4261AA; font-weight: 900; }
.tks { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; background: #fff; border: 2px solid #177083; border-top: 0; padding: 10px; }
.tk h3 { display: flex; align-items: center; gap: 6px; font-size: 14px; font-weight: 900; margin-bottom: 5px; }
.tk h3 i { font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 50%; background: #177083; color: #fff; font-size: 12px; }
.mat { position: relative; width: 224px; height: 224px; margin: 0 auto; background: #2F7A62; border-radius: 10px; box-shadow: inset 0 0 0 3px #245F4C; }
.rv { position: absolute; display: flex; gap: 1px; align-items: flex-end; white-space: nowrap; }
.rt { position: relative; display: inline-flex; } .rt.h, .rt.m, .rt.x { z-index: 2; } .rt img { display: block; }
.rt.h img { outline: 2.5px solid #E25A1C; outline-offset: 0; border-radius: 2px; } .rt.m img { outline: 2.5px solid #5B8DEF; border-radius: 2px; } .rt.x img { outline: 2.5px solid #FF5A6E; border-radius: 2px; }
.tga { position: absolute; top: 50%; width: 0; height: 0; } .tg { position: absolute; left: 0; top: 0; font-style: normal; font-size: 9.5px; font-weight: 900; color: #fff; border-radius: 4px; padding: 1px 4px; white-space: nowrap; line-height: 1.3; }
.st { position: absolute; transform: translate(-50%, 0); font-size: 10px; font-weight: 900; color: #CFE8DF; } .st.v { writing-mode: vertical-rl; transform: translate(-50%, -50%); }
.ctr { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); width: 72px; height: 72px; border-radius: 8px; background: #F4F8F6; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 10.5px; font-weight: 800; line-height: 1.35; color: #33403D; }
.ctr b { display: block; color: #C92F42; font-size: 13px; }
.cap { font-size: 11.5px; font-weight: 700; line-height: 1.5; margin-top: 6px; color: #33403D; } .cap b { font-weight: 900; color: #C92F42; } .cap b.o { color: #E25A1C; } .cap b.b { color: #4261AA; }"""
render(page("フリテンの3種類", "ロンできないのは、どんなときか", "ロンは<b>✕</b><br><span>ツモは○</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "furiten")
