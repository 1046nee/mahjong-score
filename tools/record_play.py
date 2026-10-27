# -*- coding: utf-8 -*-
"""ショート動画用に、アプリを実際に操作している画面を撮る（2026-10-27〜）。
スタブの Firebase（本番に触れない）で index.html を開き、台本どおりにタップ・入力しながら、画面を何度も撮る。
指の位置・タップの時刻は timeline.json に書き出すだけで、画面には描かない（指とタップの波紋は make_short.py が
30コマ/秒でなめらかに重ねる）。

出力: まじゃすこ素材/video/clips/<名前>/f00001.jpg … と timeline.json
  timeline.json = { "frames": [[秒, ファイル名], …], "moves": [[開始秒, 終了秒, x0, y0, x1, y1], …],
                    "taps": [[秒, x, y], …], "marks": { "名前": 秒 }, "end": 秒 }
  座標はアプリの画面の CSS px（幅390×高さ844）
使い方: python tools/record_play.py [名前]   （省略で全部）
"""
import sys, os, io, json, time, shutil, functools, threading, http.server
MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(MJ, "tools"))
from smoke_test import FIREBASE_STUB
from account_test import AUTH_STUB
from playwright.sync_api import sync_playwright

CLIPS = os.path.join(MJ, "まじゃすこ素材", "video", "clips")
PORT = 8811
NAMES = ["健太", "美咲", "翔", "陽菜"]


class Rec:
    """操作しながら画面を撮る。frames には撮った時刻（録画を始めてからの秒）を付ける"""
    def __init__(self, pg, name):
        self.pg, self.dir = pg, os.path.join(CLIPS, name)
        shutil.rmtree(self.dir, ignore_errors=True)
        os.makedirs(self.dir)
        self.frames, self.moves, self.taps, self.marks = [], [], [], {}
        self.pos = (300, 900)  # 指は画面の下の外から入ってくる
        self.t0 = time.perf_counter()

    def now(self):
        return time.perf_counter() - self.t0

    def cap(self):
        t = self.now()
        fn = f"f{len(self.frames) + 1:05d}.jpg"
        io.open(os.path.join(self.dir, fn), "wb").write(self.pg.screenshot(type="jpeg", quality=88))
        self.frames.append([round(t, 3), fn])

    def idle(self, sec):
        end = self.now() + sec
        self.cap()
        while self.now() < end:
            self.cap()

    def mark(self, name):
        self.marks[name] = round(self.now(), 3)

    def move_to(self, x, y, dur=0.45):
        t = self.now()
        self.moves.append([round(t, 3), round(t + dur, 3), self.pos[0], self.pos[1], x, y])
        self.pos = (x, y)
        self.idle(dur + 0.05)

    def tap(self, sel, dur=0.45, after=0.3):
        loc = self.pg.locator(sel).first
        loc.scroll_into_view_if_needed()
        b = loc.bounding_box()
        x, y = round(b["x"] + b["width"] / 2), round(b["y"] + b["height"] / 2)
        self.move_to(x, y, dur)
        self.taps.append([round(self.now(), 3), x, y])
        loc.click()
        self.idle(after)

    def type(self, sel, text, gap=0.16):
        self.tap(sel, after=0.15)
        for ch in text:
            self.pg.keyboard.type(ch)
            self.idle(gap)

    def swipe(self, dy, dur=0.8, steps=12):
        """指で上へなぞってスクロール（dy>0で下の内容へ）"""
        x, y = 250, 600
        self.move_to(x, y, 0.35)
        t = self.now()
        self.moves.append([round(t, 3), round(t + dur, 3), x, y, x, y - min(dy, 400)])
        for k in range(steps):
            self.pg.evaluate(f"window.scrollBy(0, {dy / steps})")
            self.cap()
        self.pos = (x, y - min(dy, 400))
        self.idle(0.2)

    def save(self):
        self.idle(0.3)
        json.dump({"frames": self.frames, "moves": self.moves, "taps": self.taps, "marks": self.marks, "end": round(self.now(), 3)},
                  io.open(os.path.join(self.dir, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False)
        print("ok", os.path.basename(self.dir), len(self.frames), "frames", f"{self.now():.1f}s",
              f"{len(self.frames) / self.now():.1f}fps")


# ---------------- 台本（操作） ----------------
def play_quick(pg):
    """LP →「はじめる」→ 4人 → 点数を3人ぶん入れて最後の1人は自動 → 総合順位 → 共有"""
    r = Rec(pg, "play-quick")
    r.idle(0.8)
    r.mark("lp")
    r.tap("#view-home .hero .cta-btn")
    r.mark("qs")
    r.idle(0.7)
    r.tap(".qs-btn.qs-4", after=0.1)
    pg.wait_for_function("() => typeof sessionId !== 'undefined' && sessionId")
    # 仮の名前 A〜D を見本の名前にする（ゲームの設定を変えたのと同じ）
    pg.evaluate("(n) => firebase.database().ref('sessions/' + sessionId + '/settings/playerNames').set(n)", NAMES)
    r.idle(1.0)
    r.mark("game")
    r.tap(".fab", after=0.5)
    r.mark("input")
    for i, v in enumerate(["452", "281", "173"]):
        r.type(f"#si-{i}", v)
    r.idle(0.3)
    r.mark("auto")
    r.tap("#auto-btn", after=0.7)
    r.tap("#confirm-btn", after=0.2)
    r.mark("done")
    r.idle(2.2)
    r.mark("share")
    r.tap("#view-game .title-edit-btn", after=1.8)
    r.save()

def play_rounds(pg):
    """何試合か入れたあとの成績を、指でスクロールして見せる"""
    r = Rec(pg, "play-rounds")
    pg.evaluate("openQuickStart()")
    pg.evaluate("quickStart(4)")
    pg.wait_for_function("() => typeof sessionId !== 'undefined' && sessionId")
    pg.evaluate("(n) => firebase.database().ref('sessions/' + sessionId + '/settings/playerNames').set(n)", NAMES)
    pg.wait_for_timeout(500)
    for pts in [[452, 281, 173, 94], [198, 336, 245, 221], [377, 122, 289, 212]]:
        pg.evaluate("""async (pts) => { openSheet(-1); await new Promise(r => setTimeout(r, 120));
          pts.forEach((v, i) => { document.getElementById('si-' + i).value = String(v); }); autoFill();
          await new Promise(r => setTimeout(r, 80)); submitRound(); await new Promise(r => setTimeout(r, 250)); }""", pts)
    pg.evaluate("window.scrollTo(0, 0)")
    pg.wait_for_timeout(400)
    r.idle(0.6)
    r.mark("input")
    r.tap(".fab", after=0.4)
    # 4試合目は美咲が大きなトップ・健太がラス → 総合順位で美咲が逆転する（字幕「逆転」と合わせる）
    for i, v in enumerate(["80", "520", "260"]):
        r.type(f"#si-{i}", v, gap=0.12)
    r.tap("#auto-btn", after=0.5)
    r.tap("#confirm-btn", after=0.2)
    r.mark("done")
    r.idle(1.6)
    r.mark("scroll")
    r.swipe(520, dur=1.0)
    r.idle(1.4)
    r.swipe(520, dur=1.0)
    r.idle(1.6)
    r.save()

PLAYS = {"play-quick": play_quick, "play-rounds": play_rounds}


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=MJ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        br = p.chromium.launch()
        for name, fn in PLAYS.items():
            if only and only not in name:
                continue
            ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP")
            ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript",
                      body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in r.request.url else ""))
            ctx.route(lambda u: not u.startswith(f"http://127.0.0.1:{PORT}") and "gstatic" not in u, lambda r: r.abort())
            pg = ctx.new_page()
            errs = []
            pg.on("pageerror", lambda e: errs.append(str(e)))
            pg.goto(f"http://127.0.0.1:{PORT}/")
            pg.wait_for_timeout(900)
            pg.add_style_tag(content="#toast, .toast { display: none !important; } * { caret-color: #177083; }")
            pg.evaluate("shareUrlOf = id => 'https://majasco.jp/#' + id")
            fn(pg)
            if errs:
                print("  errors:", errs)
            ctx.close()
        br.close()
    srv.shutdown()

if __name__ == "__main__":
    main()
