# -*- coding: utf-8 -*-
# 実アプリ（index.html）の操作画面をスマホ実機サイズで撮影する（IG画像 make_ig_v2.py の素材）。
# リポジトリのindex.htmlをローカルサーバで開き、Firebase SDKだけ最小スタブに差し替えて
# サンプルデータを流し込む方式（DOM/CSS/描画コードは本物）。本番のFirebaseには一切触らない
# ため、検証セッションの削除も不要。リモート実行環境から本番へ接続できない場合でも動く。
# 実行: PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 tools/shoot_app_screens.py
#       （要: pip install playwright。日本語フォントがOSに無いと豆腐になるので注意）
import functools
import glob
import http.server
import json
import os
import threading

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig", "shots")
os.makedirs(OUTDIR, exist_ok=True)

PORT = 8788
SID = "ssv2abcdef"  # ハッシュ8文字以上でセッションとして扱われる

# ウマ10-30・25000持ち30000返し。scoresは (点数-返し点)/1000 + ウマ + トップにオカ20 を手計算した値
GAME = {
    "id": SID,
    "name": "金曜メンバー",
    "createdAt": "2026-07-17T11:05:00.000Z",
    "settings": {
        "playerNames": ["太郎", "次郎", "三郎", "四郎"],
        "numPlayers": 4, "startPoints": 25000, "returnPoints": 30000,
        "uma": [30, 10, -10, -30], "rate": 100, "bonusEnabled": False,
        "chipRate": 1, "startChips": 0, "yakitori": False,
        "chombo": False, "chomboPenalty": 20, "teamMode": False,
    },
    "rounds": [
        {"points": [48300, 26700, 18200, 6800], "scores": [68.3, 6.7, -21.8, -53.2],
         "members": [0, 1, 2, 3], "at": "2026-07-17T11:20:00.000Z"},
        {"points": [31200, 35600, 20400, 12800], "scores": [11.2, 55.6, -19.6, -47.2],
         "members": [0, 1, 2, 3], "at": "2026-07-17T12:05:00.000Z"},
        {"points": [42100, 8900, 27600, 21400], "scores": [62.1, -51.1, 7.6, -18.6],
         "members": [0, 1, 2, 3], "at": "2026-07-17T12:50:00.000Z"},
    ],
}

# firebase-*-compat.js の代わりに配信するスタブ。アプリが使うAPIだけ実装している
# （initializeApp / database().ref() / once / on / off / set / update / remove）
FIREBASE_STUB = """
(() => {
  const STORE = { sessions: { %(sid)s: %(game)s } };
  const listeners = [];
  const get = p => { let c = STORE; for (const k of p.split('/').filter(Boolean)) { if (c == null) return null; c = c[k]; } return c === undefined ? null : c; };
  const snap = p => ({ val: () => get(p), exists: () => get(p) != null });
  const fire = () => listeners.forEach(l => l.cb(snap(l.path)));
  const setPath = (p, v) => {
    const ks = p.split('/').filter(Boolean); let c = STORE;
    ks.slice(0, -1).forEach(k => { if (c[k] == null) c[k] = {}; c = c[k]; });
    if (v === null) delete c[ks[ks.length - 1]]; else c[ks[ks.length - 1]] = v;
    fire();
  };
  const ref = p => ({
    once: () => Promise.resolve(snap(p)),
    on: (ev, cb) => { listeners.push({ path: p, cb }); setTimeout(() => cb(snap(p)), 0); return cb; },
    off: (ev, cb) => { const i = listeners.findIndex(l => l.cb === cb); if (i >= 0) listeners.splice(i, 1); },
    set: v => { setPath(p, v); return Promise.resolve(); },
    update: o => { Object.keys(o).forEach(k => setPath(p + '/' + k, o[k])); return Promise.resolve(); },
    remove: () => { setPath(p, null); return Promise.resolve(); },
  });
  window.firebase = { initializeApp: () => {}, database: () => ({ ref }) };
})();
"""


def find_chromium():
    for pat in ["/opt/pw-browsers/chromium",
                "/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium-*/chrome-linux/headless_shell"]:
        for h in sorted(glob.glob(pat)):
            if os.path.isfile(h) and os.access(h, os.X_OK):
                return h
    return None


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=BASE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    stub = FIREBASE_STUB % {"sid": json.dumps(SID), "game": json.dumps(GAME, ensure_ascii=False)}
    with sync_playwright() as p:
        exe = find_chromium()
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 390, "height": 844}, device_scale_factor=3,
            is_mobile=True, has_touch=True, locale="ja-JP",
        )
        page = ctx.new_page()

        def route_firebase(route):
            body = stub if "firebase-app-compat" in route.request.url else "/* stub */"
            route.fulfill(status=200, content_type="application/javascript", body=body)

        page.route("https://www.gstatic.com/firebasejs/**", route_firebase)
        # 計測・広告など外部リクエストは遮断（オフラインでも表示が完結するように）
        page.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}")
                   and not url.startswith("https://www.gstatic.com/firebasejs"),
                   lambda route: route.abort())

        try:
            page.goto(f"http://127.0.0.1:{PORT}/index.html#{SID}", wait_until="load", timeout=30000)
            assert page.evaluate("typeof firebase") == "object", "firebaseスタブが読み込まれていない"
            # ハッシュURLは「参加バナー」経由のため、joinSessionを直接呼んでゲーム画面へ入る
            page.evaluate(f"joinSession('{SID}')")
            page.wait_for_function(
                "() => { const el = document.querySelector('#score-main-body');"
                " return el && el.innerText.includes('太郎'); }", timeout=15000)
            page.wait_for_timeout(800)  # グラフ描画・フォント安定待ち

            # 1) 画面トップ（タイトル＋総合成績カード）
            page.evaluate("window.scrollTo(0, 0)")
            page.wait_for_timeout(300)
            page.screenshot(path=os.path.join(OUTDIR, "shot-top.png"))

            # 2) 総合成績カードを画面上部に寄せた状態
            page.evaluate("""() => {
                const el = document.querySelector('#score-main-body');
                if (el) window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - 90);
            }""")
            page.wait_for_timeout(300)
            page.screenshot(path=os.path.join(OUTDIR, "shot-score.png"))

            # 3) ページ全体（クロップ素材用）
            page.screenshot(path=os.path.join(OUTDIR, "shot-full.png"), full_page=True)

            # 4) 点数入力シート（開いた状態）
            try:
                page.click(".fab", timeout=5000)
                page.wait_for_timeout(600)
                page.screenshot(path=os.path.join(OUTDIR, "shot-sheet.png"))
            except Exception as e:
                print("入力シート撮影はスキップ:", e)

            print("saved to", OUTDIR)
        finally:
            browser.close()
            server.shutdown()


if __name__ == "__main__":
    main()
