# -*- coding: utf-8 -*-
# LPの「1分でわかるまじゃすこの使い方」4ステップ用の操作デモ動画を録画する（2026-11-05〜）。
# はじめる→何人で打つか選ぶ→共有してコピー→点数入力→結果がリアルタイムに反映、を1本で録り、
# 4つの場面の境目の時間を記録して、あとで tools/split_howto_demo.py が切り出す。
# record_app_demo.py と同じ「ローカル起動＋Firebaseスタブ」方式（本番に触れない）。
import functools
import http.server
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from record_app_demo import FIREBASE_STUB, TAP_FX, find_chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig", "video")
os.makedirs(OUTDIR, exist_ok=True)

PORT = 8815
VIEW_W, VIEW_H = 390, 844


def record():
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=BASE)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()

    marks = {}
    t0 = None

    def mark(name):
        marks[name] = round(time.time() - t0, 2)
        print(f"  mark {name} = {marks[name]}s")

    with sync_playwright() as p:
        exe = find_chromium()
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": VIEW_W, "height": VIEW_H}, locale="ja-JP",
            is_mobile=True, has_touch=True,
            record_video_dir=OUTDIR, record_video_size={"width": VIEW_W, "height": VIEW_H},
        )
        ctx.grant_permissions(["clipboard-read", "clipboard-write"])  # コピーが失敗すると生のURLがトーストに出てしまうため
        ctx.add_init_script(TAP_FX)
        t0 = time.time()  # 動画の録画はページ生成の瞬間から始まるので、ここを0秒とする
        page = ctx.new_page()

        def route_firebase(route):
            body = FIREBASE_STUB if "firebase-app-compat" in route.request.url else "/* stub */"
            route.fulfill(status=200, content_type="application/javascript", body=body)

        page.route("https://www.gstatic.com/firebasejs/**", route_firebase)
        page.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}")
                   and not url.startswith("https://www.gstatic.com/firebasejs"),
                   lambda route: route.abort())

        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=30000)
        page.wait_for_timeout(900)
        mark("start")

        # ---- 1. 人数を選ぶ ----
        page.click("#view-home .cta-btn")
        page.wait_for_timeout(700)
        page.click(".qs-4")
        page.wait_for_selector("#view-game.active", timeout=10000)
        page.wait_for_timeout(1000)
        mark("step1_end")

        # ---- 2. URLをメンバーにシェアする ----
        page.click("button:has-text('共有')")
        page.wait_for_selector("#share-sheet-url", state="visible", timeout=10000)
        page.wait_for_timeout(500)
        page.evaluate("""() => {
            const el = document.getElementById('share-sheet-url');
            if (el) el.value = el.value.replace(/^https?:\\/\\/[^/]+/, 'https://majasco.jp');
        }""")
        page.wait_for_timeout(300)
        page.click(".sh-url button")
        page.wait_for_timeout(1100)  # コピーのトーストを見せる
        page.click(".sheet-close")
        page.wait_for_selector("#form-modal", state="hidden", timeout=10000)
        page.wait_for_timeout(400)
        mark("step2_end")

        # ---- 3. 試合後に表示点数を入力する（1試合目はゆっくり） ----
        def enter_round(vals, delay, pause):
            page.click(".fab")
            page.wait_for_selector("#si-0", state="visible", timeout=10000)
            page.wait_for_timeout(pause)
            for i, val in enumerate(vals):
                page.click(f"#si-{i}")
                page.locator(f"#si-{i}").press_sequentially(val, delay=delay)
                page.wait_for_timeout(pause // 2)
            # 録画中はCPU負荷で入力が取りこぼされることがあるので、足りなければ埋め直す
            for i, val in enumerate(vals):
                cur = page.locator(f"#si-{i}").input_value()
                if cur != val:
                    page.locator(f"#si-{i}").fill(val)
                    page.wait_for_timeout(120)
            page.wait_for_selector("#auto-btn:not([disabled])", timeout=10000)
            page.click("#auto-btn")
            page.wait_for_timeout(pause)
            page.click("#confirm-btn")
            page.wait_for_selector("#score-main-body .score-card", state="visible", timeout=10000)

        enter_round(["483", "267", "182"], delay=110, pause=350)
        page.wait_for_timeout(1300)  # 総合順位が動くのを見せる
        mark("step3_end")

        # ---- 4. 結果はリアルタイムで全員に（2・3試合目は素早く入力） ----
        enter_round(["312", "356", "204"], delay=55, pause=150)
        page.wait_for_timeout(400)
        enter_round(["421", "89", "276"], delay=55, pause=150)
        page.wait_for_timeout(900)

        def smooth_scroll_to(selector, offset=90, wait=1400):
            page.evaluate("""([sel, off]) => {
                const el = document.querySelector(sel);
                if (el) window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - off, behavior: 'smooth' });
            }""", [selector, offset])
            page.wait_for_timeout(wait)

        smooth_scroll_to("#score-main-body", 90, 1200)
        smooth_scroll_to("#rank-card", 70, 1600)
        smooth_scroll_to("#chart-card", 70, 2200)
        page.wait_for_timeout(600)
        mark("step4_end")

        video = page.video
        ctx.close()
        raw_webm = video.path()
        browser.close()
    server.shutdown()
    return raw_webm, marks


def main():
    raw_webm, marks = record()
    marks_path = os.path.join(OUTDIR, "howto-marks.json")
    json.dump(marks, open(marks_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("saved:", raw_webm)
    print("saved:", marks_path)
    print("marks:", marks)


if __name__ == "__main__":
    main()
