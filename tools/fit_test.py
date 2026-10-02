# -*- coding: utf-8 -*-
"""狭い画面（320/360/390px）と大きな数字（-12,300点・+1,000超のスコア）で、数字が欠けないか・横にはみ出さないか・
見出しの左右が重ならないか・ボタンの文字が折れていないかを確かめる（マイページ・結果のシート・推移の点・仲間ページの順位とメンバー）。
スタブのFirebase（tools/smoke_test・account_test と同じ）。本番には触らない。

2026-10-02: 点数の欄の最低点数（-12,300）が欠けた・320px で期間のボタンが縦に折れた・成績カードの見出しが重なった、の再発防止。
実行: python tools/fit_test.py [画面を撮る先のフォルダ]   （フォルダを省くと撮らない）
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
from playwright.sync_api import sync_playwright  # noqa: E402

PORT = 8794
OUT = sys.argv[1] if len(sys.argv) > 1 else None


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


CHECK_JS = r"""(sel) => {
  const bad = [];
  document.querySelectorAll(sel).forEach(el => {
    if (!el.offsetParent) return;
    const r = el.getBoundingClientRect();
    if (!r.width) return;
    const box = el.closest('.mc-card, .ms-pts, .card, .sheet-body, .sp-pop, .rs-box, .podium, .lb-row, .pp-cell, .mp-col') || document.body;
    const b = box.getBoundingClientRect();
    const clipped = el.scrollWidth > el.clientWidth + 1 && getComputedStyle(el).overflow !== 'visible';
    if (r.right > b.right + 0.5 || r.left < b.left - 0.5 || clipped) bad.push(`${el.className || el.tagName}「${el.textContent.trim().slice(0, 20)}」 right=${Math.round(r.right)} box=${Math.round(b.right)}${clipped ? ' clipped' : ''}`);
  });
  const page = document.documentElement.scrollWidth > window.innerWidth + 1 ? [`ページが横にはみ出し ${document.documentElement.scrollWidth} > ${window.innerWidth}`] : [];
  // 見出しの左右が重なっていないか・期間のボタンが1行か・切り替えの文字が折れていないか
  document.querySelectorAll('.mc-head').forEach(h => { if (!h.offsetParent) return; const a = h.querySelector('b'), c = h.querySelector(':scope > span'); if (a && c && a.getBoundingClientRect().right > c.getBoundingClientRect().left + 0.5) bad.push(`mc-head が重なる「${h.textContent.trim().slice(0, 30)}」`); });
  document.querySelectorAll('.mp-period').forEach(p => { if (p.offsetParent && p.getBoundingClientRect().height > 34) bad.push(`期間のボタンが折れている（高さ ${Math.round(p.getBoundingClientRect().height)}）`); });
  document.querySelectorAll('.seg.xs button, .ch-act, .pill').forEach(b => { if (b.offsetParent && b.scrollHeight > b.clientHeight + 2) bad.push(`ボタンの文字が折れている「${b.textContent.trim()}」`); });
  return page.concat(bad);
}"""
# 数字や短い文を出す所（欠けてはいけない所）
NUM_SEL = ".mp-it b, .mp-it span, .mc-grid b, .mc-head > span, .mc-head b, .lb-val, .lb-sub, .pd-val, .pd-sub, .rs-sc, .rs-n, .sp-sc, .cc-row, .ch-act, .gm-sc, .gm-res, .pp-sub2"


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=MJ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{PORT}/"
    allbad, errors = [], []
    with sync_playwright() as p:
        br = p.chromium.launch()
        for width in (320, 360, 390):
            ctx = br.new_context(viewport={"width": width, "height": 760}, locale="ja-JP", device_scale_factor=2)
            ctx.route("https://www.gstatic.com/firebasejs/**", lambda route: route.fulfill(status=200, content_type="application/javascript",
                      body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in route.request.url else "/* stub */"))
            ctx.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}") and not url.startswith("https://www.gstatic.com/firebasejs"), lambda route: route.abort())
            pg = ctx.new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(app, wait_until="load")
            pg.wait_for_timeout(500)
            # 大きな数字の試合: 最低点数 -15,000・通算スコア +1,000超・長い名前
            pg.evaluate("showView('setup')")
            pg.evaluate("(a) => { setupMembers = a; renderMembers(); document.getElementById('s-name').value = 'とても長い名前のゲーム（大きな数字の確認）'; }",
                        ["むにぃ", "たろうたろうたろう", "じろう", "さぶろう"])
            pg.evaluate("startGame()")
            pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=10000)
            pg.evaluate("showView('game')")
            rounds = [["-123", "700", "300"]] + [["900", "100", "50"]] * 13 + [["-150", "800", "200"]]
            for pts in rounds:
                pg.evaluate("""async (pts) => { openSheet(-1); await new Promise(r => setTimeout(r, 60));
                  sheetSelected = [0, 1, 2, 3]; renderSheetMembers(); renderSheetInputs();
                  pts.forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
                  await new Promise(r => setTimeout(r, 60)); submitRound(); await new Promise(r => setTimeout(r, 250)); }""", pts)
            gid = pg.evaluate("sessionId")
            pg.evaluate("leaveGame()")
            pg.evaluate(f"setTag('{gid}', 'play', 0)")
            pg.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", "uidFIT0001")
            pg.evaluate("signInWithGoogle()")
            pg.wait_for_load_state("load")
            pg.wait_for_function("() => typeof currentUser !== 'undefined' && currentUser && !accountBusy", timeout=15000)
            pg.wait_for_timeout(500)
            pg.evaluate("showView('history'); setMpPeriod('all')")
            pg.wait_for_timeout(400)
            vals = pg.evaluate("[...document.querySelectorAll('#mp-stats .mp-it')].map(e => e.innerText.split('\\n').join(' ')).join(' / ')")
            print(f"[{width}] 点数の欄: {vals}")
            allbad += [f"[{width}] マイページ: {b}" for b in pg.evaluate(CHECK_JS, NUM_SEL)]
            if OUT:
                pg.screenshot(path=os.path.join(OUT, f"fit_{width}_mypage.png"), full_page=False)
            # 結果のシート
            pg.evaluate(f"openResultSheet('{gid}')")
            pg.wait_for_timeout(300)
            allbad += [f"[{width}] 結果のシート: {b}" for b in pg.evaluate(CHECK_JS, NUM_SEL)]
            pg.evaluate("closeFormModal()")
            # 推移の点
            pg.evaluate("document.querySelector('#mp-stats .sp-hit').dispatchEvent(new MouseEvent('click', { bubbles: true }))")
            allbad += [f"[{width}] 推移の点: {b}" for b in pg.evaluate(CHECK_JS, NUM_SEL)]
            # 仲間ページ（長い名前で作って試合を入れる）
            pg.evaluate("openCreateCircle(); document.getElementById('cc-name').value = 'とても長い名前の仲間ページ（はみ出しの確認用）'; document.getElementById('cc-me').value = 'むにぃ';")
            pg.evaluate("runCreateCircle()")
            pg.wait_for_function("() => document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=10000)
            pg.evaluate(f"openCircleAddGames(); document.querySelectorAll('.cadd-pick').forEach(el => {{ el.checked = false; }}); document.getElementById('cadd-text').value = 'https://majasco.jp/#{gid}';")
            pg.evaluate("runCircleAddGames()")
            pg.wait_for_function("() => circleData && circleData.games && Object.keys(circleData.games).length >= 1", timeout=15000)
            pg.wait_for_timeout(500)
            pg.evaluate("closeFormModal && closeFormModal()")
            for t in ["rank", "people"]:
                pg.evaluate(f"circleTab = '{t}'; renderCircle()")
                pg.wait_for_timeout(200)
                allbad += [f"[{width}] 仲間ページ {t}: {b}" for b in pg.evaluate(CHECK_JS, NUM_SEL)]
            if OUT:
                pg.screenshot(path=os.path.join(OUT, f"fit_{width}_circle.png"), full_page=True)
            ctx.close()
        br.close()
    srv.shutdown()
    print("\n".join(allbad) if allbad else "はみ出し・欠け・重なり: なし")
    if errors:
        print("PAGE ERRORS:", errors[:5])
    ok = not allbad and not errors
    print("FIT TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
