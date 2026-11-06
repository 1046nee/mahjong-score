# -*- coding: utf-8 -*-
"""メンバー100人（MAX_MEMBERS）のゲームで、作成・チーム戦・入力・画面・画像が成り立つかを確かめる（2026-11-06〜。40人→100人に広げたとき）。
スタブのFirebase（tools/smoke_test・account_test と同じ）。本番には触らない。
確かめること: 100人で作れる・101人目は止まる／25チーム×4人のチーム戦で試合を入れられる／
ゲームの画面が 320・390px で横にはみ出さない（fit_test と同じ判定）／結果の画像が項目ごとに作れる（作れない項目は IMG_TOO_LARGE で案内される）
実行: python tools/members100_test.py
"""
import functools
import http.server
import os
import sys
import threading

MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(MJ, "tools"))
from smoke_test import FIREBASE_STUB  # noqa: E402
from account_test import AUTH_STUB  # noqa: E402
from fit_test import CHECK_JS, NUM_SEL  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PORT = 8796
N, TEAMS, ROUNDS = 100, 25, 60


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=MJ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{PORT}/"
    bad, errors = [], []
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 760}, locale="ja-JP")
        ctx.route("https://www.gstatic.com/firebasejs/**", lambda route: route.fulfill(status=200, content_type="application/javascript",
                  body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in route.request.url else "/* stub */"))
        ctx.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}") and not url.startswith("https://www.gstatic.com/firebasejs"), lambda route: route.abort())
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(app, wait_until="load")
        pg.wait_for_timeout(500)
        if pg.evaluate("MAX_MEMBERS") != N:
            bad.append(f"MAX_MEMBERS が {N} ではない")
        pg.evaluate("showView('setup')")
        names = [f"メンバー{i + 1:03d}" for i in range(N)]
        # 101人目は止まる
        pg.evaluate("(a) => { setupMembers = a; renderMembers(); }", names)
        pg.evaluate("document.getElementById('member-input').value = 'あふれる人'; addMember()")
        if pg.evaluate("setupMembers.length") != N:
            bad.append(f"101人目が入った（{pg.evaluate('setupMembers.length')}人）")
        # 25チーム×4人のチーム戦
        pg.evaluate("setMatchType(true)")
        pg.evaluate("""([n, t]) => { setupTeams = Array.from({ length: t }, (_, k) => ({ name: 'チーム' + (k + 1), members: [] }));
            for (let i = 0; i < n; i++) setupTeams[i % t].members.push(i); initSetupTeamEditor(); }""", [N, TEAMS])
        pg.evaluate("document.getElementById('s-name').value = '100人のチーム戦'")
        pg.evaluate("startGame()")
        pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=15000)
        pg.evaluate("showView('game')")
        if pg.evaluate("activeGame.settings.playerNames.length") != N:
            bad.append("100人で作れていない")
        # 試合を入れる（毎回ちがうチームの4人）
        for r in range(ROUNDS):
            mem = [(r * 4 + k) % N for k in range(4)]  # i % 25 がチーム → 連続4人は別のチーム
            pts = [str(300 + (r * 37) % 200), str(250 - (r * 13) % 120), str(200 + (r * 7) % 90)]
            pg.evaluate("""async ([mem, pts]) => { openSheet(-1); await new Promise(r => setTimeout(r, 40));
              sheetSelected = mem; renderSheetMembers(); renderSheetInputs();
              pts.forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
              await new Promise(r => setTimeout(r, 40)); submitRound(); await new Promise(r => setTimeout(r, 120)); }""", [mem, pts])
        n_rounds = pg.evaluate("(activeGame.rounds || []).length")
        if n_rounds != ROUNDS:
            bad.append(f"試合が {n_rounds}/{ROUNDS} しか入っていない")
        # 総合順位は10位まで・試合結果は直近20試合（2026-11-06〜）。ボタンで全部を出せる
        fold = pg.evaluate("""() => { const box = [...document.querySelectorAll('#view-game .score-cards')].find(b => b.querySelector('.rk-toggle'));
            if (!box) return null; const vis = () => [...box.querySelectorAll('.score-card')].filter(e => e.offsetParent).length;
            const before = vis(); box.querySelector('.rk-toggle').click(); const after = vis(); box.querySelector('.rk-toggle').click();
            return [before, after, vis()]; }""")
        if not fold or fold[0] != 10 or fold[1] != N or fold[2] != 10:
            bad.append(f"総合順位の畳み方が違う（見える行: 最初・全部・戻す = {fold}）")
        rows = pg.evaluate("() => document.querySelectorAll('#view-game .rounds-table tbody tr').length")
        btn = pg.evaluate("() => [...document.querySelectorAll('#view-game .auto-btn')].some(b => b.textContent.includes('すべての試合を表示する'))")
        if not btn:
            bad.append(f"試合結果の「すべての試合を表示する」が無い（行 {rows}）")
        # 画面のはみ出し
        for w in (320, 390):
            pg.set_viewport_size({"width": w, "height": 760})
            pg.evaluate("showView('game')")
            pg.wait_for_timeout(500)
            got = pg.evaluate(CHECK_JS, NUM_SEL)
            bad += [f"[{w}] {x}" for x in got]
        # 結果の画像（項目ごと・全部を1枚）
        res = pg.evaluate("""() => { const g = activeGame; const out = {};
            imgAvailableSections(g).forEach(s => { const c = buildResultCanvas(g, s.kind); out[s.kind] = c === IMG_TOO_LARGE ? 'too-large' : c ? c.width + 'x' + c.height : 'none'; });
            const all = buildComposedCanvas(g, imgAvailableSections(g).map(s => s.kind)); out['全部を1枚'] = all === IMG_TOO_LARGE ? 'too-large' : all ? all.width + 'x' + all.height : 'none';
            return out; }""")
        for k, v in res.items():
            print(f"  画像 {k}: {v}")
            if v == "none":
                bad.append(f"画像 {k} が作れない")
        br.close()
    srv.shutdown()
    bad += [f"ページのエラー: {e}" for e in errors]
    if bad:
        print("NG:")
        for b in bad:
            print("  " + b)
        print("MEMBERS100 TEST: FAIL")
        sys.exit(1)
    print(f"{N}人・{TEAMS}チーム・{ROUNDS}試合: はみ出し・エラーなし")
    print("MEMBERS100 TEST: ALL PASS")


if __name__ == "__main__":
    main()
