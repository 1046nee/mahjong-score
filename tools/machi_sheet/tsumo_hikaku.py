# -*- coding: utf-8 -*-
"""Mリーグの実戦の7枚形（三索の暗刻＋四五六＋八）に、一〜八のどれを引くと待ちがいちばん広がるかの順位の画像
（Xのリプ用。1080×1350。2026-11-20 ユーザーの依頼。実戦は筒子だったが、画像は索子で作る＝ユーザーの指定）。
列は待ちの形の一覧と同じ: 牌姿・横から見た図（字牌の列なし）・待ち・枚数。切る牌・ツモ切りは書かない（ユーザーの指定）。
引いたあとは、いちばん枚数が多くなる1枚を切った形を出す（同じ枚数ならツモ切り）。
枚数＝4−自分の手にある枚数−切った牌（切った牌が待ちなら1枚減る。その待ちはフリテン）。待ちは machi3.waits で出す。
出力: まじゃすこ素材/x/machi/reply-333456-2.png
実行: python3.13 tools/machi_sheet/tsumo_hikaku.py（Playwright は /opt/pw-browsers/chromium を使えるようにして）
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import ROOT, T, TEAL, ORANGE, INK
from sheet_logo import LOGO_CSS, logo_html
import machi3 as M
import detail as D

S = "s"; BASE = "3334568"; DRAWS = "12345678"
DIR = os.path.join(ROOT, "まじゃすこ素材", "x", "machi")
def hand_of(s): return [S + c for c in s]
def tile(code, w): return f'<img src="{T}/{code}.svg" style="width:{w}px">'


def shape(s, cut=None):
    """7枚の形 s（cut＝切った牌）の待ち・待ち方・枚数・切った牌（待ちに入っているときだけ）"""
    hand = hand_of(s); ws = M.waits(hand, 2, 1); km = {w: D.kinds(hand, w, 2) for w, _ in ws}
    gone = {S + cut: 1} if cut and S + cut in dict(ws) else {}
    n = sum(k - gone.get(w, 0) for w, k in ws)
    return hand, ws, km, n, gone


def best_after(x):
    h = sorted(BASE + x); cands = []
    for d in sorted(set(h)):
        hh = list(h); hh.remove(d); r = "".join(hh)
        cands.append((shape(r, d)[3], d == x, d, r))
    n, _, d, r = max(cands)
    return d, r, n


ROWS = {x: best_after(x) for x in DRAWS}
assert ROWS["7"] == ("8", "3334567", 16) and ROWS["2"] == ("8", "2333456", 14) and ROWS["4"] == ("8", "3334456", 13), ROWS
RANK = {x: 1 + sum(1 for y in ROWS if ROWS[y][2] > ROWS[x][2]) for x in ROWS}
ORDER = sorted(DRAWS, key=lambda x: (RANK[x], x))
NMAX = max(r[2] for r in ROWS.values())


def html():
    hand0, ws0, km0, n0, _ = shape(BASE)
    trs = ""
    for x in ORDER:
        d, r, n = ROWS[x]; hand, ws, km, _, gone = shape(r, d); rk = RANK[x]
        fr = '<i class="fr">フリテン</i>' if gone else ""
        trs += (f'<tr class="r{rk}"><td class="rk"><b>{rk}<small>位</small></b></td><td class="dr">{tile(S + x, 20)}</td>'
                f'<td class="hd"><div class="tl">{"".join(tile(c, 18) for c in hand)}</div></td>'
                f'<td class="sv">{D.side_view(hand, ws, km, scale=0.58, gone=gone, honor=False)}</td>'
                f'<td class="wt"><div class="tl">{"".join(tile(c, 16) for c, _ in ws)}</div></td>'
                f'<td class="nn"><b>{n}</b>枚{fr}<span class="bar"><i style="width:{n / NMAX * 100:.0f}%"></i></span></td></tr>')
    leg = ('<span class="lg hd"><i></i>手にある牌</span>'
           + "".join(f'<span class="lg" style="--c:{c}"><i></i>{t}</span>' for t, c in D.TYPES)
           + '<span class="lg go"><i></i>切った牌</span>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=block" rel="stylesheet">
<style>* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 540px; height: 675px; overflow: hidden; }}
body {{ font-family: 'Noto Sans JP', sans-serif; background: #EEF6F3; color: {INK}; padding: 18px 20px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: {TEAL}; color: #fff; border-radius: 8px; padding: 9px 14px; }}
header h1 {{ font-size: 24px; font-weight: 900; line-height: 1.15; }} header h1 i {{ font-style: normal; color: #FFE68A; }}
header h1 small {{ display: block; font-size: 11.5px; font-weight: 700; color: #DDF0EC; margin-top: 3px; }}
{LOGO_CSS} .logo-pill img {{ height: 28px; }}
.base {{ display: flex; align-items: center; gap: 8px; margin: 6px 0 4px; font-size: 12px; font-weight: 900; }}
.base .tl {{ display: flex; gap: 1px; }} .base img {{ display: block; }} .base em {{ font-style: normal; color: #5E6B69; font-size: 11.5px; }}
.base .lab {{ color: #fff; background: #5E6B69; border-radius: 4px; padding: 1px 7px; font-size: 11px; }}
.legend {{ display: flex; flex-wrap: wrap; align-items: center; gap: 3px 9px; margin: 0 2px 4px; font-size: 10.5px; font-weight: 900; }}
.lg {{ display: inline-flex; align-items: center; gap: 4px; color: var(--c); }} .lg i {{ width: 15px; height: 8px; border-radius: 2px; background: var(--c); opacity: .5; }}
.lg.hd {{ color: {INK}; }} .lg.hd i {{ opacity: 1; background: repeating-linear-gradient(45deg, #1F2A28 0 1.4px, #fff 1.4px 3.2px); border: 1px solid #1F2A28; }}
.lg.go {{ color: #6B7A77; }} .lg.go i {{ opacity: 1; background: #C9D2D0; }}
table {{ width: 100%; border-collapse: collapse; background: #fff; }}
th {{ background: #1C4E5A; color: #fff; font-size: 11px; font-weight: 900; padding: 4px 0; border-left: 1px solid rgba(255,255,255,.3); }}
td {{ border: 1px solid #B4C4C0; padding: 11px 4px; vertical-align: middle; text-align: center; }}
.tl {{ display: flex; gap: 1px; justify-content: center; }} .tl img {{ display: block; }}
td.dr img {{ display: block; margin: 0 auto; }}
td.rk b {{ font-size: 19px; font-weight: 900; color: #6B7A77; }} td.rk small {{ font-size: 10px; }}
tr.r1 td {{ background: #FFF3EC; }} tr.r1 td.rk b {{ color: {ORANGE}; }} tr.r2 td.rk b {{ color: {TEAL}; }} tr.r3 td.rk b {{ color: #4261AA; }}
td.sv svg {{ display: block; margin: 0 auto; }}
td.nn {{ text-align: left; padding: 3px 6px; font-size: 10.5px; font-weight: 900; white-space: nowrap; }} td.nn b {{ font-size: 19px; color: {ORANGE}; }}
.fr {{ font-style: normal; display: block; font-size: 9px; color: #fff; background: #8A6FB8; border-radius: 3px; padding: 0 3px; width: fit-content; margin-top: 1px; }}
.bar {{ display: block; height: 5px; background: #E6ECEB; border-radius: 3px; margin-top: 2px; }} .bar i {{ display: block; height: 100%; background: {ORANGE}; border-radius: 3px; }}
.note {{ margin-top: 6px; font-size: 10.5px; font-weight: 700; line-height: 1.55; color: #33403D; }} .note b {{ color: #8A6FB8; }}
footer {{ position: absolute; left: 20px; right: 20px; bottom: 11px; display: flex; justify-content: space-between; font-size: 10px; color: #6E7F7B; font-weight: 700; }}
footer b {{ color: {TEAL}; }}
</style></head><body>
<header><h1>どれを引くと<i>いちばん広がる？</i><small>三三三四五六八（索子）に、一〜八を引いたら</small></h1>{logo_html()}</header>
<div class="base"><span class="lab">元の形</span><div class="tl">{"".join(tile(c, 18) for c in hand0)}</div><em>待ち 七・八（{len(ws0)}種{n0}枚）</em></div>
<div class="legend">{leg}</div>
<table><thead><tr><th style="width:38px">順位</th><th style="width:36px">引く</th><th>牌姿</th><th>横から見た図</th><th>待ち</th><th style="width:58px">枚数</th></tr></thead><tbody>{trs}</tbody></table>
<p class="note">牌姿は、引いたあと待ちがいちばん広くなる1枚を切った形。<b>フリテン</b>＝切った牌が待ちに入っていて、ロンできずツモだけでアガれる。枚数は自分の手と切った牌だけで数えた数。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>全32形の表は「麻雀の待ちの形一覧」</span></footer>
</body></html>"""


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        out = os.path.join(DIR, "reply-333456-2")
        io.open(out + ".html", "w", encoding="utf-8").write(html())
        pg = b.new_page(viewport={"width": 540, "height": 675}, device_scale_factor=2)
        pg.goto("file:///" + out.replace("\\", "/").lstrip("/") + ".html"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        gap = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - document.querySelector('.note').getBoundingClientRect().bottom")
        wide = pg.evaluate("document.querySelector('table').getBoundingClientRect().right > document.body.clientWidth - 19")
        print("余白", round(gap)); assert gap > 0 and not wide, "はみ出す"
        pg.screenshot(path=out + ".png"); pg.close(); os.remove(out + ".html")
        b.close()


if __name__ == "__main__":
    for x in ORDER: print(RANK[x], x, ROWS[x])
    main()
