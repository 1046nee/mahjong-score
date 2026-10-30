# -*- coding: utf-8 -*-
"""牌の絵・数字のはみ出しと重なりを全ページで調べる（2026-10-30〜・ユーザーの指摘「イラストと数字のはみ出し・被りが多い。しっかり確認して」）。
幅 360・390・768・1100px で、
  1. 表のセルの中の絵が、セルの外にはみ出していないか
  2. 牌の絵が、入れ物（図・カード・セル・リストの1行）の外にはみ出していないか
  3. 同じ並びの牌の絵どうしが重なっていないか（横向きの牌・点棒・チップのわざと重ねる絵は除く）
  4. 表のセルの文字（数字）がセルの外にはみ出していないか
を調べる。見つかったら 1 で終わる。図や表を足したら必ず通す。
実行: python tools/overlap_check.py            （blog-*.html と主なページ）
      python tools/overlap_check.py blog-xxx.html
"""
import functools, glob, http.server, os, socketserver, sys, threading
from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WIDTHS = (360, 390, 768, 1100)
JS = r"""() => {
  const out = [];
  const R = e => e.getBoundingClientRect();
  const name = e => (e.closest('figure[id], table, .fg-card, section[id]') || {}).id || (e.closest('table') ? 'table.' + (e.closest('table').className || '') : '');
  const vis = e => { const r = R(e); return r.width > 1 && r.height > 1 && getComputedStyle(e).visibility !== 'hidden'; };
  const tiles = [...document.querySelectorAll('img[src*="/assets/tiles/"]')].filter(vis)
    .filter(i => !/\/(tb|ct|chip|tenbo|chicha|yakitori|dice|d\d|taku|sidetable|oshibori|oolong|haiyose)/.test(i.getAttribute('src')));
  // 1・2: 入れ物からのはみ出し
  for (const im of [...document.querySelectorAll('.blog-post img, main img, .lp img')].filter(vis)) {
    const box = im.closest('td, th, .fg-card, .kq, .rj-t, .tc-c, .se, .yl-yaku, .hs-card, .kw, .ai-c, figure');
    if (!box || box.classList.contains('eyecatch')) continue;
    const a = R(im), b = R(box);
    const o = Math.max(b.left - a.left, a.right - b.right, b.top - a.top, a.bottom - b.bottom);
    // 横にスクロールする入れ物の中は、スクロールで見えるので除く
    let sc = im.parentElement, scroll = false;
    while (sc && sc !== box) { const s = getComputedStyle(sc); if (/(auto|scroll)/.test(s.overflowX) && sc.scrollWidth > sc.clientWidth) { scroll = true; break; } sc = sc.parentElement; }
    if (o > 1 && !scroll) out.push(['はみ出し', name(im), im.getAttribute('src').split('/').pop(), o.toFixed(1)]);
  }
  // 3: 牌どうしの重なり（同じ親の中）
  const byParent = new Map();
  for (const t of tiles) { const p = t.parentElement; if (!byParent.has(p)) byParent.set(p, []); byParent.get(p).push(t); }
  for (const [p, ts] of byParent) for (let i = 1; i < ts.length; i++) {
    const a = R(ts[i - 1]), b = R(ts[i]);
    const ox = Math.min(a.right, b.right) - Math.max(a.left, b.left), oy = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
    if (ox > 1.5 && oy > 1.5) out.push(['牌の重なり', name(ts[i]), ts[i].getAttribute('src').split('/').pop(), ox.toFixed(1)]);
  }
  // 4: セルの文字のはみ出し
  for (const c of document.querySelectorAll('.blog-post td, .blog-post th')) {
    if (!vis(c)) continue;
    if (c.scrollWidth > c.clientWidth + 2 && getComputedStyle(c).overflowX === 'visible')
      out.push(['文字のはみ出し', name(c), (c.textContent || '').trim().slice(0, 14), (c.scrollWidth - c.clientWidth).toFixed(0)]);
  }
  return out;
}"""


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    files = sys.argv[1:] or sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, "blog-*.html"))) + ["index.html", "score-basics.html", "about.html"]
    srv = socketserver.TCPServer(("127.0.0.1", 0), functools.partial(Q, directory=ROOT))
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    bad = 0
    with sync_playwright() as p:
        br = p.chromium.launch()
        for w in WIDTHS:
            pg = br.new_page(viewport={"width": w, "height": 900})
            pg.route("**/*", lambda r: r.abort() if any(h in r.request.url for h in ("googlesyndication", "googletagmanager", "gstatic.com/firebasejs", "youtube.com", "twitter.com", "x.com/")) else r.continue_())
            for f in files:
                if not os.path.exists(os.path.join(ROOT, f)):
                    continue
                pg.goto(f"http://127.0.0.1:{port}/{f}", wait_until="load")
                pg.evaluate("() => document.querySelectorAll('details').forEach(d => d.open = true)")
                pg.wait_for_timeout(150)
                seen = set()
                for kind, where, what, px in pg.evaluate(JS):
                    key = (kind, where, what)
                    if key in seen:
                        continue
                    seen.add(key)
                    bad += 1
                    print(f"NG {w}px {f} {kind} [{where}] {what} {px}px")
            pg.close()
        br.close()
    srv.shutdown()
    print("OK" if not bad else f"{bad} 件")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
