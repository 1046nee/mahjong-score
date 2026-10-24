# -*- coding: utf-8 -*-
"""試合の控え（IndexedDB）の確認。スタブで動く（本番DBに触らない）。
  [1] 古い端末（localStorage に試合）から IndexedDB へ移し替え、localStorage から外れる
  [2] 開き直しても全部ある  [3] 変更が残り、消した試合は戻らない  [4] 起動直後の保存でも減らない
  [5] 1万件を読み込め、成績に全部入る（時間も出す）  [6] 空にすると空のまま  [7] アカウントの1500件を全部取り込む
  [7b] 取り込みでは確定した試合の変更の履歴（log）を読まない（開いたときに読む）
実行: python tools/storage_test.py   （保存の仕組み・引き継ぎ・過去の試合の一覧を触ったら通す）
"""
import functools, http.server, sys, threading, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from smoke_test import FIREBASE_STUB
from account_test import AUTH_STUB
from playwright.sync_api import sync_playwright
PORT=8836
srv=http.server.ThreadingHTTPServer(("127.0.0.1",PORT),functools.partial(http.server.SimpleHTTPRequestHandler,directory=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
threading.Thread(target=srv.serve_forever,daemon=True).start()
app = f"http://127.0.0.1:{PORT}/"
C = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
GEN = """(n, prefix) => { const C = '%s'; const out = [];
  for (let i = 0; i < n; i++) { const id = prefix + C[Math.floor(i / 3025) %% 55] + C[Math.floor(i / 55) %% 55] + C[i %% 55];
    const at = new Date(Date.UTC(2020, 0, 1) + i * 3600e3).toISOString();
    const pts = [[40000, 30000, 20000, 10000], [10000, 20000, 30000, 40000]][i %% 2];
    out.push({ id, name: '試合' + i, createdAt: at, lastAccess: at, lockAt: 1, settings: { playerNames: ['むにぃ','たろう','じろう','さぶろう'], numPlayers: 4, startPoints: 25000, returnPoints: 30000, uma: [30, 10, -10, -30] },
      rounds: [{ id: 'r' + i, at, points: pts, members: [0,1,2,3], scores: i %% 2 ? [-50, -10, 10, 50] : [50, 10, -10, -50] }], log: [] }); }
  return out; }""" % C
results = []
def ok(name, cond): results.append((name, bool(cond))); print(('PASS ' if cond else 'FAIL ') + name)
with sync_playwright() as p:
    br = p.chromium.launch()
    def ctx_new():
        ctx = br.new_context(viewport={"width":390,"height":844})
        ctx.route("https://www.gstatic.com/firebasejs/**", lambda r: r.fulfill(status=200, content_type="application/javascript", body=(FIREBASE_STUB+AUTH_STUB) if "firebase-app-compat" in r.request.url else "/* stub */"))
        ctx.route(lambda u: not u.startswith(f"http://127.0.0.1:{PORT}") and not u.startswith("https://www.gstatic.com/firebasejs"), lambda r: r.abort())
        return ctx
    errs = []
    # 1) 古い端末（localStorage に試合がある）から移し替え
    ctx = ctx_new(); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(app, wait_until="load"); pg.wait_for_timeout(300)
    pg.evaluate(f"(() => {{ const games = ({GEN})(300, 'MMMMMMM'); localStorage.removeItem('mahjong-games-idb'); localStorage.setItem('mahjong-v3', JSON.stringify({{ games, players: [] }})); indexedDB.deleteDatabase('majasco'); }})()")
    pg.wait_for_timeout(300)
    pg.reload(wait_until="load"); pg.wait_for_function("() => idbState.loaded && idbState.migrated", timeout=15000); pg.wait_for_timeout(500)
    ls = pg.evaluate("JSON.parse(localStorage.getItem('mahjong-v3')).games.length")
    idbn = pg.evaluate("new Promise(r => { const q = indexedDB.open('majasco'); q.onsuccess = () => { const c = q.result.transaction('games').objectStore('games').count(); c.onsuccess = () => r(c.result); }; })")
    ok(f'[1] 移し替え: 300件が IndexedDB に入り（{idbn}）、localStorage から外れる（{ls}）', idbn == 300 and ls == 0)
    pg.reload(wait_until="load"); pg.wait_for_function("() => idbState.loaded", timeout=15000); pg.wait_for_timeout(500)
    ok('[2] 開き直しても300件ある', pg.evaluate("appState.games.length") == 300)
    # 3) 変更が残る・消したものは戻らない
    pg.evaluate("(() => { const g = appState.games[0]; appState.games[0] = { ...g, name: '名前を変えた' }; saveStorage(); })()"); pg.wait_for_timeout(400)
    gone = pg.evaluate("appState.games[1].id")
    pg.evaluate(f"(() => {{ markDeleted('{gone}'); appState.games = appState.games.filter(g => g.id !== '{gone}'); saveStorage(); }})()"); pg.wait_for_timeout(400)
    pg.reload(wait_until="load"); pg.wait_for_function("() => idbState.loaded", timeout=15000); pg.wait_for_timeout(500)
    ok('[3] 変更が残り、消した試合は戻らない', pg.evaluate("appState.games.some(g => g.name === '名前を変えた')") and not pg.evaluate(f"appState.games.some(g => g.id === '{gone}')") and pg.evaluate("appState.games.length") == 299)
    # 4) 読み込みの前に保存が走っても消えない（起動直後に saveStorage）
    pg.add_init_script("window.addEventListener('DOMContentLoaded', () => { try { saveStorage(); } catch (e) {} })")
    pg.reload(wait_until="load"); pg.wait_for_function("() => idbState.loaded", timeout=15000); pg.wait_for_timeout(600)
    ok('[4] 起動直後の保存でも試合が減らない', pg.evaluate("appState.games.length") == 299)
    ctx.close()
    # 5) 1万件: 読み込み・成績・一覧の速さ
    ctx = ctx_new(); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(app, wait_until="load"); pg.wait_for_function("() => idbState.loaded", timeout=15000)
    pg.evaluate(f"""() => new Promise(res => {{ const games = ({GEN})(10000, 'NNNNNNN'); const q = indexedDB.open('majasco'); q.onsuccess = () => {{
      const tx = q.result.transaction('games', 'readwrite'); const st = tx.objectStore('games'); games.forEach(g => st.put(g)); tx.oncomplete = () => {{ games.forEach(g => {{ gameTags[g.id] = {{ role: 'play', me: 0 }}; }}); saveTags(); localStorage.setItem('mahjong-games-idb', '1'); res(); }}; }}; }})""")
    t0 = time.time(); pg.reload(wait_until="load"); pg.wait_for_function("() => idbState.loaded && appState.games.length >= 10000", timeout=60000); t1 = time.time()
    n = pg.evaluate("appState.games.length")
    tm = pg.evaluate("(() => { setMpPeriod('all'); const a = performance.now(); const st = collectMyStats(); const b = performance.now(); showView('history'); renderHistory(); const c = performance.now(); return [Math.round(b - a), Math.round(c - b), st.modes[4].groups, st.modes[4].score]; })()")
    ok(f'[5] 1万件を読み込める（{n}件・{t1 - t0:.1f}秒）・成績に全部入る（{tm[2]}ゲーム・スコア {tm[3]}）・成績 {tm[0]}ms・マイページ {tm[1]}ms', n == 10000 and tm[2] == 10000 and abs(tm[3]) < 1e-6)
    prof = pg.evaluate('''(() => { const out = {}; const T = (k, f) => { const a = performance.now(); f(); out[k] = Math.round(performance.now() - a); };
      T('renderHistory', () => renderHistory()); T('mpStats', () => document.getElementById('mp-stats').innerHTML = mpStatsHtml(collectMyStats()));
      T('panes', () => renderMpPanes(collectMyStats())); T('histList', () => renderHistoryList()); T('circleSection', () => renderCircleSection()); return out; })()''')
    print('     内訳', prof)
    for v in ['tile', 'list', 'cal']:
        t = pg.evaluate(f"(() => {{ histView = '{v}'; const a = performance.now(); renderHistoryList(); return [Math.round(performance.now() - a), document.querySelectorAll('#history-body .gr, #history-body .ht').length]; }})()")
        print(f'     過去の試合（{v}）: {t[0]}ms・行 {t[1]}')
    # 6) ログアウトで端末の控え（IndexedDB）も空になる
    pg.evaluate("appState.games = []; saveStorage(); idbClearGames()"); pg.wait_for_timeout(800)
    pg.reload(wait_until="load"); pg.wait_for_function("() => idbState.loaded", timeout=15000); pg.wait_for_timeout(500)
    ok('[6] 空にすると開き直しても空', pg.evaluate("appState.games.length") == 0)
    ctx.close()
    # 7) アカウントから1500件を取り込む（100件ずつ）
    ctx = ctx_new(); pg = ctx.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto(app, wait_until="load"); pg.wait_for_function("() => idbState.loaded", timeout=15000)
    pg.evaluate(f"""async () => {{ const games = ({GEN})(1500, 'PPPPPPP'); const groups = {{}};
      for (const g of games) {{ await db.ref('sessions/' + g.id).set({{ ...g, lastAccess: null }}); groups[g.id] = {{ at: g.createdAt, name: g.name, role: 'play', me: 0 }}; }}
      await db.ref('mylists/LLLLLLLLLLLLLL').set({{ id: 'LLLLLLLLLLLLLL', groups }}); }}""")
    t0 = time.time()
    added = pg.evaluate("(async () => { const s = await db.ref('mylists/LLLLLLLLLLLLLL').once('value'); return await mergeMyListData(s.val()); })()")
    ok(f'[7] アカウントの1500件を全部取り込む（{added}件・{time.time() - t0:.1f}秒）・成績にも入る', added == 1500 and pg.evaluate("(setMpPeriod('all'), collectMyStats().modes[4].groups)") == 1500)
    # 7b) 取り込みは軽く: 確定した古い試合は変更の履歴（log）を読まない（_slim）。まだ確定していない新しい試合は log も読む。結果を開くと log が戻る
    r7 = pg.evaluate("""async () => { const now = Date.now(), iso = t => new Date(t).toISOString();
      const base = { settings: { playerNames: ['むにぃ','たろう','じろう','さぶろう'], numPlayers: 4, startPoints: 25000, returnPoints: 30000, uma: [30, 10, -10, -30] },
        rounds: [{ id: 'r1', at: iso(now - 9e8), points: [40000, 30000, 20000, 10000], members: [0,1,2,3], scores: [50, 10, -10, -50] }] };
      await db.ref('sessions/QQQQQQQQQ2').set({ ...base, id: 'QQQQQQQQQ2', name: '古い試合', createdAt: iso(now - 9e8), lockAt: now - 5e8, log: [{ type: 'add', at: iso(now - 9e8), no: 1 }] });
      await db.ref('sessions/QQQQQQQQQ3').set({ ...base, id: 'QQQQQQQQQ3', name: '今日の試合', createdAt: iso(now - 3600e3), lockAt: now + 8e7, log: [{ type: 'add', at: iso(now - 3600e3), no: 1 }] });
      await db.ref('mylists/MMMMMMMMMMMMMM').set({ id: 'MMMMMMMMMMMMMM', groups: { QQQQQQQQQ2: { at: iso(now - 9e8), name: '古い試合' }, QQQQQQQQQ3: { at: iso(now - 3600e3), name: '今日の試合' } } });
      const added = await mergeMyListData((await db.ref('mylists/MMMMMMMMMMMMMM').once('value')).val());
      const o = appState.games.find(g => g.id === 'QQQQQQQQQ2'), n = appState.games.find(g => g.id === 'QQQQQQQQQ3');
      const before = [added, !!o._slim, (o.log || []).length, (o.rounds || []).length, !n._slim, (n.log || []).length];
      viewDetailById('QQQQQQQQQ2'); await new Promise(r => setTimeout(r, 800));
      const o2 = appState.games.find(g => g.id === 'QQQQQQQQQ2');
      return before.concat([!(detailGame || {})._slim, ((detailGame || {}).log || []).length]); }""")
    ok(f'[7b] 確定した試合は log を読まずに取り込み（成績の中身はある）、新しい試合は log も読む。結果を開くと log が戻る {r7}', r7 == [2, True, 0, 1, True, 1, True, 1])
    ctx.close()
    ok('[8] ページのエラーなし ' + str(errs[:3]), not errs)
    br.close()
ok_all = all(c for _, c in results)
print('STORAGE TEST:', 'ALL PASS' if ok_all else 'FAILED')
sys.exit(0 if ok_all else 1)
