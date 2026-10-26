# shoot_lp_screens.py から読み込む撮影の段取り（どの画面をどの順に撮るか）。期間は「すべて」・四麻
def clip(sel, name, maxh):
    """長い要素は上から maxh（CSS px）だけ撮る"""
    el = pg.locator(sel).first
    el.scroll_into_view_if_needed()
    pg.evaluate("(s) => { const e = document.querySelector(s); window.scrollTo(0, e.getBoundingClientRect().top + scrollY - 8); }", sel)
    pg.wait_for_timeout(350)
    b = pg.evaluate("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height}; }", sel)
    h = min(b["h"], maxh)
    pg.set_viewport_size({"width": 390, "height": int(max(844, h + 40))})
    pg.wait_for_timeout(200)
    b = pg.evaluate("(s) => { const r = document.querySelector(s).getBoundingClientRect(); return {x: r.left, y: r.top, w: r.width, h: r.height}; }", sel)
    path = os.path.join(OUT, "lp-" + name + ".png")
    pg.screenshot(path=path, clip={"x": b["x"], "y": b["y"], "width": b["w"], "height": min(b["h"], maxh)})
    pg.set_viewport_size({"width": 390, "height": 844})
    shots.append((name, path, pg.evaluate(CUT_JS, sel)))

# 横にスクロールする並び（指標のボタン）は、撮るときだけ折り返して全部見せる（右端で文字が切れないように）
pg.add_style_tag(content="#circle-body [onclick*=shiftCircleMetricTo] { flex-shrink: 0; } ")
pg.evaluate("""() => { const b = document.querySelector("#circle-body [onclick*=shiftCircleMetricTo]"); if (b) window.__chipRowCls = b.parentElement.className; }""")
pg.evaluate("setMpPeriod('all'); mpMode = 4; circleTab = 'rank'; circleMetric = 'score'; renderCircle()")
pg.wait_for_timeout(900)
row = pg.evaluate("(() => { const b = document.querySelector('#circle-body [onclick*=shiftCircleMetricTo]'); return b ? b.parentElement.className : ''; })()")
if row:
    pg.add_style_tag(content="." + row.split()[0] + " { flex-wrap: wrap !important; overflow: visible !important; }")
    pg.wait_for_timeout(200)
# 通算順位：表彰台と4〜7位のカードまで（カードの途中で切らない）
cut = pg.evaluate("""(() => { const card = document.querySelector('#circle-body .rank-card'); const top = card.getBoundingClientRect().top;
  const items = [...card.querySelectorAll('[onclick^=openCircleMember]')]; const it = items[5] || items[items.length - 1];
  return Math.round(it.getBoundingClientRect().bottom - top + 3); })()""")
clip("#circle-body .rank-card", "rank", cut)
pg.evaluate("circleTab = 'h2h'; renderCircle()"); pg.wait_for_timeout(800)
# 総当たり表は相手4人ぶんの列だけ見せる（右の列が途中で切れないように）
pg.add_style_tag(content="#circle-body .card table th:nth-child(n+6), #circle-body .card table td:nth-child(n+6) { display: none !important; } #circle-body .card table { width: 100% !important; min-width: 0 !important; }")
pg.wait_for_timeout(300)
cut = pg.evaluate("""(() => { const card = document.querySelector('#circle-body .card'); const top = card.getBoundingClientRect().top;
  const rows = [...card.querySelectorAll('tbody tr')]; const r = rows[Math.min(6, rows.length - 1)]; return Math.round(r.getBoundingClientRect().bottom - top + 1); })()""")
clip("#circle-body .card", "h2h", cut)
pg.evaluate("circleTab = 'rank'; renderCircle()"); pg.wait_for_timeout(500)
pg.evaluate("openCircleMember('HjepWbWQ')"); pg.wait_for_timeout(900)
clip("#form-modal .form-modal-box", "member", 760)
pg.evaluate("closeFormModal()"); pg.wait_for_timeout(300)
# マイページ（仲間ページの試合を自分の過去の試合に入れてから）
pg.evaluate("(async () => { await syncCircleGamesToMine(); })()"); pg.wait_for_timeout(1500)
pg.evaluate("showView('history'); setMpPeriod('all'); mpMode = 4; renderHistory()"); pg.wait_for_timeout(1200)
shot("#view-history .mc-card", "mypage")
# グラフを月ごとにして、点を押すと出る「その月の試合」（勝った月・ゲームが2つ以上の月を選ぶ）
pg.evaluate("setMpPane('sum'); sparkUnit = 'm'; renderHistory()"); pg.wait_for_timeout(1000)
n = pg.evaluate("document.querySelectorAll('#view-history .sp-hit').length")
best = None
for k in range(n):
    pg.evaluate(f"document.querySelectorAll('#view-history .sp-hit')[{k}].dispatchEvent(new MouseEvent('click', {{ bubbles: true }}))")
    pg.wait_for_timeout(250)
    info = pg.evaluate("""(() => { const p = document.querySelector('#view-history .sp-pop'); if (!p) return null;
      const t = (p.querySelector('.sp-sum') || {}).innerText || ''; const m = t.replace(/−/g, '-').match(/([+-][0-9,]+\.?[0-9]*)\s*$/);
      return { sum: m ? parseFloat(m[1].replace(/,/g, '')) : null, games: p.querySelectorAll('.sp-g').length, h: p.offsetHeight, t: t.replace(/\s+/g, ' ') }; })()""")
    if info and info["sum"] is not None and 2 <= info["games"] <= 3 and info["h"] < 900 and (best is None or info["sum"] > best[1]["sum"]):
        best = (k, info)
print("best month", best)
if best:
    pg.evaluate(f"document.querySelectorAll('#view-history .sp-hit')[{best[0]}].dispatchEvent(new MouseEvent('click', {{ bubbles: true }}))")
    pg.wait_for_timeout(400)
    b = pg.evaluate("(() => { const p = document.querySelector('#view-history .sp-pop'); p.scrollIntoView({block: 'center'}); return 1; })()")
    pg.wait_for_timeout(300)
    b = pg.evaluate("(() => { const p = document.querySelector('#view-history .sp-pop'); const tag = p.querySelector('.sp-tag'); const r = p.getBoundingClientRect(); const t = tag.getBoundingClientRect(); const top = Math.min(r.top, t.top) - 4; return {x: r.left - 4, y: top, w: r.width + 8, h: r.bottom - top + 6}; })()")
    path = os.path.join(OUT, "lp-month.png")
    pg.screenshot(path=path, clip={"x": b["x"], "y": b["y"], "width": b["w"], "height": b["h"]})
    shots.append(("month", path, pg.evaluate(CUT_JS, "#view-history .sp-pop")))
