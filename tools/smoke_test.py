# -*- coding: utf-8 -*-
# デプロイ前スモークテスト: アプリの「主要動線」が壊れていないかを実ブラウザで検証する。
# GitHub Actions（firebase-hosting-merge.yml）がmainへのpushごとに実行し、
# 失敗したらデプロイを中止する。ローカルでも実行可能。
#
# 検証する動線（2026-07-18の「共有URLで開くとLPしか出ない」障害の再発防止が起点）:
#   1. LPが表示される
#   2. グループ作成 → URL共有画面が出て、URLに#セッションIDが含まれる
#   3. 共有URLを開き直す（受け取った人のシミュレーション）→ 試合画面が自動で開く
#   4. 点数入力（自動入力ボタン含む）→ 総合成績にスコアが表示される
#   5. スコア推移グラフのカードが存在する
#
# Firebaseは最小スタブに差し替え（本番に触れない）。ページ再読み込み後も
# データが残るよう、スタブの保存先はlocalStorage。
# 実行: python3 tools/smoke_test.py
#   （ローカルは PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers を付与。CIは不要）
import functools
import glob
import http.server
import os
import sys
import threading

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8794

# localStorageに永続化するFirebaseスタブ（リロードしても同じデータが見える）
FIREBASE_STUB = """
(() => {
  const KEY = '__smoke_db';
  const load = () => { try { return JSON.parse(localStorage.getItem(KEY)) || { sessions: {} }; } catch (e) { return { sessions: {} }; } };
  const STORE = load();
  const save = () => localStorage.setItem(KEY, JSON.stringify(STORE));
  const listeners = [];
  const get = p => { let c = STORE; for (const k of p.split('/').filter(Boolean)) { if (c == null) return null; c = c[k]; } return c === undefined ? null : c; };
  const snap = p => ({ val: () => get(p), exists: () => get(p) != null });
  const fire = () => listeners.forEach(l => l.cb(snap(l.path)));
  const setPath = (p, v) => {
    const ks = p.split('/').filter(Boolean); let c = STORE;
    ks.slice(0, -1).forEach(k => { if (c[k] == null) c[k] = {}; c = c[k]; });
    if (v === null) delete c[ks[ks.length - 1]]; else c[ks[ks.length - 1]] = v;
    save(); fire();
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
    for pat in ["/opt/pw-browsers/chromium-*/chrome-linux/chrome",
                "/opt/pw-browsers/chromium-*/chrome-linux/headless_shell"]:
        for h in sorted(glob.glob(pat)):
            if os.path.isfile(h) and os.access(h, os.X_OK):
                return h
    return None  # CIではPlaywright標準のChromiumを使う


def active_view(page):
    return page.evaluate(
        "[...document.querySelectorAll('.view')].filter(v => v.classList.contains('active')).map(v => v.id)")


def main():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=BASE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        exe = find_chromium()
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        ctx = browser.new_context(viewport={"width": 390, "height": 844})
        page_errors = []

        def route_firebase(route):
            body = FIREBASE_STUB if "firebase-app-compat" in route.request.url else "/* stub */"
            route.fulfill(status=200, content_type="application/javascript", body=body)

        # ルーティングはコンテキストに設定（後で開く「受け取り側」のページにも効く）
        ctx.route("https://www.gstatic.com/firebasejs/**", route_firebase)
        ctx.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}")
                  and not url.startswith("https://www.gstatic.com/firebasejs"),
                  lambda route: route.abort())
        page = ctx.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))

        # ---- 1. LP表示 ----
        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=30000)
        page.wait_for_timeout(400)
        assert active_view(page) == ["view-home"], f"LPが表示されない: {active_view(page)}"
        print("OK 1/5: LP表示")

        # ---- 2. グループ作成 → 共有URLに#IDがあること ----
        page.click("#view-home .cta-btn")
        page.fill("#s-name", "スモークテスト")
        for name in ["太郎", "次郎", "三郎", "四郎"]:
            page.fill("#member-input", name)
            page.click("#member-add-btn")
        page.click("#setup-submit")
        page.wait_for_selector(".go-game-btn", state="visible", timeout=15000)
        share_url = page.evaluate("document.getElementById('share-url').value")
        assert "#" in share_url, f"共有URLに#がない: {share_url}"
        sid = share_url.split("#")[1]
        assert len(sid) == 10, f"セッションIDが10文字でない: {sid}"
        print(f"OK 2/5: グループ作成・共有URL発行（#{sid}）")

        # ---- 3. 共有URLを別タブで開く（受け取り側のシミュレーション）→ 試合画面が自動で開く ----
        # 同一URLへのgotoはハッシュ移動扱いで再読み込みされないため、必ず新しいページで開くこと
        page = ctx.new_page()
        page.on("pageerror", lambda e: page_errors.append(str(e)))
        page.goto(f"http://127.0.0.1:{PORT}/index.html#{sid}", wait_until="load", timeout=30000)
        page.wait_for_function(
            "() => { const v = document.querySelector('#view-game');"
            " const b = document.querySelector('#score-main-body');"
            " return v && v.classList.contains('active') && b && b.innerText.includes('太郎'); }",
            timeout=15000)
        print("OK 3/5: 共有URLからの自動参加（試合画面表示）")

        # ---- 4. 点数入力（3人分＋残り1人自動入力）→ スコア表示 ----
        page.click(".fab")
        page.wait_for_selector("#si-0", state="visible", timeout=10000)
        for i, val in enumerate(["483", "267", "182"]):
            page.fill(f"#si-{i}", val)
        page.click("#auto-btn")
        page.click("#confirm-btn")
        page.wait_for_function(
            "() => { const c = document.querySelector('#score-main-body .score-card');"
            " return c && c.innerText.includes('太郎') && c.innerText.includes('+'); }",
            timeout=10000)
        print("OK 4/5: 点数入力→総合成績にスコア表示")

        # ---- 5. グラフカードの存在 ----
        assert page.evaluate("!!document.querySelector('#chart-card')"), "スコア推移カードがない"
        print("OK 5/5: スコア推移カードあり")

        assert not page_errors, f"ページ内JSエラー: {page_errors}"
        browser.close()
    server.shutdown()
    print("SMOKE TEST: ALL PASS")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"SMOKE TEST FAILED: {e}", file=sys.stderr)
        sys.exit(1)
