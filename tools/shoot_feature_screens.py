# -*- coding: utf-8 -*-
# 記事・LP・IG用の実画面（見本のデータ・スタブのFirebase。本番に触れない）。2026-10-13 お知らせ3本・LP「実際の画面で見る。」・IG ig-v2-8〜10 の素材
# 出力: まじゃすこ素材/ig/shots/oct-*.png（サイト用は PIL で幅720に縮小して assets/screens/*.jpg へ）
# 実行: python tools/shoot_feature_screens.py
import sys, os, functools, threading, http.server, random
MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(MJ, "tools"))
from smoke_test import FIREBASE_STUB
from account_test import AUTH_STUB
from playwright.sync_api import sync_playwright

OUT = os.path.join(MJ, "まじゃすこ素材", "ig", "shots")
os.makedirs(OUT, exist_ok=True)


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


srv = http.server.ThreadingHTTPServer(("127.0.0.1", 8805), functools.partial(Q, directory=MJ))
threading.Thread(target=srv.serve_forever, daemon=True).start()
W = 390
rnd = random.Random(7)


def deal(n):
    # n人分の持ち点（合計 25,000×4 = 100,000。先頭 n-1 人分を返す。最後は自動）
    while True:
        a = [rnd.randrange(60, 520) * 100 for _ in range(n - 1)]
        last = 100000 - sum(a)
        if 0 <= last <= 60000 and len(set(a + [last])) == n:
            return [str(v // 100) for v in a]


# （名前, 日付の配列（試合ごと）, メンバー, 試合ごとの卓（席番号4つ））
GAMES = [
    ("8月の定例会", ["2026-08-07T20:00"] * 5, ["太郎", "次郎", "三郎", "四郎"]),
    ("お盆の集まり", ["2026-08-14T15:00"] * 6, ["太郎", "次郎", "三郎", "四郎", "五郎"]),
    ("9月の定例会", ["2026-09-04T20:00"] * 5, ["太郎", "次郎", "三郎", "四郎"]),
    ("連休の2日間", ["2026-09-20T13:00"] * 4 + ["2026-09-21T13:00"] * 4, ["太郎", "次郎", "三郎", "四郎", "五郎", "六郎"]),
    ("10月の定例会", ["2026-10-02T20:00"] * 6, ["太郎", "次郎", "三郎", "四郎"]),
    ("金曜の夜", ["2026-10-09T20:00"] * 4, ["太郎", "次郎", "四郎", "五郎"]),
]

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": W, "height": 844}, device_scale_factor=2, locale="ja-JP")
    ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript",
              body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in r.request.url else ""))
    ctx.route(lambda u: not u.startswith("http://127.0.0.1:8805") and "gstatic" not in u, lambda r: r.abort())
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8805/")
    pg.wait_for_timeout(600)
    made = []
    for name, ats, mem in GAMES:
        pg.evaluate("showView('setup')")
        pg.evaluate("applyMode(4)")
        pg.evaluate("(a) => { setupMembers = a.m; renderMembers(); document.getElementById('s-name').value = a.n; }", {"m": mem, "n": name})
        pg.evaluate("startGame()")
        pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=10000)
        pg.evaluate("showView('game')")
        for k in range(len(ats)):
            seats = list(range(len(mem)))
            if len(mem) > 4:
                rnd.shuffle(seats)
                seats = sorted(seats[:4])
                if 0 not in seats and k % 2 == 0:
                    seats = sorted([0] + seats[1:])
            pts = deal(4)
            pg.evaluate("""async (a) => { openSheet(-1); await new Promise(r => setTimeout(r, 60));
              sheetSelected = a.s; renderSheetMembers(); renderSheetInputs();
              a.p.forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
              await new Promise(r => setTimeout(r, 60)); submitRound(); await new Promise(r => setTimeout(r, 160)); }""", {"s": seats, "p": pts})
        gid = pg.evaluate("sessionId")
        made.append((gid, ats))
        pg.evaluate("leaveGame()")
        pg.evaluate(f"setTag('{gid}', 'play', 0)")
    for gid, ats in made:
        pg.evaluate("""async ([gid, ats]) => { const g = appState.games.find(x => x.id === gid);
          for (let i = 0; i < g.rounds.length; i++) { const t = new Date(ats[i] + ':00+09:00'); t.setMinutes(t.getMinutes() + i * 40);
            g.rounds[i].at = t.toISOString(); await firebase.database().ref('sessions/' + gid + '/rounds/' + i + '/at').set(g.rounds[i].at); }
          g.createdAt = g.rounds[0].at; await firebase.database().ref('sessions/' + gid + '/createdAt').set(g.createdAt);
          const lk = Date.now() - 1000; g.lockAt = lk; await firebase.database().ref('sessions/' + gid + '/lockAt').set(lk); saveStorage(); }""", [gid, ats])
    pg.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", "uidSHOT01")
    pg.evaluate("signInWithGoogle()")
    pg.wait_for_load_state("load")
    pg.wait_for_function("() => typeof currentUser !== 'undefined' && currentUser && !accountBusy", timeout=15000)
    pg.wait_for_timeout(600)
    pg.add_style_tag(content="#toast, .toast { display: none !important; }")

    def shot(sel, name, pad=0):
        el = pg.locator(sel).first
        el.scroll_into_view_if_needed()
        pg.wait_for_timeout(250)
        el.screenshot(path=os.path.join(OUT, "oct-" + name + ".png"))

    pg.evaluate("showView('history'); setMpPeriod('all'); mpMode = 4; sparkUnit = 'm'; renderHistory()")
    pg.wait_for_timeout(500)
    shot("#mp-stats .mc-card", "mypage-card")
    pg.evaluate("document.querySelector('#mp-stats .sp-hit[data-i=\"1\"]').dispatchEvent(new MouseEvent('click', { bubbles: true }))")
    pg.wait_for_timeout(300)
    shot("#mp-stats .sp-pop", "spark-pop")
    pg.evaluate("setMpPane('h2h')"); pg.wait_for_timeout(300)
    shot("#mp-pane-h2h .card", "my-h2h")
    # 仲間ページ
    pg.evaluate("openCreateCircle(); document.getElementById('cc-name').value = '金曜定例会'; document.getElementById('cc-me').value = '太郎';")
    pg.evaluate("runCreateCircle()")
    pg.wait_for_function("() => document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=10000)
    pg.evaluate("(t) => { openCircleAddGames(); document.querySelectorAll('.cadd-pick').forEach(el => { el.checked = false; }); document.getElementById('cadd-text').value = t; }",
                "\n".join("https://majasco.jp/#" + g for g, _ in made))
    pg.evaluate("runCircleAddGames()")
    pg.wait_for_function(f"() => circleData && circleData.games && Object.keys(circleData.games).length >= {len(made)}", timeout=20000)
    pg.wait_for_timeout(800)
    pg.evaluate("closeFormModal()")
    pg.evaluate("setMpPeriod('all'); circleTab = 'rank'; circleMetric = 'score'; renderCircle()")
    pg.wait_for_timeout(500)
    shot("#circle-body .rank-card", "circle-rank")
    for t, nm in [("grid", "circle-grid"), ("h2h", "circle-h2h")]:
        pg.evaluate(f"circleTab = '{t}'; renderCircle()")
        pg.wait_for_timeout(500)
        shot("#circle-body .card", nm)
    pg.evaluate("window.scrollTo(0, 0)")
    pg.wait_for_timeout(200)
    pg.screenshot(path=os.path.join(OUT, "oct-circle-top.png"))
    r = pg.evaluate("Object.entries(rosterOf()).map(([m, x]) => [m, x.name])")
    ids = {n: m for m, n in r}
    pg.evaluate(f"openCircleMatchup(['{ids['太郎']}', '{ids['次郎']}'])")
    pg.wait_for_timeout(500)
    shot("#form-modal .mu-vs", "matchup-vs")
    shot("#form-modal .mu-card", "matchup-table")
    pg.evaluate("closeFormModal()")
    pg.evaluate(f"openResultSheet('{made[3][0]}', {{ from: 'circle', me: 0 }})")
    pg.wait_for_timeout(500)
    pg.locator("#form-modal .form-modal-box").screenshot(path=os.path.join(OUT, "oct-result-sheet.png"))
    print("errors", errs)
    br.close()
srv.shutdown()
