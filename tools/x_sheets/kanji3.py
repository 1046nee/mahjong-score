# 麻雀の難しい漢字40 第3弾・最終回（第1弾 kanji.py・第2弾 kanji2.py の80語とは別の語。門風・吃・碰はユーザーの指定 2026-11-28）。QUIZ=1 で問題の版（kanji3-q.png）
# 読みは漢字辞典 jiten.py（2026-11-27 に複数の出どころで確かめた）と同じ
# 読みの出どころ（2026-11-27 に照らし合わせた）: ウィキペディア「麻雀用語一覧」「麻雀牌」「和了」「壁牌」・麻雀豆腐の用語集・雀魂の用語集（game8）・最高位戦の競技規定。
#   読みが2つ以上ある語は「・」で全部のせる（2026-11-27 ユーザーの指定「読み方が一通りじゃないものもあるので、いろんな情報源で確かめる」）
# 出題の裏付け（2026-11-25 に調べた）: 最高位戦のプロテストは麻雀用語の漢字の書き取りが出た時期があり、読みの問題が出た時期もある（受験者の分析 note.com/negihsoy_999。50期前期では無くなった）。
#   日本プロ麻雀協会も漢字の問題がある（範囲は競技規定。受験者の note.com/naoki_fujii）。どの語が出るかは団体・年で違う
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
Q = bool(os.environ.get("QUIZ"))
LV = [("初級", "卓でよく聞く", "#177083", [("吃", "チー", "上家の牌で順子"), ("碰", "ポン", "人の牌で刻子"), ("槓", "カン", "同じ牌4枚で鳴く"), ("暗刻", "アンコ", "自分でそろえた刻子"), ("明刻", "ミンコ", "鳴いてそろえた刻子"),
        ("手牌", "テハイ", "持っている牌"), ("配牌", "ハイパイ", "最初の手牌"), ("打牌", "ダハイ", "牌を切る"), ("他家", "ターチャ", "自分以外の3人"), ("場風", "バカゼ", "東場なら東")]),
      ("中級", "本や放送で見る", "#4261AA", [("門風", "メンフォン", "自分の席の風"), ("両面", "リャンメン", "両側の2種を待つ"), ("栄和", "ロンホー・ロン", "人の牌でアガる"), ("自摸和", "ツモホー", "ツモでアガる"), ("不聴", "ノーテン", "テンパイしていない"),
        ("一向聴", "イーシャンテン", "あと1枚でテンパイ"), ("跳満", "ハネマン", "6翻から"), ("倍満", "バイマン", "8翻から"), ("喰い断", "クイタン", "鳴いて断么九"), ("罰符", "バップ", "反則で払う点")]),
      ("上級", "役の正式な名前", "#B8741A", [("平和", "ピンフ", "順子4つと両面待ち"), ("一盃口", "イーペーコー", "同じ順子2つ"), ("三色同刻", "サンショクドウコー", "3色で同じ刻子"), ("混老頭", "ホンロウトウ", "一・九・字牌だけ"),
        ("小三元", "ショウサンゲン", "三元牌2つと雀頭"), ("大三元", "ダイサンゲン", "三元牌の刻子3つ"), ("清老頭", "チンロウトウ", "一と九だけ"), ("大四喜", "ダイスーシー", "風牌の刻子4つ"), ("天和", "テンホー", "親が配牌でアガる"), ("地和", "チーホー", "子が最初のツモでアガる")]),
      ("プロ試験級", "読めたらすごい", "#C92F42", [("尖張牌", "センチャンパイ", "三と七の数牌"), ("中張牌", "チュンチャンパイ", "二〜八の数牌"), ("熟牌", "シューパイ", "場に出ている牌"), ("懸賞牌", "ドラ", "ドラの古い書き方"), ("輪荘", "リンチャン・ロンチャン", "親が移る"),
        ("副底", "フーテイ", "必ず付く20符"), ("九種九牌", "キュウシュキュウハイ", "么九牌9種で流局"), ("四家立直", "スーチャリーチ", "4人リーチで流局"), ("三家和", "サンチャホー", "3人ロンで流局"), ("四槓散了", "スーカンサンラ", "2人以上で4回カンの流局")])]
n = 0; secs = ""
for nm, sb, c, ws in LV:
    cells = ""
    for k, y, m in ws:
        n += 1
        fs = {1: 34, 2: 34, 3: 30, 4: 26, 5: 23, 6: 19.5}[len(k)]; ys = 14 if len(y) <= 8 else 12.5 if len(y) <= 10 else 11 if len(y) <= 12 else 9.5 if len(y) <= 16 else 7.6
        an = '<div class="y q"></div>' if Q else (lambda yy: f'<div class="y" style="font-size:{14 if len(yy[0]) <= 8 else 12.5 if len(yy[0]) <= 10 else 11}px">{yy[0]}</div>' + (f'<div class="alt">（{yy[1]}）</div>' if len(yy) > 1 else '') + f'<div class="m">{m}</div>')(y.split("・"))      # 読みはメインを上、別の読みをカッコで下（2026-11-27 ユーザーの指定）
        multi = "・" in y
        cells += f'<div class="c"><i>{n}</i>{"<u>別の読みあり</u>" if multi and not Q else ""}<div class="k" style="font-size:{fs}px">{k}</div>{an}</div>'
    secs += f'<div class="sec" style="--c:{c}"><div class="sb"><b>{nm}</b><span>{sb}</span><em>{n - 9}〜{n}</em></div><div class="g">{cells}</div></div>'
rank = [("0〜9", "これから"), ("10〜19", "脱初心者"), ("20〜29", "麻雀通"), ("30〜39", "プロ試験級"), ("40", "満点！")]
body = secs + '<div class="rank"><b>いくつ読めた？</b>' + "".join(f"<span><em>{a}</em>{b}</span>" for a, b in rank) + "</div>" + \
    '<p class="note">' + ("答えはリプライの画像に。" if Q else "（ ）は、別の読み方。") + "プロ試験の筆記で、麻雀用語の漢字が出た団体や年がある（この40語が出るという意味ではない）</p>"
css = """.sec { border: 2px solid var(--c); border-radius: 8px; overflow: hidden; margin-bottom: 9px; background: #fff; } .sb { display: flex; align-items: baseline; gap: 10px; background: var(--c); color: #fff; padding: 3px 12px; } .sb b { font-size: 18px; font-weight: 900; } .sb span { font-size: 12.5px; font-weight: 700; } .sb em { margin-left: auto; font-style: normal; font-size: 12px; font-weight: 800; }
.g { display: grid; grid-template-columns: repeat(5, 1fr); } .c { position: relative; text-align: center; padding: 9px 2px 7px; border-right: 1px solid #D5DEDC; border-bottom: 1px solid #D5DEDC; min-width: 0; } .c:nth-child(5n) { border-right: 0; } .c:nth-child(n+6) { border-bottom: 0; }
.c i { position: absolute; top: 3px; left: 6px; font-style: normal; font-size: 10.5px; font-weight: 900; color: var(--c); } .c .k { color: #1F2A28; font-weight: 900; line-height: 1.2; height: 44px; display: flex; align-items: center; justify-content: center; white-space: nowrap; }
.y { font-weight: 900; color: var(--c); white-space: nowrap; height: 20px; line-height: 20px; } .m { font-size: 11px; font-weight: 700; color: #4C5B58; white-space: nowrap; } .y.q { width: 78%; height: 26px; margin: 4px auto 3px; border: 1.5px dashed #A9B6B3; border-radius: 5px; }
.alt { font-size: 11px; font-weight: 800; color: #6B7A77; line-height: 14px; white-space: nowrap; } .c u { position: absolute; top: 3px; right: 4px; text-decoration: none; font-size: 8.5px; font-weight: 900; color: #fff; background: #E25A1C; border-radius: 3px; padding: 0 3px; } .fix { margin-top: 8px; border: 2px solid #E25A1C; border-radius: 8px; background: #FFF4EE; padding: 6px 12px; font-size: 12.5px; font-weight: 700; color: #1F2A28; line-height: 1.6; } .fix b { color: #E25A1C; font-weight: 900; margin-right: 8px; }
.rank { display: grid; grid-template-columns: auto repeat(5, 1fr); gap: 8px; align-items: center; background: #177083; color: #fff; border-radius: 8px; padding: 8px 12px; } .rank b { font-size: 16px; font-weight: 900; } .rank span { text-align: center; font-size: 12.5px; font-weight: 800; background: rgba(255,255,255,.14); border-radius: 6px; padding: 3px 0; } .rank em { display: block; font-style: normal; font-size: 15px; font-weight: 900; color: #FFE27A; }"""
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "まじゃすこ素材", "x", "kanji", "kanji3")
if len(sys.argv) < 2 and Q: out = os.path.join(ROOT, "まじゃすこ素材", "x", "kanji", "kanji3-q"); os.makedirs(os.path.dirname(out), exist_ok=True)
render(page("麻雀の漢字、読める？ 最終回", "第1弾・第2弾と別の40語　全40問" + ("" if Q else "の答え"), "いくつ<br><span>読める？</span>" if Q else "読みと<br><span>意味つき</span>", body, css), out)
