# -*- coding: utf-8 -*-
"""3D用の牌の絵（表の面だけ・PNG）を assets/tiles/*.svg から作る。python tools/b3d/make_tile_tex.py <出力フォルダ>"""
import os, re, sys, glob
from playwright.sync_api import sync_playwright
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
codes = [f"{s}{n}" for s in "mps" for n in range(1, 10)] + [f"z{n}" for n in range(1, 8)] + ["m5r", "p5r", "s5r"]
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 300, "height": 400}, device_scale_factor=1)
    for c in codes:
        svg = open(os.path.join(ROOT, "assets", "tiles", c + ".svg"), encoding="utf-8").read()
        svg = re.sub(r'viewBox="[^"]*"', 'viewBox="0 0 60 80" width="240" height="320"', svg, count=1)
        pg.set_content(f'<body style="margin:0;background:#FFFDF6">{svg}</body>')
        pg.locator("svg").first.screenshot(path=os.path.join(out, c + ".png"))
    b.close()
print("ok", len(codes))
