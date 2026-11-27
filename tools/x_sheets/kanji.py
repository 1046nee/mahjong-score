# 麻雀の難しい漢字40（プロ試験の筆記の用語をふくむ）。QUIZ=1 で、読みと意味を伏せた問題の版（kanji-q.png）
# 出題の裏付け（2026-11-25 に調べた）: 最高位戦のプロテストは麻雀用語の漢字の書き取りが出た時期があり、読みの問題が出た時期もある（受験者の分析 note.com/negihsoy_999。50期前期では無くなった）。
# 2026-11-27: 読みが2つ以上ある語は「・」で全部のせた（ウィキペディア「麻雀用語一覧」「和了」「壁牌」「荒牌平局」など。ユーザーの指定）。答えの版の出力は kanji-ans2
#   日本プロ麻雀協会も漢字の問題がある（範囲は競技規定。受験者の note.com/naoki_fujii）。どの語が出るかは団体・年で違う
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
Q = bool(os.environ.get("QUIZ"))
LV = [("初級", "卓でよく聞く", "#177083", [("聴牌", "テンパイ", "あと1枚でアガれる"), ("立直", "リーチ", "1,000点棒を出す"), ("自摸", "ツモ", "山から1枚取る"), ("面子", "メンツ", "3枚1組"), ("雀頭", "ジャントウ", "同じ牌2枚の頭"),
        ("嵌張", "カンチャン", "間の1種を待つ"), ("辺張", "ペンチャン", "三か七だけを待つ"), ("半荘", "ハンチャン", "東場と南場"), ("対子", "トイツ", "同じ牌2枚"), ("么九牌", "ヤオチューハイ・ヤオチューパイ", "一・九・字牌")]),
      ("中級", "本や放送で見る", "#4261AA", [("和了", "ホーラ・アガリ", "アガること"), ("副露", "フーロ", "鳴き"), ("搭子", "ターツ", "順子の手前の2枚"), ("双碰", "シャンポン", "対子2つで待つ"), ("振聴", "フリテン", "ロンできない状態"),
        ("起家", "チーチャ", "最初の親"), ("連荘", "レンチャン", "親が続く"), ("理牌", "リーパイ", "手牌を並べかえる"), ("王牌", "ワンパイ", "最後に残す14枚"), ("放銃", "ホウジュウ・ホーチャン", "ロンされる牌を切る")]),
      ("上級", "役の正式な名前", "#B8741A", [("断么九", "タンヤオ(チュー)", "二〜八だけ"), ("二盃口", "リャンペーコー", "一盃口が2組"), ("緑一色", "リューイーソー", "緑の牌だけ"), ("九蓮宝燈", "チューレンポウトウ・チューレンポートン", "1種類で9面待ちの役満"), ("搶槓", "チャンカン", "加槓の牌でロン"),
        ("嶺上開花", "リンシャンカイホウ", "カンの牌でツモ"), ("海底摸月", "ハイテイモーユエ", "最後の牌でツモ"), ("河底撈魚", "ホウテイラオユイ", "最後の捨て牌でロン"), ("混全帯么九", "ホンチャンタイヤオチュー", "チャンタ"), ("門前清自摸和", "メンゼンチンツモホー", "メンゼンツモ")]),
      ("プロ試験級", "読めたらすごい", "#C92F42", [("散家", "サンチャ", "子"), ("荘家", "チャンチャ・ソウチャ", "親"), ("洗牌", "シーパイ・センパイ", "牌をかき混ぜる"), ("砌牌", "チーパイ", "山を積む"), ("壁牌", "ピーパイ・ビーパイ", "積んだ山"),
        ("幢", "トン", "山の上下2枚1組"), ("摸打", "モウダ・モウター", "ツモって切る"), ("少牌", "ショウハイ・シャオパイ", "手牌が足りない"), ("四開槓", "スーカイカン", "カン4回の流局"), ("荒牌平局", "ホワンパイピンチュー・コウハイヘイキョク", "ふつうの流局")])]
n = 0; secs = ""
for nm, sb, c, ws in LV:
    cells = ""
    for k, y, m in ws:
        n += 1
        fs = {1: 34, 2: 34, 3: 30, 4: 26, 5: 23, 6: 19.5}[len(k)]; ys = 14 if len(y) <= 8 else 12.5 if len(y) <= 10 else 11 if len(y) <= 12 else 9.5
        an = '<div class="y q"></div>' if Q else (f'<div class="y" style="font-size:{ys}px">{y}</div>' if len(y) <= 13 else f'<div class="y" style="font-size:11.5px;height:auto;line-height:14px;padding:2px 0">{y.replace("・", "・<br>")}</div>') + f'<div class="m">{m}</div>'
        cells += f'<div class="c"><i>{n}</i>{"<u>読み2つ以上</u>" if "・" in y and not Q else ""}<div class="k" style="font-size:{fs}px">{k}</div>{an}</div>'
    secs += f'<div class="sec" style="--c:{c}"><div class="sb"><b>{nm}</b><span>{sb}</span><em>{n - 9}〜{n}</em></div><div class="g">{cells}</div></div>'
rank = [("0〜9", "これから"), ("10〜19", "脱初心者"), ("20〜29", "麻雀通"), ("30〜39", "プロ試験級"), ("40", "満点！")]
body = secs + '<div class="rank"><b>いくつ読めた？</b>' + "".join(f"<span><em>{a}</em>{b}</span>" for a, b in rank) + "</div>" + \
    '<p class="note">' + ("答えはリプライの画像に。" if Q else "「・」は、どちらの読みも使われるもの。") + "プロ試験の筆記で、麻雀用語の漢字が出た団体や年がある（この40語が出るという意味ではない）</p>"
css = """.sec { border: 2px solid var(--c); border-radius: 8px; overflow: hidden; margin-bottom: 9px; background: #fff; } .sb { display: flex; align-items: baseline; gap: 10px; background: var(--c); color: #fff; padding: 3px 12px; } .sb b { font-size: 18px; font-weight: 900; } .sb span { font-size: 12.5px; font-weight: 700; } .sb em { margin-left: auto; font-style: normal; font-size: 12px; font-weight: 800; }
.g { display: grid; grid-template-columns: repeat(5, 1fr); } .c { position: relative; text-align: center; padding: 9px 2px 7px; border-right: 1px solid #D5DEDC; border-bottom: 1px solid #D5DEDC; min-width: 0; } .c:nth-child(5n) { border-right: 0; } .c:nth-child(n+6) { border-bottom: 0; }
.c i { position: absolute; top: 3px; left: 6px; font-style: normal; font-size: 10.5px; font-weight: 900; color: var(--c); } .c .k { color: #1F2A28; font-weight: 900; line-height: 1.2; height: 44px; display: flex; align-items: center; justify-content: center; white-space: nowrap; }
.y { font-weight: 900; color: var(--c); white-space: nowrap; height: 20px; line-height: 20px; } .m { font-size: 11px; font-weight: 700; color: #4C5B58; white-space: nowrap; } .y.q { width: 78%; height: 26px; margin: 4px auto 3px; border: 1.5px dashed #A9B6B3; border-radius: 5px; }
.c u { position: absolute; top: 3px; right: 4px; text-decoration: none; font-size: 8.5px; font-weight: 900; color: #fff; background: #E25A1C; border-radius: 3px; padding: 0 3px; }
.rank { display: grid; grid-template-columns: auto repeat(5, 1fr); gap: 8px; align-items: center; background: #177083; color: #fff; border-radius: 8px; padding: 8px 12px; } .rank b { font-size: 16px; font-weight: 900; } .rank span { text-align: center; font-size: 12.5px; font-weight: 800; background: rgba(255,255,255,.14); border-radius: 6px; padding: 3px 0; } .rank em { display: block; font-style: normal; font-size: 15px; font-weight: 900; color: #FFE27A; }"""
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "まじゃすこ素材", "x", "kanji", "kanji-ans2")
if len(sys.argv) < 2 and Q: out = os.path.join(ROOT, "まじゃすこ素材", "x", "kanji", "kanji-q"); os.makedirs(os.path.dirname(out), exist_ok=True)
render(page("麻雀の漢字、読める？", "プロ試験の筆記に出るような用語も　全40問" + ("" if Q else "の答え"), "いくつ<br><span>読める？</span>" if Q else "読みと<br><span>意味つき</span>", body, css), out)
