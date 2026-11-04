# shoot_lp_screens.py から読み込む撮影の段取り（2026-11-05〜）。
# LPの成績の節（成績表・総当たり表・通算順位・過去の試合）を、画像ではなく「自分の成績」と同じ
# 本物のHTMLの埋めこみにする。表は本物のposition:stickyのまま＝横スクロールが本当に動く。
# 出力: まじゃすこ素材/ig/shots/lp-live-*.html（1枚ずつ）＋ lp-live-meta.json（各カードの実際の幅）
import json as _json


def clone_html(sel, strip_sel=()):
    return pg.evaluate("""([sel, strip]) => {
      const c = document.querySelector(sel).cloneNode(true);
      strip.forEach(s => c.querySelectorAll(s).forEach(e => e.remove()));
      [c, ...c.querySelectorAll('*')].forEach(e => [...e.attributes].forEach(a => { if (/^on|^id$|^data-|^role$|^aria-|^tabindex$/.test(a.name)) e.removeAttribute(a.name); }));
      return c.outerHTML;
    }""", [sel, list(strip_sel)])


def native_width(sel):
    return pg.evaluate("(s) => Math.ceil(document.querySelector(s).getBoundingClientRect().width)", sel)


META = {}

pg.evaluate("setMpPeriod('all'); mpMode = 4; circleTab = 'rank'; circleMetric = 'score'; renderCircle()")
pg.wait_for_timeout(900)

# ---- 通算順位: 指標ごとに1枚（4枚）。タブは本物のボタンのまま（押すとcircleMetric切り替え）なので消さない ----
rank_htmls = {}
for mk in ("score", "avg", "top", "las"):
    pg.evaluate(f"circleMetric = '{mk}'; renderCircle()"); pg.wait_for_timeout(500)
    pg.evaluate("""() => { const c = document.querySelector('#circle-body .rank-card'), b = [...c.querySelectorAll('button')].find(x => x.textContent.includes('通算スコア')), r = b.parentElement;
      const a = r.querySelector('.on') || b; r.scrollLeft = a.offsetLeft - (r.clientWidth - a.offsetWidth) / 2; c.style.boxShadow = 'none'; }""")
    pg.wait_for_timeout(250)
    rank_htmls[mk] = clone_html("#circle-body .rank-card")
    if mk == "score":
        META["rank"] = {"w": native_width("#circle-body .rank-card")}
pg.evaluate("circleMetric = 'score'; renderCircle()"); pg.wait_for_timeout(300)
for mk, html in rank_htmls.items():
    io.open(os.path.join(OUT, f"lp-live-rank-{mk}.html"), "w", encoding="utf-8").write(html)
    print("rank", mk, len(html))

# ---- 成績表（合計のみ）----
pg.evaluate("circleTab = 'grid'; renderCircle()"); pg.wait_for_timeout(700)
pg.evaluate("document.querySelector('#circle-body > .card').style.boxShadow = 'none'")
grid_html = clone_html("#circle-body > .card")
META["grid"] = {"w": native_width("#circle-body > .card")}
io.open(os.path.join(OUT, "lp-live-grid.html"), "w", encoding="utf-8").write(grid_html)
print("grid", len(grid_html))

# ---- 総当たり表（合計のみ）----
pg.evaluate("circleTab = 'h2h'; renderCircle()"); pg.wait_for_timeout(700)
pg.evaluate("document.querySelector('#circle-body > .card').style.boxShadow = 'none'")
h2h_html = clone_html("#circle-body > .card")
META["h2h"] = {"w": native_width("#circle-body > .card")}
io.open(os.path.join(OUT, "lp-live-h2h.html"), "w", encoding="utf-8").write(h2h_html)
print("h2h", len(h2h_html))

# ---- 過去の試合（タイル・一覧）----
pg.evaluate("circleTab = 'rank'; renderCircle()"); pg.wait_for_timeout(300)
pg.evaluate("(async () => { await syncCircleGamesToMine(); })()"); pg.wait_for_timeout(1500)
pg.evaluate("showView('history'); setMpPeriod('all'); mpMode = 4; setMpPane('hist'); histView = 'tile'; renderHistoryList()"); pg.wait_for_timeout(1000)
pg.evaluate("document.querySelector('#mp-pane-hist .hist-card').style.boxShadow = 'none'")
games_tile_html = clone_html("#mp-pane-hist .hist-card")
META["games"] = {"w": native_width("#mp-pane-hist .hist-card")}
io.open(os.path.join(OUT, "lp-live-games-tile.html"), "w", encoding="utf-8").write(games_tile_html)
print("games-tile", len(games_tile_html))
pg.evaluate("histView = 'new'; renderHistoryList()"); pg.wait_for_timeout(1000)
pg.evaluate("document.querySelector('#mp-pane-hist .hist-card').style.boxShadow = 'none'")
games_list_html = clone_html("#mp-pane-hist .hist-card")
io.open(os.path.join(OUT, "lp-live-games-list.html"), "w", encoding="utf-8").write(games_list_html)
print("games-list", len(games_list_html))

# ---- 自分の成績（既存どおり）----
pg.evaluate("setMpPeriod('all'); mpMode = 4; setMpPane('sum'); sparkUnit = 'm'; renderHistory()"); pg.wait_for_timeout(1000)
pg.evaluate("document.querySelectorAll('.sp-pop').forEach(p => p.remove())")
pg.evaluate("myAv = { k: 's1', c: '#E75620' }; renderHistory()"); pg.wait_for_timeout(900)
card_html = clone_html("#view-history .mc-card", [".sp-pop", ".sp-ring", ".sp-lab"])
io.open(os.path.join(OUT, "lp-card.html"), "w", encoding="utf-8").write(card_html)
META["self"] = {"w": native_width("#view-history .mc-card")}
print("card", len(card_html))

io.open(os.path.join(OUT, "lp-live-meta.json"), "w", encoding="utf-8").write(_json.dumps(META, ensure_ascii=False, indent=2))
print("meta", META)
