# -*- coding: utf-8 -*-
"""LP「実際の画面で見る。」の画面を、実際の仲間ページの数字（名前は置きかえたもの）で撮る（2026-10-26〜）。
本番には触れない（smoke_test のスタブの Firebase に、名前を置きかえたデータを先に入れてから開く）。
データ（仲間ページ1つ分。名前・アカウントは置きかえ済み）はリポジトリに入れない。手元のファイルを引数で渡す:
  python tools/shoot_lp_screens.py <circle_anon.json> [--explore]
出力: まじゃすこ素材/ig/shots/lp-*.png（2倍の解像度）。サイト用の JPEG（幅720）は assets/screens/lp-*.jpg
"""
import sys, os, io, json, functools, threading, http.server
MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(MJ, "tools"))
from smoke_test import FIREBASE_STUB
from account_test import AUTH_STUB
from playwright.sync_api import sync_playwright

DATA = sys.argv[1]
EXPLORE = "--explore" in sys.argv
OUT = os.path.join(MJ, "まじゃすこ素材", "ig", "shots")
SITE = os.path.join(MJ, "assets", "screens")
os.makedirs(OUT, exist_ok=True)
UID = "uidSHOT01"


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8806), functools.partial(Q, directory=MJ))
threading.Thread(target=srv.serve_forever, daemon=True).start()

d = json.load(io.open(DATA, encoding="utf-8"))
circle = d["circle"]
# ゲーム名が長いと画面で「…」に省略されるので、日付のあとの場所などは撮るときだけ外す（「2026.10.03（土）京都」→「2026.10.03（土）」）
import re as _re
def _short(n):
    m = _re.match(r"^(\d{4}\.\d{2}\.\d{2}（.）)", n or "")
    return m.group(1) if m else n
for _v in d["sessions"].values():
    if _v.get("name"): _v["name"] = _short(_v["name"])
for _g in circle.get("games", {}).values():
    if _g.get("name"): _g["name"] = _short(_g["name"])
CID = circle["id"]
store = {"sessions": d["sessions"], "circles": {CID: circle},
         "users": {UID: {"circles": {CID: {"at": circle.get("createdAt"), "name": circle["name"]}}}}}
SEED = "if (!localStorage.getItem('__seeded')) { localStorage.setItem('__smoke_db', " + json.dumps(json.dumps(store, ensure_ascii=False)) + "); localStorage.setItem('__seeded', '1'); }"

# 文字が切れていないか（はみ出し・…で省略）を、撮る要素の中で調べる
CUT_JS = """(sel) => { const root = document.querySelector(sel); if (!root) return ['(no element)'];
  const bad = [];
  root.querySelectorAll('*').forEach(e => { const cs = getComputedStyle(e);
    if (!e.children.length && e.textContent.trim() && (e.scrollWidth > e.clientWidth + 1) && (cs.overflow !== 'visible' || cs.textOverflow === 'ellipsis' || cs.whiteSpace === 'nowrap'))
      bad.push(e.className + ': ' + e.textContent.trim().slice(0, 20)); });
  return bad; }"""

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP")
    ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript",
              body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in r.request.url else ""))
    ctx.route(lambda u: not u.startswith("http://127.0.0.1:8806") and "gstatic" not in u, lambda r: r.abort())
    ctx.add_init_script(SEED)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8806/")
    pg.wait_for_timeout(600)
    pg.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", UID)
    pg.evaluate("signInWithGoogle()")
    pg.wait_for_load_state("load")
    pg.wait_for_function("() => typeof currentUser !== 'undefined' && currentUser && !accountBusy", timeout=20000)
    pg.wait_for_timeout(800)
    pg.add_style_tag(content="#toast, .toast { display: none !important; }")
    pg.evaluate(f"openCircle('{CID}')")
    pg.wait_for_function("() => document.querySelector('#view-circle').classList.contains('active') && circleData && Object.keys(circleSess || {}).length > 50", timeout=30000)
    pg.wait_for_timeout(1500)
    if EXPLORE:
        pg.screenshot(path=os.path.join(OUT, "lp-explore.png"), full_page=True)
        print("tabs", pg.evaluate("[...document.querySelectorAll('#view-circle [onclick]')].map(e => e.getAttribute('onclick')).filter((v, i, a) => a.indexOf(v) === i).slice(0, 60)"))
        print("errors", errs)
        br.close(); srv.shutdown(); sys.exit(0)

    shots = []

    def shot(sel, name, modal=False):
        el = pg.locator(sel).first
        el.scroll_into_view_if_needed()
        pg.wait_for_timeout(350)
        path = os.path.join(OUT, "lp-" + name + ".png")
        el.screenshot(path=path)
        cut = pg.evaluate(CUT_JS, sel)
        shots.append((name, path, cut))

    exec(open(os.path.join(MJ, "tools", "shoot_lp_screens_plan.py"), encoding="utf-8").read())
    print("errors", errs)
    for name, path, cut in shots:
        print(name, "切れ:", cut if cut else "なし")
    br.close()
srv.shutdown()

# サイト用（幅720の JPEG）
from PIL import Image
for name, path, cut in shots:
    im = Image.open(path).convert("RGB")
    if im.width > 720:
        im = im.resize((720, round(im.height * 720 / im.width)), Image.LANCZOS)
    im.save(os.path.join(SITE, "lp-" + name + ".jpg"), quality=86, optimize=True, progressive=True)
print("saved", [s[0] for s in shots])
