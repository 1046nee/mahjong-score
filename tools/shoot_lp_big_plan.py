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

# 2026-11-04〜: 周りごと撮る。カードの縁でぴったり切らない（角の外に別の色が残る・枠が欠けるのを防ぐ）。
# 画面の地の色を少し残し、期間の行やタブも入れる。横に長い表はカードの枠ごと全部広げて撮る
APP_PAD = 12
LP_META = {}  # 撮った画像の大きさ。最後に index.html の数字を書きかえる（tools/lp_hd_meta.py）
def wshot(js_parts, name, maxw=3000, col=False):
    """js_parts: 要素の並びを返すJS。複製して1つの箱に入れ、表を全部広げてから撮る。col=True なら左の列だけの細い画像（-c）も作る"""
    info = pg.evaluate("""([parts, pad]) => { const els = eval(parts).filter(e => !e.classList.contains('card') || e.querySelector('table')); const bg = getComputedStyle(els[0].closest('.view') || document.body).backgroundColor;
      // 幅は複製する前の本物で測る（複製の中で測ると、タブのボタンなどが伸びて幅が暴れる）。カード＝表の全部の幅＋（カード−表の箱）
      const oc = els.filter(e => e.querySelector('table')).pop(), otb = oc.querySelector('table'), obox = otb.closest('.stt, .tbl-scroll, .mx-scroll') || otb.parentElement;
      const w = Math.ceil(otb.scrollWidth + oc.getBoundingClientRect().width - obox.getBoundingClientRect().width);
      const b = document.createElement('div'); b.id = 'hd-box';
      b.style.cssText = `position:absolute;left:0;top:0;z-index:2147483000;background:${bg};padding:${pad}px;width:${w + pad * 2}px;box-sizing:border-box;display:flex;flex-direction:column;gap:8px`;
      els.forEach(e => b.appendChild(e.cloneNode(true))); document.body.appendChild(b);
      [...b.children].forEach(x => { x.style.width = w + 'px'; x.style.margin = '0'; x.style.boxSizing = 'border-box'; x.style.flex = 'none'; });
      b.querySelectorAll('*').forEach(x => { const cs = getComputedStyle(x); if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible') x.style.overflow = 'visible'; if (cs.maxHeight !== 'none') x.style.maxHeight = 'none'; if (cs.position === 'sticky') x.style.position = 'relative'; });
      const card = [...b.children].filter(e => e.querySelector('table')).pop(), th = card.querySelector('table tr > *:first-child'), bl = b.getBoundingClientRect().left;
      const bt = b.getBoundingClientRect().top, tt = card.querySelector('table').getBoundingClientRect();
      return { colRight: th ? th.getBoundingClientRect().right - bl : 0, boxW: b.getBoundingClientRect().width, boxH: b.getBoundingClientRect().height, tTop: tt.top - bt, tBot: tt.bottom - bt }; }""", [js_parts, APP_PAD])
    eshot("#hd-box", name, maxw=maxw)
    pg.evaluate("document.getElementById('hd-box').remove()")
    if col and info["colRight"]:
        im = _I.open(os.path.join(SITE, "lp-hd-" + name + ".webp")).convert("RGB")
        k = im.width / info["boxW"]; x = round((info["colRight"] + 1) * k)
        y0, y1 = round(info["tTop"] * k), round(info["tBot"] * k)  # 表の上から下まで（上の期間の行・タブは動かす）
        im.crop((0, y0, x, y1)).save(os.path.join(SITE, "lp-hd-" + name + "-c.webp"), quality=88, method=6)
        LP_META[name] = {"ct": round(y0 / im.height, 4), "ch": round((y1 - y0) / im.height, 4), "w": im.width, "h": im.height, "cw": x, "chh": y1 - y0}
        print("col", name, LP_META[name])
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
      const a = r.querySelector('.on') || b; r.scrollLeft = a.offsetLeft - (r.clientWidth - a.offsetWidth) / 2; }""")
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
wshot("[...document.querySelectorAll('#circle-body > .low-filt, #circle-body > .tabbar, #circle-body > .card')]", "grid", col=True)
pg.evaluate("circleTab = 'h2h'; renderCircle()"); pg.wait_for_timeout(900)
wshot("[...document.querySelectorAll('#circle-body > .low-filt, #circle-body > .tabbar, #circle-body > .card')]", "h2h", col=True)
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
pg.evaluate("setMpPane('hist'); histView = 'new'; renderHistoryList()"); pg.wait_for_timeout(1200)
cshot(["#mp-pane-filt", "#mp-pane-tabs", "#mp-pane-hist .hist-card"], "games", max_h=2300, q=82)

# 撮った画像の大きさに合わせて、LPの数字（画像の縦横・止める列の位置・順位のタブの高さ）を書きかえる
gi = _I.open(os.path.join(SITE, "lp-hd-games.webp")); LP_META["games"] = {"w": gi.width, "h": gi.height}
for n in ("grid", "h2h"):
    LP_META[n]["w"], LP_META[n]["h"] = _I.open(os.path.join(SITE, "lp-hd-" + n + ".webp")).size
import json as _json
if not os.environ.get("LP_SITE"):
    import subprocess
    subprocess.run([sys.executable, os.path.join(MJ, "tools", "lp_hd_meta.py"), _json.dumps(LP_META)], check=True)
print("meta", LP_META)
