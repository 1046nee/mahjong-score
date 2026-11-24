import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
import table_art as A      # tools/ は base が sys.path に入れてある
def stick(): return f'<svg viewBox="-1 -1 92 13" style="width:70px;vertical-align:middle">{A.tenbo_color(1000, 0, 0, L=90, H=10)}</svg>'
wait = tl("s5", 22) + tl("s6", 22) + '<span class="ar">待ち</span>' + tl("s4", 18) + tl("s7", 18)
ROWS = [
 ("捨て牌の<br>フリテン", "ステハイ", '自分の河に<b class="o">待ちの牌</b>がある', '<span class="lab">自分の河</span>' + tl("z1", 20) + tl("m9", 20) + tl("s7", 20, "hl") + tl("p1", 20),
  "✕", "○", '待ちが変わるまで<small>（その待ちのあいだずっと）</small>'),
 ("同巡内<br>フリテン", "ドウジュンナイ", 'アガリ牌が出たのに<b class="o">見逃した</b>', '<span class="lab">他家が切る</span>' + tl("s4", 20, "hl") + '<span class="mi">見逃し</span>',
  "✕", "○", '次に<b class="k">自分が打牌</b>するまで'),
 ("リーチ後の<br>フリテン", "リーチゴ", '<b class="o">リーチのあと</b>に見逃した', stick() + '<span class="mi">のあと</span>' + tl("s4", 20, "hl") + '<span class="mi">見逃し</span>',
  "✕", "○", '<b class="o">その局が終わるまで</b>'),
]
rows = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="tx">{c}<div class="pic">{d}</div></td><td class="mk ng">{e}</td><td class="mk ok">{f}</td><td class="tx">{g}</td></tr>' for a, b, c, d, e, f, g in ROWS)
body = f"""
<div class="bar" style="margin-top:0">3つのフリテン<small>例は四索・七索の両面待ち　{wait}</small></div>
<table><colgroup><col style="width:104px"><col><col style="width:62px"><col style="width:62px"><col style="width:178px"></colgroup>
<thead><tr><th>種類</th><th>なるとき</th><th>ロン</th><th>ツモ</th><th>ロンできないのは</th></tr></thead><tbody>{rows}</tbody></table>
<div class="tip"><b>待ちが2種類以上のとき</b>　どれか1種でも自分の河にあれば、<b>どの待ちでもロンできない</b>（四索・七索待ちで七索を切っていたら、四索でもロンできない）。<br>
<b>どれも、ツモアガリはできる</b>　フリテンで止まるのはロンだけ。</div>
<p class="note">役が無くてロンできなかったときも、見逃したのと同じ扱い（同巡内フリテン）。フリテンのままロンすると<b>チョンボ</b>になるのがふつう</p>"""
css = """td.tx { font-size: 12.5px; } td.tx small { display: block; font-size: 10.5px; color: #6B7A77; } .pic { margin-top: 4px; display: flex; align-items: center; gap: 2px; }
.lab, .mi { font-size: 10.5px; font-weight: 800; color: #6B7A77; margin: 0 4px; } img.hl { outline: 2.5px solid #E25A1C; outline-offset: 1px; border-radius: 3px; }
td.mk { text-align: center; font-size: 26px; font-weight: 900; } td.ng { color: #C92F42; } td.ok { color: #177083; } .ar { font-size: 10.5px; font-weight: 800; color: #DDF0EC; margin: 0 4px; }
.bar img.t { vertical-align: -6px; } tbody tr { height: 74px; }"""
render(page("フリテンの3種類", "ロンできないのは、どんなときか", "ロンは<b>✕</b><br><span>ツモは○</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "furiten")
