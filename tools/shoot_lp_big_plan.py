# shoot_lp_screens.py から読み込む撮影の段取り（2026-11-04）。LPの成績の節の高画質の画像。
# LP_PLAN=tools/shoot_lp_big_plan.py LP_DSF=3 python tools/shoot_lp_screens.py <circle_anon.json>
# 表は全員分を1枚に撮る（横にはみ出す所をなくしてから撮る）。出力は assets/screens/lp-hd-*.webp
from PIL import Image as _I
def save_hd(path, name, maxw=2600, q=88, cut=None):
    im = _I.open(path).convert("RGB")
    if cut: im = im.crop((0, 0, im.width, min(im.height, cut)))
    if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)), _I.LANCZOS)
    im.save(os.path.join(SITE, "lp-hd-" + name + ".webp"), quality=q, method=6)
    print("hd", name, im.size, os.path.getsize(os.path.join(SITE, "lp-hd-" + name + ".webp")) // 1024, "KB")
def eshot(sel, name, **k):
    # 画面より大きい要素は撮れないので、画面の大きさを要素に合わせてから撮る
    r = pg.evaluate("(s) => { const b = document.querySelector(s).getBoundingClientRect(); return [Math.ceil(b.width), Math.ceil(b.height)]; }", sel)
    print(name, "size", r)
    vp = pg.viewport_size
    pg.set_viewport_size({"width": max(390, r[0] + 60), "height": max(844, r[1] + 200)}) if r[0] > 400 else None
    pg.wait_for_timeout(500)
    el = pg.locator(sel).first
    el.scroll_into_view_if_needed(); pg.wait_for_timeout(400)
    path = os.path.join(OUT, "hd-" + name + ".png")
    el.screenshot(path=path)
    pg.set_viewport_size(vp)
    save_hd(path, name, **k)
def tshot(sel, name):
    """表だけを写し取って全部広げ、ほかの要素が混ざらない所で撮る（マスの大きさは画面と同じ）"""
    pg.evaluate("""(s) => { const b = document.createElement('div'); b.id = 'hd-box';
      b.style.cssText = 'position:absolute;left:0;top:0;z-index:2147483000;background:#fff';
      const t = document.querySelector(s); b.style.width = t.offsetWidth + 'px'; b.appendChild((t.closest('.stt, .tbl-scroll, .mx-scroll') || t.parentElement).cloneNode(true)); document.body.appendChild(b);
      b.querySelectorAll('*').forEach(e => { e.style.overflow = 'visible'; e.style.maxWidth = 'none'; e.style.position = 'static'; e.style.maxHeight = 'none'; if (e.tagName === 'DIV') e.style.height = 'auto'; }); return [document.querySelector(s).offsetWidth, b.offsetHeight]; }""", sel)
    eshot("#hd-box", name, maxw=3000)
    pg.evaluate("document.getElementById('hd-box').remove()")

# 2026-11-04〜: カードの縁でぴったり切らない（角の外に別の色が残る・枠が欠けるのを防ぐ）が、
# 余白は最小限（地の色の帯がカードを囲う空間に見えないように。自分の成績カードと同じく、枠＝カードそのもの）。
# カードの色つきの枠（仲間ページの色・#177083の box-shadow）は「自分の成績」のカードに無いので、
# 撮るときに消す（消さないと枠だけ色が浮いて見える）
# 2026-11-05〜: 成績表・総当たり表は横に広げず、モバイルで実際に見えるとおりの大きさ・範囲のまま撮る
# （期間の行・タブは入れずカードだけ。表は端末の横スクロールと同じく、見えている列だけでよい＝ユーザーの指定）
APP_PAD = 3
LP_META = {}  # 撮った画像の大きさ。最後に index.html の数字を書きかえる（tools/lp_hd_meta.py）
def cshot(sels, name, pad=APP_PAD, max_h=None, q=86):
    """選んだ要素を囲む四角＋地の色の余白で、画面のまま撮る（縦に長いときは max_h の所で、要素の切れ目で切る）"""
    pg.evaluate("(s) => { const e = document.querySelector(s); window.scrollTo(0, Math.max(0, e.getBoundingClientRect().top + scrollY - 40)); }", sels[0])
    pg.wait_for_timeout(300)
    r = pg.evaluate("""([ss, mh]) => { let L = 1e9, T = 1e9, R = -1e9, B = -1e9;
      ss.forEach(s => document.querySelectorAll(s).forEach(e => { const b = e.getBoundingClientRect(); L = Math.min(L, b.left); T = Math.min(T, b.top); R = Math.max(R, b.right); B = Math.max(B, b.bottom); }));
      if (mh && B - T > mh) { // 一覧の1件（カード）の下の切れ目で切る
        const cards = [...document.querySelectorAll(ss[ss.length - 1] + ' .gm-card, ' + ss[ss.length - 1] + ' .ht, ' + ss[ss.length - 1] + ' button')].map(e => e.getBoundingClientRect().bottom).filter(y => y - T <= mh);
        if (cards.length) B = Math.max(...cards); else B = T + mh; }
      return [L + scrollX, T + scrollY, R + scrollX, B + scrollY]; }""", [sels, max_h])
    L, T, R, B = max(0, r[0] - pad), max(0, r[1] - pad), min(390, r[2] + pad), r[3] + pad
    path = os.path.join(OUT, "hd-" + name + ".png")
    pg.screenshot(path=path, full_page=True, clip={"x": L, "y": T, "width": R - L, "height": B - T})
    save_hd(path, name, q=q)
pg.evaluate("setMpPeriod('all'); mpMode = 4; circleTab = 'rank'; circleMetric = 'score'; renderCircle()")
pg.wait_for_timeout(900)
# 通算順位: 指標ごとに1枚。カードの外に地の色を少し残して撮り、指標のタブの下で上下に分ける（上はLPで止めて、下だけ動かす）
for mk in ("score", "avg", "top", "las"):
    pg.evaluate(f"circleMetric = '{mk}'; renderCircle()"); pg.wait_for_timeout(700)
    pg.evaluate("""() => { const c = document.querySelector('#circle-body .rank-card'), b = [...c.querySelectorAll('button')].find(x => x.textContent.includes('通算スコア')), r = b.parentElement;
      const a = r.querySelector('.on') || b; r.scrollLeft = a.offsetLeft - (r.clientWidth - a.offsetWidth) / 2; c.style.boxShadow = 'none'; }""")
    pg.wait_for_timeout(300)
    pg.set_viewport_size({"width": 390, "height": 3000}); pg.wait_for_timeout(300)
    pg.evaluate("window.scrollTo(0, 0)")
    g = pg.evaluate("""() => { const c = document.querySelector('#circle-body .rank-card'), cb = c.getBoundingClientRect(), b = [...c.querySelectorAll('button')].find(x => x.textContent.includes('通算スコア')).parentElement.getBoundingClientRect();
      return [cb.left + scrollX, cb.top + scrollY, cb.width, cb.height, b.bottom - cb.top]; }""")
    path = os.path.join(OUT, "hd-rank.png")
    L, T = max(0, g[0] - APP_PAD), g[1] - APP_PAD
    pg.screenshot(path=path, full_page=True, clip={"x": L, "y": T, "width": min(390 - L, g[2] + APP_PAD * 2), "height": g[3] + APP_PAD * 2})
    pg.set_viewport_size({"width": 390, "height": 844})
    im = _I.open(path).convert("RGB"); d = im.width / min(390 - L, g[2] + APP_PAD * 2); y = round((g[4] + APP_PAD + 8) * d)
    im.crop((0, 0, im.width, y)).save(os.path.join(SITE, f"lp-hd-rank-{mk}-t.webp"), quality=88, method=6)
    im.crop((0, y, im.width, im.height)).save(os.path.join(SITE, f"lp-hd-rank-{mk}.webp"), quality=86, method=6); print("hd rank", mk, im.width, y, im.height - y)
    LP_META["rank"] = {"rt": round(y / im.width, 4), "w": im.width, "th": y, "bh": im.height - y}
pg.evaluate("circleMetric = 'score'; renderCircle()"); pg.wait_for_timeout(300)
pg.evaluate("circleTab = 'grid'; renderCircle()"); pg.wait_for_timeout(900)
pg.evaluate("document.querySelector('#circle-body > .card').style.boxShadow = 'none'")
cshot(["#circle-body > .card"], "grid", q=86)
pg.evaluate("circleTab = 'h2h'; renderCircle()"); pg.wait_for_timeout(900)
pg.evaluate("document.querySelector('#circle-body > .card').style.boxShadow = 'none'")
cshot(["#circle-body > .card"], "h2h", q=86)
pg.evaluate("circleTab = 'rank'; renderCircle()"); pg.wait_for_timeout(500)
pg.evaluate("(async () => { await syncCircleGamesToMine(); })()"); pg.wait_for_timeout(1500)
pg.evaluate("showView('history'); setMpPeriod('all'); mpMode = 4; setMpPane('sum'); sparkUnit = 'm'; renderHistory()"); pg.wait_for_timeout(1200)
pg.evaluate("document.querySelectorAll('.sp-pop').forEach(p => p.remove())")
# 自分の成績はLPに本物の部品のまま載せる（数字とグラフを動かすため）。押せないように属性を外して書き出す
pg.evaluate("myAv = { k: 's1', c: '#E75620' }; renderHistory()"); pg.wait_for_timeout(900)
card = pg.evaluate("""() => { const c = document.querySelector('#view-history .mc-card').cloneNode(true);
  c.querySelectorAll('.sp-pop, .sp-ring, .sp-lab').forEach(e => e.remove());
  [c, ...c.querySelectorAll('*')].forEach(e => [...e.attributes].forEach(a => { if (/^on|^id$|^data-|^role$|^aria-|^tabindex$/.test(a.name)) e.removeAttribute(a.name); }));
  return c.outerHTML; }""")
io.open(os.path.join(OUT, "lp-card.html"), "w", encoding="utf-8").write(card); print("card", len(card))
pg.evaluate("setMpPane('hist'); histView = 'tile'; renderHistoryList()"); pg.wait_for_timeout(1200)
pg.evaluate("document.querySelector('#mp-pane-hist .hist-card').style.boxShadow = 'none'")
cshot(["#mp-pane-hist .hist-card"], "games-tile", max_h=2300, q=86)
pg.evaluate("histView = 'new'; renderHistoryList()"); pg.wait_for_timeout(1200)
pg.evaluate("document.querySelector('#mp-pane-hist .hist-card').style.boxShadow = 'none'")
cshot(["#mp-pane-hist .hist-card"], "games-list", q=82)

# 撮った画像の大きさに合わせて、LPの数字（画像の縦横・止める列の位置・順位のタブの高さ）を書きかえる
gt = _I.open(os.path.join(SITE, "lp-hd-games-tile.webp")); LP_META["games-tile"] = {"w": gt.width, "h": gt.height}
gl = _I.open(os.path.join(SITE, "lp-hd-games-list.webp")); LP_META["games-list"] = {"w": gl.width, "h": gl.height}
for n in ("grid", "h2h"):
    im = _I.open(os.path.join(SITE, "lp-hd-" + n + ".webp")); LP_META[n] = {"w": im.width, "h": im.height}
import json as _json
if not os.environ.get("LP_SITE"):
    import subprocess
    subprocess.run([sys.executable, os.path.join(MJ, "tools", "lp_hd_meta.py"), _json.dumps(LP_META)], check=True)
print("meta", LP_META)
