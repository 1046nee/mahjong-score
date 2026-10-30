# -*- coding: utf-8 -*-
"""マイページのアイコンが、どこに出してもはみ出さないかを確かめる（2026-10-28〜。スタブ・本番DBには触らない）。
仮のログインで試合2つ・仲間ページ（自分は本人確認済み）を作り、用意している絵（AV_ICONS）を1つずつ自分のアイコンにして、
マイページ・仲間ページの各タブ・メンバーのシート・ヘッダーを開き、アイコンの絵（img.av-ill）が入れ物の丸からはみ出していないか・丸の真ん中にあるか・
丸いっぱいに広がっていないか（Googleの写真用の指定が効いていないか）を測る。
実行: python tools/avatar_fit_test.py   （ALL PASS と出ればよい。--shot で崩れた所を撮る）
"""
import os, sys, json, functools, http.server, threading
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_test import FIREBASE_STUB  # noqa: E402
from account_test import AUTH_STUB, SAFE  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8797
U1 = "uidTEST0001"
SHOT = "--shot" in sys.argv

# 入れ物から何px までのはみ出しを許すか（線の太さ・丸め）
TOL = 1.5
MEASURE = """() => {
  const out = [];
  document.querySelectorAll('img.av-ill').forEach(im => {
    if (!im.offsetParent) return;              // 見えていないもの
    const b = im.getBoundingClientRect();
    let p = im.parentElement;                  // 地の色が付いた入れ物（丸）
    while (p && getComputedStyle(p).backgroundColor === 'rgba(0, 0, 0, 0)' && p !== document.body) p = p.parentElement;
    if (!p) return;
    const r = p.getBoundingClientRect();
    const over = Math.max(r.left - b.left, b.right - r.right, r.top - b.top, b.bottom - r.bottom);
    const off = Math.max(Math.abs((b.left + b.right) / 2 - (r.left + r.right) / 2), Math.abs((b.top + b.bottom) / 2 - (r.top + r.bottom) / 2));
    const big = b.width > r.width * 0.9 && b.height > r.height * 0.9;   // 丸いっぱいに広がっている＝写真用の指定が効いている
    if (over > %s || off > 2 || big) out.push({ cls: p.className || p.tagName, w: Math.round(r.width), h: Math.round(r.height), over: Math.round(Math.max(over, off) * 10) / 10, src: im.src.split('/').pop(), why: big ? '丸いっぱい' : off > 2 ? '真ん中からずれ' : 'はみ出し' });
  });
  return out;
}""" % TOL


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Quiet, directory=BASE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{PORT}/"
    bad, errors = [], []
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, locale="ja-JP", device_scale_factor=2)
        ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript",
                  body=FIREBASE_STUB + AUTH_STUB if "firebase-app-compat" in r.request.url else "/* stub */"))
        ctx.route(lambda url: not url.startswith(app[:-1]) and not url.startswith("https://www.gstatic.com/firebasejs"), lambda r: r.abort())
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(app, wait_until="load"); pg.wait_for_timeout(600)

        def make_game(name, members, rounds):
            pg.evaluate("showView('setup')")
            pg.evaluate("(a) => { setupMembers = a[1]; renderMembers(); document.getElementById('s-name').value = a[0]; }", [name, members])
            pg.evaluate("startGame()")
            pg.wait_for_function(SAFE % "document.querySelector('#view-share').classList.contains('active')", timeout=10000)
            pg.evaluate("showView('game')")
            for sel, pts in rounds:
                pg.evaluate("""async (a) => { openSheet(-1); await new Promise(r => setTimeout(r, 100));
                  sheetSelected = a[0].slice(); renderSheetMembers(); renderSheetInputs();
                  a[1].forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
                  await new Promise(r => setTimeout(r, 100)); submitRound(); await new Promise(r => setTimeout(r, 500)); }""", [sel, pts])
            sid = pg.evaluate("sessionId"); pg.evaluate("leaveGame()")
            return sid

        g1 = make_game("金曜会1", ["むにぃ", "たろう", "じろう", "さぶろう", "しろう"],
                       [([0, 1, 2, 3], ["450", "280", "190"]), ([0, 1, 2, 4], ["150", "320", "290"]), ([1, 2, 3, 4], ["400", "300", "250"])])
        g2 = make_game("金曜会2", ["むにぃ", "たろう", "じろう", "しろう"], [([0, 1, 2, 3], ["380", "200", "250"])])
        pg.evaluate(f"setTag('{g1}', 'play', 0); setTag('{g2}', 'play', 0)")
        pg.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", U1)
        pg.evaluate("signInWithGoogle()"); pg.wait_for_load_state("load")
        pg.wait_for_function(SAFE % "currentUser && !accountBusy", timeout=10000); pg.wait_for_timeout(500)
        pg.evaluate("showView('history')"); pg.wait_for_timeout(300)
        pg.evaluate("openCreateCircle(); document.getElementById('cc-name').value = '金曜会'; document.getElementById('cc-me').value = 'むにぃ';")
        pg.evaluate("runCreateCircle()")
        pg.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=10000)
        pg.evaluate("openCircleAddGames()")
        pg.evaluate(f"() => {{ document.querySelectorAll('.cadd-pick').forEach(el => {{ el.checked = false; }}); document.getElementById('cadd-text').value = 'https://majasco.jp/#{g1}\\nhttps://majasco.jp/#{g2}'; }}")
        pg.evaluate("runCircleAddGames()")
        pg.wait_for_function(f"() => circleData && circleData.games && circleData.games['{g1}'] && circleData.games['{g2}']", timeout=15000)
        pg.wait_for_timeout(500)
        cid = pg.evaluate("circleId")
        icons = pg.evaluate("AV_ICONS.map(x => x[0]).filter(k => k !== 'ini')")

        def check(where, k):
            pg.wait_for_timeout(250)
            for b in pg.evaluate(MEASURE):
                b.update(where=where, icon=k); bad.append(b)
                if SHOT and len([x for x in bad if x["where"] == where]) == 1:
                    pg.screenshot(path=os.path.join(BASE, f"_avfit_{where}_{k}.png"))

        for k in icons:
            pg.evaluate("(k) => { myAv = { k, c: '#E82F2F' }; localStorage.setItem('mahjong-my-avatar', JSON.stringify(myAv)); renderHeaderAccount(); }", k)
            pg.evaluate("showView('history')"); check("マイページ", k)
            check("右上のマイページ", k)
            for t in ["rank", "grid", "h2h", "games", "people"]:
                pg.evaluate(f"openCircle('{cid}')"); pg.wait_for_timeout(200)
                pg.evaluate(f"circleTab = '{t}'; renderCircle()"); check(f"仲間ページ:{t}", k)
            pg.evaluate("openCircleMember(myCircleMid())"); check("メンバーのシート", k); pg.evaluate("closeFormModal()")
            pg.evaluate("openMyAvatarEdit()"); check("アイコンのシート", k); pg.evaluate("closeFormModal()")
            if pg.evaluate("typeof renderMyStats === 'function'"):
                pg.evaluate("showView('mystats')"); check("自分の成績", k)
        br.close()
    srv.shutdown()
    seen = {}
    for b in bad:
        key = (b["where"], b["cls"])
        seen.setdefault(key, []).append(f'{b["icon"]}({b["why"]} {b["over"]}px in {b["w"]}x{b["h"]})')
    for (w, c), v in seen.items():
        print(f"FAIL {w} .{c}: " + ", ".join(v[:6]) + (" …" if len(v) > 6 else ""))
    if errors:
        print("JSエラー:", errors[:3])
    print("AVATAR FIT TEST:", "ALL PASS" if not bad and not errors else f"{len(seen)} か所でFAIL")
    return 0 if not bad and not errors else 1


if __name__ == "__main__":
    sys.exit(main())
