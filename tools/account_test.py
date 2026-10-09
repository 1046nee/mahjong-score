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
U1, U2, U3, U4 = 'uidTEST0001', 'uidTEST0002', 'uidTEST0003', 'uidTEST0004'

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
        results.append(("[2c] トップ（LP）の「最近の試合」は2件まで。未ログインはログインして残す案内", True,
                        pg.evaluate("(showView('home'), (() => { const n = document.querySelectorAll('#recent-games-list .rg-row').length; return n >= 1 && n <= 2 && document.getElementById('recent-games-list').innerText.includes('ログインすると'); })())")))
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
                        pg.evaluate("document.getElementById('hist-circles').innerText.includes('作る・参加する')")))
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
        # 仲間ページに入れた試合は、追加から24時間だけ外せる（それを過ぎると確定して外せない）
        lock_g1 = circ["games"][g1].get("lockAt")
        pg.evaluate(f"openCircleGameMenu('{g1}')")
        menu_open = pg.evaluate("document.getElementById('form-modal-body').innerText")
        pg.evaluate(f"closeFormModal(); circleData.games['{g1}'].lockAt = serverNow() - 1000; openCircleGameMenu('{g1}')")
        menu_fixed = pg.evaluate("document.getElementById('form-modal-body').innerText")
        pg.evaluate(f"closeFormModal(); circleData.games['{g1}'].lockAt = {lock_g1 or 0}")
        results.append(("[5c2] 仲間ページに入れた試合は追加から24時間だけ外せる（メニューに期限）、過ぎたら確定して外す入口が出ない", True,
                        isinstance(lock_g1, (int, float)) and 23.5 * 3600000 < lock_g1 - pg.evaluate("serverNow()") < 24.5 * 3600000
                        and "この仲間ページから外す" in menu_open and "外せるのは" in menu_open
                        and "この仲間ページから外す" not in menu_fixed and "外せません" in menu_fixed))
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
        results.append(("[5g] メンバーを押すと、その人の成績（平均着順・通算スコア・トップ率・ラス回避・直近のスコアの推移）と対戦成績のカードが出る", True,
                        all(w in mt for w in ["たろう", "平均着順", "通算スコア", "ラス回避", "スコアの推移", "対戦成績", "直接対決の合計"])))
        # 仲間ページに入れたあとで、試合にメンバーを足して入力した → そのメンバーも結びつけられる
        pg.evaluate(f"""async () => {{ const r = (await db.ref('sessions/{g1}').once('value')).val();
          r.settings.playerNames.push('ろくろう'); r.rounds.push({{ members: [0, 1, 2, 5], points: [40000, 30000, 20000, 10000], scores: [50, 10, -20, -40], at: new Date().toISOString() }});
          await db.ref('sessions/{g1}').set(r); }}""")
        pg.evaluate(f"openBindEditor('{g1}')")
        added_rows = pg.evaluate("bindState.rows.map(r => r.name)")
        pg.evaluate("closeFormModal()")
        results.append(("[5h] 仲間ページに入れたあとで試合に足したメンバーも、結びつけの画面に出る", True, "ろくろう" in added_rows))
        pg.evaluate("circleTab = 'games'; circleGamesView = 'cal'; renderCircle()")
        cal0 = pg.evaluate("(() => { const on = document.querySelector('#circle-body .cal-mode .on'); const cur = document.querySelector('#circle-body .cal-year .cal-m.today'); const seg = [...document.querySelectorAll('#circle-body .hist-viewseg .seg button')].map(b => b.textContent).join('|'); return (on ? on.textContent : '') + '/' + (cur ? cur.textContent : '') + '/' + seg; })()")
        pg.evaluate("calS.circle.mode = 'month'; renderCircle()")
        cal = pg.evaluate("document.getElementById('circle-body').innerText")
        pg.evaluate("circleGamesView = 'list'; circleTab = 'rank'; renderCircle()")
        results.append(("[5i] 試合タブのカレンダーは最初は年一覧（今年に枠）、見せ方は「タイル｜一覧｜カレンダー」。月にすると年月・曜日", True,
                        cal0.startswith("年一覧/" + str(__import__('datetime').date.today().year) + "年") and cal0.endswith("タイル|一覧|カレンダー")
                        and "年" in cal and "月" in cal and "日" in cal and "土" in cal))
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
        # 2人目の端末ではまだその試合を持っていない状態にする（テストのブラウザは1人目と保存領域を共有しているため）
        pgb.evaluate(f"() => {{ ['{g1}', '{g2}'].forEach(id => {{ delete gameTags[id]; }}); saveTags(); appState.games = appState.games.filter(g => g.id !== '{g1}' && g.id !== '{g2}'); saveStorage(); }}")
        pgb.evaluate(f"claimCircleMember('{tr}')")
        pgb.wait_for_timeout(600)
        results.append(("[6c] 「たろう」を本人として登録（名簿に✓本人・結びつけ済みの席は本人の確認に切り替わる）", True,
                        db_of(pgb)["circles"][cid]["roster"][tr].get("uid") == U2))
        pgb.evaluate(f"openVerifyInfo('{tr}')")
        vf = pgb.evaluate("document.getElementById('form-modal-body').innerText")
        pgb.evaluate("closeFormModal()")
        results.append(("[6c2] 確認済みにしたGoogleアカウントの表示名が名簿に残り、「確認済み」を押すと見られる（メールアドレスは残さない）", True,
                        db_of(pgb)["circles"][cid]["roster"][tr].get("gname") == "テスト2" and "テスト2" in vf and "たろう" in vf
                        and "email" not in str(db_of(pgb)["circles"][cid]["roster"][tr])))
        pgb.wait_for_function(f"() => (appState.games || []).some(g => g.id === '{g1}') && (appState.games || []).some(g => g.id === '{g2}')", timeout=15000)
        results.append(("[6j] 仲間ページで自分（たろう）を選ぶと、その試合が自分の過去の試合に入り、たろうの席が「自分」になる（個人の成績に入る）", True,
                        pgb.evaluate(f"tagOf('{g1}').me === 1 && tagOf('{g2}').me === 1 && collectMyStats(null).groups.length >= 2")))
        # 1人目（むにぃ）の選択に戻しておく（保存領域を共有しているため、あとの確認に影響しないように）
        pgb.evaluate(f"setTag('{g1}', 'play', 0); setTag('{g2}', 'play', 0)")
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
        try:
            pg.wait_for_function(SAFE % "currentUser && document.querySelector('#view-circle').classList.contains('active') && circleMembers", timeout=15000)
        except Exception:
            print("DEBUG6g:", pg.evaluate("({view: (document.querySelector('.view.active')||{}).id, hash: location.hash, cid: typeof circleId !== 'undefined' && circleId, m: typeof circleMembers !== 'undefined' && circleMembers, u: currentUser && currentUser.uid})"), errors[-5:])
            raise
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
        pgb.evaluate("closeFormModal()")
        mu = [m for m, r in db_of(pgb)["circles"][cid]["roster"].items() if r.get("uid") == U1][0]
        pgb.evaluate(f"openVerifyInfo('{mu}')")
        results.append(("[6g2] 管理者は、ほかの人の確認済みを外す入口が見られる", True,
                        "この人の確認済みを外す" in pgb.evaluate("document.getElementById('form-modal-body').innerText")))
        pgb.evaluate("closeFormModal()")
        # 仲間ページに入れたあとで、名簿にいる人を試合に足した → 仲間ページを開いたときに自動で連携される
        add_nm = pgb.evaluate(f"""(() => {{ const names = circleSess['{g2}'].settings.playerNames.map(personKey);
          const e = Object.entries(circleData.roster).find(([m, r]) => !names.includes(personKey(r.name))); return e ? e[1].name : null; }})()""")
        if add_nm:
            pgb.evaluate(f"""async () => {{ const r = (await db.ref('sessions/{g2}').once('value')).val();
              r.settings.playerNames.push('{add_nm}'); const k = r.settings.playerNames.length - 1;
              r.rounds.push({{ members: [0, 1, 2, k], points: [40000, 30000, 20000, 10000], scores: [50, 10, -20, -40], at: new Date().toISOString() }});
              await db.ref('sessions/{g2}').set(r); }}""")
            pgb.evaluate(f"openCircle('{cid}')")
            pgb.wait_for_timeout(1500)
            seats = db_of(pgb)["circles"][cid]["games"][g2]["seats"]
            k = pgb.evaluate(f"circleSess['{g2}'].settings.playerNames.length - 1")
            sk = seats[k] if isinstance(seats, list) and len(seats) > k else (seats.get(str(k)) if isinstance(seats, dict) else None)
            results.append(("[6n] 仲間ページに入れたあとで足した人（名簿にいる名前）は、仲間ページを開くと自動で連携される", True,
                            bool(sk) and db_of(pgb)["circles"][cid]["roster"][sk["mid"]]["name"] == add_nm))
        else:
            results.append(("[6n] 仲間ページに入れたあとで足した人（名簿にいる名前）は、仲間ページを開くと自動で連携される", True, False))
        # 対戦を見る（仲間ページ・2026-10-07 目線・同卓の代わり）: 選んだ人が全員同じ卓にいた試合で、勝ち越しといっしょに打った試合
        cw = pgb.evaluate("""(async () => {
          const top = document.getElementById('circle-top').innerText;
          const ji = Object.keys(circleData.roster).find(m => circleData.roster[m].name === 'じろう');
          const sa = Object.keys(circleData.roster).find(m => circleData.roster[m].name === 'さぶろう');
          openCircleMatchup([myCircleMid(), ji]);
          const two = document.getElementById('form-modal-body');
          const vs = !!two.querySelector('.mu-vs'), tbl = !!two.querySelector('.grid-cmp');
          // いっしょに打ったゲームは タイル（既定）｜一覧｜カレンダー（過去の試合と同じ・2026-10-08）
          const tiles = mupGamesView === 'tile' && two.querySelectorAll('.ht-grid .ht').length;
          mupGamesView = 'list'; renderMatchup();
          const games = two.querySelectorAll('.yr-sec .mo-sec .gm-list .gr').length && tiles;
          mupGamesView = 'cal'; renderMatchup();
          const cal = !!two.querySelector('.cal-mode');
          mupGamesView = 'tile'; renderMatchup();
          mupToggle(sa); // 3人目は足せない（2人まで・2026-10-08）
          const rows = mup.P.length === 2 && !document.querySelector('#form-modal-body .mu-row') && !document.querySelector('#form-modal-body .mu-cand');
          // 自分以外の2人だけでも見られる（自分を外してから足す）
          mupToggle(myCircleMid()); mupToggle(sa);
          const others = document.querySelectorAll('#form-modal-body .mu-vs').length;
          document.querySelector('#form-modal-body .ht-grid .ht').click();
          await new Promise(r => setTimeout(r, 50)); // ヘッダーの「‹ 戻る」は中身が入れ替わったあとに付く
          const back = document.querySelector('#form-modal-back .fm-back');
          const backTxt = back ? back.title : '';
          if (back) back.click();
          const again = !!document.querySelector('#form-modal-body .mu-sheet');
          closeFormModal();
          return { pill: !top.includes('対戦を見る') && !top.includes('目線') && !top.includes('同卓'), vs, games: games > 0, cal, tbl, rows, others: others === 1, back: backTxt.includes('対戦に戻る'), again };
        })()""")
        results.append(("[6o] 仲間ページの「対戦を見る」: 2人なら勝ち越し・いっしょに打った試合、選べるのは2人まで（3人目は足せない）、自分以外どうしも可。2人は成績表と同じ表でくらべる。いっしょに打ったゲームは過去の試合と同じタイル｜一覧｜カレンダーで、タイルから×の左の「‹ 戻る」で対戦に戻る（成績カードの上に目線・同卓・対戦を見るのピルは無い）", True, all(cw.values())))
        # 仲間ページの「直近n戦」は各自の直近n戦（一人ひとりが出た新しい方からn試合。誰が見ても同じ順位）
        pn = pgb.evaluate("""(() => {
          const prev = curPeriod();
          setMpPeriod('n100');
          const pill = document.querySelector('#circle-top .mp-period').innerText;
          const note = document.getElementById('circle-body').innerText;
          const opts = [...document.querySelectorAll('#circle-top .mp-period option')].map(o => o.textContent).join(' ');
          const per = circleStatsP(circleMode), all = circleStats(circleData, circleSess, circleMode, null);
          // 1試合だけにすると、全員が自分の直近1試合だけで数えられる
          const one = circleStats(circleData, circleSess, circleMode, null, 1);
          setMpPeriod(prev);
          return { pill: pill.includes('各自の直近100戦'), note: note.includes('一人ひとりが出た'), opts: opts.includes('各自の直近1000戦'),
            same: JSON.stringify(per.list.map(p => [p.key, p.n])) === JSON.stringify(all.list.map(p => [p.key, p.n])), one: one.list.length > 0 && one.list.every(p => p.n === 1) };
        })()""")
        results.append(("[6p] 仲間ページの「直近n戦」は各自の直近n戦（期間のボタン・カードの注記・選択肢に「各自の」。一人ひとりの試合数で数える）", True, all(pn.values())))
        # 同じ試合を別のアカウントからもう一度追加しても二重にならず、誰が追加したかがわかる
        pgb.evaluate("closeFormModal()")
        dup = pgb.evaluate(f"addGameToCircle(circleId, circleSess['{g1}'], true)")
        n_games = len(db_of(pgb)["circles"][cid]["games"])
        results.append(("[6h] 同じ試合を別のアカウントから追加しても二重にならず「○○さんが追加済み」と返る", True,
                        bool(dup.get("already")) and dup.get("by") == "むにぃ" and n_games == 2 and db_of(pgb)["circles"][cid]["games"][g1]["addedBy"] == U1))
        pgb.evaluate(f"joinSession('{g1}')")
        pgb.wait_for_function("() => document.getElementById('game-circles').innerText.includes('追加済み')", timeout=10000)
        gc = pgb.evaluate("document.getElementById('game-circles').innerText")
        results.append(("[6i] 仲間ページに入っている試合は、ほかのメンバーの試合の画面にも「金曜会 に追加済み（むにぃさん）」と出る", True,
                        "金曜会" in gc and "むにぃさん" in gc))
        pgb.close()

        # ---- 6k. 参加していない人（見るだけのリンク）も、ログインすれば名簿で自分を選べる。仲間ページの試合には確定の期限が付く ----
        pg.evaluate(f"(u) => localStorage.setItem('__smoke_user', JSON.stringify({{ uid: u, displayName: 'テスト4' }}))", U4)
        pgk = new_page()
        pgk.goto(app + "#c=" + cid, wait_until="load")
        pgk.wait_for_function(SAFE % "currentUser && document.querySelector('#view-circle').classList.contains('active') && circleData && circleStore[circleId]", timeout=15000)
        pgk.wait_for_timeout(500)
        kb = pgk.evaluate("document.getElementById('circle-body').innerText")
        jr = [m for m, r in db_of(pgk)["circles"][cid]["roster"].items() if r["name"] == "じろう"][0]
        results.append(("[6k] 参加していない人にも「名簿のどの人ですか？」が出る（名簿にない名前を足す入口は出ない）", True,
                        "あなたは名簿のどの人ですか" in kb and "名簿にいない" not in kb and pgk.evaluate("circleRole() === null")))
        pgk.evaluate(f"claimCircleMember('{jr}')")
        pgk.wait_for_timeout(700)
        d = db_of(pgk)
        klog = list(d["circles"][cid].get("log", {}).values())
        results.append(("[6l] 参加していない人が「じろう」を自分にすると確認済みになり、メンバー（編集できる人）にはならない", True,
                        d["circles"][cid]["roster"][jr].get("uid") == U4 and U4 not in d["circleMembers"][cid]
                        and any(e.get("by") == U4 and e.get("kind") == "claim" for e in klog)))
        results.append(("[6m] 仲間ページの試合には記録の確定の期限（最後の入力から24時間）が付く", True,
                        all(isinstance(d["sessions"][x].get("lockAt"), (int, float)) for x in [g1, g2])))
        # あとの確認に影響しないように、じろうの本人登録を外す
        pgk.evaluate(f"db.ref('circles/{cid}/roster/{jr}/uid').remove()")
        pgk.wait_for_timeout(300)
        pgk.close()

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
        pgl.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=15000)
        cb = pgl.evaluate("document.getElementById('circle-body').innerText")
        pgl.evaluate("startCircleJoin()")
        pgl.wait_for_function(SAFE % "document.querySelector('#view-join').classList.contains('active')", timeout=15000)
        jt = pgl.evaluate("document.getElementById('join-body').innerText")
        results.append(("[8] LINEの中で仲間のリンクを開くと結果が見られ、「ログインして参加」を押すと「Safari・Chromeで開いて参加」と参加コードを出す", True,
                        "通算順位" in cb and "Googleでログインして参加" in cb and "Safari・Chromeで開いて参加する" in jt and f"{code[:4]}-{code[4:]}" in jt))
        lctx.close()

        # ---- 9. 未ログインで招待リンク→ログイン→自動で参加 ----
        pgj = new_page()
        pgj.goto(app + "?openExternalBrowser=1#join=" + code, wait_until="load")
        pgj.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=15000)
        cbj = pgj.evaluate("document.getElementById('circle-body').innerText")
        results.append(("[9a] 未ログインで仲間のリンクを開くと、結果（通算順位）がそのまま見られ、「Googleでログインして参加」も出る", True,
                        "通算順位" in cbj and "Googleでログインして参加" in cbj))
        pgj.evaluate(f"(u) => localStorage.setItem('__smoke_next_uid', u)", U3)
        pgj.evaluate("startCircleJoin()")
        pgj.wait_for_load_state("load")
        pgj.wait_for_function(SAFE % "document.querySelector('#view-circle').classList.contains('active') && circleMembers", timeout=15000)
        results.append(("[9b] ログインから戻ると自動で参加が完了し、仲間ページが開く", True,
                        db_of(pgj)["circleMembers"][cid].get(U3, {}).get("role") == "editor"))

        # ---- 10. マイページ（成績が最初・四麻/三麻は別カード・期間・自分をその場で選ぶ・まとめて送る/取り込む・対局日） ----
        pg.evaluate("(u) => localStorage.setItem('__smoke_user', JSON.stringify({ uid: u, displayName: 'テスト1' }))", U1)
        pg.reload(wait_until="load")
        pg.wait_for_function(SAFE % "currentUser && !accountBusy", timeout=10000)
        g3, _ = make_game("金曜会3", ["むにぃ", "たろう", "じろう", "しろう"], [([0, 1, 2, 3], ["420", "300", "200"])])
        pg.evaluate("showView('history')")
        pg.wait_for_timeout(300)
        top = pg.evaluate("document.getElementById('mp-me').firstElementChild.innerText")
        # 名前とアイコンの帯はやめた（2026-10-08）。名前とログアウトはヘッダー右上のマイページを押したメニューに
        bar = pg.evaluate("(() => { hdrAcctClick(); const t = document.getElementById('form-modal-body').innerText; closeFormModal(); return t.includes('ログアウト') && document.getElementById('account-card').style.display === 'none' && document.getElementById('mp-head').innerText.includes('個人') ? t : ''; })()")
        results.append(("[10a] マイページのいちばん上は自分の成績（四麻のカード：平均着順・通算スコア・トップ率・ラス回避・直近のスコアの推移）", True,
                        "テスト1" in bar and all(w in top for w in ["四麻", "平均着順", "通算スコア", "トップ率", "ラス回避", "スコアの推移"])))
        tabs = pg.evaluate("document.getElementById('mp-pane-tabs').innerText")
        stats_txt = pg.evaluate("document.getElementById('mp-stats').innerText")
        shown = pg.evaluate("document.getElementById('mp-pane-hist').style.display === 'none' && document.getElementById('mp-pane-sum').innerText.includes('成績表')")
        results.append(("[10a2] 成績カードのすぐ下に素点・順位点・最高/最低点数などの欄、その下に［成績表｜対戦成績｜過去の試合］（最初は成績表）。ホーム画面に追加の案内は無い", True,
                        all(w in stats_txt for w in ["素点", "順位点", "最高点数", "最低点数", "箱下"]) and tabs.replace(chr(10), '').replace(' ', '').startswith('成績表対戦成績過去の試合') and shown
                        and "ホーム画面に追加" not in pg.evaluate("document.getElementById('mp-me').innerText")))
        # 過去の試合の行を押すと、画面を移らずに結果のシート（総合順位・試合ごとのスコア）。閉じればマイページのまま
        pg.evaluate("window.scrollTo(0, 300)")
        y0 = pg.evaluate("window.scrollY")
        pg.evaluate("appState.games.forEach(g => { g._lk = g.lockAt; g.lockAt = Date.now() - 1000; })")  # 記録が確定した試合は「詳しく見る」（確定前は「ゲームを見る」＝試合の画面。2026-10-09）
        pg.evaluate("histView = 'new'; renderHistoryList()")  # 既定はタイル（2026-10-07）。ここからは一覧の行を押して確かめる
        pg.evaluate("document.querySelector('#history-body .gr').click()")
        sheet = pg.evaluate("document.getElementById('form-modal').classList.contains('open') ? document.getElementById('form-modal-body').innerText : ''")
        pg.evaluate("closeFormModal()")
        results.append(("[10a6] 過去の試合を押すと、その場で結果のシート（総合順位・試合ごとのスコア・詳しく見る）が開き、閉じてもマイページの同じ位置のまま", True,
                        all(w in sheet for w in ["試合ごとのスコア", "詳しく見る"]) and pg.evaluate("document.getElementById('view-history').classList.contains('active')") and pg.evaluate("window.scrollY") == y0))
        # 詳しく見る → 戻る で、マイページの元の位置へ
        pg.evaluate("document.querySelector('#history-body .gr').click()")
        pg.evaluate("[...document.querySelectorAll('#form-modal-body .menu-btn')].find(b => b.innerText.includes('詳しく見る')).click()")
        pg.wait_for_timeout(200)
        in_detail = pg.evaluate("document.getElementById('view-detail').classList.contains('active')")
        pg.evaluate("document.getElementById('header-back').click()")
        pg.wait_for_timeout(300)
        results.append(("[10a7] 結果のシートの「詳しく見る」→ 戻るで、マイページの見ていた位置に戻る（ホームに戻らない）", True,
                        in_detail and pg.evaluate("document.getElementById('view-history').classList.contains('active')") and abs(pg.evaluate("window.scrollY") - y0) < 4))
        pg.evaluate("appState.games.forEach(g => { g.lockAt = g._lk; delete g._lk; if (g.lockAt == null) delete g.lockAt; })")  # 確定前に戻す（「ゲームを見る」で試合の画面へ）
        # 試合の画面 → 戻るでも、ホームではなくマイページの元の位置へ
        # 結果のシートには点数の入力の入口を置かない（2026-10-09）。試合の画面は一覧の「…」の「ゲームを見る」から
        pg.evaluate("document.querySelector('#history-body .gr').click()")
        pg.evaluate("(() => { const id = rsState.id; closeFormModal(); openHistMenu(id); })()")
        pg.evaluate("[...document.querySelectorAll('#form-modal-body .menu-btn')].find(b => /ゲームを見る/.test(b.innerText)).click()")
        pg.wait_for_function("() => document.getElementById('view-game').classList.contains('active') && activeGame", timeout=10000)
        pg.evaluate("document.getElementById('header-back').click()")
        pg.wait_for_timeout(300)
        results.append(("[10a8] 過去の試合の「…」から試合の画面を開いて戻ると、ホームではなくマイページの見ていた位置に戻る", True,
                        pg.evaluate("document.getElementById('view-history').classList.contains('active') && !activeGame") and abs(pg.evaluate("window.scrollY") - y0) < 4))
        # 端末（ブラウザ）の「戻る」でも同じ
        # 結果のシートには点数の入力の入口を置かない（2026-10-09）。試合の画面は一覧の「…」の「ゲームを見る」から
        pg.evaluate("document.querySelector('#history-body .gr').click()")
        pg.evaluate("(() => { const id = rsState.id; closeFormModal(); openHistMenu(id); })()")
        pg.evaluate("[...document.querySelectorAll('#form-modal-body .menu-btn')].find(b => /ゲームを見る/.test(b.innerText)).click()")
        pg.wait_for_function("() => document.getElementById('view-game').classList.contains('active') && activeGame", timeout=10000)
        pg.go_back()
        pg.wait_for_timeout(400)
        results.append(("[10a9] 試合の画面で端末の「戻る」を押しても、マイページの見ていた位置に戻る（試合の画面の後始末もする）", True,
                        pg.evaluate("document.getElementById('view-history').classList.contains('active') && !activeGame && !sessionRef") and abs(pg.evaluate("window.scrollY") - y0) < 4))
        pg.evaluate("appState.games.forEach(g => { g._lk = g.lockAt; g.lockAt = Date.now() - 1000; })")  # 記録が確定した試合は「詳しく見る」（確定前は「ゲームを見る」＝試合の画面。2026-10-09）
        # 推移の点のカード → 試合 → 結果の画面 → 詳しく見る → 戻る で、カードと結果の画面まで開き直す
        pg.evaluate("window.scrollTo(0, 0); document.querySelector('#mp-stats .sp-hit').dispatchEvent(new MouseEvent('click', { bubbles: true }))")
        pg.evaluate("document.querySelector('#mp-stats .sp-g').click()")
        pg.evaluate("[...document.querySelectorAll('#form-modal-body .menu-btn')].find(b => b.innerText.includes('詳しく見る')).click()")
        pg.wait_for_timeout(200)
        pg.evaluate("document.getElementById('header-back').click()")
        pg.wait_for_timeout(400)
        back_ok = pg.evaluate("document.getElementById('view-history').classList.contains('active') && !document.querySelector('#mp-stats .sp-pop').hidden && document.getElementById('form-modal').classList.contains('open') && document.getElementById('form-modal-body').innerText.includes('試合ごとのスコア')")
        pg.evaluate("closeFormModal()")
        results.append(("[10a10] グラフのカードから開いた試合の詳しい画面から戻ると、グラフのカードと結果の画面まで開き直す", True, back_ok))
        pg.evaluate("setMpPane('hist')")
        # ほかの人があとから試合の名前・対局日を変えた → マイページを開き直すと、過去の試合の控えも最新になる（開き直さなくても）
        pg.evaluate(f"""async () => {{ await db.ref('sessions/{g2}/name').set('名前を変えた試合'); await db.ref('sessions/{g2}/settings/playDate').set('2026-08-15'); }}""")
        pg.evaluate("refreshHistoryGames(true)")
        pg.wait_for_function(f"() => (appState.games.find(g => g.id === '{g2}') || {{}}).name === '名前を変えた試合'", timeout=10000)
        results.append(("[10a3] あとから変えた試合の名前・対局日が、開き直さなくても過去の試合に反映される", True,
                        pg.evaluate(f"(() => {{ const g = appState.games.find(g => g.id === '{g2}'); return g.settings.playDate === '2026-08-15' && new Date(gameDayMs(g)).getMonth() === 7; }})()")))
        # 「出ていない」にしたあとでメンバーが足された → もう一度「あなたはどれ？」を聞く
        again = pg.evaluate(f"""(() => {{ setTag('{g3}', 'watch', null); const g = appState.games.find(x => x.id === '{g3}');
          const before = histState(g); g.settings.playerNames = g.settings.playerNames.concat(['あとから']); const after = histState(g);
          g.settings.playerNames = g.settings.playerNames.slice(0, -1); setTag('{g3}', 'play', null); return [before, after]; }})()""")
        results.append(("[10a4] 「出ていない」にしたあとで人が足された試合は、もう一度「あなたはどれ？」を聞く", True, again == ["out", "ask"]))
        # 期間: すべて／年／直近の期間／直近の試合数／開始・終了を指定（区切り付き）
        pr = pg.evaluate("""(() => {
          const html = mpPeriodHtml();
          const nAll = collectMyStats(periodFilter('all')).groups.length;
          const n1m = collectMyStats(periodFilter('r1m')).groups.length;
          const c100 = periodFilter('n100');  // 100戦に満たなければ全部（null）
          const old = collectMyStats(periodFilter('c20200101_20200131')).groups.length;
          setMpPeriod('c20200101_'); const lab = periodLabel(); setMpPeriod('all');
          return { groups: ['年', '直近の期間', '直近の試合数', '期間を指定'].every(l => html.includes('label="' + l + '"')),
            opts: ['直近1か月', '直近半年', '直近1000戦', '開始・終了を指定'].every(l => html.includes(l)), nAll, n1m, c100: c100 === null, old, lab };
        })()""")
        results.append(("[10p] 期間に「年」「直近の期間」「直近の試合数」「期間を指定」の区切りがあり、それぞれで数えられる", True,
                        pr["groups"] and pr["opts"] and pr["nAll"] > 0 and 1 <= pr["n1m"] < pr["nAll"] and pr["c100"] and pr["old"] == 0 and pr["lab"] == "2020/1/1〜"))
        # 過去の試合の各行に、仲間ページへの追加と連携の状態が出る
        pg.evaluate("circleStore && prefetchCircles()")
        pg.wait_for_timeout(1500)
        pg.evaluate("renderHistoryList()")
        hl = pg.evaluate("document.getElementById('history-body').innerText")
        results.append(("[10a5] 過去の試合の行に、仲間ページの連携の状態（全員連携済み／未連携 n人）が出る", True,
                        "金曜会" in hl and ("未連携" in hl or "全員連携済み" in hl)))
        me_txt = pg.evaluate("document.getElementById('mp-me').innerText")
        sw = pg.evaluate("document.getElementById('hist-circles').innerText")
        results.append(("[10b] 上に「個人｜仲間ページ」の切り替え、「過去の試合」のタブに「追加」「送る」（見せ方と同じ1行）・形式のピル・並び順、自分が出た試合（月の見出し）", True,
                        all(w in me_txt for w in ["追加", "送る", "すべて", "一覧", "カレンダー", "タイル", "年", "月", "金曜会1"]) and all(w in sw for w in ["個人", "金曜会", "作る・参加する"])))
        pg.evaluate("histOthersOpen = true; renderHistoryList()")
        row3 = pg.evaluate(f"(() => {{ const r = [...document.querySelectorAll('#history-body .gr')].find(x => x.innerText.includes('金曜会3')); return r ? r.className + '|' + r.innerText : ''; }})()")
        results.append(("[10c] 自分を選んでいない試合は「その他の試合」にたたまれ、その行で名前（いつもの名前）か「出ていない」を選べる", True,
                        " ask" in row3 and pg.evaluate("!!document.querySelector('#history-body details.mp-others .gr.ask')") and "いつもの名前" in row3 and "出ていない" in row3))
        pg.evaluate(f"quickTag('{g3}', 0)")
        results.append(("[10d] 名前を1回押すと自分に決まり、行が「自分の順位・スコア」の形に変わる", True,
                        pg.evaluate(f"tagOf('{g3}').me === 0 && [...document.querySelectorAll('#history-body .gr.me')].some(x => x.innerText.includes('金曜会3') && x.innerText.includes('位'))")))
        pg.evaluate(f"openTagEditor('{g1}')")
        tag_txt = pg.evaluate("document.getElementById('form-modal-body').innerText")
        pg.evaluate("closeFormModal()")
        results.append(("[10e] 「この試合での自分」に参加/観戦の区別はなく、名前か「自分は出ていない」を選ぶ", True,
                        "観戦" not in tag_txt and "自分は出ていない" in tag_txt and "たろう" in tag_txt))
        pg.evaluate(f"startSelectSend(); toggleMpSel('{g1}'); toggleMpSel('{g3}')")
        text = pg.evaluate("bundleText()")
        bar_txt = pg.evaluate("document.getElementById('mp-sendbar').innerText")
        results.append(("[10f] 「まとめて送る」で選んだ試合の名前とURLが1つの文になる", True,
                        "2件を選択中" in bar_txt and f"#{g1}" in text and f"#{g3}" in text and "試合を追加" in text))
        pg.evaluate("endSelectSend()")
        # 受け取った人の側: 一覧から消してから、送られた文を「試合を追加」に貼る（アプリが拾うのは majasco.jp のURL）
        pg.evaluate(f"deleteHistoryItem('{g3}'); delete gameTags['{g3}']; saveTags()")
        pg.evaluate("openAddGames()")
        pg.evaluate("(t) => { document.getElementById('ag-text').value = t; }", text.replace(app.rstrip("/"), "https://majasco.jp"))
        pg.evaluate("runAddGames()")
        pg.wait_for_function(f"() => (appState.games || []).some(g => g.id === '{g3}')", timeout=10000)
        results.append(("[10g] 送られた文を「試合を追加」に貼ると取り込まれ、いつもの名前が自分に自動で決まる", True,
                        pg.evaluate(f"tagOf('{g3}').me === 0")))
        # 過去の試合をあとから入力: 対局日を選んで作る → その年の期間で絞れる
        pg.evaluate("showView('setup')")
        pg.evaluate("() => { setupMembers = ['むにぃ', 'たろう', 'じろう', 'しろう']; renderMembers(); document.getElementById('s-date').value = '2025-05-10'; onSetupDateChange(); }")
        nm = pg.evaluate("document.getElementById('s-name').value")
        pg.evaluate("startGame()")
        pg.wait_for_function(SAFE % "document.querySelector('#view-share').classList.contains('active')", timeout=10000)
        g4 = pg.evaluate("sessionId")
        pg.evaluate("showView('game')")
        results.append(("[10h] 対局日を過去にして作れる（ゲーム名もその日付に合わせ、画面に「対局日」が出る）", True,
                        db_of()["sessions"][g4]["settings"].get("playDate") == "2025-05-10" and nm.startswith("2025.05.10")
                        and "対局日 2025/5/10" in pg.evaluate("document.getElementById('game-date').textContent")))
        pg.evaluate("leaveGame()")
        pg.evaluate("showView('history')")
        pills = pg.evaluate("(() => { const sel = document.querySelector('#mp-stats .mp-period select'); return sel ? [...sel.options].map(o => o.text).join(' ') : ''; })()")  # 期間は1つのボタン（選択肢）
        pg.evaluate("histOthersOpen = true; setMpPeriod('y2025')")
        rows25 = pg.evaluate("document.getElementById('history-body').innerText")
        pg.evaluate("setMpPeriod('all')")
        results.append(("[10i] 期間（年）で成績と一覧を切り替えられ、過去の日付の試合はその年に入る", True,
                        "2025年" in pills and f"{__import__('datetime').date.today().year}年" in pills and "2025.05.10" in rows25 and "金曜会1" not in rows25))
        # 対局日をあとから変える（結果の編集から）
        pg.evaluate(f"viewDetailById('{g1}')")
        pg.evaluate("openDetailEdit()")
        pg.wait_for_function("() => document.getElementById('d-date')", timeout=10000)
        pg.evaluate("document.getElementById('d-date').value = '2025-12-24'; saveDetailEdit()")
        pg.wait_for_function(f"() => {{ const d = JSON.parse(localStorage.getItem('__smoke_db')); return d.sessions['{g1}'].settings.playDate === '2025-12-24'; }}", timeout=15000)
        results.append(("[10j] 結果の編集から対局日を変えられ、変更の履歴にも残る", True,
                        any("対局日" in str(e) for e in (db_of()["sessions"][g1].get("log") or []))))
        pg.evaluate("showView('history')")
        # 2日以上にわたる対局: 設定画面で終了日を選ぶ → 両方の日が打った日になる
        pg.evaluate("showView('setup')")
        pg.evaluate("() => { setupMembers = ['むにぃ', 'たろう', 'じろう', 'しろう']; renderMembers(); document.getElementById('s-date').value = '2025-08-23'; document.getElementById('s-multi').checked = true; toggleDateEnd('s'); }")
        pg.evaluate("startGame()")
        pg.wait_for_function(SAFE % "document.querySelector('#view-share').classList.contains('active')", timeout=10000)
        g5 = pg.evaluate("sessionId")
        st5 = db_of()["sessions"][g5]["settings"]
        days5 = pg.evaluate("gameDaysList(activeGame || { settings: %s })" % json.dumps(st5))
        pg.evaluate("leaveGame()")
        results.append(("[10k] 2日以上にわたる対局は開始日と終了日を持ち、打った日が2日になる", True,
                        st5.get("playDate") == "2025-08-23" and st5.get("playDateEnd") == "2025-08-24" and days5 == ["2025-08-23", "2025-08-24"]))

        # ---- 11. 共有シート・見るだけのリンク ----
        pg.evaluate(f"joinSession('{g1}')")
        pg.wait_for_function(SAFE % "document.querySelector('#view-game').classList.contains('active') && activeGame", timeout=10000)
        pg.evaluate("openShareSheet()")
        pg.wait_for_function(SAFE % "document.getElementById('share-sheet') && document.getElementById('share-sheet').innerText.includes('この試合のURL')", timeout=10000)
        sh = pg.evaluate("document.getElementById('share-sheet').innerText")
        results.append(("[11a] 共有シートは試合のURL1つだけ（一緒に打つ人・見る人でリンクを分けない）", True,
                        "この試合のURL" in sh and "見るだけ" not in sh and pg.evaluate("document.getElementById('share-sheet-url').value") == share1))
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
