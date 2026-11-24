import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
from rule_compare_sheet import badge  # noqa: E402  Mリーグ・雀魂の印（流局の種類と同じ）
# Mリーグ・雀魂の列（2026-11-24 ユーザーの指定）。Mリーグ＝公式サイト m-league.jp/about の公式戦ルール第7章（2026-11-24 に確認）。
# フリテンでのロンは公式ルールに名指しが無い。「正当でないアガリを宣言し、手牌を公開」（チョンボ）に当たるので、チョンボと書く。
# 雀魂はゲームの仕様上、どれも発生しない（「ゲームが止める」とは書かない。2026-11-24 ユーザーの指定。ロン・リーチ・鳴きのボタンは、できるときにしか出ない）。各表の雀魂の列は1つのます
# Mの値: "c|補足"＝チョンボ・"a|補足"＝アガリ放棄・"y|補足"＝イエローカード。
# 手牌を倒した＝第5条の「故意とは認められない2枚以上の見せ牌（山・手牌共通）」でイエローカード、故意は第4条2(4)でチョンボ。山を崩す＝第4条2(3)〜(5)（点棒授受前・故意・築牌時に続行不可能）だけがチョンボ（2026-11-24 に原文で確認）
CH = [("誤ロン・誤ツモ", "ゴロン・ゴツモ", "アガっていないのに「ロン」「ツモ」と言って、手牌を倒した", "c|倒す前ならアガリ放棄"),
      ("フリテンでロン", "", "自分の河に待ちの牌があるのに、ロンした", "c|正当でないアガリ"),
      ("ノーテンリーチ", "", "テンパイしていないのにリーチして、流局で手牌を見せた", "c|分かったときか流局で"),
      ("山を大きく崩す", "", "山を崩して、そのあとのツモが分からなくなった", "c|続行不可・わざとなら")]
AH = [("多牌・少牌", "ターハイ・ショウハイ", "手牌の数が多い・少ない（ツモ忘れ・2枚ツモなど）", "a|"),
      ("手牌を倒した", "", "鳴き・アガリ以外で、手牌を見せてしまった", "y|2枚以上で<br>わざとならチョンボ"),
      ("誤ポン・誤チー", "", "声をかけたあとに、鳴けない・やめた（ルールにより注意だけ）", "a|鳴きは取り消し")]
CA = [("喰い替え", "クイカエ", "鳴いた直後に、切れない牌を切った", "打ち直し・チョンボなど", "a|"),
      ("見せ牌", "ミセハイ", "手牌や、次にツモる牌を見せてしまった", "注意・その牌でアガれない", "y|2枚以上で"),
      ("先ヅモ", "サキヅモ", "上家が切る前に山に手をのばした", "注意（くり返すとアガリ放棄）", "a|")]
ML = {"c": ("チョンボ", "mc"), "a": ("アガリ放棄", "ma"), "y": ("イエロー<br>カード", "my")}
def m(v):
    k, _, t = v.partition("|"); lab, cls = ML[k]
    return f'<td class="ml {cls}">{lab}{f"<small>{t}</small>" if t else ""}</td>'
def jan(n): return f'<td class="jn" rowspan="{n}">発生<br>しない<small>ゲームの<br>仕様上</small></td>'
def rows(items):
    return "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="tx">{c}</td>{m(d)}{jan(len(items)) if i == 0 else ""}</tr>' for i, (a, b, c, d) in enumerate(items))
ca = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="tx">{c}</td><td class="tx o2">{d}</td>{m(e)}{jan(len(CA)) if i == 0 else ""}</tr>' for i, (a, b, c, d, e) in enumerate(CA))
HD = f'<th class="lo">{badge("M")}<br>Mリーグ</th><th class="lo">{badge("J")}<br>雀魂</th>'
COLS = '<col style="width:108px"><col style="width:72px">'
body = f"""
<div class="bar red" style="margin-top:0">チョンボ<small>満貫を払うのがふつう（子は親に4,000・子に2,000、親は4,000ずつ）。その局はやり直し</small></div>
<table><colgroup><col style="width:140px"><col>{COLS}</colgroup><thead><tr><th>反則</th><th>どんなとき</th>{HD}</tr></thead><tbody>{rows(CH)}</tbody></table>
<div class="bar blue">アガリ放棄<small>その局はアガれない。ツモと打牌だけ続ける（流局ではノーテン扱い）</small></div>
<div class="ah"><span class="lb">アガリ放棄の人は</span><span class="cx">チー ✕</span><span class="cx">ポン ✕</span><span class="cx">カン ✕</span><span class="cx">リーチ ✕</span><span class="co">ツモ・打牌 ○</span><span class="nt">{badge("M")} Mリーグも同じ。破るとチョンボ</span></div>
<table><colgroup><col style="width:140px"><col>{COLS}</colgroup><tbody>{rows(AH)}</tbody></table>
<div class="bar gray">場所で扱いが違うもの</div>
<table><colgroup><col style="width:140px"><col><col style="width:162px">{COLS}</colgroup><thead><tr><th>反則</th><th>どんなとき</th><th>よくある扱い</th>{HD}</tr></thead><tbody>{ca}</tbody></table>
<div class="tip"><b>Mリーグのチョンボ</b>は、満貫を払うのではなく<b>スコアから20pt引く</b>（親でも子でも同じ）。その局はやり直しで、積み棒は増えない。<br>イエローカードは1日に2枚でレッドカードになり、同じく20pt引かれる。<br>
<b>始める前に決めておく</b>　チョンボの払い方と、どれをアガリ放棄にするかは、場所やルールでかなり違う。<br>もめないように、最初に確かめておくと安心。</div>
<p class="note">Mリーグは公式サイトの公式戦ルール（2026年11月）<br>雀魂はゲームの仕様上、これらの反則は発生しない（ロン・リーチ・鳴きのボタンは、できるときにしか出ない）</p>"""
css = """.bar.red { background: #C92F42; } .bar.blue { background: #4261AA; } .bar.gray { background: #5E6B69; } .bar small { color: #fff; opacity: .92; }
td.tx { font-size: 12.5px; } td.o2 { color: #B23A0E; font-size: 12px; } tbody tr { height: 44px; } table + .bar { margin-top: 12px; }
.ah { display: flex; align-items: center; gap: 6px; background: #fff; border: 2px solid #1F2A28; border-bottom: 0; padding: 7px 10px; font-size: 12.5px; font-weight: 900; }      /* アガリ放棄の人ができないこと（2026-11-24 ユーザーの指定）。Mリーグ公式戦ルール第7章第2条1 */
.ah .lb { color: #4261AA; margin-right: 4px; } .ah .cx, .ah .co { border-radius: 12px; padding: 2px 10px; } .ah .cx { color: #C92F42; background: #FDECEE; } .ah .co { color: #177083; background: #E4F3EC; }
.ah .nt { margin-left: auto; font-size: 11px; font-weight: 800; color: #4F5C5A; display: inline-flex; align-items: center; gap: 4px; }
td.ml { text-align: center; font-size: 12.5px; font-weight: 900; line-height: 1.2; padding: 4px 3px; } td.ml small { display: block; font-size: 9.5px; font-weight: 800; color: #4F5C5A; margin-top: 2px; line-height: 1.3; }
td.mc { color: #C92F42; background: #FDECEE; } td.ma { color: #4261AA; background: #EAF0FB; } td.my { color: #9A6A00; background: #FFF6D6; }
td.jn { text-align: center; font-size: 13px; font-weight: 900; color: #177083; background: #E4F3EC; line-height: 1.3; } td.jn small { display: block; font-size: 10px; font-weight: 800; color: #4F5C5A; margin-top: 3px; }
th.lo { font-size: 10.5px; line-height: 1.5; } th.lo i { --d: 22px; margin: 0 !important; }
i.bm, i.bj { --d: 17px; font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: var(--d); height: var(--d); border-radius: 50%; overflow: hidden; background: #fff; box-shadow: 0 0 0 1.5px #fff; flex: none; vertical-align: middle; }
i.bm img { height: 72%; width: auto; display: block; } i.bj img { width: 100%; height: 100%; display: block; }"""
render(page("チョンボとアガリ放棄", "やってしまいやすい反則と、よくある扱い", "まずは<br><span>ルール確認</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "chombo")
