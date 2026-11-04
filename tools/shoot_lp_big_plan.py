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
pg.evaluate("setMpPeriod('all'); mpMode = 4; circleTab = 'rank'; circleMetric = 'score'; renderCircle()")
pg.wait_for_timeout(900)
# 通算順位: 指標ごとに1枚。指標のタブから下を、カードと同じ縦横の比で切る
for mk in ("score", "avg", "top", "las"):
    pg.evaluate(f"circleMetric = '{mk}'; renderCircle()"); pg.wait_for_timeout(700)
    off = pg.evaluate("""() => { const c = document.querySelector('#circle-body .rank-card'), b = [...c.querySelectorAll('button')].find(x => x.textContent.includes('通算スコア')), r = b.parentElement;
      const a = r.querySelector('.on') || b; r.scrollLeft = a.offsetLeft - (r.clientWidth - a.offsetWidth) / 2; return r.getBoundingClientRect().top - c.getBoundingClientRect().top - 10; }""")
    pg.wait_for_timeout(300)
    path = os.path.join(OUT, "hd-rank.png")
    pg.locator("#circle-body .rank-card").first.screenshot(path=path)
    im = _I.open(path).convert("RGB"); d = pg.evaluate("window.devicePixelRatio"); y = int(off * d)
    sh = round(im.width * .17)  # タブの帯（LPでは上に固定して、下の順位だけ動かす）
    im.crop((0, y, im.width, y + sh)).save(os.path.join(SITE, f"lp-hd-rank-{mk}-t.webp"), quality=88, method=6)
    b = im.crop((0, y + sh, im.width, y + sh + int(880 * d)))
    b.save(os.path.join(SITE, f"lp-hd-rank-{mk}.webp"), quality=86, method=6); print("hd rank", mk, b.size)
pg.evaluate("circleMetric = 'score'; renderCircle()"); pg.wait_for_timeout(300)
pg.evaluate("circleTab = 'grid'; renderCircle()"); pg.wait_for_timeout(900)
tshot("#circle-body .card table", "grid")
pg.evaluate("circleTab = 'h2h'; renderCircle()"); pg.wait_for_timeout(900)
tshot("#circle-body .card table", "h2h")
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
eshot("#history-body", "games", cut=3 * 2300, q=82)
