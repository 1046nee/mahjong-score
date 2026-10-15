# -*- coding: utf-8 -*-
"""名前やキーに「スクリプトを動かす文字列」を入れても、ほかの人の画面で何も動かないかを確かめる（スタブのFirebase。本番に触らない）。

試合の名前・メンバーの名前・仲間ページの名前・名簿の名前・履歴のキーに、
  ・HTMLの中で <img onerror> を作る文字列（" > < で属性やタグを閉じる）
  ・onclick="f('…')" の JS の文字列を ' で閉じて命令を足す文字列
を入れて、ゲームの画面・結果のシート・過去の試合・自分の成績・仲間ページの各タブ・メンバーのシート・対戦・設定・履歴を描く。
どこかで動いたら window.__xss に印が付く。ボタンを押したときに動くもの（onclick の中）も、押して確かめる。

2026-10-15 セキュリティ点検: onclick の中に '${x}' で値を入れていた所が、値に ' があると JS を書き換えられた（jsq() に統一）。
実行: python tools/xss_test.py
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

PORT = 8796
# HTML を閉じる型と、JS の文字列を閉じる型（どちらも動けば __xss に印）
P1 = '"><img src=x onerror="__xss.push(1)">'
P2 = "');__xss.push(2);('"
P3 = "\\');__xss.push(3);//"
NAMES = [P1 + "あ", P2 + "い", P3 + "う", "</b><svg onload=__xss.push(4)>"]


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORT), functools.partial(Q, directory=MJ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    app = f"http://127.0.0.1:{PORT}/"
    errors, steps = [], []
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 390, "height": 800}, locale="ja-JP")
        ctx.add_init_script("window.__xss = [];")
        ctx.route("https://www.gstatic.com/firebasejs/**", lambda route: route.fulfill(status=200, content_type="application/javascript",
                  body=(FIREBASE_STUB + AUTH_STUB) if "firebase-app-compat" in route.request.url else "/* stub */"))
        ctx.route(lambda url: not url.startswith(f"http://127.0.0.1:{PORT}") and not url.startswith("https://www.gstatic.com/firebasejs"), lambda route: route.abort())
        pg = ctx.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("dialog", lambda d: d.dismiss())
        pg.goto(app, wait_until="load")
        pg.wait_for_timeout(500)

        def step(label, js=None, wait=250):
            if js:
                try:
                    pg.evaluate(js)
                except Exception as e:  # 画面が無い等は記録して続ける（目的は「動かないこと」）
                    errors.append(f"{label}: {str(e)[:120]}")
            pg.wait_for_timeout(wait)
            steps.append(label)

        def click_all(label, sel):
            # 押せる所を順に押して、onclick の中で動かないかを見る（画面を移るものは押したあと戻さない＝押す数は少なめ）
            n = pg.evaluate("""(sel) => { let n = 0; document.querySelectorAll(sel).forEach(el => {
              if (n >= 25 || !el.offsetParent) return; const h = el.getAttribute('onclick') || '';
              if (/delete|remove|leave|signOut|logout|confirm|closeFormModal\\(\\);(un|admin)/i.test(h)) return;
              try { el.click(); n++; } catch (e) {} }); return n; }""", sel)
            pg.wait_for_timeout(200)
            steps.append(f"{label}（{n}か所を押した）")

        # ゲームを作る（名前に仕掛け）
        step("ゲームを作る", "showView('setup')")
        pg.evaluate("(a) => { setupMembers = a; renderMembers(); }", NAMES)
        pg.evaluate("(n) => { document.getElementById('s-name').value = n; }", P1 + P2 + "試合")
        step("開始", "startGame()", 400)
        pg.wait_for_function("() => document.querySelector('#view-share').classList.contains('active')", timeout=10000)
        step("ゲームの画面", "showView('game')")
        for pts in (["300", "100", "-200"], ["-100", "200", "50"]):
            pg.evaluate("""async (pts) => { openSheet(-1); await new Promise(r => setTimeout(r, 60));
              sheetSelected = [0, 1, 2, 3]; renderSheetMembers(); renderSheetInputs();
              pts.forEach((v, i) => { document.getElementById('si-' + i).value = v; }); autoFill();
              await new Promise(r => setTimeout(r, 60)); submitRound(); await new Promise(r => setTimeout(r, 250)); }""", pts)
        step("ゲームの画面（点数あり）", "renderGame()")
        click_all("ゲームの画面のボタン", "#view-game [onclick]")
        step("閉じる", "closeFormModal && closeFormModal()")
        step("入力の履歴", "showLogModal('game')")
        step("閉じる", "closeFormModal()")
        gid = pg.evaluate("sessionId")
        step("ゲームを出る", "leaveGame()")
        pg.evaluate(f"setTag('{gid}', 'play', 0)")
        step("結果のシート", f"openResultSheet('{gid}')")
        click_all("結果のシートのボタン", "#form-modal-body [onclick]")
        step("閉じる", "closeFormModal()")
        step("過去の試合のメニュー", f"openHistMenu('{gid}')")
        step("閉じる", "closeFormModal()")
        step("タグ", f"openTagEditor('{gid}')")
        step("閉じる", "closeFormModal()")

        # ログインして自分の成績・仲間ページ
        pg.evaluate("(u) => localStorage.setItem('__smoke_next_uid', u)", "uidXSS00001")
        pg.evaluate("signInWithGoogle()")
        pg.wait_for_load_state("load")
        pg.wait_for_function("() => typeof currentUser !== 'undefined' && currentUser && !accountBusy", timeout=15000)
        pg.wait_for_timeout(500)
        step("マイページ", "showView('history'); setMpPeriod('all')", 400)
        click_all("マイページのボタン", "#view-history [onclick]")
        step("閉じる", "closeFormModal && closeFormModal(); showView('history')")
        step("自分の成績", "showView('mystats'); renderMyStats()", 400)
        pg.evaluate("(n) => { openCreateCircle(); document.getElementById('cc-name').value = n; document.getElementById('cc-me').value = n; }", P2 + P1 + "仲間")
        step("仲間ページを作る", "runCreateCircle()", 400)
        pg.wait_for_function("() => document.querySelector('#view-circle').classList.contains('active') && circleData", timeout=10000)
        step("試合を選ぶ", "openCircleAddGames()", 400)
        pg.evaluate("document.querySelectorAll('.cadd-pick').forEach(el => { el.checked = true; })")
        step("試合を追加", "runCircleAddGames()", 400)
        try:
            pg.wait_for_function("() => circleData && circleData.games && Object.keys(circleData.games).length >= 1", timeout=15000)
        except Exception:
            print("試合を追加できなかった:", errors[-3:], steps[-4:])
            print(pg.evaluate("[document.querySelector('.view.active') && document.querySelector('.view.active').id, (document.getElementById('form-modal-body') || {}).innerText, (document.getElementById('toast') || {}).textContent].map(x => String(x).slice(0, 300))"))
            raise
        step("閉じる", "closeFormModal && closeFormModal()", 400)
        # 履歴のキーに仕掛け（ルールでは弾くが、画面でも動かないこと）
        pg.evaluate("""(k) => db.ref('circles/' + circleId + '/log/' + k).set({ at: new Date().toISOString(), by: myUid(), byName: 'x', kind: 'add_game', text: 'x', undo: { sid: Object.keys(circleData.games)[0] } })""", "k');__xss.push(5);('")
        step("最新にする", "refreshCircle()", 600)
        for t in ["rank", "grid", "h2h", "games", "people"]:
            step(f"仲間ページ {t}", f"circleTab = '{t}'; renderCircle()")
            click_all(f"仲間ページ {t} のボタン", "#circle-body [onclick]")
            step("閉じる", "closeFormModal && closeFormModal(); showView('circle'); renderCircle()")
        mids = pg.evaluate("Object.keys((circleData && circleData.roster) || {})")
        for mid in mids[:4]:
            step(f"メンバー {mid}", f"openCircleMember('{mid}')")
            click_all("メンバーのシートのボタン", "#form-modal-body [onclick]")
            step("閉じる", "closeFormModal()")
        if len(mids) >= 2:
            step("対戦", f"openCircleMatchup(['{mids[0]}','{mids[1]}'])", 400)
            click_all("対戦のボタン", "#form-modal-body [onclick]")
            step("閉じる", "closeFormModal()")
        step("設定", "openCircleSettings()")
        step("閉じる", "closeFormModal()")
        step("共有", "openCircleShare()")
        step("閉じる", "closeFormModal()")
        step("試合のメニュー", f"openCircleGameMenu('{gid}')")
        step("閉じる", "closeFormModal()")
        step("連携", f"openBindEditor('{gid}')")
        step("閉じる", "closeFormModal()")

        hits = pg.evaluate("window.__xss")
        bad_dom = pg.evaluate("document.querySelectorAll('img[src=\"x\"], svg[onload]').length")
        ctx.close()
        br.close()
    srv.shutdown()
    print("通った画面:", len(steps))
    ignorable = [e for e in errors if "__xss" not in e]
    if ignorable:
        print("（参考）途中のエラー:", ignorable[:6])
    ok = not hits and not bad_dom and not any("__xss" in e for e in errors)
    if not ok:
        print("動いた印:", hits, " 仕掛けの要素:", bad_dom)
    print("XSS TEST:", "ALL PASS" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
