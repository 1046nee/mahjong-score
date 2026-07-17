# -*- coding: utf-8 -*-
# 実アプリ（index.html）の操作画面をスマホ実機サイズで撮影する（IGv2シリーズ make_ig_v2.py の素材）。
# リポジトリのindex.htmlをローカルサーバで開き、Firebase SDKだけ最小スタブに差し替えて
# サンプルデータを流し込む方式（DOM/CSS/描画コードは本物）。本番のFirebaseには一切触れない
# ため、検証セッションの削除も不要。リモート実行環境から本番へ接続できない場合でも動く。
# 実行: PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 tools/shoot_app_screens.py
#       （要: pip install playwright。日本語フォントがOSに無いと豆腐になるので注意）
#
# 撮影セッション: 通常四麻 ／ 三麻（青テーマ） ／ チーム戦（8人4チーム） ／ チップ・焼き鳥・チョンボあり
# 出力: まじゃすこ素材/ig/shots/（shot-*=画面全体、el-*=カード等の要素単位）
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

# セッションID: セキュリティルールの文字集合 [A-HJ-NP-Za-hj-km-np-z2-9] で10文字（i/l/o/0/1は使えない）
SID_NORMAL = "ssv2abcdef"
SID_SANMA = "sanmav2abc"
SID_TEAM = "teamv2abcd"
SID_CHIPS = "chpv2abcde"

# scoresは (点数-返し点)/1000 + ウマ + トップにオカ を手計算した値（四麻: 25000/30000でオカ20、
# 三麻: 35000/40000でオカ15）。チョンボは罰符ptsをそのまま減算
GAMES = {
    SID_NORMAL: {
        "id": SID_NORMAL, "name": "金曜メンバー", "createdAt": "2026-07-17T11:05:00.000Z",
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
    },
    SID_SANMA: {
        "id": SID_SANMA, "name": "木曜三麻会", "createdAt": "2026-07-16T20:00:00.000Z",
        "settings": {
            "playerNames": ["太郎", "次郎", "三郎"],
            "numPlayers": 3, "startPoints": 35000, "returnPoints": 40000,
            "uma": [15, 0, -15], "rate": 100, "bonusEnabled": False,
            "chipRate": 1, "startChips": 0, "yakitori": False,
            "chombo": False, "chomboPenalty": 20, "teamMode": False,
        },
        "rounds": [
            {"points": [52300, 33400, 19300], "scores": [42.3, -6.6, -35.7],
             "members": [0, 1, 2], "at": "2026-07-16T20:15:00.000Z"},
            {"points": [30200, 48100, 26700], "scores": [-9.8, 38.1, -28.3],
             "members": [0, 1, 2], "at": "2026-07-16T20:55:00.000Z"},
            {"points": [45600, 24100, 35300], "scores": [35.6, -30.9, -4.7],
             "members": [0, 1, 2], "at": "2026-07-16T21:30:00.000Z"},
        ],
    },
    SID_TEAM: {
        "id": SID_TEAM, "name": "サークル団体戦", "createdAt": "2026-07-15T19:00:00.000Z",
        "settings": {
            "playerNames": ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎", "七郎", "八郎"],
            "numPlayers": 4, "startPoints": 25000, "returnPoints": 30000,
            "uma": [30, 10, -10, -30], "rate": 100, "bonusEnabled": False,
            "chipRate": 1, "startChips": 0, "yakitori": False,
            "chombo": False, "chomboPenalty": 20, "teamMode": True,
            "teams": [
                {"name": "赤組", "members": [0, 4]}, {"name": "青組", "members": [1, 5]},
                {"name": "緑組", "members": [2, 6]}, {"name": "橙組", "members": [3, 7]},
            ],
        },
        "rounds": [
            {"points": [48300, 26700, 18200, 6800], "scores": [68.3, 6.7, -21.8, -53.2],
             "members": [0, 1, 2, 3], "at": "2026-07-15T19:20:00.000Z"},
            {"points": [31200, 35600, 20400, 12800], "scores": [11.2, 55.6, -19.6, -47.2],
             "members": [4, 5, 6, 7], "at": "2026-07-15T20:05:00.000Z"},
            {"points": [42100, 8900, 27600, 21400], "scores": [62.1, -51.1, 7.6, -18.6],
             "members": [0, 5, 6, 3], "at": "2026-07-15T20:50:00.000Z"},
        ],
    },
    SID_CHIPS: {
        "id": SID_CHIPS, "name": "金曜メンバー", "createdAt": "2026-07-17T11:05:00.000Z",
        "settings": {
            "playerNames": ["太郎", "次郎", "三郎", "四郎"],
            "numPlayers": 4, "startPoints": 25000, "returnPoints": 30000,
            "uma": [30, 10, -10, -30], "rate": 100, "bonusEnabled": True,
            "chipRate": 500, "startChips": 20, "yakitori": True,
            "chombo": True, "chomboPenalty": 20, "teamMode": False,
        },
        "rounds": [
            # 四郎がチョンボ（-20pts減算）、三郎が焼き鳥。chipsはチップ差（合計0）
            {"points": [48300, 26700, 18200, 6800], "scores": [68.3, 6.7, -21.8, -73.2],
             "chips": [3, -2, 1, -2], "yakitori": [0, 0, 1, 0], "chombo": [0, 0, 0, 1],
             "members": [0, 1, 2, 3], "at": "2026-07-17T11:20:00.000Z"},
            {"points": [31200, 35600, 20400, 12800], "scores": [11.2, 55.6, -19.6, -47.2],
             "chips": [1, 4, -2, -3], "yakitori": [0, 0, 0, 1], "chombo": [0, 0, 0, 0],
             "members": [0, 1, 2, 3], "at": "2026-07-17T12:05:00.000Z"},
        ],
    },
}

# firebase-*-compat.js の代わりに配信するスタブ。アプリが使うAPIだけ実装している
# （initializeApp / database().ref() / once / on / off / set / update / remove）
FIREBASE_STUB = """
(() => {
  const STORE = { sessions: %(sessions)s };
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


def shot(page, name):
    page.wait_for_timeout(300)
    page.screenshot(path=os.path.join(OUTDIR, name))
    print("shot:", name)


def shot_el(page, selector, name, nth=0):
    loc = page.locator(selector).nth(nth)
    loc.scroll_into_view_if_needed()
    page.wait_for_timeout(200)
    loc.screenshot(path=os.path.join(OUTDIR, name))
    print("shot:", name)


def join(page, sid):
    page.evaluate(f"joinSession('{sid}')")
    page.wait_for_function(
        "() => { const el = document.querySelector('#score-main-body');"
        " return el && el.innerText.includes('太郎'); }", timeout=15000)
    page.wait_for_timeout(800)  # グラフ描画・フォント安定待ち
    page.evaluate("window.scrollTo(0, 0)")


def scroll_to(page, selector, offset=90):
    page.evaluate("""([sel, off]) => {
        const el = document.querySelector(sel);
        if (el) window.scrollTo(0, el.getBoundingClientRect().top + window.scrollY - off);
    }""", [selector, offset])


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=BASE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    stub = FIREBASE_STUB % {"sessions": json.dumps(GAMES, ensure_ascii=False)}
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
            page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=30000)
            assert page.evaluate("typeof firebase") == "object", "firebaseスタブが読み込まれていない"

            # ---- 通常四麻 ----
            join(page, SID_NORMAL)
            shot(page, "shot-top.png")
            scroll_to(page, "#score-main-body")
            shot(page, "shot-score.png")
            page.screenshot(path=os.path.join(OUTDIR, "shot-full.png"), full_page=True)
            shot_el(page, "#score-main-body .score-card", "el-row1.png", 0)
            shot_el(page, "#score-main-body .score-card", "el-row2.png", 1)
            shot_el(page, "#chart-card", "el-graph.png")
            scroll_to(page, "#chart-card")
            shot(page, "shot-graph.png")
            page.evaluate("window.scrollTo(0, 0)")
            # URL共有画面
            page.evaluate(
                f"() => {{ document.getElementById('share-url').value = 'https://majasco.jp/#{SID_NORMAL}';"
                f" showView('share'); }}")
            shot(page, "shot-share.png")
            page.evaluate("showView('game')")
            page.wait_for_timeout(400)
            # 点数入力シート（第3試合の修正=数値が入った状態）
            page.evaluate("openSheet(2)")
            shot(page, "shot-sheet-edit.png")
            page.evaluate("closeSheet()")
            page.wait_for_timeout(300)

            # ---- 三麻（青テーマ） ----
            join(page, SID_SANMA)
            shot(page, "sanma-top.png")
            scroll_to(page, "#score-main-body")
            shot(page, "sanma-score.png")
            shot_el(page, "#score-main-body .score-card", "el-sanma-row1.png", 0)

            # ---- チーム戦 ----
            join(page, SID_TEAM)
            shot(page, "team-top.png")
            shot_el(page, "#team-card", "el-team.png")
            shot_el(page, "#chart-card", "el-team-chart.png")
            page.evaluate("window.scrollTo(0, 0)")

            # ---- チップ・焼き鳥・チョンボあり ----
            join(page, SID_CHIPS)
            scroll_to(page, "#score-main-body")
            shot(page, "chips-score.png")
            shot_el(page, "#score-main-body .score-card", "el-chips-row1.png", 0)
            page.evaluate("openSheet(0)")  # 第1試合の修正（チップ・🐔・💩が入った状態）
            shot(page, "chips-sheet.png")
            page.evaluate("closeSheet()")

            print("saved to", OUTDIR)
        finally:
            browser.close()
            server.shutdown()


if __name__ == "__main__":
    main()
