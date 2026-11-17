# -*- coding: utf-8 -*-
"""待ち当て5問（7枚形）の問題の画像（1080×1350。XとInstagramで共用。2026-11-17 ユーザーの指定）。
答えは載せない（答えはリプ欄で）。答えの確かめは machi3.py の waits（下の assert）。
出力: まじゃすこ素材/x/machi/quiz-7mai-sou.png ／ -man.png ／ -pin.png（画像の元は公開リポジトリに入れない）
正解の画像（答えのリプ用・2026-11-17〜）: quiz-7mai-sou-ans.png ／ -man-ans.png ／ -pin-ans.png（手・形の名前・待ちの牌・枚数。待ちは waits で出す）
実行: python tools/machi_sheet/quiz.py（問題3枚）／ python tools/machi_sheet/quiz.py --ans（正解3枚）
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import ROOT, T, TEAL, ORANGE, INK
from sheet_logo import LOGO_CSS, logo_html
import machi3 as M

# 色ごとの5問 (手, 答えの数字, 答えの枚数)（2026-11-17 ユーザーの指定。3日とも形が重ならない。4枚使いは萬子・筒子に2問ずつ。
# 萬子は四萬から・筒子は五筒からの手。筒子のQ1 1・2・2・1・1 は表に載っていない形＝表には足さない）
SETS = {
    "sou": ("s", "索子", [("2345567", "258", 9), ("2223444", "12345", 13), ("2222344", "134", 9), ("2333345", "1245", 13), ("2223334", "2345", 9)]),   # 11/17
    "man": ("m", "萬子", [("4455566", "456", 5), ("4446678", "569", 10), ("4555566", "3467", 13), ("4444666", "5", 4), ("4445678", "35689", 17)]),   # 11/18
    "pin": ("p", "筒子", [("5667789", "69", 5), ("5556677", "5678", 9), ("5557999", "678", 11), ("5555667", "467", 9), ("5556666", "47", 8)]),     # 11/19
}
for suit, _, qs in SETS.values():
    for h, a, n in qs:
        w = M.waits([suit + c for c in h], 2, 1)
        assert "".join(c[1] for c, _ in w) == a and sum(x for _, x in w) == n, (h, w)
DIR = os.path.join(ROOT, "まじゃすこ素材", "x", "machi")


def tile(code, w): return f'<img src="{T}/{code}.svg" style="width:{w}px">'


def html(suit, sname, QS):
    rows = "".join(
        f'<div class="q"><b>Q{i}</b><span class="hand">{"".join(tile(suit + c, 46) for c in h)}</span>'
        f'<span class="ask">何待ち？</span></div>' for i, (h, _, _) in enumerate(QS, 1))
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=block" rel="stylesheet">
<style>* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 540px; height: 675px; overflow: hidden; }}
body {{ font-family: 'Noto Sans JP', sans-serif; background: #EEF6F3; color: {INK}; padding: 20px 22px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: {TEAL}; color: #fff; border-radius: 8px; padding: 10px 14px; }}
header h1 {{ font-size: 30px; font-weight: 900; line-height: 1.15; letter-spacing: .02em; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 3px; letter-spacing: 0; }}
{LOGO_CSS} .logo-pill img {{ height: 30px; }}
.lead {{ margin: 14px 2px 8px; font-size: 14px; font-weight: 900; }} .lead em {{ font-style: normal; color: {ORANGE}; }}
.q {{ display: flex; align-items: center; gap: 10px; background: #fff; border: 2px solid #1F2A28; padding: 12px 12px; margin-top: -2px; }}
.q b {{ width: 44px; font-size: 24px; font-weight: 900; color: {TEAL}; }}
.q .hand {{ display: flex; gap: 2px; }} .q .hand img {{ display: block; }}
.q .ask {{ margin-left: auto; font-size: 15px; font-weight: 900; color: {ORANGE}; border: 2px dashed {ORANGE}; border-radius: 6px; padding: 6px 8px; white-space: nowrap; }}
.note {{ margin-top: 14px; font-size: 14px; font-weight: 700; line-height: 1.6; }}
footer {{ position: absolute; left: 22px; right: 22px; bottom: 14px; display: flex; justify-content: space-between; font-size: 11px; color: #6E7F7B; font-weight: 700; }}
footer b {{ color: {TEAL}; }}
</style></head><body>
<header><h1>待ち当て 5問<small>2面子1雀頭を作る形（7枚形）・全部{sname}</small></h1>{logo_html()}</header>
<p class="lead">待ちの牌を<em>全部</em>言えたら正解</p>
{rows}
<p class="note">全問正解なら中級者。答えはリプ欄に。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>全32形の表は「麻雀の待ちの形一覧」</span></footer>
</body></html>"""


KANJI = "〇一二三四五六七八九"


def shape_name(hand):
    """表（machi3.SECS）の形の名前。数字の並びが同じ（左右逆も）ものを探す。無ければ「表にない形」"""
    pat = M.pattern(hand)
    for _, _, _, rows in M.SECS:
        for name, _, h, _ in rows:
            if all(c[0] != "z" for c in h) and M.pattern(h) in (pat, pat[::-1]):
                return name
    return "表にない形"


def html_ans(suit, sname, QS):
    """正解の画像: 1問1行。横から見た図（手の牌＝斜め線・待ちの残り＝待ち方の色。解説の表と同じ描き方）＋待ち方ごとの待ち＋形の名前＋枚数（2026-11-17 ユーザーの指定）"""
    import detail as D
    rows = ""
    for i, (h, _, _) in enumerate(QS, 1):
        hand = [suit + c for c in h]
        ws = M.waits(hand, 2, 1)
        km = {w: D.kinds(hand, w, 2) for w, _ in ws}
        n = sum(x for _, x in ws)
        pat = "".join(map(str, M.pattern(hand)))
        rows += (f'<div class="q"><b>Q{i}</b><div class="body"><div class="sv">{D.side_view(hand, ws, km, scale=1.22)}</div>'
                 f'<div class="exs">{D.explain(hand, ws, km)}</div></div>'
                 f'<div class="rt"><span class="nm">{shape_name(hand)}</span><small class="pt">{pat}</small><span class="wn">{len(ws)}種<em>{n}</em>枚</span></div></div>')
    leg = "".join(f'<span class="lg" style="--c:{c}"><i></i>{t}</span>' for t, c in D.TYPES)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=block" rel="stylesheet">
<style>* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 540px; height: 675px; overflow: hidden; }}
body {{ font-family: 'Noto Sans JP', sans-serif; background: #EEF6F3; color: {INK}; padding: 20px 22px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: {TEAL}; color: #fff; border-radius: 8px; padding: 10px 14px; }}
header h1 {{ font-size: 30px; font-weight: 900; line-height: 1.15; letter-spacing: .02em; }} header h1 i {{ font-style: normal; color: #FFE68A; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 3px; letter-spacing: 0; }}
{LOGO_CSS} .logo-pill img {{ height: 30px; }}
.legend {{ display: flex; flex-wrap: wrap; align-items: center; gap: 4px 12px; margin: 8px 2px 6px; font-size: 11.5px; font-weight: 900; }}
.lg {{ display: inline-flex; align-items: center; gap: 4px; color: var(--c); }} .lg i {{ width: 16px; height: 9px; border-radius: 2px; background: var(--c); opacity: .5; }}
.lg.hd {{ color: {INK}; }} .lg.hd i {{ opacity: 1; background: repeating-linear-gradient(45deg, #1F2A28 0 1.4px, #fff 1.4px 3.2px); border: 1px solid #1F2A28; }}
.q {{ display: flex; align-items: center; gap: 4px; background: #fff; border: 2px solid #1F2A28; padding: 4px 8px 5px; margin-top: -2px; }}
.q > b {{ width: 32px; flex: none; font-size: 21px; font-weight: 900; color: {TEAL}; }}
.body {{ flex: 1; min-width: 0; }} .sv svg {{ display: block; }}
.exs {{ display: flex; flex-wrap: wrap; gap: 2px 10px; margin-top: 1px; }}
.rt {{ flex: none; width: 96px; text-align: right; line-height: 1.2; }}
.rt .nm {{ display: block; font-size: 11px; font-weight: 900; color: #33403D; }} .rt .pt {{ display: block; font-size: 10px; font-weight: 900; color: #6B7A77; letter-spacing: .1em; }}
.ex {{ display: inline-flex; align-items: center; gap: 4px; font-size: 12.5px; font-weight: 900; color: var(--c); }} .ex b {{ background: var(--c); color: #fff; font-size: 10.5px; padding: 1px 6px; border-radius: 3px; }}
.wn {{ display: block; margin-top: 4px; font-size: 12px; font-weight: 900; white-space: nowrap; }} .wn em {{ font-style: normal; font-size: 26px; color: {ORANGE}; margin-left: 3px; }}
.note {{ margin-top: 6px; font-size: 12px; font-weight: 700; line-height: 1.6; }} .note .or {{ color: {ORANGE}; }}
footer {{ position: absolute; left: 22px; right: 22px; bottom: 14px; display: flex; justify-content: space-between; font-size: 11px; color: #6E7F7B; font-weight: 700; }}
footer b {{ color: {TEAL}; }}
</style></head><body>
<header><h1>待ち当て 5問 <i>正解</i><small>2面子1雀頭を作る形（7枚形）・全部{sname}</small></h1>{logo_html()}</header>
<div class="legend"><span class="lg hd"><i></i>手にある牌</span>{leg}</div>
{rows}
<p class="note">横から見た図は、横＝数字・縦＝枚数。色の箱が<b class="or">残りの待ちの牌</b>（2色は2通りの待ち方）。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>全32形の表は「麻雀の待ちの形一覧」</span></footer>
</body></html>"""


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
      b = pw.chromium.launch()
      for key, (suit, sname, qs) in SETS.items():
        OUT = os.path.join(DIR, f"quiz-7mai-{key}" + ("-ans" if ANS else ""))
        io.open(OUT + ".html", "w", encoding="utf-8").write((html_ans if ANS else html)(suit, sname, qs))
        pg = b.new_page(viewport={"width": 540, "height": 675}, device_scale_factor=2)
        pg.goto("file:///" + OUT.replace("\\", "/") + ".html"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        over = pg.evaluate("document.querySelector('.note').getBoundingClientRect().bottom > document.querySelector('footer').getBoundingClientRect().top")
        assert not over, "下にはみ出す"
        pg.screenshot(path=OUT + ".png"); pg.close()
        os.remove(OUT + ".html"); print(OUT + ".png")
      b.close()


ANS = "--ans" in sys.argv
if __name__ == "__main__":
    main()
