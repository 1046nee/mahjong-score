# -*- coding: utf-8 -*-
"""同時入力・オフライン復帰で試合が消えないかを、本番のFirebase（Realtime Database）で確かめる。

2つのブラウザ（＝2台のスマホ）で同じゲームを開き、次を確認する。
  [1] 片方が圏外のあいだに両方が入力 → 復帰しても、もう片方の試合が消えない
      （古い画面の端末が rounds 配列を丸ごと上書きしていた。2026-09 に実際に起きた事故）
  [2] 圏外で入力 → 送信前に再読み込み → 入力が残っていて、つながったら送られる
      （送れていないあいだは画面上部に「未送信」の帯、試合行に「未送信」印が出る）
  [3] 再送の仕組みで同じ試合が二重に登録されない
  [4] 設定の変更が「ウマ: 10-30 → 10-20」のような変更点つきで履歴に残る
  [5] 設定の編集中に他の人が先に設定を変えたら、上書きせずに知らせる

smoke_test.py と違ってFirebaseはスタブにしない。本番のセキュリティルール
（database.rules.json）で書き込みが弾かれないことも、ここで初めて確認できる
（送信キューは sessions/{id} 全体をトランザクションで書くので、直下に新しいキーを足すと本番で全滅する）。
検証用のゲームを1つ本番に作り、最後に必ず削除する（CLAUDE.md 絶対ルール2）。
GTM・GA4・広告への通信は遮断する（アクセス解析に検証アクセスを混ぜないため）。

実行: python tools/sync_test.py   （要: pip install playwright ／ playwright install chromium）
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
PORT = 8791
DB_URL = "https://mahjong-score-2e8aa-default-rtdb.asia-southeast1.firebasedatabase.app"
BLOCK = ("googletagmanager.com", "google-analytics.com", "analytics.google.com",
         "googlesyndication.com", "doubleclick.net", "adservice.google", "adtrafficquality.google")


def server_get(sid, path=""):
    """サーバー上の値をREST APIで読む（どちらのブラウザのキャッシュも通さない正解の値）"""
    with urllib.request.urlopen(f"{DB_URL}/sessions/{sid}{path}.json", timeout=15) as r:
        return json.loads(r.read().decode("utf-8"))


def as_list(v):
    if v is None:
        return []
    return [x for x in (v if isinstance(v, list) else v.values()) if x]


def server_rounds(sid):
    return as_list(server_get(sid, "/rounds"))


def open_game(ctx, url):
    page = ctx.new_page()
    page.route("**/*", lambda route: route.abort()
               if any(b in route.request.url for b in BLOCK) else route.continue_())
    page.goto(url, wait_until="load", timeout=30000)
    return page


def wait_game(page):
    page.wait_for_function(
        "() => { const v = document.querySelector('#view-game');"
        " const b = document.querySelector('#score-main-body');"
        " return v && v.classList.contains('active') && b && b.innerText.includes('A'); }",
        timeout=20000)
    page.wait_for_timeout(800)


def enter_round(page, pts):
    """点数入力シートから1試合を入れる（3人ぶん＋残り1人は自動入力）"""
    page.click(".fab")
    page.wait_for_selector("#si-0", state="visible", timeout=10000)
    for i, v in enumerate(pts):
        page.fill(f"#si-{i}", v)
    page.click("#auto-btn")
    page.click("#confirm-btn")
    page.wait_for_timeout(1500)


def wait_until(fn, timeout_ms=20000, step_ms=500):
    import time
    end = time.time() + timeout_ms / 1000
    while time.time() < end:
        v = fn()
        if v:
            return v
        time.sleep(step_ms / 1000)
    return fn()


def main():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=BASE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{PORT}/index.html"

    results, sid = [], None
    with sync_playwright() as p:
        browser = p.chromium.launch()
        # 2台のスマホ。localStorage（送信キュー）も別々
        dev_a = browser.new_context(viewport={"width": 390, "height": 844}, locale="ja-JP")
        dev_b = browser.new_context(viewport={"width": 390, "height": 844}, locale="ja-JP")
        try:
            # ---- 準備: Aがクイックスタートでゲームを作り、Bが共有URLから参加 ----
            a = open_game(dev_a, app)
            a.click("#view-home .cta-btn")
            a.wait_for_selector("#quick-start.open", state="visible", timeout=10000)
            a.click("#quick-start .qs-4")
            wait_game(a)
            sid = a.evaluate("location.hash.slice(1)")
            assert len(sid) in (10, 22), f"セッションIDが取れない: {sid!r}"
            b = open_game(dev_b, f"{app}#{sid}")
            wait_game(b)
            print(f"準備: 検証用ゲーム #{sid} を作成（最後に削除します）")

            # ---- [1] Bが圏外のあいだに、AとBが1試合ずつ入力 → Bが復帰 ----
            b.evaluate("db.goOffline()")
            enter_round(a, ["483", "267", "182"])
            enter_round(b, ["412", "301", "190"])
            b.evaluate("db.goOnline()")
            n = wait_until(lambda: len(server_rounds(sid)) >= 2 and len(server_rounds(sid)), 15000) or len(server_rounds(sid))
            b.wait_for_timeout(2000)
            n = len(server_rounds(sid))
            results.append(("[1] 圏外の端末が復帰しても、他の人の試合が消えない", 2, n))

            # ---- [2] 圏外で入力 → 送信前に再読み込み → 入力が残って送られる ----
            before = len(server_rounds(sid))
            b.evaluate("db.goOffline()")
            enter_round(b, ["395", "288", "207"])
            bar = b.evaluate("(() => { const e = document.getElementById('sync-bar'); return e && !e.hidden ? e.innerText : ''; })()")
            marks = b.evaluate("document.querySelectorAll('#rounds-table .pend-mark').length")
            results.append(("[2a] 圏外のあいだは「未送信」の帯と試合行の印が出る",
                            "帯あり・印1", f"帯{'あり' if '未送信' in bar else 'なし'}・印{marks}"))
            b.reload(wait_until="load")          # 再読み込みでメモリ上の送信待ちは消える
            wait_game(b)
            n = wait_until(lambda: len(server_rounds(sid)) >= before + 1 and len(server_rounds(sid)), 20000) or len(server_rounds(sid))
            n = len(server_rounds(sid))
            results.append(("[2b] 圏外で入力→再読み込みしても、入力が消えずに届く", before + 1, n))

            # ---- [3] 二重登録されない（自動再送を1周以上待っても件数が増えない） ----
            b.wait_for_timeout(17000)
            a.reload(wait_until="load")
            wait_game(a)
            n2 = len(server_rounds(sid))
            results.append(("[3] 再送で同じ試合が二重に登録されない", n, n2))

            # ---- [4] 設定変更の履歴（変更点つき）がサーバーに残る ----
            a.evaluate("openGameEdit()")
            a.wait_for_selector("#e-uma", state="visible", timeout=10000)
            a.select_option("#e-uma", "10-20")
            a.evaluate("saveGameEdit()")
            def last_settings_log():
                lg = as_list(server_get(sid, "/log"))
                hit = [e for e in lg if e.get("type") == "settings"]
                return hit[-1] if hit else None
            e = wait_until(last_settings_log, 15000)
            got = "、".join(e.get("changes", [])) if e else "(履歴なし)"
            results.append(("[4] 設定の変更点が履歴に残る", "ウマ: 10-30 → 10-20", got))

            # ---- [5] 設定の編集中に他の人が先に変えたら、上書きせずに知らせる ----
            a.evaluate("openGameEdit()")
            a.wait_for_selector("#e-start", state="visible", timeout=10000)
            a.fill("#e-start", "30000")             # Aは持ち点を変えようとしている（まだ保存しない）
            b.evaluate("openGameEdit()")
            b.wait_for_selector("#e-return", state="visible", timeout=10000)
            b.fill("#e-return", "35000")            # そのあいだにBが返し点を変えて保存
            b.evaluate("saveGameEdit()")
            wait_until(lambda: (server_get(sid, "/settings") or {}).get("returnPoints") == 35000, 15000)
            a.wait_for_timeout(1500)                # Aの画面にBの変更が届くのを待つ
            a.evaluate("saveGameEdit()")
            toast = a.evaluate("document.getElementById('toast').innerText")
            a.evaluate("closeFormModal()")
            a.wait_for_timeout(3000)
            st = server_get(sid, "/settings") or {}
            ok5 = st.get("startPoints") == 25000 and st.get("returnPoints") == 35000 and "他の人が設定を変更" in toast
            results.append(("[5] 編集中に他の人が設定を変えたら上書きせず知らせる", "Bの変更だけ残る・通知あり",
                            "Bの変更だけ残る・通知あり" if ok5 else f"持ち点{st.get('startPoints')}/返し点{st.get('returnPoints')}／通知:{toast[:30]!r}"))

            # ---- 後片付けの前に: 送信キューが空になっていること ----
            left_a = a.evaluate("outbox.length")
            left_b = b.evaluate("outbox.length")
            results.append(("[6] すべて送り終えて、どちらの端末にも未送信が残っていない", "0件", f"{left_a + left_b}件"))
        finally:
            if sid:
                try:
                    pg = dev_a.pages[0] if dev_a.pages else open_game(dev_a, app)
                    pg.evaluate(f"db.ref('sessions/{sid}').remove()")
                    pg.wait_for_timeout(1500)
                except Exception as ex:
                    print("削除でエラー:", ex)
                gone = server_get(sid) is None
                print(f"後片付け: 検証用ゲーム #{sid} を削除 → {'削除済み' if gone else '残っている！手動で消すこと'}")
            browser.close()
            server.shutdown()

    print()
    ok = True
    for label, expected, got in results:
        passed = expected == got
        ok &= passed
        print(f"{'PASS' if passed else 'FAIL'}  {label}（期待 {expected} / 実際 {got}）")
    print()
    print("SYNC TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
