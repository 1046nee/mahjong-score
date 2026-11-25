# 条件戦の早見表: そのアガリで、ねらう相手との点差が何点縮まるか（直撃・ほかからロン・ツモ）。数字はすべて計算で出す
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
def up(v): return -(-v // 100) * 100
def base(han, fu): return {5: 2000, 6: 3000, 8: 4000, 13: 8000}.get(han) or min(2000, fu * 2 ** (2 + han))
HANDS = [("30符1翻", 1, 30), ("30符2翻", 2, 30), ("30符3翻", 3, 30), ("40符3翻", 3, 40), ("30符4翻", 4, 30), ("満貫", 5, 0), ("跳満", 6, 0), ("倍満", 8, 0), ("役満", 13, 0)]
f = lambda v: f"{v:,}"
BIG = lambda n: n in ("満貫", "跳満", "倍満", "役満")
ko = oy = ""
for nm, han, fu in HANDS:
    b = base(han, fu); r = up(4 * b); c, o = up(b), up(2 * b); R = up(6 * b); e = up(2 * b)
    cl = ' class="mg"' if nm == "満貫" else ""
    th = lambda v: f'<th class="rh">{nm if BIG(nm) else f(v)}<small>{f(v) if BIG(nm) else nm}</small></th>'
    ko += f'<tr{cl}>{th(r)}<td class="n dk">{f(2 * r)}</td><td class="n">{f(c * 3 + o)}</td><td class="n">{f(c * 2 + o * 2)}</td><td class="n">{f(r)}</td></tr>'
    oy += f'<tr{cl}>{th(R)}<td class="n dk">{f(2 * R)}</td><td class="n">{f(e * 4)}</td><td class="n">{f(R)}</td></tr>'
# 例の図: 9,000点差のゴールの線に、満貫の3通りがとどくか
def bar(lb, v, ok):
    w = v / 16000 * 100
    return f'<div class="bl"><span class="lb">{lb}</span><div class="tr"><i style="width:{w}%" class="{"ok" if ok else "ng"}"><b>{f(v)}</b></i><u style="left:{9000 / 16000 * 100}%"></u></div><span class="{"go" if ok else "no"}">{"逆転！" if ok else "あと1,000足りない"}</span></div>'
body = f"""
<div class="two" style="grid-template-columns: 1.2fr 1fr">
<div><div class="bar" style="margin-top:0">子がアガったとき<small>縮まる点差</small></div>
<table><colgroup><col style="width:74px"><col><col><col><col></colgroup>
<thead><tr><th>アガリ</th><th>直撃<small>相手からロン</small></th><th>ツモ<small>相手が子</small></th><th>ツモ<small>相手が親</small></th><th>ほかから<br>ロン</th></tr></thead><tbody>{ko}</tbody></table></div>
<div><div class="bar" style="margin-top:0">親がアガったとき<small>縮まる点差</small></div>
<table><colgroup><col style="width:74px"><col><col><col></colgroup>
<thead><tr><th>アガリ</th><th>直撃<small>相手からロン</small></th><th>ツモ</th><th>ほかから<br>ロン</th></tr></thead><tbody>{oy}</tbody></table></div>
</div>
<p class="note">相手＝追いこしたい人。<b>表の数字が、相手との点差より大きければ逆転</b>。同じなら同点で、順位の決め方はルールによって違う</p>
<div class="bar">積み棒・リーチ棒がある局は、さらに足す</div>
<table class="add"><colgroup><col style="width:34%"><col><col><col></colgroup>
<thead><tr><th></th><th>直撃</th><th>ツモ</th><th>ほかからロン</th></tr></thead>
<tbody><tr><th class="rh">1本場ごとに</th><td class="n dk">＋600</td><td class="n">＋400</td><td class="n">＋300</td></tr>
<tr><th class="rh">場にあるリーチ棒1本ごとに</th><td class="n dk">＋1,000</td><td class="n">＋1,000</td><td class="n">＋1,000</td></tr></tbody></table>
<p class="note">点差はリーチ棒を出したあとの点数で数える。自分もリーチするなら、点差が1,000広がり、アガれば戻る（差し引き0）</p>
<div class="bar">例　オーラス、トップ（子）と9,000点差。子の満貫で逆転できる？</div>
<div class="ex">{bar("ほかからロン", 8000, False)}{bar("ツモ", 10000, True)}{bar("直撃", 16000, True)}<div class="goal"><span>9,000点差</span></div></div>"""
css = """td.n { text-align: center; font-size: 14.5px; font-weight: 800; padding: 3px 2px; } td.dk { background: #FFF5EF; color: #E25A1C; font-weight: 900; }
th small { display: block; font-size: 9.5px; font-weight: 700; color: #DDF0EC; } th { line-height: 1.2; } table { width: 100%; }
.two { display: grid; gap: 14px; } .two tbody tr { height: 37px; } tr.mg td, tr.mg th.rh { border-top: 2.5px solid #1F2A28; } .add tbody tr { height: 30px; }
.ex { position: relative; background: #fff; border: 2px solid #1F2A28; border-top: 0; padding: 30px 14px 10px; }
.bl { display: grid; grid-template-columns: 92px 1fr 122px; gap: 10px; align-items: center; height: 36px; } .lb { font-size: 13px; font-weight: 900; text-align: right; }
.tr { position: relative; height: 24px; background: #E9EFEE; border-radius: 4px; } .tr i { display: flex; align-items: center; justify-content: flex-start; height: 100%; border-radius: 4px; font-style: normal; color: #fff; }
.tr i b { font-size: 13px; padding-left: 10px; } .ok { background: #177083; } .ng { background: #8FA29D; }
.tr u { position: absolute; top: -6px; bottom: -6px; border-left: 3px dashed #E25A1C; }
.go { color: #E25A1C; font-size: 15px; font-weight: 900; } .no { color: #4C5B58; font-size: 12px; font-weight: 800; }
.goal { position: absolute; top: 6px; left: 116px; right: 146px; } .goal span { position: absolute; left: 56.25%; transform: translateX(-50%); color: #E25A1C; font-size: 13px; font-weight: 900; white-space: nowrap; }"""
render(page("その1回で、点差は何点縮まる？", "条件戦の早見表　直撃・ツモ・ロンで比べる", "直撃は<br><span>2倍</span>縮まる", body, css), sys.argv[1] if len(sys.argv) > 1 else "joken")
