# Xに出す1枚の表（流局・フリテン・条件戦・掛け声・守り・チョンボ）の共通部分（2026-11-16 に作り、2026-11-23 に scratchpad から移した）
# 実行: python3.13 tools/x_sheets/<名前>.py → まじゃすこ素材/x/<名前>/<名前>.png
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); TOOLS = os.path.dirname(HERE); ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import hai_sheets as H
from sheet_logo import LOGO_CSS, logo_html
import pathlib
T = pathlib.Path(ROOT, "assets", "tiles").as_uri()      # Windows でも Linux でも正しい file:// になる（2026-11-24 会社PCで動かすため）
TEAL, BLUE, ORANGE, INK, RED = "#177083", "#4261AA", "#E25A1C", "#1F2A28", "#C92F42"
def tl(code, w=26, cls=""): return f'<img class="t {cls}" src="{T}/{code}.svg" style="width:{w}px">'
BASE_CSS = f"""
.bar {{ display: flex; align-items: baseline; gap: 10px; color: #fff; background: {TEAL}; border-radius: 6px 6px 0 0; padding: 4px 12px; font-size: 17px; font-weight: 900; margin-top: 10px; }}
.bar small {{ font-size: 11.5px; font-weight: 700; color: #DDF0EC; }}
th {{ background: {TEAL}; color: #fff; font-size: 12.5px; font-weight: 900; padding: 4px 0; border-left: 1px solid rgba(255,255,255,.35); }}
td {{ border: 1px solid #8FA29D; padding: 5px 6px; vertical-align: middle; font-size: 12px; font-weight: 700; line-height: 1.45; }}
th.rh {{ background: #E9EFEE; color: {INK}; border: 1px solid #8FA29D; font-size: 13px; line-height: 1.2; }} th.rh small {{ display: block; font-size: 10px; color: {TEAL}; font-weight: 800; }}
.note {{ font-size: 11px; font-weight: 700; margin-top: 6px; line-height: 1.55; color: #33403D; }} .note b {{ color: {ORANGE}; }}
.tip {{ margin-top: 8px; border: 1.5px solid {ORANGE}; border-radius: 6px; padding: 6px 10px; font-size: 11.5px; font-weight: 700; line-height: 1.55; background: #FFF5EF; }} .tip b {{ color: {ORANGE}; }}
.k {{ color: {TEAL}; font-weight: 900; }} .o {{ color: {ORANGE}; font-weight: 900; }}
img.t {{ vertical-align: middle; }}
body {{ background: #EEF6F3 !important; }} table {{ background: #fff; }} .card {{ background: #fff; }}      /* 紙の地は薄い緑（役の出やすさランキングと同じ）。表の中は白のまま */
"""
def page(title, sub, legend, body, css=""):
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{H.FONT}<style>{H.CSS}{LOGO_CSS}{H.FIT_CSS}{BASE_CSS}{css}</style></head><body>
<header><h1>{title}<small>{sub}</small></h1><div class="legend">{legend}</div>{logo_html()}</header>
{body}
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""
def render(html, out):
    if "/" not in out and os.sep not in out:      # 名前だけなら素材リポジトリの x/<名前>/ に
        d = os.path.join(ROOT, "まじゃすこ素材", "x", out); os.makedirs(d, exist_ok=True); out = os.path.join(d, out)
    io.open(out + ".html", "w", encoding="utf-8").write(html)
    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        ex = "/opt/pw-browsers/chromium"; b = pw.chromium.launch(**({"executable_path": ex} if os.path.exists(ex) else {})); pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
        pg.goto(pathlib.Path(out + ".html").as_uri()); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        h = pg.evaluate("Math.ceil(document.body.getBoundingClientRect().height)")
        pg.set_viewport_size({"width": 794, "height": h}); pg.screenshot(path=out + ".png", full_page=True); b.close(); print("h", h, out + ".png")
