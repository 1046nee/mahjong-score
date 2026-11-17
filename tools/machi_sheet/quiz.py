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
    rows = ""
    for i, (h, _, _) in enumerate(QS, 1):
        hand = [suit + c for c in h]
        w = M.waits(hand, 2, 1)
        n = sum(x for _, x in w)
        pat = "".join(map(str, M.pattern(hand)))
        rows += (f'<div class="q"><b>Q{i}</b><div class="body"><div class="top"><span class="hand">{"".join(tile(c, 25) for c in hand)}</span>'
                 f'<span class="nm">{shape_name(hand)}<small>{pat}</small></span></div>'
                 f'<div class="ans"><span class="wl">待ち</span><span class="wt">{"".join(tile(c, 25) for c, _ in w)}</span>'
                 f'<span class="wn">{len(w)}種<em>{n}</em>枚</span></div></div></div>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=block" rel="stylesheet">
<style>* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 540px; height: 675px; overflow: hidden; }}
body {{ font-family: 'Noto Sans JP', sans-serif; background: #EEF6F3; color: {INK}; padding: 20px 22px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: {TEAL}; color: #fff; border-radius: 8px; padding: 10px 14px; }}
header h1 {{ font-size: 30px; font-weight: 900; line-height: 1.15; letter-spacing: .02em; }} header h1 i {{ font-style: normal; color: #FFE68A; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 3px; letter-spacing: 0; }}
{LOGO_CSS} .logo-pill img {{ height: 30px; }}
.lead {{ margin: 12px 2px 8px; font-size: 14px; font-weight: 900; }} .lead em {{ font-style: normal; color: {ORANGE}; }}
.q {{ display: flex; align-items: center; gap: 8px; background: #fff; border: 2px solid #1F2A28; padding: 6px 10px; margin-top: -2px; }} .q:first-of-type {{ margin-top: 12px; }}
.q > b {{ width: 40px; flex: none; font-size: 22px; font-weight: 900; color: {TEAL}; }}
.body {{ flex: 1; min-width: 0; }}
.top, .ans {{ display: flex; align-items: center; gap: 8px; }} .ans {{ margin-top: 5px; }}
.hand, .wt {{ display: flex; gap: 1px; }} .hand img, .wt img {{ display: block; }}
.nm {{ margin-left: auto; text-align: right; font-size: 12.5px; font-weight: 900; line-height: 1.25; white-space: nowrap; }}
.nm small {{ display: block; font-size: 11px; color: #5E6B69; letter-spacing: .1em; }}
.wl {{ font-size: 12px; font-weight: 900; color: #fff; background: {ORANGE}; border-radius: 4px; padding: 3px 7px; }}
.wt {{ background: #FDE3D5; border-radius: 5px; padding: 3px; }}
.wn {{ margin-left: auto; font-size: 14px; font-weight: 900; white-space: nowrap; }} .wn em {{ font-style: normal; font-size: 24px; color: {ORANGE}; margin-left: 4px; }}
.note {{ margin-top: 10px; font-size: 12.5px; font-weight: 700; line-height: 1.6; }} .note .or {{ color: {ORANGE}; }}
footer {{ position: absolute; left: 22px; right: 22px; bottom: 14px; display: flex; justify-content: space-between; font-size: 11px; color: #6E7F7B; font-weight: 700; }}
footer b {{ color: {TEAL}; }}
</style></head><body>
<header><h1>待ち当て 5問 <i>正解</i><small>2面子1雀頭を作る形（7枚形）・全部{sname}</small></h1>{logo_html()}</header>
{rows}
<p class="note">枚数は、手で使っている牌を除いた<b class="or">残りの枚数</b>。並びが同じなら、どの色でも同じ待ち。</p>
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
