import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
CH = [("誤ロン・誤ツモ", "ゴロン・ゴツモ", "アガっていないのに「ロン」「ツモ」と言って、手牌を倒した"),
      ("フリテンでロン", "", "自分の河に待ちの牌があるのに、ロンした"),
      ("ノーテンリーチ", "", "テンパイしていないのにリーチして、流局で手牌を見せた"),
      ("山を大きく崩す", "", "山を崩して、そのあとのツモが分からなくなった")]
AH = [("多牌・少牌", "ターハイ・ショウハイ", "手牌の数が多い・少ない（ツモ忘れ・2枚ツモなど）"),
      ("手牌を倒した", "", "鳴き・アガリ以外で、手牌を見せてしまった"),
      ("誤ポン・誤チー", "", "声をかけたあとに、鳴けない・やめた（ルールにより注意だけ）")]
CA = [("喰い替え", "クイカエ", "鳴いた直後に、切ってはいけない牌を切った", "打ち直し・チョンボなど"),
      ("見せ牌", "ミセハイ", "手牌や、次にツモる牌を見せてしまった", "注意・その牌でアガれない"),
      ("先ヅモ", "サキヅモ", "上家が切る前に山に手をのばした", "注意（くり返すとアガリ放棄）")]
def rows(items, cls): return "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="tx">{c}</td></tr>' for a, b, c in items)
ca = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="tx">{c}</td><td class="tx o2">{d}</td></tr>' for a, b, c, d in CA)
body = f"""
<div class="bar red" style="margin-top:0">チョンボ<small>満貫を払うのがふつう（子は親に4,000・子に2,000、親は4,000ずつ）。その局はやり直し</small></div>
<table><colgroup><col style="width:150px"><col></colgroup><tbody>{rows(CH, "r")}</tbody></table>
<div class="bar blue">アガリ放棄<small>その局はアガれない。ツモと打牌は続ける（流局ではノーテン扱い）</small></div>
<table><colgroup><col style="width:150px"><col></colgroup><tbody>{rows(AH, "b")}</tbody></table>
<div class="bar gray">場所で扱いが違うもの</div>
<table><colgroup><col style="width:150px"><col><col style="width:210px"></colgroup><tbody>{ca}</tbody></table>
<div class="tip"><b>始める前に決めておく</b>　チョンボの払い方（満貫・スコアから引くなど）と、どれをアガリ放棄にするかは、場所やルールでかなり違う。もめないように、最初に確かめておくと安心。</div>"""
css = """.bar.red { background: #C92F42; } .bar.blue { background: #4261AA; } .bar.gray { background: #5E6B69; } .bar small { color: #fff; opacity: .92; }
td.tx { font-size: 12.5px; } td.o2 { color: #B23A0E; font-size: 12px; } tbody tr { height: 40px; } table + .bar { margin-top: 12px; }"""
render(page("チョンボとアガリ放棄", "やってしまいやすい反則と、よくある扱い", "まずは<br><span>ルール確認</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "chombo")
