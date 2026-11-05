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
VIEW_W, VIEW_H = 390, 792  # LPのスマホの枠の中と同じ縦横（高いと下が切れて、右下の点数入力のボタンが枠から出る）

# LINEのアプリは録れないので、送り先を選んで送るところを見本の画面で見せる（本物の画面ではない）
LINE_MOCK = r"""
window.demoLine = {
  open() {
    if (document.getElementById('dl')) return; // タップが2回届いても1枚だけ
    const css = `#dl{position:fixed;inset:0;z-index:9000;background:#fff;font-family:inherit;color:#1F2A28;display:flex;flex-direction:column}
      #dl .h{display:flex;align-items:center;justify-content:space-between;height:52px;padding:0 14px;border-bottom:1px solid #E3E9E8;font-size:16px;font-weight:800}
      #dl .h span{color:#8A9694;font-size:14px;font-weight:700} #dl .h b.on{color:#06C755}
      #dl .q{margin:10px 12px;padding:9px 12px;border-radius:10px;background:#F1F3F3;color:#8A9694;font-size:13px}
      #dl .l{padding:8px 14px 4px;font-size:12px;font-weight:800;color:#8A9694}
      #dl .r{display:flex;align-items:center;gap:12px;padding:9px 14px;font-size:15px;font-weight:700}
      #dl .r i{width:44px;height:44px;border-radius:50%;display:grid;place-items:center;color:#fff;font-style:normal;font-weight:800}
      #dl .r em{margin-left:auto;width:24px;height:24px;border-radius:50%;border:2px solid #C3CECB;display:grid;place-items:center;color:#fff;font-style:normal;font-size:14px}
      #dl .r.on em{background:#06C755;border-color:#06C755}
      #dl .t{flex:1;background:#8CABD8;padding:14px 12px;display:flex;flex-direction:column;align-items:flex-end;gap:6px}
      #dl .m{max-width:80%;padding:10px 12px;border-radius:14px;background:#A8E06C;font-size:14px;line-height:1.55;word-break:break-all}
      #dl .y{align-self:flex-start;display:flex;align-items:flex-start;gap:8px;animation:dlin .25s ease both} #dl .y i{flex:none;width:34px;height:34px;border-radius:50%;display:grid;place-items:center;color:#fff;font-style:normal;font-size:13px;font-weight:800}
      #dl .y small{display:block;margin-bottom:2px;font-size:11px;color:#fff} #dl .y .m{background:#fff}
      #dl .y img{display:block;width:74px;height:auto;filter:drop-shadow(0 3px 5px rgba(0,0,0,.25))} #dl .y em{display:block;margin-top:3px;padding:1px 8px;border-radius:9px;background:#E75620;color:#fff;font-style:normal;font-size:13px;font-weight:800;text-align:center}
      @keyframes dlin{from{opacity:0;transform:translateY(10px) scale(.96)}to{opacity:1;transform:none}}`;
    const st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
    const d = document.createElement('div'); d.id = 'dl';
    d.innerHTML = `<div class="h"><span>キャンセル</span>送信先を選択<b id="dl-send">送信</b></div><div class="q">検索</div><div class="l">グループ</div>
      <div class="r" id="dl-g"><i style="background:#177083">麻</i>麻雀グループ（4）<em>✓</em></div><div class="r"><i style="background:#8A9694">大</i>大学の友だち（6）<em></em></div>
      <div class="l">友だち</div><div class="r"><i style="background:#C07A22">さ</i>さとし<em></em></div><div class="r"><i style="background:#4261AA">ゆ</i>ゆうた<em></em></div><div class="r"><i style="background:#5FA3A6">け</i>けんじ<em></em></div>`;
    document.body.appendChild(d);
    document.getElementById('dl-g').onclick = e => { e.currentTarget.classList.add('on'); document.getElementById('dl-send').classList.add('on'); };
    document.getElementById('dl-send').onclick = () => { d.innerHTML = '<div class="h">麻雀グループ（4）</div><div class="t"><div class="m">今日のスコアはここから見られます<br>https://majasco.jp/#L7Nv5rXUS</div></div>'; };
  },
  // 仲間からの返信。スタンプはサイトの牌の絵（LINEのスタンプは使わない）
  reply(name, color, html) { const y = document.createElement('div'); y.className = 'y'; y.innerHTML = `<i style="background:${color}">${name.slice(0, 1)}</i><div><small>${name}</small>${html}</div>`; document.querySelector('#dl .t').appendChild(y); },
  close() { const d = document.getElementById('dl'); if (d) d.remove(); },
};
"""


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
        ctx.add_init_script(LINE_MOCK)
        page = ctx.new_page()
        t0 = time.time()  # 動画はページができてから始まる。ページを作る前を0秒にすると、切れ目が約1秒ずれて次の画面が映りこむ

        def route_firebase(route):
            body = FIREBASE_STUB if "firebase-app-compat" in route.request.url else "/* stub */"
            route.fulfill(status=200, content_type="application/javascript", body=body)

        page.route("https://www.gstatic.com/firebasejs/**", route_firebase)
        page.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}")
                   and not url.startswith("https://www.gstatic.com/firebasejs"),
                   lambda route: route.abort())

        page.goto(f"http://127.0.0.1:{PORT}/index.html", wait_until="load", timeout=30000)
        # 共有の画面に出すURLは本番のものに（録画のローカルのアドレスを映さない）
        page.evaluate("window.shareUrlOf = id => 'https://majasco.jp/#' + id")
        page.wait_for_timeout(300)
        mark("start")
        page.wait_for_timeout(1500)  # LPの最初の画面を見せる

        # ---- 1. 人数を選ぶ ----
        page.click("#view-home .cta-btn")
        page.wait_for_timeout(700)
        page.click(".qs-4")
        page.wait_for_selector("#view-game.active", timeout=10000)
        page.wait_for_timeout(1000)
        mark("step1_end")
        page.wait_for_timeout(350)

        # ---- 2. URLをメンバーにシェアする ----
        page.click("#view-game button:has-text('共有')")
        page.wait_for_selector("#share-sheet-url", state="visible", timeout=10000)
        page.wait_for_timeout(800)
        page.click(".sh-url button")
        page.wait_for_timeout(1100)  # コピーのトーストを見せる
        # 「LINEで送る」→ 麻雀グループを選ぶ → 送信（アプリの代わりに見本の画面）
        def demo_tap(sel):  # 見本の画面は固定の重ね表示で、スマホの再現では page.click の当たり判定がずれるので、波紋を出して直接押す
            page.evaluate("""(s) => { const e = document.querySelector(s), r = e.getBoundingClientRect();
                document.dispatchEvent(new PointerEvent('pointerdown', { clientX: r.left + r.width / 2, clientY: r.top + r.height / 2, bubbles: true })); e.click(); }""", sel)

        page.evaluate("window.shareLine = () => setTimeout(() => demoLine.open(), 450)")
        page.click(".sh-btns .line")
        page.wait_for_selector("#dl-g", timeout=5000)
        page.wait_for_timeout(800)
        demo_tap("#dl-g")
        page.wait_for_timeout(700)
        demo_tap("#dl-send")
        page.wait_for_timeout(900)
        page.evaluate("""demoLine.reply('ゆうた', '#4261AA', '<div class="m">ありがとう！見れた</div>')""")
        page.wait_for_timeout(800)
        page.evaluate("""demoLine.reply('さとし', '#C07A22', '<img src="/assets/tiles/z7.svg" alt=""><em>了解！</em>')""")
        page.wait_for_timeout(800)
        page.evaluate("""demoLine.reply('けんじ', '#5FA3A6', '<div class="m">点数の入力もできるね</div>')""")
        page.wait_for_timeout(1400)
        mark("step2_end")  # 2は仲間の返信で終わる。まじゃすこの画面には戻らない
        page.wait_for_timeout(700)
        page.evaluate("demoLine.close()")
        page.wait_for_timeout(250)
        page.click(".sheet-close")
        page.wait_for_selector("#form-modal", state="hidden", timeout=10000)
        page.wait_for_timeout(700)
        mark("step3_start")  # 3は1の最後と同じゲームの画面から
        page.wait_for_timeout(1300)

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
            page.wait_for_timeout(pause * 2)  # オレンジに光るのを見せる
            page.click("#auto-btn")
            page.wait_for_timeout(pause)
            page.click("#confirm-btn")
            page.wait_for_selector("#score-main-body .score-card", state="visible", timeout=10000)

        enter_round(["483", "267", "182"], delay=110, pause=350)
        page.wait_for_timeout(1300)  # 総合順位が動くのを見せる
        mark("step3_end")
        page.wait_for_timeout(700)  # 切れ目に次の点数入力が映らないように

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
