import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
G = [("対局の前と後", [("よろしくお願いします", "", "始める前、全員がそろったとき", "あいさつから始めると気持ちよく打てる"),
                       ("ありがとうございました", "", "半荘・対局が終わったとき", "勝っても負けても")]),
     ("鳴くとき", [("ポン", "", "だれかが切った牌で、刻子を作るとき", "チーより先。はっきり大きな声で"),
                   ("チー", "", "上家が切った牌で、順子を作るとき", "ポンが優先なので、一拍おいてから"),
                   ("カン", "", "同じ牌4枚で槓子を作るとき", "暗槓は自分の番に。大明槓は人の切った牌で")]),
     ("アガるとき", [("ロン", "", "人が切った牌でアガるとき", "ポン・チーより優先"), ("ツモ", "", "自分で引いた牌でアガるとき", "アガリ牌は手牌に入れずに見せる")]),
     ("そのほか", [("リーチ", "", "門前でテンパイして、リーチするとき", "言ってから牌を横に切り、1,000点棒を出す"),
                  ("〇〇点（申告）", "", "アガったあと、点数を言うとき", "役は言わず、点数だけでよいことが多い")])]
body = ""
for g, items in G:
    rows = "".join(f'<tr><th class="rh w">{a}</th><td class="tx">{c}</td><td class="tx s">{d}</td></tr>' for a, b, c, d in items)
    body += f'<div class="bar">{g}</div><table><colgroup><col style="width:190px"><col><col style="width:300px"></colgroup><tbody>{rows}</tbody></table>'
body = body.replace('<div class="bar">', '<div class="bar" style="margin-top:0">', 1)
body += '<p class="note">流局のときは、テンパイの人は手牌を倒し、ノーテンの人は伏せるだけ（声はかけないことが多い）。声は相手に聞こえる大きさで、はっきりと</p>'
css = """th.w { font-size: 17px; font-weight: 900; color: #E25A1C; } td.tx { font-size: 12.5px; } td.s { color: #4C5B58; font-size: 12px; } tbody tr { height: 42px; }"""
render(page("麻雀の掛け声", "いつ、何と言うか", "声は<br><span>はっきりと</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "kakegoe")
