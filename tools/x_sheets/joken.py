import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
# 子のアガリ: (名前, ロンの点, ツモの子の払い, ツモの親の払い)
KO = [("1,000", "30符1翻", 1000, 300, 500), ("2,000", "30符2翻", 2000, 500, 1000), ("3,900", "30符3翻", 3900, 1000, 2000), ("満貫", "8,000", 8000, 2000, 4000),
      ("跳満", "12,000", 12000, 3000, 6000), ("倍満", "16,000", 16000, 4000, 8000), ("役満", "32,000", 32000, 8000, 16000)]
OYA = [("1,500", "30符1翻", 1500, 500), ("2,900", "30符2翻", 2900, 1000), ("5,800", "30符3翻", 5800, 2000), ("満貫", "12,000", 12000, 4000),
       ("跳満", "18,000", 18000, 6000), ("倍満", "24,000", 24000, 8000), ("役満", "48,000", 48000, 16000)]
f = lambda v: f"{v:,}"
ko = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="n dk">{f(2 * r)}</td><td class="n">{f(r)}</td><td class="n">{f(c * 2 + o + c)}</td><td class="n">{f(c * 2 + o + o)}</td></tr>' for a, b, r, c, o in KO)
oy = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="n dk">{f(2 * r)}</td><td class="n">{f(r)}</td><td class="n">{f(e * 3 + e)}</td></tr>' for a, b, r, e in OYA)
body = f"""
<div class="tip" style="margin-top:0"><b>考え方</b>　<b>直撃</b>（その人からロン）＝点数の<b>2倍</b>縮まる。<b>ほかの人からロン</b>＝点数のぶんだけ。<b>ツモ</b>＝もらう点の合計に、その人が払った点を足したぶん</div>
<div class="two">
<div><div class="bar">子がアガったとき<small>縮まる点差</small></div>
<table><colgroup><col style="width:78px"><col><col><col><col></colgroup>
<thead><tr><th>アガリ</th><th>直撃ロン</th><th>ほかから<br>ロン</th><th>ツモ<small>相手が子</small></th><th>ツモ<small>相手が親</small></th></tr></thead><tbody>{ko}</tbody></table></div>
<div><div class="bar">親がアガったとき<small>縮まる点差</small></div>
<table><colgroup><col style="width:78px"><col><col><col></colgroup>
<thead><tr><th>アガリ</th><th>直撃ロン</th><th>ほかから<br>ロン</th><th>ツモ</th></tr></thead><tbody>{oy}</tbody></table></div>
</div>
<p class="note">相手＝点差を縮めたい人。ツモは「相手が子」なら相手は子の払い、「相手が親」なら親の払いをする。<b>積み棒・リーチ棒（供託）は入れていない</b>（入るとそのぶん多く縮まる）</p>
<div class="tip"><b>例</b>　オーラス、トップと<b>9,000点差</b>の子。満貫なら、ほかからロン（8,000）では届かないが、<b>トップが子ならツモで10,000</b>縮まって逆転、<b>直撃なら16,000</b>。</div>"""
css = """td.n { text-align: center; font-size: 14.5px; font-weight: 800; } td.dk { background: #FFF5EF; color: #E25A1C; font-weight: 900; }
th small { display: block; font-size: 9.5px; font-weight: 700; color: #DDF0EC; } th { line-height: 1.2; }
.two { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; } tbody tr { height: 38px; }"""
render(page("その1回で、点差は何点縮まる？", "条件戦の早見表　直撃・ロン・ツモで比べる", "直撃は<br><span>2倍</span>縮まる", body, css), sys.argv[1] if len(sys.argv) > 1 else "joken")
