# -*- coding: utf-8 -*-
"""LPの成績の節の画像の大きさに合わせて、index.html の数字を書きかえる（shoot_lp_big_plan.py が最後に呼ぶ・2026-11-04〜）。
引数: 撮った画像の大きさのJSON。書きかえるもの: 画像の width/height、順位のタブの高さ（--rt）"""
import json, os, re, sys
MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
m = json.loads(sys.argv[1]); p = os.path.join(MJ, "index.html"); s = open(p, encoding="utf-8").read()
def wh(src, w, h):
    global s
    s, n = re.subn(r'(<img[^>]*src="/assets/screens/' + re.escape(src) + r'"[^>]*?) width="\d+" height="\d+"', lambda x: f'{x.group(1)} width="{w}" height="{h}"', s)
    assert n, src
for n in ("grid", "h2h"):
    g = m[n]; wh(f"lp-hd-{n}.webp", g["w"], g["h"])
r = m["rank"]
for mk in ("score", "avg", "top", "las"):
    wh(f"lp-hd-rank-{mk}-t.webp", r["w"], r["th"]); wh(f"lp-hd-rank-{mk}.webp", r["w"], r["bh"])
s, k = re.subn(r'<div class="lp-shot lp-flip" id="lp-flip"(?: style="[^"]*")?>', f'<div class="lp-shot lp-flip" id="lp-flip" style="--rt:{r["rt"]}">', s); assert k
wh("lp-hd-games-tile.webp", m["games-tile"]["w"], m["games-tile"]["h"])
wh("lp-hd-games-list.webp", m["games-list"]["w"], m["games-list"]["h"])
open(p, "w", encoding="utf-8").write(s); print("index.html updated")
