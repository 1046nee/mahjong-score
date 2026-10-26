# shoot_lp_screens.py から読み込む撮影の段取り（2026-10-26 第2版）。
# スマホ1画面（390×844）をそのまま撮る＝要素を切り抜かない（切り抜くと周りに色の縁が残る・不自然、というユーザーの指摘）。
# どの画面も中身で埋まる位置までスクロールしてから撮る。期間は「すべて」・四麻
def vshot(name, sel, top=56):
    """sel の要素の上端が画面の上から top px に来るようにスクロールして、画面1枚をそのまま撮る"""
    pg.evaluate("""([s, t]) => { const e = document.querySelector(s); if (!e) return;
      const y = e.getBoundingClientRect().top + window.scrollY - t; window.scrollTo(0, Math.max(0, y)); }""", [sel, top])
    pg.wait_for_timeout(500)
    path = os.path.join(OUT, "lp-" + name + ".png")
    pg.screenshot(path=path)
    shots.append((name, path, pg.evaluate(CUT_JS, sel)))

pg.evaluate("setMpPeriod('all'); mpMode = 4; circleTab = 'rank'; circleMetric = 'score'; renderCircle()")
pg.wait_for_timeout(900)
# 通算順位：表彰台から下の順位まで
vshot("rank", "#circle-body .rank-card", 64)
# 過去の試合：ゲームのタイルがびっしり
pg.evaluate("circleTab = 'games'; renderCircle()"); pg.wait_for_timeout(1000)
vshot("games", "#circle-body .card", 64)
# 総当たり表
pg.evaluate("circleTab = 'h2h'; renderCircle()"); pg.wait_for_timeout(900)
vshot("h2h", "#circle-body .card", 64)
# メンバーの成績（シートは画面いっぱいに開くので、そのまま撮る）
pg.evaluate("circleTab = 'rank'; renderCircle()"); pg.wait_for_timeout(500)
pg.evaluate("window.scrollTo(0, 0)")
pg.evaluate("openCircleMember('HjepWbWQ')"); pg.wait_for_timeout(1200)
path = os.path.join(OUT, "lp-member.png"); pg.screenshot(path=path); shots.append(("member", path, []))
pg.evaluate("closeFormModal()"); pg.wait_for_timeout(300)
# マイページ：月ごとのグラフの点を押して、その下にその月の試合が出ているところ
pg.evaluate("(async () => { await syncCircleGamesToMine(); })()"); pg.wait_for_timeout(1500)
pg.evaluate("showView('history'); setMpPeriod('all'); mpMode = 4; setMpPane('sum'); sparkUnit = 'm'; renderHistory()"); pg.wait_for_timeout(1200)
n = pg.evaluate("document.querySelectorAll('#view-history .sp-hit').length")
best = None
for k in range(n):
    pg.evaluate(f"document.querySelectorAll('#view-history .sp-hit')[{k}].dispatchEvent(new MouseEvent('click', {{ bubbles: true }}))")
    pg.wait_for_timeout(200)
    info = pg.evaluate("""(() => { const p = document.querySelector('#view-history .sp-pop'); if (!p) return null;
      const t = (p.querySelector('.sp-sum') || {}).innerText || ''; const m = t.replace(/−/g, '-').match(/([+-][0-9,]+\\.?[0-9]*)\\s*$/);
      return { sum: m ? parseFloat(m[1].replace(/,/g, '')) : null, games: p.querySelectorAll('.sp-g').length }; })()""")
    if info and info["sum"] is not None and 2 <= info["games"] <= 3 and (best is None or info["sum"] > best[1]["sum"]):
        best = (k, info)
print("best month", best)
pg.evaluate(f"document.querySelectorAll('#view-history .sp-hit')[{best[0]}].dispatchEvent(new MouseEvent('click', {{ bubbles: true }}))")
pg.wait_for_timeout(500)
# グラフの見出しが画面の上の方に来て、その下に選んだ月の試合が並ぶ位置
pg.evaluate("""(() => { const g = document.querySelector('#view-history .sp-pop'); const card = g.closest('.mc-card') || g.parentElement;
  const graph = card.querySelector('svg') || g; const y = graph.getBoundingClientRect().top + window.scrollY - 150; window.scrollTo(0, Math.max(0, y)); })()""")
pg.wait_for_timeout(500)
path = os.path.join(OUT, "lp-mypage.png"); pg.screenshot(path=path); shots.append(("mypage", path, []))
