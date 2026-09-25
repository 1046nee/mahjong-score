# -*- coding: utf-8 -*-
"""ログイン・アカウント同期・まとめ・共有URLを、スタブのFirebaseで確かめる（本番のDBにもGoogleにも触らない）。

Googleログインは本物のアカウントが要るので通せない。firebase.auth をスタブにして「ログインした」状態を作り、
アプリ側の同期の組み立て（attachAccount など）を検証する。
  [1] 共有URLに ?openExternalBrowser=1 が付き、それで開いてもゲームが開く（LINEで外のブラウザに出す仕組み）
  [2] はじめてのログインで、端末の履歴が users/{uid}/listId のリストに入り、自分の席が claims に登録される
  [3] 保存領域が空の端末でログインすると、過去の試合と「自分」の選択が戻る（ホーム画面アプリ・機種変更）
  [4] 別の引き継ぎリストを持っていた端末でログインすると、アカウントのリストへまとまる
  [5] まとめ（複数のゲームの通算）を作れる・URLを開けば未ログインの人も同じ結果を見られる
本物のルール（database.rules.json）でどうなるかはここでは分からない。ルールを変えたら本番で確かめること。

実行: python tools/account_test.py
"""
import functools
import http.server
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_test import FIREBASE_STUB  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8795

# firebase.auth のスタブ。signInWithRedirect で「ログインした」ことにして再読み込みする（本物のリダイレクトの代わり）
AUTH_STUB = """
(() => {
  const KEY = '__smoke_user';
  const cur = () => { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } };
  const AUTH = {
    onAuthStateChanged: cb => { setTimeout(() => cb(cur()), 0); return () => {}; },
    getRedirectResult: () => Promise.resolve(null),
    signInWithRedirect: () => { localStorage.setItem(KEY, JSON.stringify({ uid: 'uidTEST0001', displayName: 'テストユーザー' })); location.reload(); return new Promise(() => {}); },
    signOut: () => { localStorage.removeItem(KEY); return Promise.resolve(); },
  };
  const f = () => AUTH;
  f.GoogleAuthProvider = function () { this.setCustomParameters = () => {}; };
  window.firebase.auth = f;
  window.__MAJASCO_TEST_LOGIN__ = true; // 本番の LOGIN_ENABLED が false でもログインの画面を出す
})();
"""


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Quiet, directory=BASE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{PORT}/"
    results, errors = [], []
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, locale="ja-JP")

        def route_fb(route):
            body = FIREBASE_STUB + AUTH_STUB if "firebase-app-compat" in route.request.url else "/* stub */"
            route.fulfill(status=200, content_type="application/javascript", body=body)
        ctx.route("https://www.gstatic.com/firebasejs/**", route_fb)
        ctx.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}") and not url.startswith("https://www.gstatic.com/firebasejs"),
                  lambda route: route.abort())

        def new_page():
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            return pg

        pg = new_page()
        pg.goto(app, wait_until="load")
        pg.wait_for_timeout(600)

        def make_game(name, members, rounds):
            pg.evaluate("showView('setup')")
            pg.evaluate("(a) => { setupMembers = a[1]; renderMembers(); document.getElementById('s-name').value = a[0]; }", [name, members])
            pg.evaluate("startGame()")
            pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=10000)
            share = pg.evaluate("document.getElementById('share-url').value")
            pg.evaluate("showView('game')")
            for sel, pts in rounds:
                pg.evaluate("""async (a) => { openSheet(-1); await new Promise(r => setTimeout(r, 100));
                  sheetSelected = a[0].slice(); renderSheetMembers(); renderSheetInputs();
                  a[1].forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
                  await new Promise(r => setTimeout(r, 100)); submitRound(); await new Promise(r => setTimeout(r, 500)); }""", [sel, pts])
            sid = pg.evaluate("sessionId")
            pg.evaluate("leaveGame()")
            return sid, share

        def stub_db():
            return pg.evaluate("JSON.parse(localStorage.getItem('__smoke_db'))")

        # ---- 1. 共有URL ----
        g1, share1 = make_game("金曜会1", ["むにぃ", "たろう", "じろう", "さぶろう", "しろう"],
                               [([0, 1, 2, 3], ["450", "280", "190"]), ([0, 1, 2, 4], ["150", "320", "290"]),
                                ([1, 2, 3, 4], ["400", "300", "250"])])
        results.append(("[1a] 共有URLに ?openExternalBrowser=1 が付く", True, "/?openExternalBrowser=1#" in share1))
        pg2 = new_page()
        pg2.goto(share1, wait_until="load")
        pg2.wait_for_function("() => document.querySelector('#view-game').classList.contains('active')", timeout=10000)
        results.append(("[1b] そのURLで開くとゲーム画面になり、アドレスから openExternalBrowser が消える", True,
                        pg2.evaluate("location.search === '' && location.hash.length > 5")))
        pg2.close()

        # ---- 2. はじめてのログイン ----
        pg.evaluate(f"setTag('{g1}', 'play', 0)")
        pg.evaluate("showView('history')")
        results.append(("[2a] 未ログインでは「Googleでログイン」のカードが出る", True,
                        pg.evaluate("document.getElementById('account-card').innerText.includes('Googleでログイン')")))
        pg.evaluate("signInWithGoogle()")
        pg.wait_for_load_state("load")
        pg.wait_for_function("() => currentUser && !accountBusy && myListId", timeout=10000)
        pg.wait_for_timeout(500)
        db = stub_db()
        lid = db.get("users", {}).get("uidTEST0001", {}).get("listId")
        results.append(("[2b] users/{uid}/listId ができ、端末の履歴がそのリストに入る", True,
                        bool(lid) and g1 in db.get("mylists", {}).get(lid, {}).get("groups", {})))
        results.append(("[2c] 自分に選んだ席がアカウントで登録される（claims）", True,
                        db.get("claims", {}).get(g1, {}).get("0", {}).get("uid") == "uidTEST0001"))
        pg.evaluate("showView('history')")
        results.append(("[2d] ログイン中の表示になる", True,
                        pg.evaluate("document.getElementById('account-card').innerText.includes('ログイン中')")))

        # ---- 3. 保存領域が空の端末でログイン ----
        pg.evaluate("""() => { const keep = ['__smoke_db', '__smoke_user'];
          Object.keys(localStorage).forEach(k => { if (!keep.includes(k)) localStorage.removeItem(k); }); }""")
        pg.reload(wait_until="load")
        pg.wait_for_function("() => currentUser && !accountBusy && (appState.games || []).length", timeout=10000)
        results.append(("[3a] 空の端末でログインすると過去の試合が戻る", True, pg.evaluate(f"appState.games.some(g => g.id === '{g1}')")))
        results.append(("[3b] 「自分」の選択も戻る", True, pg.evaluate(f"tagOf('{g1}').me === 0")))

        # ---- 4. 別の引き継ぎリストを持っていた端末でログイン ----
        pg.evaluate("signOutAccount()")
        pg.wait_for_timeout(300)
        g2, _ = make_game("金曜会2", ["むにぃ", "たろう", "じろう", "しろう"], [([0, 1, 2, 3], ["380", "200", "250"])])
        pg.evaluate(f"setTag('{g2}', 'play', 0)")
        pg.evaluate("createMyList(true)")
        pg.wait_for_timeout(500)
        other = pg.evaluate("myListId")
        pg.evaluate("signInWithGoogle()")
        pg.wait_for_load_state("load")
        pg.wait_for_function("() => currentUser && !accountBusy", timeout=10000)
        pg.wait_for_timeout(600)
        groups = stub_db()["mylists"][lid]["groups"]
        results.append(("[4a] ログインするとアカウントのリストに乗り換える", True, pg.evaluate("myListId") == lid and other != lid))
        results.append(("[4b] 端末にあった試合もアカウントのリストへまとまる", True, g1 in groups and g2 in groups))

        # ---- 5. まとめ ----
        pg.evaluate("showView('history')")
        pg.wait_for_timeout(300)
        results.append(("[5a] 過去の試合に「まとめ」の欄が出る", True,
                        pg.evaluate("document.getElementById('hist-series').innerText.includes('まとめを作る')")))
        pg.evaluate(f"openSeriesPicker(null); seriesPick.name = '金曜会 2026'; seriesPick.checked = new Set(['{g1}', '{g2}']);")
        pg.evaluate("saveSeriesPicker()")
        pg.wait_for_function("() => document.querySelector('#view-series').classList.contains('active')", timeout=10000)
        pg.wait_for_timeout(300)
        txt = pg.evaluate("document.getElementById('series-body').innerText")
        results.append(("[5b] 通算順位に2ゲーム分の試合数が入る（むにぃ=3試合）", True, "3試合" in txt and "むにぃ" in txt))
        results.append(("[5c] アドレスが #s=ID になる", True, pg.evaluate("location.hash.startsWith('#s=')")))
        sid = pg.evaluate("seriesData.id")
        results.append(("[5d] まとめがアカウントの一覧に入る", True, sid in stub_db()["mylists"][lid].get("series", {})))
        pg.evaluate("() => { Object.keys(localStorage).forEach(k => { if (k !== '__smoke_db') localStorage.removeItem(k); }); }")
        pg.close()
        pg = new_page()  # 同じURLへのgotoはハッシュ移動になり再読み込みされないので、新しいページで開く
        pg.goto(app + "#s=" + sid, wait_until="load")
        pg.wait_for_function("() => document.querySelector('#view-series').classList.contains('active')", timeout=10000)
        results.append(("[5e] まとめのURLを開くと、ログインしていない人も同じ通算順位を見られる", True,
                        "むにぃ" in pg.evaluate("document.getElementById('series-body').innerText")))
        br.close()
    srv.shutdown()

    ok = True
    for label, exp, got in results:
        passed = exp == got
        ok &= passed
        print(("PASS  " if passed else "FAIL  ") + label + ("" if passed else f"（実際 {got!r}）"))
    if errors:
        ok = False
        print("ページのエラー:", errors[:5])
    print("ACCOUNT TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
