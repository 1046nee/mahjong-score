# -*- coding: utf-8 -*-
"""LP「1分でわかるまじゃすこの使い方」の4枚を、本物の画面のスマホ1画面（390×844）で撮る（2026-10-26〜）。
スタブの Firebase（本番に触れない）。見本の名前は 健太・美咲・翔・陽菜。
出力: まじゃすこ素材/ig/shots/howto-*.png（2倍）と assets/screens/howto-*.jpg（幅720）
実行: python tools/shoot_howto_screens.py
"""
import sys, os, functools, threading, http.server, random
MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(MJ, "tools"))
from smoke_test import FIREBASE_STUB
from account_test import AUTH_STUB
from playwright.sync_api import sync_playwright
from PIL import Image

OUT = os.path.join(MJ, "まじゃすこ素材", "ig", "shots")
SITE = os.path.join(MJ, "assets", "screens")
os.makedirs(OUT, exist_ok=True)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8807), functools.partial(Q, directory=MJ))
threading.Thread(target=srv.serve_forever, daemon=True).start()
NAMES = ["健太", "美咲", "翔", "陽菜"]
ROUNDS = [[452, 281, 173, 94], [198, 336, 245, 221], [377, 122, 289, 212], [264, 301, 158, 277]]  # 百点単位の持ち点（合計1000＝10万点）
for r in ROUNDS:
    assert sum(r) == 1000, r
shots = []
with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP")
    ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript",
              body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in r.request.url else ""))
    ctx.route(lambda u: not u.startswith("http://127.0.0.1:8807") and "gstatic" not in u, lambda r: r.abort())
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8807/")
    pg.wait_for_timeout(800)
    pg.add_style_tag(content="#toast, .toast { display: none !important; }")

    def snap(name):
        pg.wait_for_timeout(500)
        path = os.path.join(OUT, "howto-" + name + ".png")
        pg.screenshot(path=path)
        shots.append((name, path))

    # 1. 「はじめる」→ 何人で打つか
    pg.evaluate("window.scrollTo(0, 0); openQuickStart()")
    snap("1")
    pg.evaluate("closeQuickStart()")
    # ゲームを作る（名前とゲーム名を入れて開始）
    pg.evaluate("showView('setup')")
    pg.evaluate("applyMode(4)")
    pg.evaluate("(a) => { setupMembers = a; renderMembers(); document.getElementById('s-name').value = '金曜の麻雀'; }", NAMES)
    pg.evaluate("startGame()")
    pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=10000)
    pg.evaluate("showView('game'); window.scrollTo(0, 0)")
    pg.wait_for_timeout(600)
    # 2. URLを共有（手元のアドレスではなく本番のアドレスに見せる）
    pg.evaluate("shareUrlOf = id => 'https://majasco.jp/#' + id")
    pg.evaluate("openShareSheet()")
    snap("2")
    pg.evaluate("closeFormModal()")
    pg.wait_for_timeout(300)
    # 3. 点数入力（入れ終わって、合計のチェックが出ているところ）
    pg.evaluate("""async (pts) => { openSheet(-1); await new Promise(r => setTimeout(r, 120));
      pts.forEach((v, i) => { const el = document.getElementById('si-' + i); if (el) { el.value = String(v); el.dispatchEvent(new Event('input', { bubbles: true })); } });
      if (typeof autoFill === 'function') autoFill(); document.activeElement && document.activeElement.blur(); }""", ROUNDS[0])
    snap("3")
    # 4. 何試合か入れたあとの総合順位
    pg.evaluate("submitRound()")
    pg.wait_for_timeout(400)
    for r in ROUNDS[1:]:
        pg.evaluate("""async (pts) => { openSheet(-1); await new Promise(r => setTimeout(r, 120));
          pts.forEach((v, i) => { document.getElementById('si-' + i).value = String(v); }); autoFill();
          await new Promise(r => setTimeout(r, 80)); submitRound(); await new Promise(r => setTimeout(r, 200)); }""", r)
    pg.evaluate("window.scrollTo(0, 0)")
    snap("4")
    print("errors", errs)
    br.close()
srv.shutdown()
for name, path in shots:
    im = Image.open(path).convert("RGB").resize((720, round(844 * 720 / 390)), Image.LANCZOS)
    im.save(os.path.join(SITE, "howto-" + name + ".jpg"), quality=86, optimize=True, progressive=True)
print("saved", [s[0] for s in shots])
