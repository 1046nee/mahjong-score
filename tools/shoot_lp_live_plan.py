# shoot_lp_screens.py から読み込む撮影の段取り（2026-11-05〜）。
# LPの成績の節（成績表・総当たり表・通算順位・過去の試合）を、画像ではなく「自分の成績」と同じ
# 本物のHTMLの埋めこみにする。表は本物のposition:stickyのまま＝横スクロールが本当に動く。
# 成績表・総当たり表は合計/個人戦/チーム戦の3状態、通算順位は6指標、過去の試合はタイル/一覧/
# カレンダーの3状態をそれぞれ撮り、LP側でタップ・スワイプして切り替えられるようにする。
# 「画像」「個人ページに追加」「送る」ボタンは見た目だけ残っても紛らわしいので撮影時に外す。
# 出力: まじゃすこ素材/ig/shots/lp-live-*.html（1枚ずつ）＋ lp-live-meta.json（各カードの実際の幅）
import json as _json

# 「画像」ボタン（成績表・総当たり表・通算順位）／「個人ページに追加」「送る」（過去の試合）は、
# 複製からは onclick を外しているのでタップしても何も起きない＝見た目だけ残ると紛らわしいため、丸ごと外す
STRIP_IMG_BTN = [".cc-head-r"]
STRIP_HIST_BTN = [".mp-acts-r"]


def clone_html(sel, strip_sel=()):
    return pg.evaluate("""([sel, strip]) => {
      const c = document.querySelector(sel).cloneNode(true);
      strip.forEach(s => c.querySelectorAll(s).forEach(e => e.remove()));
      [c, ...c.querySelectorAll('*')].forEach(e => [...e.attributes].forEach(a => { if (/^on|^id$|^data-|^role$|^aria-|^tabindex$/.test(a.name)) e.removeAttribute(a.name); }));
      return c.outerHTML;
    }""", [sel, list(strip_sel)])


def native_width(sel):
    return pg.evaluate("(s) => Math.ceil(document.querySelector(s).getBoundingClientRect().width)", sel)


def set_kind(k):
    pg.evaluate(f"statKind = '{k}'; renderCircle()"); pg.wait_for_timeout(500)
    pg.evaluate("document.querySelector('#circle-body > .card').style.boxShadow = 'none'")


META = {}

pg.evaluate("setMpPeriod('all'); mpMode = 4; circleTab = 'rank'; circleMetric = 'score'; statKind = 'all'; renderCircle()")
pg.wait_for_timeout(900)

# ---- 通算順位: 6指標ぶん（通算スコア・平均着順・トップ率・ラス回避・最高点数・最低点数）。合計のみ ----
rank_htmls = {}
for mk in ("score", "avg", "top", "las", "pmax", "pmin"):
    pg.evaluate(f"circleMetric = '{mk}'; renderCircle()"); pg.wait_for_timeout(500)
    pg.evaluate("""() => { const c = document.querySelector('#circle-body .rank-card'), r = c.querySelector('.pill-row'), a = r && r.querySelector('.on');
      if (r && a) r.scrollLeft = a.offsetLeft - (r.clientWidth - a.offsetWidth) / 2; c.style.boxShadow = 'none'; }""")
    pg.wait_for_timeout(250)
    rank_htmls[mk] = clone_html("#circle-body .rank-card", STRIP_IMG_BTN)
    if mk == "score":
        META["rank"] = {"w": native_width("#circle-body .rank-card")}
pg.evaluate("circleMetric = 'score'; renderCircle()"); pg.wait_for_timeout(300)
for mk, html in rank_htmls.items():
    io.open(os.path.join(OUT, f"lp-live-rank-{mk}.html"), "w", encoding="utf-8").write(html)
    print("rank", mk, len(html))

# ---- 成績表（合計・個人戦・チーム戦の3状態） ----
pg.evaluate("circleTab = 'grid'; renderCircle()"); pg.wait_for_timeout(700)
grid_htmls = {}
for k in ("all", "ind", "team"):
    set_kind(k)
    grid_htmls[k] = clone_html("#circle-body > .card", STRIP_IMG_BTN)
META["grid"] = {"w": native_width("#circle-body > .card")}
pg.evaluate("statKind = 'all'; renderCircle()"); pg.wait_for_timeout(300)
for k, html in grid_htmls.items():
    io.open(os.path.join(OUT, f"lp-live-grid-{k}.html"), "w", encoding="utf-8").write(html)
    print("grid", k, len(html))

# ---- 総当たり表（合計・個人戦・チーム戦の3状態） ----
pg.evaluate("circleTab = 'h2h'; renderCircle()"); pg.wait_for_timeout(700)
h2h_htmls = {}
for k in ("all", "ind", "team"):
    set_kind(k)
    h2h_htmls[k] = clone_html("#circle-body > .card", STRIP_IMG_BTN)
META["h2h"] = {"w": native_width("#circle-body > .card")}
pg.evaluate("statKind = 'all'; renderCircle()"); pg.wait_for_timeout(300)
for k, html in h2h_htmls.items():
    io.open(os.path.join(OUT, f"lp-live-h2h-{k}.html"), "w", encoding="utf-8").write(html)
    print("h2h", k, len(html))

# ---- 過去の試合（タイル・一覧・カレンダーの3状態） ----
pg.evaluate("circleTab = 'rank'; renderCircle()"); pg.wait_for_timeout(300)
pg.evaluate("(async () => { await syncCircleGamesToMine(); })()"); pg.wait_for_timeout(1500)
pg.evaluate("showView('history'); setMpPeriod('all'); mpMode = 4; setMpPane('hist'); histView = 'tile'; renderHistoryList()"); pg.wait_for_timeout(1000)
games_htmls = {}
for hv, key in (("tile", "tile"), ("new", "list"), ("cal", "cal")):
    pg.evaluate(f"histView = '{hv}'; renderHistoryList()"); pg.wait_for_timeout(1000)
    pg.evaluate("document.querySelector('#mp-pane-hist .hist-card').style.boxShadow = 'none'")
    games_htmls[key] = clone_html("#mp-pane-hist .hist-card", STRIP_HIST_BTN)
META["games"] = {"w": native_width("#mp-pane-hist .hist-card")}
for key, html in games_htmls.items():
    io.open(os.path.join(OUT, f"lp-live-games-{key}.html"), "w", encoding="utf-8").write(html)
    print("games", key, len(html))

# ---- 自分の成績（既存どおり） ----
pg.evaluate("setMpPeriod('all'); mpMode = 4; setMpPane('sum'); sparkUnit = 'm'; renderHistory()"); pg.wait_for_timeout(1000)
pg.evaluate("document.querySelectorAll('.sp-pop').forEach(p => p.remove())")
pg.evaluate("myAv = { k: 's1', c: '#E75620' }; renderHistory()"); pg.wait_for_timeout(900)
card_html = clone_html("#view-history .mc-card", [".sp-pop", ".sp-ring", ".sp-lab"])
io.open(os.path.join(OUT, "lp-card.html"), "w", encoding="utf-8").write(card_html)
META["self"] = {"w": native_width("#view-history .mc-card")}
print("card", len(card_html))

io.open(os.path.join(OUT, "lp-live-meta.json"), "w", encoding="utf-8").write(_json.dumps(META, ensure_ascii=False, indent=2))
print("meta", META)
