# -*- coding: utf-8 -*-
"""LP「番外編：Safariからすぐ開く方法」の3枚の画面（2026-10-27〜）。
iPhoneのSafariの画面を、スマホと同じ大きさ（390×844）のHTMLで描いてブラウザで撮る。
1枚目の背景は本物のLPの画面、まじゃすこのアイコンは本物（assets/favicon.png）。ほかのお気に入りは実在のアプリに似せない一般的なアイコン。
出力: assets/screens/bm-1.jpg 〜 bm-3.jpg（幅720）。高さは決まりどおりのスマホの枠の画面（帯の下）にちょうど入る 390×793＝下が切れない
使い方: python tools/make_bookmark_steps.py [iPhoneで撮ったLPの画面.png]
  画面の写真を渡すと、1枚目の背景をそれにする（上の時計の帯を切り、下の「最近の試合」はぼかす＝個人の記録を見せない）。渡さなければ手元のLPを撮る
"""
import os, io, sys, functools, threading, http.server
from PIL import Image
from playwright.sync_api import sync_playwright

MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(MJ, "assets", "screens")
TMP = os.path.join(MJ, "まじゃすこ素材", "ig", "shots")
PORT = 8823
H = 793  # 枠の画面（帯の下）の縦横比 1.89/0.93 × 390
_WINFONT = "C:/Windows/Fonts/NotoSansJP-VF.ttf"
FONT = "file:///" + _WINFONT if os.path.exists(_WINFONT) else ""  # Windows 以外は Google Fonts の Noto Sans JP（GFONT）
GFONT = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700;800;900&display=block" rel="stylesheet">'
FAV = "file:///" + os.path.join(MJ, "assets", "favicon.png").replace("\\", "/")
ORANGE = "#E75620"

# SF Symbols 風の線のアイコン（自作）
IC = {
 "share": '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 3v12M7.5 7.5 12 3l4.5 4.5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/><path d="M8 11H6.5A1.5 1.5 0 0 0 5 12.5v7A1.5 1.5 0 0 0 6.5 21h11a1.5 1.5 0 0 0 1.5-1.5v-7a1.5 1.5 0 0 0-1.5-1.5H16" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>',
 "book": '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 6.5C10 5 7 4.6 4 5.2v13c3-.6 6-.2 8 1.3 2-1.5 5-1.9 8-1.3v-13c-3-.6-6-.2-8 1.3Zm0 0v13" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
 "star": '<svg viewBox="0 0 24 24" width="22" height="22"><path d="m12 3.5 2.6 5.3 5.8.8-4.2 4.1 1 5.8L12 16.8l-5.2 2.7 1-5.8-4.2-4.1 5.8-.8Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
 "list": '<svg viewBox="0 0 24 24" width="22" height="22"><circle cx="8.5" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M14 9h6M14 12h6M14 15h6" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
 "plus": '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M12 5v14M5 12h14" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>',
 "folder": '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M3.5 7.5A1.5 1.5 0 0 1 5 6h4.2l2 2H19a1.5 1.5 0 0 1 1.5 1.5v8A1.5 1.5 0 0 1 19 19H5a1.5 1.5 0 0 1-1.5-1.5Z" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linejoin="round"/></svg>',
 "back": '<svg viewBox="0 0 24 24" width="22" height="22"><path d="M15 5 8 12l7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "more": '<svg viewBox="0 0 24 24" width="22" height="22"><circle cx="5.5" cy="12" r="1.9" fill="currentColor"/><circle cx="12" cy="12" r="1.9" fill="currentColor"/><circle cx="18.5" cy="12" r="1.9" fill="currentColor"/></svg>',
 "reload": '<svg viewBox="0 0 24 24" width="18" height="18"><path d="M19 12a7 7 0 1 1-2.1-5" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/><path d="M17.5 3.5V7.5h-4" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "check": '<svg viewBox="0 0 24 24" width="22" height="22"><path d="m5 12.5 4.5 4.5L19 7.5" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/></svg>',
 "search": '<svg viewBox="0 0 24 24" width="18" height="18"><circle cx="10.5" cy="10.5" r="6" fill="none" stroke="currentColor" stroke-width="2"/><path d="m15 15 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>',
 "close": '<svg viewBox="0 0 24 24" width="20" height="20"><path d="M6 6l12 12M18 6 6 18" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"/></svg>',
 "person": '<svg viewBox="0 0 24 24" width="22" height="22"><circle cx="12" cy="8.5" r="3.8" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4.5 20c1.3-3.6 4.2-5.4 7.5-5.4s6.2 1.8 7.5 5.4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
}

CSS_T = """
@font-face {{ font-family: NJP; src: url('{FONT}'); font-weight: 100 900; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ width: 390px; height: {H}px; overflow: hidden; font-family: NJP, 'Noto Sans JP', -apple-system, sans-serif; color: #1C1C1E; position: relative; background: #F2F2F7; }}
.badge {{ position: absolute; z-index: 9; width: 30px; height: 30px; border-radius: 50%; background: {ORANGE}; color: #fff; font-weight: 900; font-size: 17px;
  display: grid; place-items: center; border: 2.5px solid #fff; box-shadow: 0 3px 8px rgba(0,0,0,.25); }}
.ring {{ position: absolute; z-index: 8; box-sizing: border-box; border: 3.5px solid {ORANGE}; border-radius: 16px; box-shadow: 0 0 0 4px rgba(231,86,32,.18); }}
/* Safari の下のバー */
.sbar {{ position: absolute; left: 0; right: 0; bottom: 0; height: 96px; padding: 10px 14px 0; display: flex; gap: 10px; align-items: flex-start;
  background: rgba(249,249,251,.94); border-top: 0.5px solid rgba(0,0,0,.12); }}
.sbtn {{ flex: none; width: 46px; height: 46px; border-radius: 50%; background: #fff; display: grid; place-items: center; color: #1C1C1E; box-shadow: 0 1px 3px rgba(0,0,0,.12); }}
.addr {{ flex: 1; height: 46px; border-radius: 23px; background: #fff; display: flex; align-items: center; justify-content: center; gap: 8px; font-size: 16px; font-weight: 600; color: #1C1C1E; box-shadow: 0 1px 3px rgba(0,0,0,.12); position: relative; }}
.addr .rl {{ position: absolute; right: 14px; color: #3C3C43; display: grid; }}
/* メニュー */
.menu {{ position: absolute; right: 12px; bottom: 108px; width: 268px; background: rgba(250,250,252,.98); border-radius: 18px; box-shadow: 0 12px 40px rgba(0,0,0,.25); overflow: hidden; }}
.menu .it {{ display: flex; align-items: center; justify-content: space-between; height: 48px; padding: 0 16px; font-size: 16px; border-bottom: 0.5px solid rgba(60,60,67,.18); }}
.menu .it:last-child {{ border-bottom: none; }}
.menu .it span {{ display: grid; color: #1C1C1E; }}
.dim {{ position: absolute; inset: 0; background: rgba(0,0,0,.18); }}
/* ブックマークを追加 */
.nav {{ height: 56px; display: flex; align-items: center; justify-content: space-between; padding: 0 12px; }}
.nav h1 {{ font-size: 17px; font-weight: 700; }}
.circ {{ width: 36px; height: 36px; border-radius: 50%; background: #E3E3E8; display: grid; place-items: center; color: #3C3C43; }}
.save {{ width: 36px; height: 36px; border-radius: 50%; background: #0A84FF; display: grid; place-items: center; color: #fff; }}
.grp {{ margin: 10px 16px 0; background: #fff; border-radius: 14px; overflow: hidden; }}
.row {{ display: flex; align-items: center; gap: 12px; min-height: 50px; padding: 0 16px; font-size: 16px; border-bottom: 0.5px solid rgba(60,60,67,.18); }}
.row:last-child {{ border-bottom: none; }}
.lab {{ margin: 24px 32px 0; font-size: 13px; color: #6C6C70; }}
.fav {{ width: 60px; height: 60px; border-radius: 14px; display: block; box-shadow: 0 1px 4px rgba(0,0,0,.12); }}
/* お気に入り（新規タブ） */
.grid {{ display: grid; grid-template-columns: repeat(4, 64px); gap: 22px 24px; justify-content: center; margin-top: 16px; }}
.tile {{ text-align: center; font-size: 11.5px; color: #3C3C43; }}
.tile .ic {{ width: 64px; height: 64px; border-radius: 15px; display: grid; place-items: center; font-weight: 800; font-size: 24px; color: #fff; margin-bottom: 6px; box-shadow: 0 1px 4px rgba(0,0,0,.12); }}
.tile img {{ width: 64px; height: 64px; border-radius: 15px; display: block; margin-bottom: 6px; box-shadow: 0 1px 4px rgba(0,0,0,.12); }}
"""
CSS = CSS_T.format(FONT=FONT, ORANGE=ORANGE, H=H)

# 枠と番号: 押すところに data-ring="番号" を付けておき、描いたあとに部品の実際の位置から作る（2026-10-27 手で書いた座標がずれていた）。
# 枠は部品の上下左右に同じ余白（PAD）。角の丸みは部品の丸み＋余白（丸いボタンは丸い枠）。
# 番号は枠の右上の角。画面の右端からはみ出すときは左上、上端からはみ出すときは下の角へ
PAD = 7
RING_JS = """(pad) => {
  const W = innerWidth, H = innerHeight;
  document.querySelectorAll('[data-ring]').forEach(el => {
    const r = el.getBoundingClientRect();
    const x = r.left - pad, y = r.top - pad, w = r.width + pad * 2, h = r.height + pad * 2;
    const cs = getComputedStyle(el), br = cs.borderTopLeftRadius;
    const round = br.endsWith('%') ? parseFloat(br) >= 50 : parseFloat(br) >= Math.min(r.width, r.height) / 2 - 0.5;
    const rad = round ? Math.min(w, h) / 2 : (parseFloat(br) || 10) + pad;
    const ring = document.createElement('div');
    ring.className = 'ring';
    Object.assign(ring.style, { left: x + 'px', top: y + 'px', width: w + 'px', height: h + 'px', borderRadius: rad + 'px' });
    document.body.appendChild(ring);
    const b = document.createElement('div');
    b.className = 'badge'; b.textContent = el.dataset.ring;
    const s = 30, cut = round ? (1 - Math.SQRT1_2) * rad : Math.min(rad, 14) * 0.3;
    let bx = x + w - cut - s / 2, by = y + cut - s / 2;
    if (bx + s > W - 2) bx = x + cut - s / 2;
    if (by < 2) by = y + h - cut - s / 2;
    Object.assign(b.style, { left: Math.max(2, Math.min(W - s - 2, bx)) + 'px', top: Math.max(2, Math.min(H - s - 2, by)) + 'px' });
    document.body.appendChild(b);
  });
}"""

def bar(more_ring=None):
    return ('<div class="sbar"><div class="sbtn">' + IC["back"] + '</div>'
            '<div class="addr">majasco.jp<span class="rl">' + IC["reload"] + '</span></div>'
            '<div class="sbtn"' + (f' data-ring="{more_ring}"' if more_ring else '') + '>' + IC["more"] + '</div></div>')

def step1(lp_png):
    menu = ('<div class="menu">'
            f'<div class="it">共有<span>{IC["share"]}</span></div>'
            f'<div class="it" data-ring="2" style="font-weight:700">ブックマークに追加<span>{IC["book"]}</span></div>'
            f'<div class="it">リーディングリストに追加<span>{IC["list"]}</span></div>'
            f'<div class="it">新規タブ<span>{IC["plus"]}</span></div></div>')
    return (f'<img src="{lp_png}" style="position:absolute;left:0;top:0;width:390px">'
            '<div class="dim"></div>' + menu + bar(more_ring=1))  # ① 「…」 ② 「ブックマークに追加」

def step2():
    return ('<div style="position:absolute;inset:0;background:#F2F2F7">'
            f'<div class="nav"><div class="circ">{IC["close"]}</div><h1>ブックマークを追加</h1><div class="save" data-ring="4">{IC["check"]}</div></div>'
            f'<div class="grp"><div class="row" style="padding:14px 16px;align-items:flex-start"><img class="fav" src="{FAV}">'
            '<div style="flex:1"><div style="font-size:16px;padding:6px 0 10px;border-bottom:0.5px solid rgba(60,60,67,.18)">まじゃすこ</div>'
            '<div style="font-size:15px;color:#6C6C70;padding-top:10px">https://majasco.jp/</div></div></div></div>'
            '<div class="lab">場所</div>'
            f'<div class="grp"><div class="row" data-ring="3" style="font-weight:700"><span style="color:#0A84FF;display:grid">{IC["star"]}</span><span style="flex:1">お気に入り</span><span style="color:#0A84FF;display:grid">{IC["check"]}</span></div>'
            f'<div class="row"><span style="color:#0A84FF;display:grid">{IC["folder"]}</span><span style="flex:1">ブックマーク</span></div></div>'
            '</div>')  # ③ お気に入り ④ 保存

def step3():
    tiles = [("FAV", "まじゃすこ"), ("#5E8BD6", "天気", "天"), ("#7A8A99", "ニュース", "N"), ("#4FA06B", "地図", "地"),
             ("#C9A227", "辞書", "辞"), ("#8E7CC3", "乗換", "乗"), ("#D98A5F", "レシピ", "R"), ("#9AA4AD", "", "")]
    g = ""
    for t in tiles:
        if t[0] == "FAV":
            g += f'<div class="tile" data-ring="5"><img src="{FAV}">{t[1]}</div>'
        elif t[1]:
            g += f'<div class="tile"><div class="ic" style="background:{t[0]}">{t[2]}</div>{t[1]}</div>'
        else:
            g += '<div class="tile"><div class="ic" style="background:#E3E3E8"></div></div>'
    return ('<div style="position:absolute;inset:0;background:#F2F2F7">'
            f'<div style="display:flex;align-items:center;gap:8px;margin:28px 28px 0;font-size:21px;font-weight:800">お気に入り</div>'
            f'<div class="grid">{g}</div>'
            '<div style="margin:38px 28px 0;font-size:21px;font-weight:800">よく閲覧するサイト</div>'
            '<div style="margin:12px 24px 0;display:grid;grid-template-columns:1fr 1fr;gap:12px">'
            + "".join('<div style="height:64px;border-radius:14px;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.08)"></div>' for _ in range(4)) + '</div>'
            '</div>'
            + '<div class="sbar"><div class="sbtn">' + IC["back"] + '</div><div class="addr" style="color:#8E8E93;font-weight:500"><span style="display:grid">'
            + IC["search"] + '</span>検索／サイト名を入力</div><div class="sbtn">' + IC["more"] + '</div></div>')  # ⑤ まじゃすこ

class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass

def main():
    os.makedirs(TMP, exist_ok=True)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=MJ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        b = p.chromium.launch()
        # 1枚目の背景：本物のLPの最初の画面（外の通信は止める）
        ctx = b.new_context(viewport={"width": 390, "height": H}, device_scale_factor=2, locale="ja-JP")
        ctx.route(lambda u: not u.startswith(f"http://127.0.0.1:{PORT}") and "fonts.g" not in u, lambda r: r.abort())  # 文字（Google Fonts）だけは通す
        pg = ctx.new_page()
        pg.goto(f"http://127.0.0.1:{PORT}/"); pg.wait_for_timeout(1500)
        pg.add_style_tag(content="#toast, .toast { display: none !important; }")
        lp = os.path.join(TMP, "bm-lp.png")
        pg.screenshot(path=lp)
        ctx.close()
        if len(sys.argv) > 1:  # iPhoneの本物の画面を背景にする（2026-10-31〜）
            from PIL import ImageFilter
            src = Image.open(sys.argv[1]).convert("RGB")
            top = round(src.height * 0.074)  # 時計・電池の帯（画面の高さの約7.4%）を切る
            im = src.crop((0, top, src.width, src.height))
            im = im.resize((780, round(im.height * 780 / src.width)), Image.LANCZOS)
            cut = round(im.height * 0.86)  # 「最近の試合」から下（自分の記録）はぼかす
            im.paste(im.crop((0, cut, 780, im.height)).filter(ImageFilter.GaussianBlur(14)), (0, cut))
            can = Image.new("RGB", (780, H * 2), im.getpixel((5, im.height - 5)))
            can.paste(im, (0, 0))
            can.save(lp)
        pg = b.new_page(viewport={"width": 390, "height": H}, device_scale_factor=2)
        lp_url = "file:///" + lp.replace("\\", "/")
        for i, body in enumerate([step1(lp_url), step2(), step3()], 1):
            hp = os.path.join(TMP, f"_bm{i}.html")
            io.open(hp, "w", encoding="utf-8").write(f"<!doctype html><html><head><meta charset='utf-8'>{'' if FONT else GFONT}<style>{CSS}</style></head><body>{body}</body></html>")
            pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
            pg.evaluate(RING_JS, PAD)
            png = os.path.join(TMP, f"bm-{i}.png")
            pg.screenshot(path=png)
            os.remove(hp)
            im = Image.open(png).convert("RGB").resize((720, round(H * 720 / 390)), Image.LANCZOS)
            im.save(os.path.join(OUT, f"bm-{i}.jpg"), quality=88, optimize=True, progressive=True)
            print("ok", f"bm-{i}.jpg")
        b.close()
    srv.shutdown()

if __name__ == "__main__":
    main()
