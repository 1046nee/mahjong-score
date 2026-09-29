# -*- coding: utf-8 -*-
"""対局の終了・再開・記録の確定（lockAt・endedAt）を、アプリの画面から本番のFirebaseで確かめる。

lock_rules_test.py はルールだけを REST で確かめる。こちらは実際のアプリ（index.html）が
「終了」「猶予中の修正」「再開」「再開後の入力（締め切りを延ばす）」を本番のルールに弾かれずに書けるかを見る。
さらに、確定した試合（lockAt を過去にした状態を画面の中だけで作る）では入力の入口が出ないことも見る。
検証用のゲームを1つ本番に作り、最後に削除する（締め切り前なので消せる）。

実行: python tools/lock_app_test.py
"""
import functools
import http.server
import json
import os
import sys
import threading
import urllib.request

from playwright.sync_api import sync_playwright

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8795
DB_URL = "https://mahjong-score-2e8aa-default-rtdb.asia-southeast1.firebasedatabase.app"
BLOCK = ("googletagmanager.com", "google-analytics.com", "analytics.google.com",
         "googlesyndication.com", "doubleclick.net", "adservice.google", "adtrafficquality.google")
H = 3600 * 1000


def server_get(sid, path=""):
    with urllib.request.urlopen(f"{DB_URL}/sessions/{sid}{path}.json", timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def n_rounds(v):
    r = (v or {}).get("rounds") or []
    return len([x for x in (r if isinstance(r, list) else r.values()) if x])


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Quiet, directory=BASE))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    results, errors, sid = [], [], None
    with sync_playwright() as p:
        br = p.chromium.launch()
        pg = br.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.route("**/*", lambda route: route.abort() if any(b in route.request.url for b in BLOCK) else route.continue_())
        try:
            pg.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=30000)
            pg.wait_for_function("() => dbConnected", timeout=20000)
            pg.evaluate("createGame('終了の確認用（自動で消えます）', { playerNames: ['A','B','C','D'], numPlayers: 4, startPoints: 25000, returnPoints: 30000, uma: [30,10,-10,-30], rate: 0, bonusEnabled: false, chipRate: 1, startChips: 20, yakitori: false, chombo: false, chomboPenalty: 0, teamMode: false }, { toGame: true, saveNames: false })")
            pg.wait_for_function("() => sessionId && activeGame", timeout=20000)
            sid = pg.evaluate("sessionId")

            def add_round(pts):
                pg.evaluate("""async (pts) => { openSheet(-1); await new Promise(r => setTimeout(r, 150));
                  pts.forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
                  await new Promise(r => setTimeout(r, 150)); submitRound(); }""", pts)

            add_round(["400", "300", "200"])
            pg.wait_for_function("() => outbox.length === 0", timeout=20000)
            v = server_get(sid)
            results.append(("[1] 終了を押していない試合には締め切りが付かない（毎週続けるゲームを勝手に確定しない）", True,
                            n_rounds(v) == 1 and "lockAt" not in v and pg.evaluate("document.getElementById('end-game-wrap').style.display !== 'none'")))
            pg.evaluate("setGameEnded(true)")
            pg.wait_for_function("() => activeGame && activeGame.endedAt", timeout=20000)
            v = server_get(sid)
            gap = v.get("lockAt", 0) - v.get("endedAt", 0)
            results.append(("[2] 「対局を終了」で endedAt と 12時間後の lockAt が本番に書ける", True, abs(gap - 12 * H) < 1000))
            results.append(("[3] 終了後は「＋ 点数入力」が消え、「再開する」が出る", True,
                            pg.evaluate("getComputedStyle(document.querySelector('#view-game .fab')).display === 'none' && document.getElementById('game-state').innerText.includes('再開する')")))
            lock1 = v["lockAt"]
            pg.evaluate("""async () => { openSheet(0); await new Promise(r => setTimeout(r, 150));
              document.getElementById('si-0').value = '410'; document.getElementById('si-1').value = '290'; document.getElementById('si-2').value = '200';
              autoFill(); await new Promise(r => setTimeout(r, 150)); submitRound(); }""")
            pg.wait_for_function("() => outbox.length === 0", timeout=20000)
            v = server_get(sid)
            pts0 = ((v.get("rounds") or [{}])[0] or {}).get("points", [None])[0]
            results.append(("[4] 終了後の猶予のうちは点数を修正でき、締め切りは延びない", True, pts0 == 41000 and v.get("lockAt") == lock1))
            pg.evaluate("setGameEnded(false)")
            pg.wait_for_function("() => activeGame && !activeGame.endedAt", timeout=20000)
            v = server_get(sid)
            results.append(("[5] 再開すると endedAt が消え、締め切りは約24時間後になる", True,
                            "endedAt" not in v and abs(v.get("lockAt", 0) - lock1 - 12 * H) < 5 * 60 * 1000))
            lock2 = v["lockAt"]
            pg.wait_for_timeout(1500)
            add_round(["350", "300", "250"])
            pg.wait_for_function("() => outbox.length === 0", timeout=20000)
            v = server_get(sid)
            results.append(("[6] 再開後の入力は本番に保存され、締め切りが「今から24時間後」に延びる", True,
                            n_rounds(v) == 2 and v.get("lockAt", 0) > lock2))
            # 確定した状態（画面の中だけで lockAt を過去にする）では入力の入口を出さない
            pg.evaluate("activeGame.lockAt = serverNow() - 1000; renderGame()")
            results.append(("[7] 確定した試合は「確定しています」と出て、点数入力・設定の編集・行のタップが出ない", True,
                            pg.evaluate("""document.getElementById('game-state').innerText.includes('記録は確定しています')
                              && getComputedStyle(document.querySelector('#view-game .fab')).display === 'none'
                              && document.querySelector('#view-game .title-actions button[onclick=\"openGameEdit()\"]').style.display === 'none'
                              && ![...document.querySelectorAll('#rounds-table tbody tr')].some(tr => (tr.getAttribute('onclick') || '').includes('openRoundMenu'))""")))
        finally:
            if sid:
                req = urllib.request.Request(f"{DB_URL}/sessions/{sid}.json", method="DELETE")
                try:
                    urllib.request.urlopen(req, timeout=15)
                except Exception as e:
                    errors.append("削除に失敗: " + str(e))
                results.append(("[8] 締め切り前なので検証用のゲームを削除できた", True, server_get(sid) is None))
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
    print("LOCK APP TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
