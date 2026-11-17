# -*- coding: utf-8 -*-
"""待ち当て5問（7枚形）の問題の画像（1080×1350。XとInstagramで共用。2026-11-17 ユーザーの指定）。
答えは載せない（答えはリプ欄で）。答えの確かめは machi3.py の waits（下の assert）。
出力: まじゃすこ素材/x/machi/quiz-7mai.png（画像の元は公開リポジトリに入れない）
実行: python tools/machi_sheet/quiz.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import ROOT, T, TEAL, ORANGE, INK
from sheet_logo import LOGO_CSS, logo_html
import machi3 as M

# (手, 答えの数字, 答えの枚数)（2026-11-17 ユーザーの指定）
QS = [("2345567", "258", 9), ("2223444", "12345", 13), ("2222344", "134", 9), ("2333345", "1245", 13), ("2223334", "2345", 9)]
SUIT = "s"      # 索子（2026-11-17 ユーザーの指定）
for h, a, n in QS:
    w = M.waits([SUIT + c for c in h], 2, 1)
    assert "".join(c[1] for c, _ in w) == a and sum(x for _, x in w) == n, (h, w)

OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "machi", "quiz-7mai")
KAN = "〇一二三四五六七八九"


def tile(c, w): return f'<img src="{T}/{SUIT}{c}.svg" style="width:{w}px">'


def html():
    rows = "".join(
        f'<div class="q"><b>Q{i}</b><span class="hand">{"".join(tile(c, 46) for c in h)}</span>'
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
<header><h1>待ち当て 5問<small>2面子1雀頭を作る形（7枚形）・全部索子</small></h1>{logo_html()}</header>
<p class="lead">待ちの牌を<em>全部</em>言えたら正解</p>
{rows}
<p class="note">全問正解なら中級者。答えはリプ欄に。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>全32形の表は「麻雀の待ちの形一覧」</span></footer>
</body></html>"""


def main():
    from playwright.sync_api import sync_playwright
    io.open(OUT + ".html", "w", encoding="utf-8").write(html())
    with sync_playwright() as pw:
        b = pw.chromium.launch(); pg = b.new_page(viewport={"width": 540, "height": 675}, device_scale_factor=2)
        pg.goto("file:///" + OUT.replace("\\", "/") + ".html"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        over = pg.evaluate("document.querySelector('.note').getBoundingClientRect().bottom > document.querySelector('footer').getBoundingClientRect().top")
        assert not over, "下にはみ出す"
        pg.screenshot(path=OUT + ".png"); b.close()
    os.remove(OUT + ".html"); print(OUT + ".png")


if __name__ == "__main__":
    main()
