# 麻雀の難しい漢字40 第2弾（第1弾 kanji.py の40語とは別の語）。QUIZ=1 で問題の版（kanji2-q.png）
# 読みの出どころ（2026-11-27 に照らし合わせた）: ウィキペディア「麻雀用語一覧」「麻雀牌」「和了」「壁牌」・麻雀豆腐の用語集・雀魂の用語集（game8）・最高位戦の競技規定。
#   読みが2つ以上ある語は「・」で全部のせる（2026-11-27 ユーザーの指定「読み方が一通りじゃないものもあるので、いろんな情報源で確かめる」）
# 出題の裏付け（2026-11-25 に調べた）: 最高位戦のプロテストは麻雀用語の漢字の書き取りが出た時期があり、読みの問題が出た時期もある（受験者の分析 note.com/negihsoy_999。50期前期では無くなった）。
#   日本プロ麻雀協会も漢字の問題がある（範囲は競技規定。受験者の note.com/naoki_fujii）。どの語が出るかは団体・年で違う
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
Q = bool(os.environ.get("QUIZ"))
LV = [("初級", "卓でよく聞く", "#177083", [("上家", "カミチャ・シャンチャ", "左どなりの人"), ("下家", "シモチャ", "右どなりの人"), ("対面", "トイメン", "向かいの人"), ("刻子", "コーツ", "同じ牌3枚"), ("順子", "シュンツ", "続いた3枚"),
        ("槓子", "カンツ", "同じ牌4枚"), ("向聴", "シャンテン", "テンパイまでの数"), ("字牌", "ジハイ・ツーパイ", "東南西北白發中"), ("数牌", "シュウパイ・スウパイ", "一〜九の牌"), ("自風", "ジカゼ・ジフウ", "自分の席の風")]),
      ("中級", "本や放送で見る", "#4261AA", [("黙聴", "ダマテン", "リーチしないテンパイ"), ("単騎", "タンキ", "雀頭を待つ"), ("供託", "キョウタク", "場に出した点棒"), ("現物", "ゲンブツ", "その人が切った牌"), ("生牌", "ションパイ", "まだ1枚も出ていない牌"),
        ("包", "パオ", "責任払い"), ("盲牌", "モウパイ", "指で牌を読む"), ("錯和", "チョンボ", "アガリの間違いなど"), ("形式聴牌", "ケイシキテンパイ", "役が無いテンパイ"), ("立直棒", "リーチボウ", "リーチで出す1,000点棒")]),
      ("上級", "役の正式な名前", "#B8741A", [("一気通貫", "イッキツウカン", "一〜九がそろう"), ("三色同順", "サンショクドウジュン", "3色で同じ順子"), ("対々和", "トイトイホー", "刻子4つ"), ("七対子", "チートイツ", "対子7つ"), ("混一色", "ホンイーソー・ホンイツ", "1色と字牌"),
        ("清一色", "チンイーソー・チンイツ", "1色だけ"), ("国士無双", "コクシムソウ", "么九牌13種"), ("四暗刻", "スーアンコー・スーアンコウ", "暗刻4つ"), ("字一色", "ツーイーソー", "字牌だけ"), ("小四喜", "ショウスーシー", "風牌3つと雀頭")]),
      ("プロ試験級", "読めたらすごい", "#C92F42", [("客風牌", "オタカゼハイ・コーフォンパイ・キャクフウハイ", "役にならない風"), ("圏風牌", "チャンフォンパイ・ケンフォンパイ", "場風の牌"), ("連風牌", "レンフォンパイ・リェンフォンパイ", "場風で自風の牌"), ("老頭牌", "ロウトウハイ・ラオトウパイ", "一と九の数牌"), ("骰子", "シャイツ", "サイコロ"),
        ("推牌", "トイパイ", "山を前に押し出す"), ("開門", "カイメン", "山を割ること"), ("四風子連打", "スーフォンツレンター", "同じ風4枚の流局"), ("十三么九", "シーサンヤオチュー", "国士無双の別の名"), ("十二落抬", "シーアルラオタイ", "4つ鳴いて裸単騎")])]
n = 0; secs = ""
for nm, sb, c, ws in LV:
    cells = ""
    for k, y, m in ws:
        n += 1
        fs = {1: 34, 2: 34, 3: 30, 4: 26, 5: 23, 6: 19.5}[len(k)]; ys = 14 if len(y) <= 8 else 12.5 if len(y) <= 10 else 11 if len(y) <= 12 else 9.5 if len(y) <= 16 else 7.6
        an = '<div class="y q"></div>' if Q else (f'<div class="y" style="font-size:{ys}px">{y}</div>' if len(y) <= 13 else f'<div class="y" style="font-size:11.5px;height:auto;line-height:14px;padding:2px 0">{y.replace("・", "・<br>")}</div>') + f'<div class="m">{m}</div>'
        multi = "・" in y
        cells += f'<div class="c"><i>{n}</i>{"<u>読み2つ以上</u>" if multi and not Q else ""}<div class="k" style="font-size:{fs}px">{k}</div>{an}</div>'
    secs += f'<div class="sec" style="--c:{c}"><div class="sb"><b>{nm}</b><span>{sb}</span><em>{n - 9}〜{n}</em></div><div class="g">{cells}</div></div>'
rank = [("0〜9", "これから"), ("10〜19", "脱初心者"), ("20〜29", "麻雀通"), ("30〜39", "プロ試験級"), ("40", "満点！")]
body = secs + '<div class="rank"><b>いくつ読めた？</b>' + "".join(f"<span><em>{a}</em>{b}</span>" for a, b in rank) + "</div>" + \
    '<p class="note">' + ("答えはリプライの画像に。" if Q else "「・」は、どちらの読みも使われるもの。") + "プロ試験の筆記で、麻雀用語の漢字が出た団体や年がある（この40語が出るという意味ではない）</p>" + \
    ("" if Q else '<div class="fix"><b>第1弾の補足</b>放銃は「ホウジュウ」のほか「ホーチャン」とも読む。洗牌は「シーパイ」のほか「センパイ」とも読み、雀荘では牌を拭いてきれいにすることも「センパイ」という</div>')
css = """.sec { border: 2px solid var(--c); border-radius: 8px; overflow: hidden; margin-bottom: 9px; background: #fff; } .sb { display: flex; align-items: baseline; gap: 10px; background: var(--c); color: #fff; padding: 3px 12px; } .sb b { font-size: 18px; font-weight: 900; } .sb span { font-size: 12.5px; font-weight: 700; } .sb em { margin-left: auto; font-style: normal; font-size: 12px; font-weight: 800; }
.g { display: grid; grid-template-columns: repeat(5, 1fr); } .c { position: relative; text-align: center; padding: 9px 2px 7px; border-right: 1px solid #D5DEDC; border-bottom: 1px solid #D5DEDC; min-width: 0; } .c:nth-child(5n) { border-right: 0; } .c:nth-child(n+6) { border-bottom: 0; }
.c i { position: absolute; top: 3px; left: 6px; font-style: normal; font-size: 10.5px; font-weight: 900; color: var(--c); } .c .k { color: #1F2A28; font-weight: 900; line-height: 1.2; height: 44px; display: flex; align-items: center; justify-content: center; white-space: nowrap; }
.y { font-weight: 900; color: var(--c); white-space: nowrap; height: 20px; line-height: 20px; } .m { font-size: 11px; font-weight: 700; color: #4C5B58; white-space: nowrap; } .y.q { width: 78%; height: 26px; margin: 4px auto 3px; border: 1.5px dashed #A9B6B3; border-radius: 5px; }
.c u { position: absolute; top: 3px; right: 4px; text-decoration: none; font-size: 8.5px; font-weight: 900; color: #fff; background: #E25A1C; border-radius: 3px; padding: 0 3px; } .fix { margin-top: 8px; border: 2px solid #E25A1C; border-radius: 8px; background: #FFF4EE; padding: 6px 12px; font-size: 12.5px; font-weight: 700; color: #1F2A28; line-height: 1.6; } .fix b { color: #E25A1C; font-weight: 900; margin-right: 8px; }
.rank { display: grid; grid-template-columns: auto repeat(5, 1fr); gap: 8px; align-items: center; background: #177083; color: #fff; border-radius: 8px; padding: 8px 12px; } .rank b { font-size: 16px; font-weight: 900; } .rank span { text-align: center; font-size: 12.5px; font-weight: 800; background: rgba(255,255,255,.14); border-radius: 6px; padding: 3px 0; } .rank em { display: block; font-style: normal; font-size: 15px; font-weight: 900; color: #FFE27A; }"""
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "まじゃすこ素材", "x", "kanji", "kanji2")
if len(sys.argv) < 2 and Q: out = os.path.join(ROOT, "まじゃすこ素材", "x", "kanji", "kanji2-q"); os.makedirs(os.path.dirname(out), exist_ok=True)
render(page("麻雀の漢字、読める？ 第2弾", "第1弾と別の40語　全40問" + ("" if Q else "の答え"), "いくつ<br><span>読める？</span>" if Q else "読みと<br><span>意味つき</span>", body, css), out)
