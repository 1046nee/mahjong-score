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

    def swipe(self, dy, dur=0.8, steps=12, x=250, y=620):
        """指で上へなぞってスクロール（dy>0で下の内容へ）。指の下のスクロールできる所が動く（シートの中も）"""
        self.move_to(x, y, 0.35)
        t = self.now()
        ey = y - max(-380, min(380, dy * 0.7))
        self.moves.append([round(t, 3), round(t + dur, 3), x, y, x, ey])
        self.pg.mouse.move(x, y)
        for k in range(steps):
            self.pg.mouse.wheel(0, dy / steps)
            self.cap()
        self.pos = (x, ey)
        self.idle(0.2)

    def hswipe(self, sel, dx, steps=12):
        """横にスクロールできる表を、指で左へなぞる"""
        b = self.pg.locator(sel).first.bounding_box()
        x, y = round(b["x"] + b["width"] * 0.75), round(b["y"] + min(b["height"] / 2, 300))
        y = max(120, min(760, y))
        self.move_to(x, y, 0.35)
        t = self.now()
        ex = x - max(-220, min(220, dx * 0.6))
        self.moves.append([round(t, 3), round(t + 0.9, 3), x, y, ex, y])
        self.pg.mouse.move(x, y)
        for k in range(steps):
            self.pg.mouse.wheel(dx / steps, 0)
            self.cap()
        self.pos = (ex, y)
        self.idle(0.2)

    def scroll_to(self, sel, top=64):
        """録画の前に、要素が画面の上から top px に来るようにしておく（指は出さない）"""
        self.pg.evaluate("""([s, t]) => { const e = document.querySelector(s); if (!e) return;
          window.scrollTo(0, Math.max(0, e.getBoundingClientRect().top + window.scrollY - t)); }""", [sel, top])
        self.pg.wait_for_timeout(300)

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

def explore(pg):
    """押せるところを一覧で出す（台本を書くとき用）: python tools/record_play.py explore --data <json>"""
    J = r"""(root) => [...document.querySelectorAll(root + ' [onclick]')].filter(e => e.offsetParent)
      .map(e => e.tagName + '.' + String(e.className || '').split(' ').join('.') + ' | ' + e.getAttribute('onclick').slice(0, 60) + ' | ' + e.textContent.trim().replace(/\s+/g, ' ').slice(0, 20))
      .filter((v, i, a) => a.indexOf(v) === i).slice(0, 90)"""
    for tab in ["h2h", "games", "people"]:
        pg.evaluate(f"circleTab='{tab}';renderCircle()"); pg.wait_for_timeout(800)
        print("== circle", tab); [print(x) for x in pg.evaluate(J, "#circle-body")[:25]]
    pg.evaluate("circleTab='rank';renderCircle()"); pg.wait_for_timeout(600)
    pg.evaluate("openCircleMember('HjepWbWQ')"); pg.wait_for_timeout(1200)
    print("== member sheet"); [print(x) for x in pg.evaluate(J, "body")[-30:]]
    pg.evaluate("closeFormModal()"); pg.wait_for_timeout(400)
    pg.evaluate("showView('history')"); pg.wait_for_timeout(1500)
    for pane in ["h2h", "hist"]:
        pg.evaluate(f"setMpPane('{pane}')"); pg.wait_for_timeout(900)
        print("== history", pane); [print(x) for x in pg.evaluate(J, "#view-history")[-25:]]
    print("sp-hit", pg.evaluate("document.querySelectorAll('#view-history .sp-hit').length"))

PLAYS = {"play-quick": play_quick, "play-rounds": play_rounds}
def ctab(k):
    return f"#view-circle button[onclick^=\"circleTab='{k}'\"]"

# 横にスクロールできる表（成績表・総当たり表）。見つからなければ表そのもの
HTABLE = "#circle-body .tbl-scroll"

def nakama_rank(pg):
    """仲間ページ：表彰台と、並べかえ（通算スコア→平均着順→トップ率→ラス回避）"""
    r = Rec(pg, "nakama-rank")
    r.scroll_to("#circle-body .rank-card", 64)
    r.idle(1.4); r.mark("podium")
    for k in ["avg", "top", "las"]:
        r.mark(k)
        r.tap(f"#circle-body button[onclick=\"shiftCircleMetricTo('{k}')\"]", after=1.6)
    r.mark("score")
    r.tap("#circle-body button[onclick=\"shiftCircleMetricTo('score')\"]", after=0.6)
    r.mark("list")
    r.swipe(420, dur=1.0)
    r.idle(1.4)
    r.save()

def nakama_grid(pg):
    """仲間ページ：成績表（縦にも横にも）"""
    r = Rec(pg, "nakama-grid")
    r.scroll_to(ctab("rank"), 150)
    r.idle(0.8); r.mark("tab")
    r.tap(ctab("grid"), after=1.2); r.mark("grid")
    r.swipe(300, dur=0.9)
    r.idle(0.6); r.mark("side")
    r.hswipe(HTABLE, 600)
    r.idle(1.0)
    r.hswipe(HTABLE, 600)
    r.idle(1.4)
    r.save()

def nakama_h2h(pg):
    """仲間ページ：総当たり表"""
    r = Rec(pg, "nakama-h2h")
    r.scroll_to(ctab("rank"), 150)
    r.idle(0.8); r.mark("tab")
    r.tap(ctab("h2h"), after=1.4); r.mark("h2h")
    r.swipe(260, dur=0.9)
    r.idle(1.0); r.mark("side")
    r.hswipe(HTABLE, 500)
    r.idle(1.6)
    r.save()

def nakama_member(pg):
    """仲間ページ：メンバーを押すと、その人の成績・推移・相手ごとの勝ち負け"""
    r = Rec(pg, "nakama-member")
    r.scroll_to("#circle-body .rank-card", 64)
    r.idle(1.0); r.mark("tap")
    r.tap("#circle-body .pd.p1", after=1.4); r.mark("sheet")
    r.swipe(520, dur=1.0, y=650)
    r.idle(1.2); r.mark("h2h")
    r.swipe(620, dur=1.0, y=650)
    r.idle(1.2); r.mark("vs")
    r.tap(".hg-card.tap", after=1.8)
    r.save()

def nakama_games(pg):
    """仲間ページ：過去の試合 → 1つ押すと、その日の結果"""
    r = Rec(pg, "nakama-games")
    r.scroll_to(ctab("rank"), 150)
    r.idle(0.8); r.mark("tab")
    r.tap(ctab("games"), after=1.0); r.mark("games")
    r.tap("#circle-body button[onclick^=\"circleGamesView='list'\"]", after=1.0); r.mark("list")
    r.swipe(240, dur=0.8)
    r.idle(0.6); r.mark("open")
    r.tap("#circle-body [onclick*=\"openResultSheet('F37uyBTV9d'\"]", after=1.6); r.mark("result")
    r.swipe(420, dur=1.0, y=650)
    r.idle(1.4)
    r.save()

def to_mypage(r):
    r.pg.evaluate("window.scrollTo(0, 0)")
    r.idle(0.8)
    r.tap("#view-circle .sw-chip.me", after=1.2)

def mypage_stats(pg):
    """マイページ：仲間ページから自分の成績へ。平均着順・トップ率・着順の割合・推移"""
    r = Rec(pg, "mypage-stats")
    r.mark("chip")
    to_mypage(r); r.mark("top")
    r.swipe(260, dur=0.9)
    r.idle(1.4); r.mark("graph")
    r.swipe(260, dur=0.9)
    r.idle(1.6)
    r.save()

def mypage_graph(pg):
    """マイページ：推移のグラフの月を押すと、その月の試合が並ぶ"""
    r = Rec(pg, "mypage-graph")
    to_mypage(r)
    r.scroll_to("#view-history .sp-hit", 330)
    r.idle(0.6); r.mark("month")
    r.tap("#view-history button[onclick*=\"setSparkUnit('m'\"]", after=1.0); r.mark("pick")
    n = pg.evaluate("document.querySelectorAll('#view-history .sp-hit').length")
    r.tap(f"#view-history .sp-hit >> nth={n - 1}", after=1.4); r.mark("pop")
    r.swipe(300, dur=0.9)
    r.idle(1.6)
    r.save()

def mypage_h2h(pg):
    """マイページ：対戦成績（相手ごとの勝ち負け）→ 勝率順 → 1人押す"""
    r = Rec(pg, "mypage-h2h")
    to_mypage(r)
    r.scroll_to("#view-history button[onclick=\"setMpPane('h2h')\"]", 160)
    r.mark("tab")
    r.tap("#view-history button[onclick=\"setMpPane('h2h')\"]", after=1.2); r.mark("h2h")
    r.swipe(260, dur=0.9)
    r.idle(0.6); r.mark("pct")
    r.tap("#view-history button[onclick^=\"h2hSort='pct'\"]", after=1.4); r.mark("vs")
    r.tap("#view-history .hg-card.tap", after=1.8)
    r.save()

def mypage_hist(pg):
    """マイページ：過去の試合の一覧 → 1つ押すと結果"""
    r = Rec(pg, "mypage-hist")
    to_mypage(r)
    r.scroll_to("#view-history button[onclick=\"setMpPane('hist')\"]", 160)
    r.mark("tab")
    r.tap("#view-history button[onclick=\"setMpPane('hist')\"]", after=1.0); r.mark("hist")
    r.tap("#view-history button[onclick^=\"histView='new'\"]", after=1.2); r.mark("list")
    r.swipe(320, dur=0.9)
    r.idle(0.6); r.mark("open")
    r.tap("#view-history [onclick=\"openResultSheet('F37uyBTV9d')\"]", after=1.8); r.mark("result")
    r.swipe(380, dur=1.0, y=650)
    r.idle(1.2)
    r.save()

def mypage_sanma(pg):
    """マイページ：三麻と四麻は分けて記録（押すと色も数字も切りかわる）"""
    r = Rec(pg, "mypage-sanma")
    to_mypage(r); r.mark("yonma")
    r.idle(0.6); r.mark("tap3")
    r.tap("#view-history button[onclick=\"mpMode=3;renderHistory()\"]", after=2.2); r.mark("sanma")
    r.swipe(240, dur=0.9)
    r.idle(1.0)
    r.swipe(-240, dur=0.9)
    r.mark("back")
    r.tap("#view-history button[onclick=\"mpMode=4;renderHistory()\"]", after=1.6)
    r.save()

CIRCLE_PLAYS = {"explore": explore, "nakama-rank": nakama_rank, "nakama-grid": nakama_grid, "nakama-h2h": nakama_h2h,
                "nakama-member": nakama_member, "nakama-games": nakama_games, "mypage-stats": mypage_stats,
                "mypage-graph": mypage_graph, "mypage-h2h": mypage_h2h, "mypage-hist": mypage_hist, "mypage-sanma": mypage_sanma}



class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def circle_seed(path):
    """shoot_lp_screens.py と同じ見本のデータ（実際の仲間ページの数字・名前は置きかえ済み。リポジトリに入れない）"""
    import re
    d = json.load(io.open(path, encoding="utf-8"))
    circle = d["circle"]
    def short(n):
        m = re.match(r"^\d{4}\.\d{2}\.\d{2}（(.)）", n or "")
        if m: return m.group(1) + "曜の麻雀"
        # 大会の名前には元の仲間の名前が入っているので、一般的な名前にする（2026-10-27）
        if n and "リーグ" in n: return "夏のリーグ戦"
        if n and ("トーナメント" in n or "大会" in n): return "秋の大会"
        return n
    for v in list(d["sessions"].values()) + list(circle.get("games", {}).values()):
        if v.get("name"): v["name"] = short(v["name"])
    store = {"sessions": d["sessions"], "circles": {circle["id"]: circle},
             "users": {UID: {"circles": {circle["id"]: {"at": circle.get("createdAt"), "name": circle["name"]}}}}}
    seed = ("if (!localStorage.getItem('__seeded')) { localStorage.setItem('__smoke_db', " + json.dumps(json.dumps(store, ensure_ascii=False))
            + "); localStorage.setItem('__seeded', '1'); }")
    return seed, circle["id"]

UID = "uidSHOT01"


def open_page(br, seed=None, cid=None):
    ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP")
    ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript",
              body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in r.request.url else ""))
    ctx.route(lambda u: not u.startswith(f"http://127.0.0.1:{PORT}") and "gstatic" not in u, lambda r: r.abort())
    if seed:
        ctx.add_init_script(seed)
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(f"http://127.0.0.1:{PORT}/")
    pg.wait_for_function("() => typeof signInWithGoogle === 'function' && typeof openQuickStart === 'function'", timeout=20000)
    pg.wait_for_timeout(900)
    if cid:
        pg.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", UID)
        pg.evaluate("signInWithGoogle()")
        pg.wait_for_load_state("load")
        pg.wait_for_function("() => typeof currentUser !== 'undefined' && currentUser && !accountBusy", timeout=20000)
        pg.wait_for_timeout(800)
        pg.evaluate("(async () => { await syncCircleGamesToMine(); })()")  # マイページにも仲間ページの試合を入れる
        pg.wait_for_timeout(1500)
    pg.add_style_tag(content="#toast, .toast { display: none !important; } * { caret-color: #177083; }")
    pg.evaluate("shareUrlOf = id => 'https://majasco.jp/#' + id")
    return ctx, pg, errs


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = args[0] if args else ""
    data = sys.argv[sys.argv.index("--data") + 1] if "--data" in sys.argv else None
    if data in args: args.remove(data); only = args[0] if args else ""
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=MJ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    with sync_playwright() as p:
        br = p.chromium.launch()
        jobs = [(n, f, False) for n, f in PLAYS.items()] + [(n, f, True) for n, f in CIRCLE_PLAYS.items()]
        for name, fn, needs in jobs:
            if (only and only not in name) or (not only and name == "explore"):
                continue
            if needs and not data:
                print("skip", name, "（--data <circle_anon.json> が要る）"); continue
            seed, cid = circle_seed(data) if needs else (None, None)
            ctx, pg, errs = open_page(br, seed, cid)
            if cid:
                pg.evaluate(f"openCircle('{cid}')")
                pg.wait_for_function("() => document.querySelector('#view-circle').classList.contains('active') && circleData && Object.keys(circleSess || {}).length > 50", timeout=30000)
                pg.wait_for_timeout(1200)
                pg.evaluate("window.scrollTo(0, 0)")
            fn(pg)
            if errs:
                print("  errors:", errs)
            ctx.close()
        br.close()
    srv.shutdown()

if __name__ == "__main__":
    main()
