# 5ブロックの考え方。受け入れの枚数はシャンテン数の総当たりで確かめた（2026-11-25。例1 九筒か發を切る＝五八萬・四索の12枚／例2 辺張を落とす＝五八萬・二五索の16枚、両面を落とす＝七筒・二五索の12枚）
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
COL = {"m": "#177083", "r": "#2E8B57", "k": "#B8741A", "x": "#C92F42", "t": "#7A5CB8"}
def w(cs, s=21): return "".join(tl(c, s) for c in cs.split())
def hand(gs, sz=31):
    """gs: [(牌の並び, 種類, 下の札)]"""
    return '<div class="hand">' + "".join(f'<div class="bk" style="--c:{COL[k]}"><div class="ts">{w(cs, sz)}</div><span>{lb}</span></div>' for cs, k, lb in gs) + "</div>"
def big(n, cut, res, ok): return f'<div class="res {"ok" if ok else "ng"}"><div class="ct">{cut}</div><div class="rx">{res}</div><b>{n}<small>枚</small></b></div>'
body = f"""
<div class="bar" style="margin-top:0">アガリの形は、5つのブロック<small>面子4つ＋雀頭1つ</small></div>
<div class="box">{hand([("m2 m3 m4","m","面子"),("m6 m7 m8","m","面子"),("p4 p5 p6","m","面子"),("s3 s4 s5","m","面子"),("s8 s8","t","雀頭")], 33)}
<p>手牌を<b>5つに分けて</b>、足りない所を育てる。6つ目のブロックと、どこにも入らない牌は、最後には要らなくなる</p></div>
<div class="bar">① 5つあるとき　余った牌から切る</div>
<div class="box">{hand([("m2 m3 m4","m","1 面子"),("m6 m7","r","2 両面"),("p4 p5 p6","m","3 面子"),("s3 s5","k","4 嵌張"),("s8 s8","t","5 雀頭"),("p9","x","余り"),("z6","x","余り")], 31)}
<div class="rs">{big(12, w("p9") + " か " + w("z6") + " を切る", "受け入れ " + w("m5 m8 s4"), True)}<p class="sd">ブロックに入らない牌なら、どちらを切っても受け入れは同じ12枚。<b>ブロックを壊さない</b></p></div></div>
<div class="bar">② 6つあるとき　いちばん弱いブロックを切る</div>
<div class="box">{hand([("m2 m3 m4","m","1 面子"),("m6 m7","r","2 両面"),("p4 p5 p6","m","3 面子"),("s3 s4","r","4 両面"),("s8 s8","t","5 雀頭"),("p8 p9","x","6 辺張")], 31)}
<div class="rs">{big(16, w("p8 p9") + " を切る", "受け入れ " + w("m5 m8 s2 s5"), True)}{big(12, w("m6 m7") + " を切る", "受け入れ " + w("p7 s2 s5"), False)}</div></div>
<div class="bar">ブロックの強さ<small>埋まる牌の枚数</small></div>
<table class="st"><thead><tr><th></th><th>両面<small>リャンメン</small></th><th>嵌張<small>カンチャン</small></th><th>辺張<small>ペンチャン</small></th><th>対子<small>トイツ</small></th></tr></thead>
<tbody><tr><th class="rh">形</th><td>{w("p4 p5", 25)}</td><td>{w("p4 p6", 25)}</td><td>{w("p8 p9", 25)}</td><td>{w("p5 p5", 25)}</td></tr>
<tr><th class="rh">枚数</th><td class="n g">8枚</td><td class="n">4枚</td><td class="n">4枚</td><td class="n">2枚</td></tr>
<tr><th class="rh">育ち方</th><td>このままで強い</td><td>両面に変わりやすい</td><td>両面に変わりにくい</td><td>1組は雀頭になる</td></tr></tbody></table>
<div class="tip"><b>4つしかないとき</b>　真ん中の三〜七を残すと、新しいブロックになりやすい。字牌や一・九から切る</div>
<p class="note">受け入れ＝引くとテンパイする牌の枚数（自分の手牌のほかは見えていない場合）。役・打点・守りや、七対子などの別の手は考えない場合の基本の考え方</p>"""
css = """.box { background: #fff; border: 2px solid #1F2A28; border-top: 0; padding: 10px 12px 9px; } .box p { font-size: 13px; font-weight: 700; margin: 8px 0 0; line-height: 1.5; } .box p b { color: #E25A1C; }
.hand { display: flex; gap: 8px; justify-content: center; } .bk { text-align: center; border: 2.5px solid var(--c); border-radius: 7px; padding: 4px 4px 2px; } .bk .ts { display: flex; } .bk span { font-size: 12.5px; font-weight: 900; color: var(--c); white-space: nowrap; }
.rs { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 10px; align-items: center; } .box p.sd { margin: 0; }
.res { display: grid; grid-template-columns: 1fr auto; border-radius: 7px; padding: 6px 14px; align-items: center; font-size: 12.5px; font-weight: 800; } .res.ok { background: #E4F3EC; } .res.ng { background: #EDF0EF; color: #5C6A67; }
.res b { grid-row: 1 / 3; grid-column: 2; font-size: 30px; font-weight: 900; color: #E25A1C; } .res.ng b { color: #7C8A87; } .res b small { font-size: 13px; } .ct, .rx { white-space: nowrap; line-height: 1.9; }
.st td { text-align: center; font-size: 12px; } th small { display: block; font-size: 9.5px; color: #DDF0EC; } table { width: 100%; table-layout: fixed; } .st td.n { font-size: 18px; font-weight: 900; } .st td.g { color: #E25A1C; background: #FFF5EF; }"""
render(page("何を切る？は、5つに分ける", "5ブロックの考え方　覚えるのは「5」だけ", "面子4つ<br><span>＋雀頭</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "block5")
