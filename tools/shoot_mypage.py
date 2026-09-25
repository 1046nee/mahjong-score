# -*- coding: utf-8 -*-
"""マイページ・自分の成績・仲間ページなど「ログインした人の画面」を、スタブのFirebaseでスクリーンショットに撮る。
デザインの見直し（改修前後の見比べ・崩れの確認）に使う。本番のDBにもGoogleにも触らない。

データはこのスクリプトが毎回同じ内容で作る（4つのゲーム・計30試合・三麻を含む・自分=むにぃ）。
account_test.py と同じスタブ（smoke_test.FIREBASE_STUB ＋ 偽のログイン）を使う。

実行: python tools/shoot_mypage.py <出力フォルダ> [接頭辞] [幅]
  例: python tools/shoot_mypage.py C:/tmp/shots before 390
"""
import base64
import functools
import http.server
import os
import sys
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_test import FIREBASE_STUB  # noqa: E402
from account_test import AUTH_STUB  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8797
U1 = 'uidSHOT0001'

# 1試合ぶんの点数（百点単位）。合計は四麻=1000（25,000点×4）・三麻=1050（35,000点×3）。
# 最後の1人は autoFill で埋まるので、先頭 n-1 人ぶんだけ使う
SETS4 = [[450, 300, 180, 70], [380, 290, 210, 120], [520, 250, 160, 70], [310, 300, 250, 140],
         [260, 350, 200, 190], [150, 420, 280, 150]]
SETS3 = [[520, 330, 200], [430, 380, 240], [300, 600, 150], [400, 350, 300]]

GAMES = [
    # (名前, 形式, メンバー, 自分のindex, 試合数)
    ("金曜会", 4, ["むにぃ", "たろう", "じろう", "さぶろう", "しろう"], 0, 12),
    ("社内リーグ", 4, ["はなこ", "むにぃ", "けんじ", "ゆうき"], 1, 8),
    ("三麻の会", 3, ["たろう", "むにぃ", "ゆうき"], 1, 6),
    ("年末大会", 4, ["たろう", "はなこ", "むにぃ", "じろう", "けんじ", "さぶろう"], 2, 10),
]


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "shots")
    prefix = sys.argv[2] if len(sys.argv) > 2 else "shot"
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 390
    os.makedirs(out, exist_ok=True)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Quiet, directory=BASE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{PORT}/"
    errors = []
    shots = []
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": width, "height": 844}, locale="ja-JP", device_scale_factor=2)

        def route_fb(route):
            body = FIREBASE_STUB + AUTH_STUB if "firebase-app-compat" in route.request.url else "/* stub */"
            route.fulfill(status=200, content_type="application/javascript", body=body)
        ctx.route("https://www.gstatic.com/firebasejs/**", route_fb)
        ctx.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}") and not url.startswith("https://www.gstatic.com/firebasejs"),
                  lambda route: route.abort())
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(app, wait_until="load")
        pg.wait_for_timeout(600)

        def shoot(name, full=True, modal=False):
            path = os.path.join(out, f"{prefix}_{len(shots) + 1:02d}_{name}.png")
            pg.wait_for_timeout(250)
            # 「ログインしました」などのトーストが画面に被らないように消してから撮る
            pg.evaluate("() => { const t = document.getElementById('toast'); if (t) t.classList.remove('show', 'act'); }")
            if modal:
                # モーダルの中身を全部写すため、箱の高さ制限を一時的に外す
                pg.evaluate("""() => { const b = document.querySelector('#form-modal .form-modal-box');
                  if (b) { b.dataset.shotStyle = b.getAttribute('style') || ''; b.style.maxHeight = 'none'; b.style.overflow = 'visible'; }
                  const m = document.getElementById('form-modal'); if (m) { m.style.position = 'absolute'; m.style.alignItems = 'flex-start'; } }""")
                el = pg.query_selector('#form-modal .form-modal-box')
                el.screenshot(path=path)
                pg.evaluate("""() => { const b = document.querySelector('#form-modal .form-modal-box');
                  if (b) b.setAttribute('style', b.dataset.shotStyle || '');
                  const m = document.getElementById('form-modal'); if (m) { m.style.position = ''; m.style.alignItems = ''; } }""")
            else:
                pg.evaluate("window.scrollTo(0, 0)")
                pg.screenshot(path=path, full_page=full)
            shots.append(path)

        def save_canvas(name, expr):
            """画像出力（Canvas）をPNGに書き出す。画面と画像の食い違い（メダルの数字・いちばん良い値の色など）の確認用"""
            data = pg.evaluate(f"() => {{ const c = ({expr}); return c && c.toDataURL ? c.toDataURL('image/png') : String(c); }}")
            if not str(data).startswith("data:image/png;base64,"):
                errors.append(f"image {name}: {data}")
                return
            path = os.path.join(out, f"{prefix}_img_{name}.png")
            with open(path, "wb") as f:
                f.write(base64.b64decode(data.split(",", 1)[1]))
            shots.append(path)

        def make_game(name, np, members, rounds, marks=False):
            pg.evaluate("showView('setup')")
            if np == 3:
                pg.evaluate("setGameMode(3)")
            pg.evaluate("(a) => { setupMembers = a[1]; renderMembers(); document.getElementById('s-name').value = a[0]; }", [name, members])
            if marks:  # 焼き鳥・チョンボを記録するゲーム（アイコンの見え方の確認用）
                pg.evaluate("() => { document.getElementById('s-yakitori').checked = true; document.getElementById('s-chombo').checked = true; onChomboOptChange(); }")
            pg.evaluate("startGame()")
            pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=10000)
            pg.evaluate("showView('game')")
            for ri, (sel, pts) in enumerate(rounds):
                pg.evaluate("""async (a) => { openSheet(-1); await new Promise(r => setTimeout(r, 80));
                  sheetSelected = a[0].slice(); renderSheetMembers(); renderSheetInputs();
                  a[1].forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
                  if (a[2]) { toggleSheetYaki(3); if (a[3]) toggleSheetChombo(2); }
                  await new Promise(r => setTimeout(r, 80)); submitRound(); await new Promise(r => setTimeout(r, 350)); }""",
                            [sel, pts, marks, ri % 2 == 0])
            sid = pg.evaluate("sessionId")
            pg.evaluate("leaveGame()")
            return sid

        # ---- データを作る（決まった順で回すので毎回同じ結果になる） ----
        gids = []
        for gi, (name, np, members, me, n) in enumerate(GAMES):
            rounds = []
            for r in range(n):
                # 参加者: 人数が多いゲームは回し打ち（自分は毎回入る）
                others = [i for i in range(len(members)) if i != me]
                pick = [me] + [others[(r + k) % len(others)] for k in range(np - 1)]
                pick = sorted(set(pick))[:np]
                sets = SETS4 if np == 4 else SETS3
                pts = sets[(r * 3 + gi) % len(sets)]
                # 席の並び（pickの昇順）に点数を割り当て。自分の順位が偏らないよう回す
                rot = (r + gi) % np
                pts = pts[rot:] + pts[:rot]
                rounds.append((pick, [str(v) for v in pts[:np - 1]]))
            gid = make_game(name, np, members, rounds)
            pg.evaluate(f"setTag('{gid}', 'play', {me})")
            gids.append(gid)
        # 焼き鳥・チョンボのマークが付いたゲーム（アイコンの確認用）
        gid_marks = make_game("焼き鳥あり", 4, ["むにぃ", "たろう", "じろう", "さぶろう"],
                              [([0, 1, 2, 3], ["450", "300", "180"]), ([0, 1, 2, 3], ["310", "300", "250"])], marks=True)
        pg.evaluate(f"setTag('{gid_marks}', 'play', 0)")

        # ---- ログイン → マイページ ----
        pg.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", U1)
        pg.evaluate("signInWithGoogle()")
        pg.wait_for_load_state("load")
        # ログインは再読み込みを挟むので、新しいページのスクリプトが動くまで typeof で待つ
        pg.wait_for_function("() => typeof currentUser !== 'undefined' && currentUser && !accountBusy", timeout=15000)
        pg.wait_for_timeout(600)
        pg.evaluate("showView('history'); setMpTab('me')")
        pg.wait_for_timeout(500)
        shoot("mypage_me")
        pg.evaluate("mpMode = 3; renderHistory()")
        shoot("mypage_me_sanma")
        pg.evaluate("mpMode = 4; renderHistory()")

        # 過去の試合の「…」メニュー
        pg.evaluate(f"openHistMenu('{gids[0]}')")
        shoot("hist_menu", modal=True)
        pg.evaluate("closeFormModal()")

        # 自分の成績（まとめ・相手別・ゲーム別の3タブ。相手別は先頭の行を開いた状態）
        pg.evaluate("myStatsTab = 'sum'; showView('mystats')")
        pg.wait_for_timeout(400)
        shoot("mystats_sum")
        pg.evaluate("myStatsTab = 'h2h'; renderMyStats(); const d = document.querySelector('#mystats-body details.h2-row'); if (d) d.open = true;")
        shoot("mystats_h2h")
        pg.evaluate("myStatsTab = 'groups'; renderMyStats()")
        shoot("mystats_groups")
        pg.evaluate("myStatsTab = 'sum'")
        save_canvas("mystats", "buildMyStatsCanvas()")

        # 仲間ページを作ってゲームを入れる
        pg.evaluate("showView('history'); setMpTab('circle')")
        pg.wait_for_timeout(300)
        shoot("mypage_circle_empty")
        pg.evaluate("openCreateCircle(); document.getElementById('cc-name').value = '金曜会の仲間'; document.getElementById('cc-me').value = 'むにぃ';")
        pg.evaluate("runCreateCircle()")
        pg.wait_for_function("() => document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=10000)
        pg.evaluate("openCircleAddGames()")
        text = "\\n".join(f"https://majasco.jp/#{g}" for g in gids)
        pg.evaluate(f"() => {{ document.querySelectorAll('.cadd-pick').forEach(el => {{ el.checked = false; }}); document.getElementById('cadd-text').value = '{text}'; }}")
        pg.evaluate("runCircleAddGames()")
        pg.wait_for_function("() => circleData && circleData.games && Object.keys(circleData.games).length >= %d" % len(gids), timeout=15000)
        pg.wait_for_timeout(600)
        pg.evaluate("closeFormModal && closeFormModal()")
        for t in ["rank", "grid", "h2h", "games", "people"]:
            pg.evaluate(f"circleTab = '{t}'; renderCircle()")
            shoot(f"circle_{t}")
        pg.evaluate("openCircleMember(Object.keys(circleData.roster).find(m => circleData.roster[m].name === 'たろう'))")
        shoot("circle_member", modal=True)
        pg.evaluate("closeFormModal()")
        save_canvas("circle", """(() => { const st = circleStats(circleData, circleSess, circleMode);
          return buildTablesCanvas(circleData.name, '撮影', '', [{ label: '通算順位', html: circleStandingsTableHtml(st, true) },
            { label: '成績表', html: circleGridHtml(st, true) }], circleMode === '3'); })()""")

        # マイページの「仲間」（カードが出た状態）
        pg.evaluate("showView('history'); setMpTab('circle')")
        pg.wait_for_timeout(500)
        shoot("mypage_circle")

        # 結果詳細（順位のメダル・対戦成績カード）
        pg.evaluate(f"viewDetailById('{gids[0]}')")
        pg.wait_for_timeout(400)
        shoot("detail")
        for kind in ["score", "rounds", "stats"]:
            save_canvas(f"detail_{kind}", f"buildResultCanvas(detailGame, '{kind}')")

        # 共有シート
        try:
            pg.evaluate(f"openShareSheet('{gids[0]}')")
            shoot("share_sheet", modal=True)
            pg.evaluate("closeFormModal()")
        except Exception as e:  # 共有シートの形が変わっても他の撮影は続ける
            errors.append("share: " + str(e))

        # 焼き鳥・チョンボのあるゲーム: ゲーム画面・点数入力・設定の編集
        pg.evaluate(f"rejoinGame('{gid_marks}')")
        pg.wait_for_function("() => document.querySelector('#view-game').classList.contains('active') && activeGame", timeout=10000)
        pg.wait_for_timeout(500)
        shoot("game_marks")
        pg.evaluate("""async () => { openSheet(-1); await new Promise(r => setTimeout(r, 80));
          sheetSelected = [0, 1, 2, 3]; renderSheetMembers(); renderSheetInputs(); toggleSheetYaki(1); toggleSheetChombo(3); }""")
        pg.wait_for_timeout(300)
        pg.evaluate("window.scrollTo(0, 0)")
        path = os.path.join(out, f"{prefix}_{len(shots) + 1:02d}_score_sheet.png")
        pg.evaluate("() => { const t = document.getElementById('toast'); if (t) t.classList.remove('show', 'act'); }")
        pg.query_selector('#score-sheet .sheet-box').screenshot(path=path)
        shots.append(path)
        pg.evaluate("closeSheet()")
        pg.evaluate("openGameEdit()")
        shoot("settings_edit", modal=True)
        pg.evaluate("closeFormModal()")

        br.close()
    srv.shutdown()
    for s in shots:
        print(s)
    if errors:
        print("PAGE ERRORS:", errors)
        sys.exit(1)


if __name__ == "__main__":
    main()
