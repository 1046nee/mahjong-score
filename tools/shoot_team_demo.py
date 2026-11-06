# -*- coding: utf-8 -*-
"""4チーム16人・20試合のチーム戦（架空の名前と数字）を本物の画面で作り、記事の画面とLPのデモを書き出す（2026-11-06〜）。
スタブの Firebase（本番に触れない）。実在の人の名前・記録は使わない。
出力: assets/team-league/*.jpg（記事の画面）／まじゃすこ素材/ig/shots/lp-live-team.html（LPのデモ。splice_lp_live.py が埋めこむ）
実行: python tools/shoot_team_demo.py
"""
import functools, http.server, io, os, random, sys, threading
MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(MJ, "tools"))
from smoke_test import FIREBASE_STUB
from account_test import AUTH_STUB
from playwright.sync_api import sync_playwright
from PIL import Image

PORT = 8798
OUT = os.path.join(MJ, "assets", "team-league")
SHOTS = os.path.join(MJ, "まじゃすこ素材", "ig", "shots")
os.makedirs(OUT, exist_ok=True)

TEAMS = [("ツモ軍団", ["健太", "美咲", "翔", "陽菜"]), ("副露キャンセル界隈", ["大輝", "結衣", "蓮", "葵"]),
         ("ニナキ", ["拓海", "彩", "悠斗", "凛"]), ("萬ジャロ", ["颯太", "真央", "湊", "紬"])]
ROUNDS = 20


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
    def handle(self):
        try: super().handle()
        except Exception: pass


def table_points(rng):
    """持ち点の合計が100,000点になる4人の点数（100点単位）"""
    a = rng.randrange(380, 620) * 100
    b = rng.randrange(260, 340) * 100
    c = rng.randrange(150, 250) * 100
    pts = [a, b, c, 100000 - a - b - c]
    rng.shuffle(pts)
    return pts


def shot(pg, name, sel=None, full=False):
    path = os.path.join(OUT, name + ".png")
    if sel:
        pg.locator(sel).first.screenshot(path=path)
    else:
        pg.screenshot(path=path, full_page=full)
    im = Image.open(path).convert("RGB")
    if im.width > 780:
        im = im.resize((780, round(im.height * 780 / im.width)), Image.LANCZOS)
    im.save(os.path.join(OUT, name + ".jpg"), quality=86, optimize=True)
    os.remove(path)
    print("shot", name, im.size)


def add_round(pg, who, pts):
    pg.evaluate("""async ([who, pts]) => { openSheet(-1); await new Promise(r => setTimeout(r, 80));
      who.forEach(i => toggleSheetMember(i)); await new Promise(r => setTimeout(r, 80));
      const ids = [...document.querySelectorAll('[id^="si-"]')].filter(e => e.offsetParent).map(e => e.id);
      ids.forEach((id, k) => { document.getElementById(id).value = String(Math.round(pts[k] / 100)); });
      if (typeof autoFill === 'function') autoFill();
      await new Promise(r => setTimeout(r, 60)); submitRound(); await new Promise(r => setTimeout(r, 160)); }""", [who, pts])


# LPのデモ: ゲーム画面のカードだけを複製する。画像・履歴・畳むボタン、仲間ページの札、名前の連携、まとめ画像などは入れない
CLONE_JS = r"""() => {
  const pick = ['#team-card', '#score-main-body', '#rounds-head', '#rank-card', '#chart-card'];
  const wrap = document.createElement('div');
  wrap.className = 'game-body lp-team-demo';
  const head = document.querySelector('#view-game .page-title-row').cloneNode(true);
  head.querySelectorAll('.title-actions').forEach(e => e.remove());
  wrap.appendChild(head);
  pick.forEach(s => { const e = document.querySelector(s); const c = e.closest('.card').cloneNode(true); wrap.appendChild(c); });
  wrap.querySelectorAll('.edit-tab, [id$="-collapse"], .collapse-btn, button').forEach(e => { if (!e.closest('.sk-seg') && !e.classList.contains('rk-toggle')) e.remove(); }); // 総合順位の11位以下の出し入れは残す（押すとLPの上でも動く）
  [wrap, ...wrap.querySelectorAll('*')].forEach(e => [...e.attributes].forEach(a => { if (/^on|^id$|^data-|^role$|^aria-|^tabindex$/.test(a.name)) e.removeAttribute(a.name); }));
  return wrap.outerHTML;
}"""


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=MJ))
    srv.handle_error = lambda *a: None
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    rng = random.Random(1616)
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, locale="ja-JP")
        ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript",
                  body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in r.request.url else "/* stub */"))
        ctx.route(lambda u: not u.startswith(f"http://127.0.0.1:{PORT}") and not u.startswith("https://www.gstatic.com/firebasejs"), lambda r: r.abort())
        pg = ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)[:160]))
        pg.goto(f"http://127.0.0.1:{PORT}/", wait_until="load")
        pg.wait_for_timeout(600)
        members = [m for _, ms in TEAMS for m in ms]
        pg.evaluate("showView('setup')")
        pg.evaluate("(a) => { setupMembers = a; renderMembers(); document.getElementById('s-name').value = 'チーム対抗リーグ戦'; }", members)
        pg.wait_for_timeout(200)
        shot(pg, "setup-members")
        pg.evaluate("setMatchType(true)")
        pg.wait_for_timeout(300)
        # 4チームに編成して、チーム名を入れる
        pg.evaluate("""(names) => { const c = teamEditorCtx; while (c.teams.length < 4) addTeam();
          c.teams.forEach((t, i) => { t.name = names[i]; t.members = [i * 4, i * 4 + 1, i * 4 + 2, i * 4 + 3]; }); renderTeamEditor(); }""", [t for t, _ in TEAMS])
        pg.wait_for_timeout(200)
        pg.evaluate("document.getElementById('s-team-fields').scrollIntoView({block:'start'}); window.scrollBy(0, -70)")
        pg.wait_for_timeout(300)
        shot(pg, "setup-teams")
        pg.evaluate("document.getElementById('s-chombo').checked = true; onChomboOptChange()")
        pg.evaluate("startGame()")
        pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=10000)
        pg.evaluate("showView('game')")
        pg.wait_for_timeout(400)
        # 点数入力の人の選び方
        pg.evaluate("openSheet(-1)")
        pg.wait_for_timeout(350)
        pg.evaluate("[0, 4, 8, 12].forEach(i => toggleSheetMember(i))")
        pg.wait_for_timeout(300)
        shot(pg, "input-pick")
        pg.evaluate("toggleSheetChombo(1)")
        pg.wait_for_timeout(200)
        pg.evaluate("document.querySelector('#pi-1').scrollIntoView({block:'center'})")
        pg.wait_for_timeout(200)
        shot(pg, "input-chombo")
        pg.evaluate("toggleSheetChombo(1)")
        pg.evaluate("[0, 4, 8, 12].forEach(i => toggleSheetMember(i)); closeSheet && closeSheet()")
        pg.wait_for_timeout(300)
        # 20試合。1卓は各チームから1人ずつ（同じチーム同士は同じ卓に入れない）
        for r in range(ROUNDS):
            who = [t * 4 + (r + t * (r // 4 + 1)) % 4 for t in range(4)]
            # 8試合目は2位と3位が同点（同点の分け方の例）
            add_round(pg, who, [45000, 25000, 25000, 5000] if r == 7 else table_points(rng))
            if r == 3:
                pg.evaluate("window.scrollTo(0, 0)")
                pg.wait_for_timeout(300)
                shot(pg, "game-early")
        pg.wait_for_timeout(500)
        pg.evaluate("window.scrollTo(0, 0)")
        pg.wait_for_timeout(300)
        print("rounds", pg.evaluate("activeGame && activeGame.rounds && activeGame.rounds.length"))
        shot(pg, "game-top")
        pg.add_style_tag(content=".fab { display: none !important; }")
        for name, sel in (("team-rank", "#team-card"), ("score", "#score-main-body"), ("rounds", "#rounds-wrap"), ("stats", "#rank-card"), ("h2h", "#mx-card"), ("chart", "#chart-card"), ("ichart", "#ichart-card")):
            vis = pg.evaluate("(s) => { const e = document.querySelector(s); return !!(e && e.offsetParent); }", sel)
            print(name, sel, vis)
            if vis:
                shot(pg, name, sel)
        html = pg.evaluate(CLONE_JS)
        io.open(os.path.join(SHOTS, "lp-live-team.html"), "w", encoding="utf-8").write(html)
        print("demo html", len(html))
        # まとめ画像の選び方
        pg.evaluate("openComposeModal(activeGame)")
        pg.wait_for_timeout(500)
        shot(pg, "compose")
        pg.evaluate("runCompose()")
        pg.wait_for_timeout(1600)
        url = pg.evaluate("(() => { const i = [...document.querySelectorAll('img')].filter(x => x.src.startsWith('data:') || x.src.startsWith('blob:')).pop(); return i ? i.src : null; })()")
        print("compose image", (url or "")[:30])
        if url:
            import base64
            data = pg.evaluate("async (u) => { const b = await (await fetch(u)).blob(); return await new Promise(r => { const f = new FileReader(); f.onload = () => r(f.result); f.readAsDataURL(b); }); }", url)
            p2 = os.path.join(OUT, "compose-result.png")
            open(p2, "wb").write(base64.b64decode(data.split(",", 1)[1]))
            im = Image.open(p2).convert("RGB")
            im = im.resize((780, round(im.height * 780 / im.width)), Image.LANCZOS)
            im.save(os.path.join(OUT, "compose-result.jpg"), quality=84, optimize=True)
            os.remove(p2)
            print("compose-result", im.size)
        print("errors", errs[:4])
        br.close()
    srv.shutdown()


if __name__ == "__main__":
    main()
