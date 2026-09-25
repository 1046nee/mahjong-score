# -*- coding: utf-8 -*-
"""ログイン・アカウント同期・仲間ページ・共有URLを、スタブのFirebaseで確かめる（本番のDBにもGoogleにも触らない）。

Googleログインは本物のアカウントが要るので通せない。firebase.auth をスタブにして「ログインした」状態を作り、
アプリ側の組み立て（attachAccount・仲間ページの作成/参加/結びつけ）を検証する。
アカウントの切り替えは localStorage の __smoke_user（今のユーザー）と __smoke_next_uid（次にログインするユーザー）で行う。
  [1] 共有URLはLINEの中の画面でそのまま開く形（openExternalBrowserを付けない）
  [2] はじめてのログインで、端末の履歴が users/{uid}/listId のリストに入る
  [3] 保存領域が空の端末でログインすると、過去の試合と「自分」の選択が戻る
  [4] 別の引き継ぎリストを持っていた端末でログインすると、アカウントのリストへまとまる
  [5] 仲間ページ: 作成→試合の追加（名前の自動結びつけ・本人の席）→招待（外のブラウザで開くリンク）
  [6] 2人目が招待リンクから参加→名簿で「これは私」→本人の席は変えられない→作成者が管理者にすると変えられる
  [7] ログインしていない人は、閲覧リンクで結果だけ見られる（招待・設定のボタンは出ない）
  [8] LINEの中で招待リンクを開いたら「Safari・Chromeで開く」と参加コードを出す
  [9] 未ログインで招待リンク→「Googleでログインして参加」→ログインから戻ると自動で参加が完了する
本物のルール（database.rules.json）でどうなるかはここでは分からない（スタブにはルールが無い）。
ルールは tools/circle_rules_test.py で本番のデータベースに対して確かめる。

実行: python tools/account_test.py
"""
import functools
import http.server
import json
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_test import FIREBASE_STUB  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8795
U1, U2, U3 = 'uidTEST0001', 'uidTEST0002', 'uidTEST0003'

AUTH_STUB = """
(() => {
  const KEY = '__smoke_user';
  const cur = () => { try { return JSON.parse(localStorage.getItem(KEY)); } catch (e) { return null; } };
  const AUTH = {
    onAuthStateChanged: cb => { setTimeout(() => cb(cur()), 0); return () => {}; },
    getRedirectResult: () => Promise.resolve(null),
    // 本物はGoogleへ移動して戻ってくる。スタブは「ログインした」ことにして同じURLを読み直す
    signInWithRedirect: () => {
      const uid = localStorage.getItem('__smoke_next_uid') || 'uidTEST0001';
      localStorage.setItem(KEY, JSON.stringify({ uid, displayName: 'テスト' + uid.slice(-1) }));
      location.reload();
      return new Promise(() => {});
    },
    signOut: () => { localStorage.removeItem(KEY); return Promise.resolve(); },
  };
  const f = () => AUTH;
  f.GoogleAuthProvider = function () { this.setCustomParameters = () => {}; };
  window.firebase.auth = f;
  window.__MAJASCO_TEST_LOGIN__ = true; // 本番の LOGIN_ENABLED が false でもログインの画面を出す
})();
"""



# wait_for_function の条件は SAFE % "式" で包む。ログイン・参加は location.reload() を挟むので、
# 読み直し中（HTMLが途中まで・スクリプトがまだ動いていない瞬間）に評価すると ReferenceError や
# null の classList で「待つべき所で落ちる」。例外は false（まだ）として待ち続ける
SAFE = "() => { try { return !!(%s); } catch (e) { return false; } }"

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

        def new_ctx(ua=None, seed_db=None):
            kw = {"viewport": {"width": 390, "height": 844}, "locale": "ja-JP"}
            if ua:
                kw["user_agent"] = ua
            c = br.new_context(**kw)

            def route_fb(route):
                body = FIREBASE_STUB + AUTH_STUB if "firebase-app-compat" in route.request.url else "/* stub */"
                route.fulfill(status=200, content_type="application/javascript", body=body)
            c.route("https://www.gstatic.com/firebasejs/**", route_fb)
            c.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}") and not url.startswith("https://www.gstatic.com/firebasejs"),
                    lambda route: route.abort())
            if seed_db is not None:  # 別の端末（別の保存領域）に、同じデータベースの中身を持たせる
                c.add_init_script("if (!localStorage.getItem('__smoke_db')) localStorage.setItem('__smoke_db', %s);" % json.dumps(json.dumps(seed_db)))
            return c

        ctx = new_ctx()

        def new_page(c=None):
            pg = (c or ctx).new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            return pg

        pg = new_page()
        pg.goto(app, wait_until="load")
        pg.wait_for_timeout(600)

        def make_game(name, members, rounds):
            pg.evaluate("showView('setup')")
            pg.evaluate("(a) => { setupMembers = a[1]; renderMembers(); document.getElementById('s-name').value = a[0]; }", [name, members])
            pg.evaluate("startGame()")
            pg.wait_for_function(SAFE % "document.querySelector('#view-share').classList.contains('active')", timeout=10000)
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

        def db_of(page=None):
            return (page or pg).evaluate("JSON.parse(localStorage.getItem('__smoke_db'))")

        def login_as(page, uid):
            page.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", uid)
            page.evaluate("signInWithGoogle()")
            page.wait_for_load_state("load")
            # ログインは location.reload() を挟む。読み直し中（新しいページのスクリプトがまだ動いていない瞬間）に
            # currentUser を見ると ReferenceError で落ちるので、typeof で「定義されるまで待つ」
            page.wait_for_function(SAFE % "currentUser && !accountBusy", timeout=10000)
            page.wait_for_timeout(400)

        # ---- 1. 共有URL ----
        g1, share1 = make_game("金曜会1", ["むにぃ", "たろう", "じろう", "さぶろう", "しろう"],
                               [([0, 1, 2, 3], ["450", "280", "190"]), ([0, 1, 2, 4], ["150", "320", "290"]),
                                ([1, 2, 3, 4], ["400", "300", "250"])])
        results.append(("[1a] 共有URLはLINEの中でそのまま開く形（openExternalBrowserなし）", True, "openExternalBrowser" not in share1 and "#" in share1))
        pg2 = new_page()
        pg2.goto(share1, wait_until="load")
        pg2.wait_for_function(SAFE % "document.querySelector('#view-game').classList.contains('active')", timeout=10000)
        results.append(("[1b] そのURLでゲーム画面が開く", True, True))
        pg2.close()

        # ---- 2〜4. アカウント同期 ----
        pg.evaluate(f"setTag('{g1}', 'play', 0)")
        results.append(("[2a] 未ログインのヘッダー右上は「ログイン」（使い方ではない）", True,
                        pg.evaluate("(() => { const b = document.getElementById('hdr-acct'); return !!b && b.textContent.trim() === 'ログイン' && b.classList.contains('ready'); })()")))
        pg.evaluate("showView('history')")
        results.append(("[2b] 未ログインでマイページ（過去の試合）を開くと、ログイン画面になる（ブラウザだけの履歴は出さない）", True,
                        pg.evaluate("document.getElementById('view-login').classList.contains('active') && document.getElementById('login-action').innerText.includes('Googleでログイン') && document.getElementById('login-action').innerText.includes('この端末に残っている過去の試合')")))
        results.append(("[2c] 未ログインではトップに過去の試合を並べず、ログインして残す入り口だけ出す", True,
                        pg.evaluate("(showView('home'), document.getElementById('recent-games-list').innerText.includes('ログインすると'))")))
        login_as(pg, U1)
        results.append(("[2d] ログイン後はヘッダーが「マイページ」（ログイン中とわかる）になり、ログイン画面からマイページへ移る", True,
                        pg.evaluate("document.getElementById('hdr-acct').textContent.includes('マイページ') && document.getElementById('hdr-acct').classList.contains('in')")))
        pg.wait_for_function(SAFE % "myListId", timeout=10000)
        db = db_of()
        lid = db.get("users", {}).get(U1, {}).get("listId")
        results.append(("[2e] users/{uid}/listId ができ、端末の履歴がそのリストに入る", True,
                        bool(lid) and g1 in db.get("mylists", {}).get(lid, {}).get("groups", {})))
        pg.evaluate("() => { const keep = ['__smoke_db', '__smoke_user']; Object.keys(localStorage).forEach(k => { if (!keep.includes(k)) localStorage.removeItem(k); }); }")
        pg.reload(wait_until="load")
        pg.wait_for_function(SAFE % "currentUser && !accountBusy && (appState.games || []).length", timeout=10000)
        results.append(("[3] 空の端末でログインすると、過去の試合と「自分」の選択が戻る", True,
                        pg.evaluate(f"appState.games.some(g => g.id === '{g1}') && tagOf('{g1}').me === 0")))
        pg.evaluate("signOutAccount()")
        pg.wait_for_timeout(300)
        results.append(("[3b] ログアウトすると、この端末の過去の試合の控えも消える（次に別の人がログインしても混ざらない）", True,
                        pg.evaluate("(appState.games || []).length === 0 && !myListId && document.getElementById('hdr-acct').textContent.trim() === 'ログイン'")))
        # もう一度ログインすれば、アカウントから戻る
        login_as(pg, U1)
        pg.wait_for_function(SAFE % "(appState.games || []).length", timeout=10000)
        results.append(("[3c] もう一度ログインすれば、過去の試合がアカウントから戻る", True, pg.evaluate(f"appState.games.some(g => g.id === '{g1}')")))
        pg.evaluate("signOutAccount()")
        pg.wait_for_timeout(300)
        g2, _ = make_game("金曜会2", ["むにぃ", "たろう", "じろう", "しろう"], [([0, 1, 2, 3], ["380", "200", "250"])])
        pg.evaluate(f"setTag('{g2}', 'play', 0)")
        pg.evaluate("createMyList(true)")
        pg.wait_for_timeout(500)
        login_as(pg, U1)
        pg.wait_for_timeout(500)
        groups = db_of()["mylists"][lid]["groups"]
        results.append(("[4] 別の引き継ぎリストを持っていた端末でログイン→アカウントのリストへまとまる", True,
                        pg.evaluate("myListId") == lid and g1 in groups and g2 in groups))

        # ---- 5. 仲間ページを作る・試合を追加する ----
        pg.evaluate("showView('history')")
        pg.wait_for_timeout(300)
        results.append(("[5a] 過去の試合に「仲間ページ」欄と「作る」ボタンが出る", True,
                        pg.evaluate("document.getElementById('hist-circles').innerText.includes('仲間ページを作る')")))
        pg.evaluate("openCreateCircle(); document.getElementById('cc-name').value = '金曜会'; document.getElementById('cc-me').value = 'むにぃ';")
        pg.evaluate("runCreateCircle()")
        pg.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=10000)
        cid = pg.evaluate("circleId")
        db = db_of()
        circ = db["circles"][cid]
        me_mid = [m for m, r in circ["roster"].items() if r.get("uid") == U1]
        code = db.get("circleSecrets", {}).get(cid, {}).get("code")
        results.append(("[5b] 作成者として登録され、名簿の自分に✓本人・参加コードができる", True,
                        circ["owner"] == U1 and db["circleMembers"][cid][U1]["role"] == "owner" and len(me_mid) == 1
                        and bool(code) and db["circleInvites"][code] == cid))
        pg.evaluate("openCircleAddGames()")
        pg.evaluate(f"() => {{ document.querySelectorAll('.cadd-pick').forEach(el => {{ el.checked = false; }}); document.getElementById('cadd-text').value = 'たろう 20:15 https://majasco.jp/#{g1}\\nじろう https://majasco.jp/#{g2} です'; }}")
        pg.evaluate("runCircleAddGames()")
        pg.wait_for_function(f"() => circleData && circleData.games && circleData.games['{g1}'] && circleData.games['{g2}']", timeout=15000)
        pg.wait_for_timeout(500)
        circ = db_of()["circles"][cid]
        seats1 = circ["games"][g1]["seats"]
        seat_list = seats1 if isinstance(seats1, list) else [seats1.get(str(i)) for i in range(5)]
        results.append(("[5c] LINEの文章から2試合を取り込み、名前を自動で結びつける（自分の席は✓本人）", True,
                        len(circ["roster"]) == 5 and seat_list[0]["mid"] == me_mid[0] and seat_list[0]["self"] is True
                        and all(s and s["by"] == U1 for s in seat_list)))
        tr = [m for m, r in circ["roster"].items() if r["name"] == "たろう"][0]
        g2seats = circ["games"][g2]["seats"]
        g2list = g2seats if isinstance(g2seats, list) else [g2seats.get(str(i)) for i in range(4)]
        results.append(("[5d] 2試合目の「たろう」は名簿の同じ人に結びつく（重複して増えない）", True, g2list[1]["mid"] == tr))
        tabs = {}
        for t in ["rank", "grid", "h2h", "games", "people"]:
            pg.evaluate(f"circleTab = '{t}'; renderCircle()")
            tabs[t] = pg.evaluate("document.getElementById('circle-body').innerText")
        pg.evaluate("circleTab = 'rank'; renderCircle()")
        results.append(("[5e] タブで通算順位・成績表・対戦成績（総当たり表）・試合・名簿を切り替えて見られる", True,
                        "通算順位" in tabs["rank"] and "むにぃ" in tabs["rank"] and "平均着順" in tabs["grid"] and "トップ率" in tabs["grid"]
                        and "対戦成績" in tabs["h2h"] and "総当たり表" in tabs["h2h"] and "金曜会1" in tabs["games"] and "名簿（5人）" in tabs["people"]))
        pg.evaluate("openCircleMember(Object.keys(circleData.roster).find(m => circleData.roster[m].name === 'たろう'))")
        mt = pg.evaluate("document.getElementById('form-modal-body').innerText")
        pg.evaluate("closeFormModal()")
        results.append(("[5g] メンバーを押すと、その人の成績（タイル・着順の分布・最近の着順）と相手ごとの成績が出る", True,
                        all(w in mt for w in ["たろう", "平均着順", "着順の分布", "最近の着順", "相手ごとの成績"])))
        pg.evaluate("openCircleInvite()")
        results.append(("[5f] 招待リンクは外のブラウザで開く形・参加コードも出る", True,
                        pg.evaluate(f"circleInviteLink === location.origin + '/?openExternalBrowser=1#join={code}' && document.getElementById('form-modal-body').innerText.includes('{code[:4]}-{code[4:]}')")))
        pg.evaluate("closeFormModal()")

        # ---- 6. 2人目が招待リンクから参加 ----
        pg.evaluate(f"(u) => localStorage.setItem('__smoke_user', JSON.stringify({{ uid: u, displayName: 'テスト2' }}))", U2)
        pgb = new_page()
        pgb.goto(app + "?openExternalBrowser=1#join=" + code, wait_until="load")
        try:
            pgb.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleMembers", timeout=15000)
        except Exception:
            print("DEBUG:", pgb.evaluate("({view: document.querySelector('.view.active') && document.querySelector('.view.active').id, joinCid, joinCode, joinBusy, joinError, user: currentUser && currentUser.uid, body: (document.getElementById('join-body')||{}).innerText, circleId, members: circleMembers})"), errors)
            raise
        results.append(("[6a] ログイン済みで招待リンクを開くと、そのまま参加して仲間ページが開く", True,
                        db_of(pgb)["circleMembers"][cid][U2]["role"] == "editor" and pgb.evaluate("location.search === ''")))
        results.append(("[6b] 参加直後は「名簿のどの人ですか？」を聞く", True,
                        "あなたは名簿のどの人ですか" in pgb.evaluate("document.getElementById('circle-body').innerText")))
        pgb.evaluate(f"claimCircleMember('{tr}')")
        pgb.wait_for_timeout(600)
        results.append(("[6c] 「たろう」を本人として登録（名簿に✓本人・結びつけ済みの席は本人の確認に切り替わる）", True,
                        db_of(pgb)["circles"][cid]["roster"][tr].get("uid") == U2))
        pgb.evaluate(f"openBindEditor('{g1}')")
        locked = pgb.evaluate("bindState.rows.map(r => r.locked)")
        results.append(("[6d] 2人目の画面では、作成者が本人として結びつけた「むにぃ」の席は変更できない", True,
                        locked[0] is True and locked[2] is False))
        # 「じろう」の席をゲストに変えてみる（本人でない席は編集メンバーなら変えられる）
        pgb.evaluate("bindState.rows[2].sel = ''; saveBindEditor()")
        pgb.wait_for_timeout(600)
        s1 = db_of(pgb)["circles"][cid]["games"][g1]["seats"]
        seat2 = s1[2] if isinstance(s1, list) else s1.get("2")
        log = list(db_of(pgb)["circles"][cid].get("log", {}).values())
        results.append(("[6e] 本人でない席は変更でき、誰が変えたかが履歴に残る", True,
                        seat2 is None and any(e.get("by") == U2 and e.get("kind") == "bind" for e in log)))
        # 元に戻す
        pgb.evaluate("() => { const e = Object.entries(circleData.log).find(([, v]) => v.kind === 'bind'); undoCircleLog(e[0]); }")
        pgb.wait_for_timeout(700)
        s1 = db_of(pgb)["circles"][cid]["games"][g1]["seats"]
        seat2 = s1[2] if isinstance(s1, list) else s1.get("2")
        results.append(("[6f] 履歴から元に戻せる", True, bool(seat2) and seat2["by"] == U2))
        # 作成者が2人目を管理者にする
        pgb.close()
        pg.evaluate(f"(u) => localStorage.setItem('__smoke_user', JSON.stringify({{ uid: u, displayName: 'テスト1' }}))", U1)
        pg.reload(wait_until="load")
        pg.wait_for_function(SAFE % "currentUser && document.querySelector('#view-circle').classList.contains('active') && circleMembers", timeout=15000)
        pg.evaluate(f"setCircleRole('{U2}', 'admin')")
        pg.wait_for_timeout(500)
        pg.evaluate("closeFormModal()")
        pg.evaluate(f"(u) => localStorage.setItem('__smoke_user', JSON.stringify({{ uid: u, displayName: 'テスト2' }}))", U2)
        pgb = new_page()
        pgb.goto(app + "#c=" + cid, wait_until="load")
        pgb.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleMembers", timeout=15000)
        pgb.evaluate(f"openBindEditor('{g1}')")
        results.append(("[6g] 作成者が管理者にすると、本人が結びつけた席も変更できるようになる", True,
                        pgb.evaluate("circleRole() === 'admin' && bindState.rows[0].locked === false")))
        pgb.close()

        # ---- 7. ログインしていない人が閲覧リンクで見る ----
        pg.evaluate("localStorage.removeItem('__smoke_user')")
        pgv = new_page()
        pgv.goto(app + "#c=" + cid, wait_until="load")
        pgv.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=15000)
        acts = pgv.evaluate("document.getElementById('circle-actions').innerText")
        body = pgv.evaluate("document.getElementById('circle-body').innerText")
        results.append(("[7] ログインなしでも閲覧リンクで通算順位が見られ、招待・設定は出ない", True,
                        "通算順位" in body and "むにぃ" in body and "招待" not in acts and "設定" not in acts))
        pgv.evaluate(f"circleTab = 'games'; renderCircle(); openCircleGameMenu('{g1}')")
        menu_txt = pgv.evaluate("document.getElementById('form-modal-body').innerText")
        pgv.evaluate(f"closeFormModal(); openWatchGame(circleSess['{g1}'], 'circle')")
        results.append(("[7b] 見るだけの人が仲間ページの試合を開くと、入力できない「見るだけ」の画面になる", True,
                        "結果を見る" in menu_txt and "入力・修正" not in menu_txt
                        and pgv.evaluate("document.getElementById('view-watch').classList.contains('active') && !document.querySelector('#view-watch .fab') && document.getElementById('watch-body').innerText.includes('総合順位')")))
        pgv.close()

        # ---- 8. LINEの中で招待リンクを開く ----
        seed = db_of()
        lctx = new_ctx(ua="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Safari Line/15.1.0", seed_db=seed)
        pgl = new_page(lctx)
        pgl.goto(app + "#join=" + code, wait_until="load")
        pgl.wait_for_function(SAFE % "document.querySelector('#view-join').classList.contains('active')", timeout=15000)
        jt = pgl.evaluate("document.getElementById('join-body').innerText")
        results.append(("[8] LINEの中で招待リンクを開くと「Safari・Chromeで開いて参加」と参加コードを出す（結果だけは見られる）", True,
                        "Safari・Chromeで開いて参加する" in jt and f"{code[:4]}-{code[4:]}" in jt and "参加せずに結果だけ見る" in jt))
        lctx.close()

        # ---- 9. 未ログインで招待リンク→ログイン→自動で参加 ----
        pgj = new_page()
        pgj.goto(app + "?openExternalBrowser=1#join=" + code, wait_until="load")
        pgj.wait_for_function(SAFE % "document.querySelector('#view-join').classList.contains('active')", timeout=15000)
        results.append(("[9a] 未ログインでは「Googleでログインして参加」を出す", True,
                        "Googleでログインして参加" in pgj.evaluate("document.getElementById('join-body').innerText")))
        pgj.evaluate(f"(u) => localStorage.setItem('__smoke_next_uid', u)", U3)
        pgj.evaluate("startJoinLogin()")
        pgj.wait_for_load_state("load")
        pgj.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleMembers", timeout=15000)
        results.append(("[9b] ログインから戻ると自動で参加が完了し、仲間ページが開く", True,
                        db_of(pgj)["circleMembers"][cid].get(U3, {}).get("role") == "editor"))

        # ---- 10. マイページ（個人｜仲間） ----
        pg.evaluate("(u) => localStorage.setItem('__smoke_user', JSON.stringify({ uid: u, displayName: 'テスト1' }))", U1)
        pg.reload(wait_until="load")
        pg.wait_for_function(SAFE % "currentUser && !accountBusy", timeout=10000)
        pg.evaluate("showView('history'); setMpTab('me')")
        pg.wait_for_timeout(300)
        me_txt = pg.evaluate("document.getElementById('mp-me').innerText")
        hero = pg.evaluate("document.getElementById('account-card').innerText")
        results.append(("[10a] マイページの上にログイン中のカード、「個人」に成績（タイル・着順の分布）・よく打つ相手・過去の試合が出る", True,
                        "テスト1" in hero and "ログアウト" in hero and all(w in me_txt for w in ["平均着順", "トップ率", "着順の分布", "よく打つ相手", "過去の試合", "金曜会1"])))
        pg.evaluate("setMpTab('circle')")
        pg.wait_for_timeout(300)
        results.append(("[10b] 「仲間」に切り替えると、仲間ページのカードと作るボタンが出る（個人の中身は隠れる）", True,
                        pg.evaluate("document.getElementById('mp-circle').style.display !== 'none' && document.getElementById('mp-me').style.display === 'none' && document.getElementById('hist-circles').innerText.includes('金曜会') && document.getElementById('hist-circles').innerText.includes('仲間ページを作る')")))
        pg.evaluate(f"setMpTab('me'); openTagEditor('{g1}')")
        tag_txt = pg.evaluate("document.getElementById('form-modal-body').innerText")
        pg.evaluate("closeFormModal()")
        results.append(("[10c] 「この試合での自分」に参加/観戦の区別はなく、名前か「自分は出ていない」を選ぶ", True,
                        "観戦" not in tag_txt and "自分は出ていない" in tag_txt and "たろう" in tag_txt))

        # ---- 11. 共有シート・見るだけのリンク ----
        pg.evaluate(f"joinSession('{g1}')")
        pg.wait_for_function(SAFE % "document.querySelector('#view-game').classList.contains('active') && activeGame", timeout=10000)
        pg.evaluate("openShareSheet()")
        pg.wait_for_function(SAFE % "document.getElementById('share-sheet') && document.getElementById('share-sheet').innerText.includes('見るだけのリンクを作る')", timeout=10000)
        sh = pg.evaluate("document.getElementById('share-sheet').innerText")
        results.append(("[11a] 共有シートの一番上は「一緒に打つ人に送る」（入力できるURL）、その下に見るだけのリンク", True,
                        sh.index("一緒に打つ人に送る") < sh.index("見るだけのリンク") and pg.evaluate("document.getElementById('share-sheet-url').value") == share1))
        pg.evaluate("makeViewLink()")
        pg.wait_for_function(f"() => viewIds['{g1}']", timeout=10000)
        vid = pg.evaluate(f"viewIds['{g1}']")
        d = db_of()
        snap = d.get("views", {}).get(vid, {})
        results.append(("[11b] 見るだけのリンクを作ると sessionViews と写しができ、写しに試合IDは入らない", True,
                        d.get("sessionViews", {}).get(g1) == vid and snap.get("s", {}).get("name") == "金曜会1"
                        and g1 not in json.dumps(snap.get("s", {})) and snap.get("p") == f"{g1}_{snap.get('n')}"))
        pg.evaluate("closeFormModal()")
        n_before = len(snap.get("s", {}).get("rounds", []))
        pg.evaluate("""async () => { openSheet(-1); await new Promise(r => setTimeout(r, 100));
          sheetSelected = [0, 1, 2, 3]; renderSheetMembers(); renderSheetInputs();
          ['300', '300', '250'].forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
          await new Promise(r => setTimeout(r, 100)); submitRound(); }""")
        pg.wait_for_function("(a) => { const v = JSON.parse(localStorage.getItem('__smoke_db')).views[a[0]]; return v && (v.s.rounds || []).length === a[1]; }",
                             arg=[vid, n_before + 1], timeout=15000)
        results.append(("[11c] 点数を入れると、見るだけのリンクの写しも自動で更新される", True, True))
        wctx = new_ctx(seed_db=db_of())
        pw = new_page(wctx)
        pw.goto(app + "#v=" + vid, wait_until="load")
        pw.wait_for_function(SAFE % "document.querySelector('#view-watch').classList.contains('active') && document.getElementById('watch-body').innerText.includes('総合順位')", timeout=15000)
        results.append(("[11d] 見るだけのリンクは入力の入口なしで結果が見られ、その端末の試合の一覧には残らない", True,
                        pw.evaluate("(v) => !document.querySelector('#view-watch .fab') && !document.getElementById('watch-body').innerText.includes('行をタップすると点数を修正') && (appState.games || []).length === 0 && location.hash === '#v=' + v && document.getElementById('watch-title').textContent === '金曜会1'", vid)))
        pw.close()
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
