# 守りの基本（リーチされたときの安全な牌の探し方）
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
def bar(n): return '<span class="lv">' + "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(5)) + "</span>"
AR = '<span class="ar">→</span>'
RIV = ["z3", "m9", "p1", "s4", "m2"]
river = "".join(tl(c, 30) for c in RIV) + f'<span class="yk">{tl("p7", 30)}</span>'
EX = [("s4", "現物", "河に四索がある", 5), ("z1", "字牌（3枚見え）", "東がほかに<br>3枚見えている", 4), ("s1", "スジ", "四索が切れている", 3), ("p4", "中スジ", "一筒と七筒が<br>両方切れている", 3), ("m5", "片スジ", "二萬だけ切れている<br>八萬の側が危ない", 2), ("s6", "無スジ", "三索も九索も<br>切れていない", 1)]
ex = "".join(f'<div class="e">{tl(c, 34)}<b>{n}</b><span>{d}</span>{bar(k)}</div>' for c, n, d, k in EX)
R = [("1", "現物", "ゲンブツ", "リーチした人が<b class='o'>自分で切った牌</b><br>リーチのあと、ほかの人が切って通った牌も", "ロンされない", 5, tl("s4", 22)),
     ("2", "字牌（3枚見え）", "", "自分の1枚のほかに<b class='o'>3枚見えている字牌</b><br>国士無双のほかには当たらない", "ほぼ当たらない", 4, tl("z3", 22) * 3),
     ("3", "スジ", "", "四が切れていれば<b class='o'>一と七</b><br>一と七が両方切れていれば<b class='o'>四</b>（中スジ）", "両面には当たらない", 3, tl("s4", 22) + AR + tl("s1", 22) + tl("s7", 22)),
     ("3", "壁", "カベ", "七が4枚見えていれば、<b class='o'>八と九</b><br>七を使う両面が作れない", "両面には当たらない", 3, tl("s7", 19) * 4 + AR + tl("s8", 22) + tl("s9", 22)),
     ("5", "片スジ", "", "四・五・六で、<b class='o'>片側しか切れていない</b>", "半分だけ安心", 2, tl("s2", 22) + AR + tl("s5", 22)),
     ("6", "無スジ", "ムスジ", "スジにも壁にもならない数牌<br>とくに<b class='o'>四・五・六</b>", "いちばん危ない", 1, tl("s5", 22))]
rows = "".join(f'<tr><td class="no">{a}</td><th class="rh">{b}<small>{c}</small></th><td class="tx"><div class="fx"><span>{d}</span><span class="pic">{g}</span></div></td><td class="lvc">{bar(f)}<b>{e}</b></td></tr>' for a, b, c, d, e, f, g in R)
body = f"""
<div class="bar" style="margin-top:0">リーチされたときの、安全さの目安<small>上ほど当たりにくい</small></div>
<table><colgroup><col style="width:36px"><col style="width:124px"><col><col style="width:136px"></colgroup>
<thead><tr><th></th><th>名前</th><th>どんな牌か</th><th>安全度</th></tr></thead><tbody>{rows}</tbody></table>
<div class="bar">やってみよう　どれから切る？</div>
<div class="ex"><div class="rv"><b>リーチした人の河</b><div>{river}</div></div><div class="es">{ex}</div></div>
<div class="tip"><b>まず現物</b>　無ければ、字牌（3枚見え）→ スジ・壁の順に探す。<br><b>スジと壁は「両面に当たらない」だけ</b>　嵌張・辺張・双碰・単騎には当たることがある</div>"""
css = """td.no { text-align: center; font-size: 20px; font-weight: 900; color: #fff; background: #177083; } td.tx { font-size: 12.5px; } .fx { display: flex; justify-content: space-between; align-items: center; gap: 8px; } .pic { display: flex; align-items: center; gap: 1px; flex: none; } .ar { margin: 0 4px; font-weight: 900; color: #6B7A77; }
td.lvc { text-align: center; } .lv { display: flex; justify-content: center; gap: 3px; margin-bottom: 3px; } .lv i { width: 15px; height: 9px; border-radius: 2px; background: #DDE5E3; } .lv i.on { background: #177083; }
td.lvc b { font-size: 12px; font-weight: 900; } tbody tr { height: 50px; }
.ex { background: #fff; border: 2px solid #1F2A28; border-top: 0; padding: 10px 12px; } .rv { display: flex; align-items: center; justify-content: center; gap: 14px; background: #E4F3EC; border-radius: 7px; padding: 7px; } .rv b { font-size: 14px; font-weight: 900; color: #177083; } .rv div { display: flex; align-items: center; gap: 3px; } .yk { display: inline-block; transform: rotate(90deg); margin: 0 7px; }
.es { display: grid; grid-template-columns: repeat(6, 1fr); gap: 8px; margin-top: 10px; } .e { text-align: center; } .e b { display: block; font-size: 13px; font-weight: 900; margin-top: 3px; } .e > span:not(.lv) { display: block; font-size: 10.5px; font-weight: 700; color: #4C5B58; line-height: 1.35; height: 29px; } .e .lv i { width: 11px; }"""
render(page("リーチされたら、何を切る？", "守りの基本　安全な牌の探し方", "迷ったら<br><span>現物</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "mamori")
