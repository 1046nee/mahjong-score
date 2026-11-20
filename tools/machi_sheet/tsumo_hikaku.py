# -*- coding: utf-8 -*-
"""Mリーグの対局の形（7枚形）の解説の画像（Xのリプ用。1080×1350。2026-11-20 ユーザーの依頼）。
1枚目: 実戦の2つの形（三筒の暗刻＋四五六＋八 → ツモ四・打八）を横から見た図つきで。
2枚目: 三三三四五六八に一〜六のどれを引くと、待ちがいちばん広がるか（それぞれ最も広くなる牌を切ったとき）。
待ち・枚数は machi3.waits で出す（数えるのは自分の手の牌だけ。河やドラ表示牌は数えない）。
出力: まじゃすこ素材/x/machi/reply-333456-1.png ／ -2.png
実行: python3.13 tools/machi_sheet/tsumo_hikaku.py（Playwright は /opt/pw-browsers/chromium を使えるようにして）
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import ROOT, T, TEAL, ORANGE, INK
from sheet_logo import LOGO_CSS, logo_html
import machi3 as M
import detail as D

S = "p"; BASE = "3334568"
DIR = os.path.join(ROOT, "まじゃすこ素材", "x", "machi")
def hand_of(s): return [S + c for c in s]
def tile(code, w): return f'<img src="{T}/{code}.svg" style="width:{w}px">'
def info(s):
    hand = hand_of(s); ws = M.waits(hand, 2, 1); km = {w: D.kinds(hand, w, 2) for w, _ in ws}
    return hand, ws, km, sum(n for _, n in ws)


def best_after(x):
    """x を引いて、いちばん待ちが広くなる1枚を切る（同じ枚数なら引いた牌を切る＝ツモ切り）"""
    h = sorted(BASE + x); cands = []
    for d in sorted(set(h)):
        hh = list(h); hh.remove(d); r = "".join(hh)
        cands.append((info(r)[3], d == x, d, r))
    n, _, d, r = max(cands)
    return d, r, n


ROWS = {x: best_after(x) for x in "123456"}
assert ROWS["4"] == ("8", "3334456", 13) and ROWS["2"] == ("8", "2333456", 14) and info(BASE)[3] == 7, ROWS
RANK = {x: 1 + sum(1 for y in ROWS if ROWS[y][2] > ROWS[x][2]) for x in ROWS}

CSS = f"""* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 540px; height: 675px; overflow: hidden; }}
body {{ font-family: 'Noto Sans JP', sans-serif; background: #EEF6F3; color: {INK}; padding: 18px 22px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: {TEAL}; color: #fff; border-radius: 8px; padding: 10px 14px; }}
header h1 {{ font-size: 25px; font-weight: 900; line-height: 1.15; }} header h1 i {{ font-style: normal; color: #FFE68A; }}
header h1 small {{ display: block; font-size: 12px; font-weight: 700; color: #DDF0EC; margin-top: 3px; }}
{LOGO_CSS} .logo-pill img {{ height: 28px; }}
.legend {{ display: flex; flex-wrap: wrap; align-items: center; gap: 4px 10px; margin: 8px 2px 6px; font-size: 11px; font-weight: 900; }}
.lg {{ display: inline-flex; align-items: center; gap: 4px; color: var(--c); }} .lg i {{ width: 16px; height: 9px; border-radius: 2px; background: var(--c); opacity: .5; }}
.lg.tip {{ color: #5E6B69; font-size: 10px; margin-left: auto; }}
.lg.hd {{ color: {INK}; }} .lg.hd i {{ opacity: 1; background: repeating-linear-gradient(45deg, #1F2A28 0 1.4px, #fff 1.4px 3.2px); border: 1px solid #1F2A28; }}
.hand {{ display: flex; gap: 1px; align-items: flex-end; }} .hand img {{ display: block; }}
.ex {{ display: inline-flex; align-items: center; gap: 4px; font-size: 11.5px; font-weight: 900; color: var(--c); }} .ex b {{ background: var(--c); color: #fff; font-size: 10px; padding: 1px 5px; border-radius: 3px; }}
.exs {{ display: flex; flex-wrap: wrap; gap: 2px 8px; }}
.sv svg {{ display: block; }}
footer {{ position: absolute; left: 22px; right: 22px; bottom: 12px; display: flex; justify-content: space-between; font-size: 10.5px; color: #6E7F7B; font-weight: 700; }}
footer b {{ color: {TEAL}; }}
"""
HEAD = '<!doctype html><html lang="ja"><head><meta charset="utf-8"><link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@700;900&display=block" rel="stylesheet">'
LEG = ('<div class="legend"><span class="lg hd"><i></i>手にある牌</span>'
       + "".join(f'<span class="lg" style="--c:{c}"><i></i>{t}</span>' for t, c in D.TYPES)
       + '<span class="lg tip">横から見た図の縦＝枚数</span></div>')
FOOT = '<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>枚数は自分の手の牌だけで数えた数</span></footer>'


def html1():
    """実戦の2つの形。分け方も1行ずつ書く"""
    parts = [
        ("1枚目", BASE, None, [("333＋456＋8", "8単騎"), ("33＋345＋68", "7嵌張")]),
        ("2枚目", "3334456", ("4", "8"), [("333＋44＋56", "4・7両面"), ("33＋34＋456", "2・5両面"), ("33＋345＋46", "5嵌張"), ("333＋456＋4", "4単騎")]),
    ]
    rows = ""
    for lab, s, tk, ways in parts:
        hand, ws, km, n = info(s)
        tk_html = (f'<span class="tk">ツモ{tile(S + tk[0], 20)}　切る{tile(S + tk[1], 20)}</span>' if tk else "")
        wl = "".join(f'<li><span class="sp">{a}</span><span class="ar">→</span>{b}</li>' for a, b in ways)
        rows += (f'<div class="card"><div class="top"><b class="lab">{lab}</b>{tk_html}</div>'
                 f'<div class="mid"><div class="hand">{"".join(tile(c, 30) for c in hand)}</div>'
                 f'<div class="wt"><span class="wl">待ち</span>{"".join(tile(c, 24) for c, _ in ws)}<span class="wn">{len(ws)}種{n}枚</span></div></div>'
                 f'<div class="bot"><div class="sv">{D.side_view(hand, ws, km, scale=1.2)}</div><div class="rt"><div class="exs">{D.explain(hand, ws, km)}</div><ul>{wl}</ul></div></div></div>')
    css = CSS + f"""
.card {{ background: #fff; border: 2px solid {INK}; border-radius: 6px; padding: 11px 12px; margin-top: 10px; }}
.top {{ display: flex; align-items: center; gap: 10px; }} .lab {{ font-size: 15px; font-weight: 900; color: #fff; background: {TEAL}; border-radius: 4px; padding: 1px 8px; }}
.tk {{ display: inline-flex; align-items: center; gap: 3px; font-size: 12px; font-weight: 900; color: #33403D; }} .tk img {{ vertical-align: middle; margin: 0 3px; }}
.mid {{ display: flex; align-items: flex-end; justify-content: space-between; margin-top: 7px; }}
.wt {{ display: flex; align-items: center; gap: 1px; background: #FDE3D5; border-radius: 4px; padding: 3px 6px 3px 3px; }} .wt img {{ display: block; }}
.wl {{ font-size: 11px; font-weight: 900; color: #fff; background: {ORANGE}; border-radius: 4px; padding: 2px 6px; margin-right: 4px; }}
.wn {{ font-size: 12px; font-weight: 900; margin-left: 6px; color: #33403D; }}
.bot {{ display: flex; gap: 12px; align-items: flex-start; margin-top: 8px; }} .rt {{ flex: 1; }}
ul {{ list-style: none; margin-top: 5px; white-space: nowrap; font-size: 12.5px; font-weight: 900; line-height: 1.7; }} .sp {{ font-family: monospace; font-size: 12.5px; color: {TEAL}; }} .ar {{ color: #8A9A97; margin: 0 5px; }}
.note {{ margin-top: 8px; font-size: 12px; font-weight: 700; line-height: 1.6; }} .note b {{ color: {ORANGE}; }}
"""
    return (f'{HEAD}<style>{css}</style></head><body><header><h1>筒子の7枚形を<i>横から見る</i><small>三筒の暗刻があると、待ちが重なって広くなる</small></h1>{logo_html()}</header>'
            f'{LEG}{rows}<p class="note">暗刻は<b>「3枚で面子」とも「2枚で雀頭＋1枚」とも見られる</b>。だから1つの形に、いくつもの待ちが重なる。</p>{FOOT}</body></html>')


def html2():
    hand0, ws0, km0, n0 = info(BASE)
    rows = ""
    for x in "123456":
        d, r, n = ROWS[x]; hand, ws, km, _ = info(r); rk = RANK[x]
        act = "ツモ切り（変わらない）" if d == x else f'{tile(S + d, 17)}を切る'
        rows += (f'<div class="q{" best" if rk == 1 else ""}"><div class="dr"><span class="rk r{rk}">{rk}位</span>{tile(S + x, 26)}<small>を引く</small></div>'
                 f'<div class="lt"><div class="act">{act}</div><div class="hand">{"".join(tile(c, 19) for c in hand)}</div></div>'
                 f'<div class="rt"><div class="sv">{D.side_view(hand, ws, km, scale=0.74)}</div><div class="exs">{D.explain(hand, ws, km)}</div></div>'
                 f'<div class="nn"><b>{n}</b>枚<small>{len(ws)}種</small></div></div>')
    css = CSS + f"""
.base {{ display: flex; align-items: center; gap: 8px; background: #fff; border: 2px solid {TEAL}; border-radius: 6px; padding: 5px 9px; margin-bottom: 6px; font-size: 12px; font-weight: 900; }}
.base .hand img {{ display: block; }} .base em {{ font-style: normal; color: #5E6B69; }}
.q {{ display: flex; align-items: center; gap: 7px; background: #fff; border: 2px solid {INK}; padding: 3px 8px; margin-top: -2px; }}
.q.best {{ border-color: {ORANGE}; background: #FFF5EF; position: relative; z-index: 1; }}
.dr {{ width: 62px; flex: none; display: flex; flex-direction: column; align-items: center; gap: 2px; }} .dr img {{ display: block; }} .dr small {{ font-size: 10px; font-weight: 900; color: #5E6B69; }}
.rk {{ font-size: 11px; font-weight: 900; color: #fff; background: #8A9A97; border-radius: 9px; padding: 0 7px; }} .rk.r1 {{ background: {ORANGE}; }} .rk.r2 {{ background: {TEAL}; }}
.lt {{ width: 140px; flex: none; }} .act {{ font-size: 11px; font-weight: 900; color: #33403D; display: flex; align-items: center; gap: 3px; margin-bottom: 3px; height: 21px; }} .act img {{ display: block; }}
.rt {{ flex: 1; min-width: 0; }} .rt .exs {{ margin-top: 2px; }} .rt .ex {{ font-size: 10.5px; }}
.nn {{ width: 50px; flex: none; text-align: right; font-size: 11px; font-weight: 900; }} .nn b {{ font-size: 24px; line-height: 1; }} .nn small {{ display: block; font-size: 10px; color: #5E6B69; }}
.q.best .nn b {{ color: {ORANGE}; }}
"""
    return (f'{HEAD}<style>{css}</style></head><body><header><h1>どれを引くと<i>いちばん広がる？</i><small>三三三四五六八（筒子）に、一〜六を引いたら</small></h1>{logo_html()}</header>'
            f'{LEG}<div class="base"><span>元の形</span><div class="hand">{"".join(tile(c, 19) for c in hand0)}</div><em>待ち 7・8（{n0}枚）</em></div>{rows}{FOOT}</body></html>')


def main():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for k, f in (("1", html1), ("2", html2)):
            out = os.path.join(DIR, f"reply-333456-{k}")
            io.open(out + ".html", "w", encoding="utf-8").write(f())
            pg = b.new_page(viewport={"width": 540, "height": 675}, device_scale_factor=2)
            pg.goto("file:///" + out.replace("\\", "/").lstrip("/") + ".html"); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
            gap = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - [...document.querySelectorAll('.q, .card, .note')].pop().getBoundingClientRect().bottom")
            print(k, "余白", round(gap)); assert gap > 0, "下にはみ出す"
            pg.screenshot(path=out + ".png"); pg.close(); os.remove(out + ".html")
        b.close()


if __name__ == "__main__":
    for x in "123456": print(x, ROWS[x], RANK[x])
    main()
