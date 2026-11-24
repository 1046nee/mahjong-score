import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
Y = ["z1", "m1", "m9", "p1", "p9", "s1", "z5", "z6", "z7"]
ROWS = [
 ("荒牌平局", "ホワンパイピンチュー", "ふつうの流局", "山が無くなって、だれもアガれなかった", "".join(tl(c, 17) for c in ["back"] * 7) + '<span class="mi">王牌14枚だけ</span>', "あり", "テンパイなら続く"),
 ("九種九牌", "キュウシュキュウハイ", "途中流局", "最初のツモのときに、<b class='o'>么九牌が9種類以上</b>ある（鳴きが入る前）。言えば流せる", "".join(tl(c, 17) for c in Y), "なし", "続く（やり直す）"),
 ("四風連打", "スーフーレンダ", "途中流局", "1巡目に、4人が<b class='o'>同じ風牌</b>を切った（鳴きが入る前）", "".join(tl("z2", 17) for _ in range(4)), "なし", "続く"),
 ("四開槓", "スーカイカン", "途中流局", "<b class='o'>2人以上</b>で、カンが合わせて4回（1人で4回なら流れない）", tl("back", 17) + tl("z3", 17) + tl("z3", 17) + tl("back", 17) + '<span class="mi">×4回</span>', "なし", "続く"),
 ("四家立直", "スーチャリーチ", "途中流局", "<b class='o'>4人全員</b>がリーチした（4人目のリーチが通ったとき）", '<span class="mi">リーチ ×4人</span>', "なし", "続く"),
 ("三家和", "サンチャホー", "途中流局", "1枚の牌に、<b class='o'>3人が同時にロン</b>した", '<span class="mi">ロン ×3人</span>', "なし", "続く"),
]
# Mリーグ・雀魂（段位戦）で採用されているか（2026-11-23 ユーザーの指定）。Mリーグ公式サイト＝途中流局なし・3人同時ロンは頭ハネ。
# Wikipedia「雀魂」＝九種九牌・四風連打・四家立直・四開槓あり、3人同時ロンはトリロン（三家和にならない）。ルールチェックシートと同じ
# ○×の下に、採用していないときにどうなるかを小さく書く（2026-11-23 ユーザーの指定「三家和はMリーグは頭ハネ・雀魂はトリロンと載せる」）
USE = {"荒牌平局": ("○", "○"), "九種九牌": ("×|続ける", "○"), "四風連打": ("×|続ける", "○"), "四開槓": ("×|続ける<br>5回目のカンは<br>できない", "○"), "四家立直": ("×|続ける", "○"),
       "三家和": ("×|頭ハネで<br>1人のアガリ", "×|トリロンで<br>3人ともアガリ")}
sys.path.insert(0, TOOLS)
from rule_compare_sheet import badge
if WEB: badge = text_badge  # noqa: E402  ロゴ（Mリーグ・雀魂の印。元の画像は非公開の素材リポジトリ）
def yn(v):
    m, _, t = v.partition("|")
    return f'<td class="yn {"y" if m == "○" else "n"}">{m}{f"<small>{t}</small>" if t else ""}</td>'
rows = "".join(f'<tr><th class="rh">{a}<small>{b}</small></th><td class="kd {"f" if c == "ふつうの流局" else ""}">{c}</td><td class="tx">{d}<div class="pic">{e}</div></td><td class="mk">{f}</td><td class="tx c">{g}</td>{yn(USE[a][0])}{yn(USE[a][1])}</tr>' for a, b, c, d, e, f, g in ROWS)
body = f"""
<div class="bar" style="margin-top:0">6つの流局<small>アガリが出ないまま局が終わること</small></div>
<table><colgroup><col style="width:112px"><col style="width:80px"><col><col style="width:58px"><col style="width:112px"><col style="width:72px"><col style="width:72px"></colgroup>
<thead><tr><th>名前</th><th>種類</th><th>起きるとき</th><th>ノーテン<br>罰符</th><th>親は</th><th class="lo">{badge("M")}<br>Mリーグ</th><th class="lo">{badge("J")}<br>雀魂</th></tr></thead><tbody>{rows}</tbody></table>
<div class="tip"><b>途中流局</b>は、山が残っていても局を流す決まり。流れたら<b>本場が1つ増える</b>（積み棒が1本ふえる）。リーチ棒（供託）は場に残って、次にアガった人がもらう。</div>
<p class="note">途中流局をありにするか、九種九牌を親が流したときに親が続くかは、ルールで違う。右の2列はMリーグの公式戦ルールと雀魂の段位戦（2026年11月）</p>"""
css = """td.tx { font-size: 12px; } td.c { text-align: center; } .pic { margin-top: 3px; display: flex; align-items: center; gap: 1px; } .mi { font-size: 10.5px; font-weight: 800; color: #6B7A77; margin: 0 4px; }
td.kd { text-align: center; font-size: 11px; font-weight: 900; color: #4261AA; } td.kd.f { color: #177083; } td.mk { text-align: center; font-size: 14px; font-weight: 900; }
tbody tr { height: 60px; }
td.yn { text-align: center; font-size: 22px; font-weight: 900; line-height: 1.1; padding: 4px 2px; } td.yn small { display: block; font-size: 9.5px; font-weight: 800; color: #4F5C5A; line-height: 1.3; margin-top: 3px; } td.yn.y { color: #177083; background: #E4F3EC; } td.yn.n { color: #C92F42; }
th.lo { font-size: 10.5px; line-height: 1.5; } th.lo i { --d: 24px; margin: 0 !important; }
i.bm, i.bj { --d: 17px; font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: var(--d); height: var(--d); border-radius: 50%; overflow: hidden; background: #fff; box-shadow: 0 0 0 1.5px #fff; flex: none; vertical-align: middle; }
i.bm img { height: 72%; width: auto; display: block; } i.bj img { width: 100%; height: 100%; display: block; }"""
render(page("流局の種類", "アガリなしで局が終わる6つのパターン", "途中流局は<br><span>本場+1</span>", body, css), sys.argv[1] if len(sys.argv) > 1 else "ryukyoku")
