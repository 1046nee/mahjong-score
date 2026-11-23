import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
Y = ["z1", "m1", "m9", "p1", "p9", "s1", "z5", "z6", "z7"]
ROWS = [
 ("荒牌平局", "ホワンパイピンチュー", "ふつうの流局", "山が無くなって、だれもアガれなかった", "".join(tl(c, 17) for c in ["back"] * 7) + '<span class="mi">王牌14枚だけ</span>', "あり", "親がテンパイなら続く"),
 ("九種九牌", "キュウシュキュウハイ", "途中流局", "最初のツモのときに、<b class='o'>么九牌が9種類以上</b>ある（鳴きが入る前）。言えば流せる", "".join(tl(c, 17) for c in Y), "なし", "続く（流れた局をやり直す）"),
 ("四風連打", "スーフーレンダ", "途中流局", "1巡目に、4人が<b class='o'>同じ風牌</b>を切った（鳴きが入る前）", "".join(tl("z2", 17) for _ in range(4)), "なし", "続く"),
 ("四開槓", "スーカイカン", "途中流局", "<b class='o'>2人以上</b>で、カンが合わせて4回（1人で4回なら流れない）", tl("back", 17) + tl("z3", 17) + tl("z3", 17) + tl("back", 17) + '<span class="mi">×4回</span>', "なし", "続く"),
 ("四家立直", "スーチャリーチ", "途中流局", "<b class='o'>4人全員</b>がリーチした（4人目のリーチが通ったとき）", '<span class="mi">リーチ ×4人</span>', "なし", "続く"),
 ("三家和", "サンチャホー", "途中流局", "1枚の牌に、<b class='o'>3人が同時にロン</b>した", '<span class="mi">ロン ×3人</span>', "なし", "続く"),
]
rows = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="kd {"f" if c == "ふつうの流局" else ""}">{c}</td><td class="tx">{d}<div class="pic">{e}</div></td><td class="mk">{f}</td><td class="tx c">{g}</td></tr>' for a, b, c, d, e, f, g in ROWS)
body = f"""
<div class="bar" style="margin-top:0">6つの流局<small>アガリが出ないまま局が終わること</small></div>
<table><colgroup><col style="width:112px"><col style="width:80px"><col><col style="width:68px"><col style="width:150px"></colgroup>
<thead><tr><th>名前</th><th>種類</th><th>起きるとき</th><th>ノーテン<br>罰符</th><th>親は</th></tr></thead><tbody>{rows}</tbody></table>
<div class="tip"><b>途中流局</b>は、山が残っていても局を流す決まり。流れたら<b>本場が1つ増える</b>（積み棒が1本ふえる）。リーチ棒（供託）は場に残って、次にアガった人がもらう。</div>
<p class="note">途中流局をありにするか、九種九牌を親が流したときに親が続くかは、ルールで違う（ネット麻雀やMリーグでも決めが違う）。三家和はロンを3人とも認めるルールもある</p>"""
css = """td.tx { font-size: 12px; } td.c { text-align: center; } .pic { margin-top: 3px; display: flex; align-items: center; gap: 1px; } .mi { font-size: 10.5px; font-weight: 800; color: #6B7A77; margin: 0 4px; }
td.kd { text-align: center; font-size: 11px; font-weight: 900; color: #4261AA; } td.kd.f { color: #177083; } td.mk { text-align: center; font-size: 14px; font-weight: 900; }
tbody tr { height: 60px; }"""
render(page("流局の種類", "アガリなしで局が終わる6つのパターン", "途中流局は<br><span>本場+1</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "ryukyoku")
