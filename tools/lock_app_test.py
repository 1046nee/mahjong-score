# -*- coding: utf-8 -*-
"""対局の終了・再開・記録の確定（lockAt・endedAt）を、アプリの画面から本番のFirebaseで確かめる。

lock_rules_test.py はルールだけを REST で確かめる。こちらは実際のアプリ（index.html）が
「作成・入力（締め切り＝今から24時間後）」「終了」「猶予中の修正」「再開」「再開後の入力（締め切りを延ばす）」を
本番のルールに弾かれずに書けるかを見る。締め切りの無い古い試合（2026-10-02 より前の試合）を開くと、
最後の編集から24時間で確定したものとして扱い、過ぎた締め切りを書き込むことも見る（[9][10]。[10]はルールの貼り替え後）。
さらに、確定した試合（lockAt を過去にした状態を画面の中だけで作る）では入力の入口が出ないことも見る。
検証用のゲームを1つ本番に作る。試合は誰も消せないルール（2026-09-29〜）なので本番に残る。

実行: python tools/lock_app_test.py
"""
import functools
import http.server
import json
import os
import sys
import threading
import time
import urllib.error
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


def server_put(path, body):
    req = urllib.request.Request(f"{DB_URL}/{path}.json", data=json.dumps(body).encode("utf-8"), method="PUT",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status
    except urllib.error.HTTPError as e:
        return e.code


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
            left = (v.get("lockAt", 0) - time.time() * 1000) / H
            results.append(("[1] 終了を押していなくても、入力すると締め切りが「今から24時間後」に付く（最後の入力から24時間で確定）", True,
                            n_rounds(v) == 1 and 23.8 < left < 24.2 and pg.evaluate("document.getElementById('end-game-wrap').style.display !== 'none' && document.querySelector('#end-game-wrap .end-game-note').textContent.includes('最後の入力から24時間')")))
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
            # 締め切りの無い古い試合（2日前に作って入力したまま）を開く → 確定したものとして扱い、過ぎた締め切りを書き込む
            import random
            old = "".join(random.choice("ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789") for _ in range(10))
            two_days = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime(time.time() - 2 * 86400))
            server_put(f"sessions/{old}", {"id": old, "name": "古い試合の確認用（自動で確定）", "createdAt": two_days,
                                           "settings": {"playerNames": ["A", "B", "C", "D"], "numPlayers": 4, "startPoints": 25000, "returnPoints": 30000, "uma": [30, 10, -10, -30]},
                                           "rounds": [{"at": two_days, "points": [40000, 30000, 20000, 10000], "scores": [50, 10, -20, -40]}]})
            pg.evaluate(f"leaveGame(); joinSession('{old}')")
            pg.wait_for_function(f"() => activeGame && activeGame.id === '{old}'", timeout=20000)
            pg.wait_for_timeout(2500)
            results.append(("[9] 締め切りの無い古い試合（最後の入力が2日前）を開くと「確定しています」になり、入力の入口が出ない", True,
                            pg.evaluate("isGameLocked(activeGame) && document.getElementById('game-state').innerText.includes('記録は確定しています') && getComputedStyle(document.querySelector('#view-game .fab')).display === 'none'")))
            ov = server_get(old) or {}
            results.append(("[10] 古い試合に、過ぎた締め切り（最後の入力から24時間）が本番に書き込まれる（ルールの貼り替え後）", True,
                            isinstance(ov.get("lockAt"), (int, float)) and ov["lockAt"] < time.time() * 1000))
            if not isinstance(ov.get("lockAt"), (int, float)):  # 後片付け: 締め切りの無いまま残さない（ルールの貼り替え前は書けない）
                print(f"古い試合の確認用 {old} に締め切りを付けられませんでした（ルールの貼り替え前）")
        finally:
            if sid:
                req = urllib.request.Request(f"{DB_URL}/sessions/{sid}.json", method="DELETE")
                try:
                    urllib.request.urlopen(req, timeout=15)
                except Exception as e:
                    pass  # 消せないのが正しい（ルールで拒否）
                results.append(("[8] 試合は締め切り前でも消せない（ルール）", True, server_get(sid) is not None))
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
