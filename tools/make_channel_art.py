# -*- coding: utf-8 -*-
"""YouTube・TikTok のチャンネル画像を作る（2026-11-06〜）。HTMLをブラウザで描いて撮る（make_sns_v3 と同じやり方）。
出力: まじゃすこ素材/channel/
- icon-1080.png      プロフィール画像（丸く切り抜かれる前提。マークは丸の中に余裕をもって収める）
- icon-preview.png   丸く切り抜いたときの見え方（大・中・小）の確認用
- yt-banner.png      YouTubeのバナー 2560×1440（文字とマークは全端末で見える中央 1546×423 に入れる）
- yt-banner-guide.png バナーの見える範囲（テレビ／PC／スマホ）の線を重ねた確認用
- yt-watermark.png   YouTubeの動画の透かし 300×300（右下に小さく出る。背景は透明）
- x-header.png       Xのヘッダー 1500×500（YouTubeのバナーと同じ見た目。左下はプロフィール画像が重なるので空ける・上下は端末で約60px切れる）
- x-header-guide.png Xのヘッダーの重なる所・切れる所の線を重ねた確認用
実行: python tools/make_channel_art.py
"""
import base64
import math
import os
from playwright.sync_api import sync_playwright

MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(MJ, "まじゃすこ素材", "channel")
TEAL, DEEP, ORANGE = "#177083", "#0B4C59", "#E3571F"

# favicon の M を512の座標で写したもの（同じ形を大きくても滲まずに描くため）
M_PTS = "131,367 131,147 175,147 256,282 337,147 380,147 380,367 334,367 334,235 269,344 243,344 178,235 178,367"


def tile(size, shadow=True):
    """白い角丸の札にオレンジのM（favicon と同じ比率）。size は札の一辺(px)"""
    # favicon の札は 68〜444（376px）・角は約44px。M はその中
    sh = f"box-shadow: 0 {size*0.05:.0f}px 0 {DEEP}, 0 {size*0.09:.0f}px {size*0.16:.0f}px rgba(0,0,0,.22);" if shadow else ""
    return f'''<div style="width:{size}px;height:{size}px;border-radius:{size*0.13:.0f}px;background:#fff;{sh}position:relative;flex:none">
      <svg viewBox="68 68 376 376" width="{size}" height="{size}" style="position:absolute;inset:0"><polygon points="{M_PTS}" fill="{ORANGE}"/></svg></div>'''


BASE = '<!doctype html><html><head><meta charset="utf-8"><style>*{margin:0;box-sizing:border-box}body{font-family:"Noto Sans JP",sans-serif}</style></head><body>'


def icon_html(S):
    # 丸に切り抜くと四隅が消えるので、飾りは丸の内側だけ。札は直径の54%（角が丸の縁に近づきすぎない）
    t = S * 0.54
    dots = "".join(f'<circle cx="{S/2 + S*0.40*math.cos(a):.1f}" cy="{S/2 + S*0.40*math.sin(a):.1f}" r="{S*0.010:.1f}" fill="{c}"/>'
                   for a, c in [(-2.0, "#fff"), (-1.85, "rgba(255,255,255,.5)"), (-1.70, "rgba(255,255,255,.5)"), (1.15, ORANGE), (1.30, "rgba(255,255,255,.5)"), (1.45, "rgba(255,255,255,.5)")])
    arcs = ""
    for a0, a1 in [(-1.45, -0.55), (0.35, 0.95), (1.75, 2.35), (2.75, 3.65)]:
        r = S * 0.40
        x0, y0 = S/2 + r*math.cos(a0), S/2 + r*math.sin(a0)
        x1, y1 = S/2 + r*math.cos(a1), S/2 + r*math.sin(a1)
        arcs += f'<path d="M{x0:.1f},{y0:.1f} A{r:.1f},{r:.1f} 0 0 1 {x1:.1f},{y1:.1f}" fill="none" stroke="rgba(255,255,255,.55)" stroke-width="{S*0.008:.1f}" stroke-linecap="round"/>'
    return BASE + f'''<div style="width:{S}px;height:{S}px;background:radial-gradient(circle at 50% 42%, #1E8296 0%, {TEAL} 55%, #0F6172 100%);position:relative;display:grid;place-items:center">
      <svg width="{S}" height="{S}" style="position:absolute;inset:0">{arcs}{dots}</svg>
      <div style="margin-top:-{S*0.025:.0f}px">{tile(t)}</div></div></body></html>'''


def sparkle(x, y, r, c):
    w = r * 0.22
    return f'<path d="M{x},{y-r} Q{x+w},{y-w} {x+r},{y} Q{x+w},{y+w} {x},{y+r} Q{x-w},{y+w} {x-r},{y} Q{x-w},{y-w} {x},{y-r}Z" fill="{c}"/>'


def banner_html(guide=False):
    W, H = 2560, 1440
    sx, sy, sw, sh = (W-1546)//2, (H-423)//2, 1546, 423  # 全端末で見える範囲
    # 背景: 淡い緑の地に、薄い牌の列と✨（見える範囲の外は飾りだけ。テレビでは全体が見える）
    tiles = ""
    for i in range(14):
        x = 120 + i * 175
        tiles += f'<rect x="{x}" y="1180" width="130" height="170" rx="18" fill="#fff" opacity=".55"/><rect x="{x}" y="1330" width="130" height="22" rx="8" fill="{TEAL}" opacity=".18"/>'
    sp = sparkle(400, 640, 46, TEAL) + sparkle(470, 820, 24, ORANGE) + sparkle(2170, 600, 30, ORANGE) + sparkle(2120, 820, 40, TEAL)  # 文字とマークに重ねない（見える範囲の外側の左右）
    g = ""
    if guide:
        for k, (gw, gh, c, n) in enumerate([(2560, 1440, "#999", "テレビ"), (2560, 423, "#E3571F", "PC（最大）"), (1855, 423, "#4261AA", "タブレット"), (1546, 423, "#177083", "スマホ・すべて")]):
            g += f'<rect x="{(W-gw)/2}" y="{(H-gh)/2}" width="{gw}" height="{gh}" fill="none" stroke="{c}" stroke-width="6" stroke-dasharray="24 14"/><text x="{(W-gw)/2+16}" y="{(H-gh)/2+46 if k < 2 else (H+gh)/2-18}" font-size="34" font-weight="800" fill="{c}">{n}</text>'
    return BASE + f'''<div style="width:{W}px;height:{H}px;position:relative;overflow:hidden;background:linear-gradient(180deg,#EAF6F1 0%,#DBF4F9 100%)">
      <svg width="{W}" height="{H}" style="position:absolute;inset:0">
        <circle cx="{W/2}" cy="{H/2}" r="640" fill="#fff" opacity=".45"/>
        <circle cx="300" cy="260" r="220" fill="{TEAL}" opacity=".06"/><circle cx="2300" cy="1120" r="260" fill="{TEAL}" opacity=".06"/>
        {tiles}{sp}
        <circle cx="770" cy="470" r="10" fill="{TEAL}" opacity=".35"/><circle cx="1830" cy="980" r="12" fill="{ORANGE}" opacity=".6"/>
      </svg>
      <div style="position:absolute;left:{sx}px;top:{sy}px;width:{sw}px;height:{sh}px;display:flex;align-items:center;justify-content:center;gap:64px">
        {tile(300)}
        <div style="color:#1F2A28">
          <div style="font-size:44px;font-weight:800;color:#8A9896;letter-spacing:.02em">majasco.jp</div>
          <div style="font-size:120px;font-weight:900;color:{TEAL};line-height:1.05;letter-spacing:.02em;margin:2px 0 14px">まじゃすこ</div>
          <div style="font-size:50px;font-weight:800;line-height:1.3">麻雀のスコア記録を、もっとかんたんに</div>
          <div style="font-size:38px;font-weight:700;color:#55635F;margin-top:12px"><span style="color:{ORANGE};font-weight:900">登録不要・無料</span>　URLひとつで全員のスマホに共有</div>
        </div>
      </div>
      <svg width="{W}" height="{H}" style="position:absolute;inset:0">{g}</svg>
    </div></body></html>'''


def x_header_html(guide=False):
    W, H = 1500, 500
    tiles = ""  # 下の端は切れることがあり、牌の列が縞に見えるので置かない
    sp = sparkle(1400, 120, 30, ORANGE) + sparkle(1430, 330, 22, TEAL) + sparkle(160, 120, 34, TEAL) + sparkle(250, 210, 16, ORANGE)
    g = ""
    if guide:
        g = (f'<rect x="0" y="60" width="{W}" height="{H-120}" fill="none" stroke="{ORANGE}" stroke-width="4" stroke-dasharray="18 10"/>'
             f'<text x="12" y="52" font-size="22" font-weight="800" fill="{ORANGE}">上下は端末で切れることがある</text>'
             f'<circle cx="200" cy="{H}" r="168" fill="rgba(0,0,0,.25)"/><text x="80" y="{H-40}" font-size="22" font-weight="800" fill="#fff">プロフィール画像</text>')
    return BASE + f'''<div style="width:{W}px;height:{H}px;position:relative;overflow:hidden;background:linear-gradient(180deg,#EAF6F1 0%,#DBF4F9 100%)">
      <svg width="{W}" height="{H}" style="position:absolute;inset:0">
        <circle cx="900" cy="250" r="380" fill="#fff" opacity=".45"/>
        <circle cx="90" cy="60" r="150" fill="{TEAL}" opacity=".06"/><circle cx="1440" cy="470" r="170" fill="{TEAL}" opacity=".06"/>
        {tiles}{sp}
      </svg>
      <div style="position:absolute;left:400px;right:120px;top:60px;bottom:60px;display:flex;align-items:center;justify-content:center;gap:40px">
        {tile(200)}
        <div style="color:#1F2A28">
          <div style="font-size:28px;font-weight:800;color:#8A9896">majasco.jp</div>
          <div style="font-size:78px;font-weight:900;color:{TEAL};line-height:1.05;letter-spacing:.02em;margin:0 0 10px">まじゃすこ</div>
          <div style="font-size:32px;font-weight:800;line-height:1.3">麻雀のスコア記録を、もっとかんたんに</div>
          <div style="font-size:24px;font-weight:700;color:#55635F;margin-top:8px"><span style="color:{ORANGE};font-weight:900">登録不要・無料</span>　URLひとつで全員のスマホに共有</div>
        </div>
      </div>
      <svg width="{W}" height="{H}" style="position:absolute;inset:0">{g}</svg>
    </div></body></html>'''


def watermark_html():
    return BASE.replace("<body>", '<body style="background:transparent">') + f'<div style="width:300px;height:300px;display:grid;place-items:center">{tile(236, shadow=False)}</div></body></html>'


def preview_html(src):
    return BASE + f'''<div style="display:flex;align-items:center;gap:60px;padding:50px 60px;background:#fff">
      {"".join(f'<div style="text-align:center"><img src="{src}" style="width:{s}px;height:{s}px;border-radius:50%;display:block"><div style="font-size:18px;color:#6B7A77;margin-top:10px">{s}px</div></div>' for s in (320, 120, 48, 32))}
      <div style="background:#0F0F0F;padding:30px 36px;border-radius:16px;display:flex;align-items:center;gap:18px"><img src="{src}" style="width:72px;height:72px;border-radius:50%"><div style="color:#fff;font-size:26px;font-weight:700">まじゃすこ<div style="font-size:16px;color:#aaa;font-weight:400">@majasco_jp</div></div></div>
    </div></body></html>'''


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()

        def shot(html, w, h, name, transparent=False):
            pg = b.new_page(viewport={"width": w, "height": h})
            pg.set_content(html)
            pg.wait_for_timeout(300)
            path = os.path.join(OUT, name)
            pg.screenshot(path=path, omit_background=transparent, clip={"x": 0, "y": 0, "width": w, "height": h})
            pg.close()
            print("  " + path)
            return path

        ic = shot(icon_html(1080), 1080, 1080, "icon-1080.png")
        shot(preview_html("data:image/png;base64," + base64.b64encode(open(ic, "rb").read()).decode()), 1180, 440, "icon-preview.png")
        shot(banner_html(), 2560, 1440, "yt-banner.png")
        shot(banner_html(guide=True), 2560, 1440, "yt-banner-guide.png")
        shot(watermark_html(), 300, 300, "yt-watermark.png", transparent=True)
        shot(x_header_html(), 1500, 500, "x-header.png")
        shot(x_header_html(guide=True), 1500, 500, "x-header-guide.png")
        b.close()


if __name__ == "__main__":
    main()
