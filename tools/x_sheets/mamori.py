import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
R = [("1", "現物", "ゲンブツ", "リーチした人が<b class='o'>自分で切った牌</b>（リーチのあと、ほかの人が切って通った牌も）", "ぜったいに当たらない", 5, tl("s4", 20)),
     ("2", "字牌（3枚見え）", "", "場に<b class='o'>3枚見えている字牌</b>。残り1枚なので、単騎でしか当たらない", "ほぼ当たらない", 4, tl("z3", 20) * 3),
     ("3", "スジ", "", "<b class='o'>4が切られていたら1と7</b>は、両面では当たらない（2-5-8・3-6-9も同じ）", "両面では当たらない", 3, tl("s4", 20) + '<span class="ar">→</span>' + tl("s1", 20) + tl("s7", 20)),
     ("4", "壁", "カベ", "ある牌が<b class='o'>4枚見えている</b>と、それをまたぐ両面が作れない（七が4枚なら八・九は安全寄り）", "両面では当たらない", 3, tl("s7", 18) * 4 + '<span class="ar">→</span>' + tl("s8", 20) + tl("s9", 20)),
     ("5", "字牌（1・2枚見え）", "", "単騎・シャンポンでは当たる", "まあまあ", 2, tl("z3", 20)),
     ("6", "スジでない中張牌", "ムスジ", "2〜8の牌で、スジにも壁にもなっていない", "いちばん危ない", 1, tl("s5", 20))]
def bar(n): return '<span class="lv">' + "".join(f'<i class="{"on" if k < n else ""}"></i>' for k in range(5)) + "</span>"
rows = "".join(f'<tr><td class="no">{a}</td><th class="rh">{b}<small>{c}</small></th><td class="tx">{d}<div class="pic">{g}</div></td><td class="lvc">{bar(f)}<b>{e}</b></td></tr>' for a, b, c, d, e, f, g in R)
body = f"""
<div class="bar" style="margin-top:0">リーチされたとき、安全な順<small>上ほど当たりにくい</small></div>
<table><colgroup><col style="width:40px"><col style="width:130px"><col><col style="width:150px"></colgroup>
<thead><tr><th></th><th>名前</th><th>どんな牌か</th><th>安全度</th></tr></thead><tbody>{rows}</tbody></table>
<div class="tip"><b>まずは現物</b>　迷ったら、リーチした人の河にある牌から切る。現物が無いときに、字牌・スジ・壁の順で探す。<br>
<b>スジと壁は「両面では当たらない」だけ</b>　嵌張・単騎・シャンポンでは当たることがある。</div>"""
css = """td.no { text-align: center; font-size: 20px; font-weight: 900; color: #fff; background: #177083; } td.tx { font-size: 12px; } .pic { margin-top: 3px; display: flex; align-items: center; gap: 1px; } .ar { margin: 0 5px; font-weight: 900; color: #6B7A77; }
td.lvc { text-align: center; } .lv { display: flex; justify-content: center; gap: 3px; margin-bottom: 3px; } .lv i { width: 16px; height: 9px; border-radius: 2px; background: #DDE5E3; } .lv i.on { background: #177083; }
td.lvc b { font-size: 11.5px; font-weight: 900; } tbody tr { height: 62px; }"""
render(page("守りの基本", "リーチされたら、どの牌が安全か", "迷ったら<br><span>現物</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "mamori")
