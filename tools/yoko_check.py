# 横向きの牌（-yoko）が、となりの縦の牌と同じ縮尺で出ているか（幅は縦の牌×82/62）。python tools/yoko_check.py（localhost:8931 にサーバー）
import glob, sys
from playwright.sync_api import sync_playwright
JS = r"""() => { const out=[]; document.querySelectorAll('img[src*="-yoko.svg"]').forEach(y=>{ const r=y.getBoundingClientRect(); if(!r.width) return;
  let p=y.parentElement, up=null; for(let k=0;k<4&&p&&!up;k++){ up=[...p.querySelectorAll('img[src*="/tiles/"]')].find(i=>!i.src.includes('-yoko')&&!i.src.includes("back")&&!/tenbo|chip|dice|d[0-9]\.svg/.test(i.src)&&i.getBoundingClientRect().width>0); p=p.parentElement; }
  if(!up) return; const u=up.getBoundingClientRect(); const ratio=(r.width/82)/(u.width/62);
  if(ratio<0.93||ratio>1.07) out.push([y.getAttribute('src').split('/').pop(), Math.round(r.width*10)/10, Math.round(u.width*10)/10, Math.round(ratio*100)/100, (y.closest('[class]')||{}).className||'']); }); return out; }"""
pages = sorted(glob.glob("*.html") + glob.glob("*/*.html"))
tot = 0
with sync_playwright() as p:
    b = p.chromium.launch()
    for w in (390, 1280):
        pg = b.new_page(viewport={"width": w, "height": 900})
        for f in pages:
            if "-yoko" not in open(f, encoding="utf-8").read(): continue
            pg.goto("http://localhost:8931/" + f); pg.wait_for_timeout(400)
            r = pg.evaluate(JS)
            if r:
                tot += len(r); print(w, f, len(r), r[:3])
    b.close()
# SVG の中の <image>（卓の図）: 横向きの牌の枠が 82:69 か。枠の比がちがうと、絵が枠の中で縮んで小さく見える
import re
for f in pages:
    for m in re.finditer(r'<image href="[^"]*-yoko\.svg"[^>]*?width="([\d.]+)" height="([\d.]+)"', open(f, encoding="utf-8").read()):
        w, h = float(m.group(1)), float(m.group(2))
        if abs(w / h - 82 / 69) > .03:
            tot += 1; print("svg", f, w, h, round(w / h, 2))
print("total", tot)
