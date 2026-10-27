# -*- coding: utf-8 -*-
"""絵（SVG）に埋め込んだ文字・数字が、枠からはみ出したり重なったりしていないかを調べる（2026-10-27〜）。

SVG の <text> は見る人の端末の書体で描かれるので、書体によって幅が変わり、マスや丸からはみ出すことがある
（点数早見表の記事の絵で「1,000」「7,700」がマスの幅いっぱい・はみ出しになっていた）。
iPhone のヒラギノに近い Noto Sans JP（Google Fonts）を読み込んだ状態で、次を見つける:
  - 文字が、それを囲む四角（<rect>）・丸（<circle>）の内側に余白 PAD をとって収まっていない
  - 文字が絵（viewBox）の外にはみ出している
  - 2つの文字が重なっている
調べるもの: assets/thumbs・assets/art・assets 直下の SVG ファイルと、記事・LP・固定ページの中に直接書いた SVG。
使い方: python tools/svg_text_check.py   （1件でも見つかれば終了コード1）
        python tools/svg_text_check.py --pad 3 assets/thumbs/blog-score-table.svg   （ファイルを指定）
        python tools/svg_text_check.py score-basics.html   （ページの中の絵だけ）
"""
import functools
import glob
import http.server
import os
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8831
FONT_CSS = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;800;900&display=block" rel="stylesheet">'

# 書体を確実に読み込んでから測る（SVG の中の文字だけだと、読み込みが始まる前に測ってしまうことがある）
LOAD_JS = "Promise.all([400, 500, 700, 800, 900].map(w => document.fonts.load(w + ' 16px \\'Noto Sans JP\\'', '0123456789,.+-翻符満貫跳倍役東南西北白發中あア漢'))).then(() => document.fonts.ready)"

CHECK_JS = r"""
(pad) => {
  const out = [];
  // 位置はすべて画面の上の位置（拡大・縮小した絵でも同じ物差し）。余白 pad は絵の座標の単位なので、絵の拡大率をかける
  const box = el => { const b = el.getBoundingClientRect(); return { x0: b.left, y0: b.top, x1: b.right, y1: b.bottom }; };
  document.querySelectorAll('svg').forEach((svg, si) => {
    if (svg.closest('svg') !== svg && svg.parentElement.closest('svg')) return; // 入れ子のSVGは外側でまとめて見る
    const label = svg.getAttribute('data-src') || ('svg#' + si + (svg.closest('[class]') ? ' in .' + svg.closest('[class]').className.toString().split(' ')[0] : ''));
    const sr = svg.getBoundingClientRect();
    if (sr.width < 2) return;
    const vbw = svg.viewBox && svg.viewBox.baseVal && svg.viewBox.baseVal.width ? svg.viewBox.baseVal.width : sr.width;
    const k = sr.width / vbw, P = pad * k;
    const vb = { x: sr.left, y: sr.top }, vw = sr.width, vh = sr.height;
    const texts = [...svg.querySelectorAll('text')].filter(t => t.textContent.trim() && getComputedStyle(t).display !== 'none' && t.getAttribute('opacity') !== '0');
    if (!texts.length) return;
    const rects = [...svg.querySelectorAll('rect')].map(r => ({ r, b: box(r), rx: parseFloat(r.getAttribute('rx') || 0) })).filter(o => o.b.x1 - o.b.x0 > 4 && o.b.y1 - o.b.y0 > 4);
    const circles = [...svg.querySelectorAll('circle')].map(c => { const b = box(c); return { b, cx: (b.x0 + b.x1) / 2, cy: (b.y0 + b.y1) / 2, r: (b.x1 - b.x0) / 2 }; }).filter(o => o.r > 3);
    const tb = texts.map(t => ({ t, b: box(t) }));
    // 線（<line>）で区切ったマス: 縦の線・横の線
    const lines = [...svg.querySelectorAll('line')].map(l => box(l));
    const vlines = lines.filter(l => l.x1 - l.x0 < 3 && l.y1 - l.y0 > 6), hlines = lines.filter(l => l.y1 - l.y0 < 3 && l.x1 - l.x0 > 6);
    // 縦の線だけ（年表の目盛りなど）はマスではない。縦と横の両方の線があるときだけマスの壁として使う
    if (!hlines.length) vlines.length = 0;
    tb.forEach(({ t, b }) => {
      const txt = t.textContent.trim().slice(0, 20), cx = (b.x0 + b.x1) / 2, cy = (b.y0 + b.y1) / 2, area = (b.x1 - b.x0) * (b.y1 - b.y0);
      if (b.x0 < vb.x - 0.5 || b.y0 < vb.y - 0.5 || b.x1 > vb.x + vw + 0.5 || b.y1 > vb.y + vh + 0.5) out.push([label, txt, '絵の外にはみ出し']);
      // 囲む四角: 文字の真ん中を含み、文字より大きく、絵全体の背景ではないもののうち一番小さいもの
      const inR = rects.filter(o => o.b.x0 <= cx && cx <= o.b.x1 && o.b.y0 <= cy && cy <= o.b.y1 && (o.b.x1 - o.b.x0) * (o.b.y1 - o.b.y0) > area * 0.9
        && !(o.b.x1 - o.b.x0 >= vw * 0.95 && o.b.y1 - o.b.y0 >= vh * 0.95));
      inR.sort((p, q) => (p.b.x1 - p.b.x0) * (p.b.y1 - p.b.y0) - (q.b.x1 - q.b.x0) * (q.b.y1 - q.b.y0));
      let r = inR[0];
      // 縦の線で区切ったマスなら、文字のすぐ左右の線をマスの壁とする
      const vl = vlines.filter(l => l.y0 <= cy && cy <= l.y1), lft = vl.filter(l => (l.x0 + l.x1) / 2 < cx), rgt = vl.filter(l => (l.x0 + l.x1) / 2 > cx);
      if (lft.length || rgt.length) {
        const L = lft.length ? Math.max(...lft.map(l => (l.x0 + l.x1) / 2)) : (r ? r.b.x0 : vb.x), R = rgt.length ? Math.min(...rgt.map(l => (l.x0 + l.x1) / 2)) : (r ? r.b.x1 : vb.x + vw);
        r = { b: { x0: Math.max(L, r ? r.b.x0 : L), x1: Math.min(R, r ? r.b.x1 : R), y0: r ? r.b.y0 : 0, y1: r ? r.b.y1 : 0 } };
      }
      const inC = circles.filter(c => Math.hypot(c.cx - cx, c.cy - cy) < c.r * 0.6 && c.r * 2 > Math.min(b.x1 - b.x0, b.y1 - b.y0)).sort((p, q) => p.r - q.r)[0];
      if (r && inC && Math.PI * inC.r * inC.r < (r.b.x1 - r.b.x0) * (r.b.y1 - r.b.y0)) r = null;
      if (r) {
        const lx = b.x0 - r.b.x0, rx = r.b.x1 - b.x1;
        if (lx < P || rx < P) out.push([label, txt, `四角の左右の余白が足りない（左${(lx / k).toFixed(1)}・右${(rx / k).toFixed(1)}）`]);
      }
      if (inC && !r) {
        // 字の箱の左右の端（縦の真ん中）が丸の内側か
        const far = Math.max(Math.abs(b.x0 - inC.cx), Math.abs(b.x1 - inC.cx));
        if (far > inC.r - P * 0.6) out.push([label, txt, `丸からはみ出し（${((far - inC.r) / k).toFixed(1)}）`]);
      }
    });
    for (let i = 0; i < tb.length; i++) for (let j = i + 1; j < tb.length; j++) {
      const a = tb[i].b, c = tb[j].b;
      const w = Math.min(a.x1, c.x1) - Math.max(a.x0, c.x0), h = Math.min(a.y1, c.y1) - Math.max(a.y0, c.y0);
      // 字の箱には上下のすき間が入っているので、高さの4割・幅の2割以上かぶるときだけ「重なる」とする（ふりがなや牌の字は近くて正しい）
      const mh = Math.min(a.y1 - a.y0, c.y1 - c.y0), mw = Math.min(a.x1 - a.x0, c.x1 - c.x0);
      // 大きさが大きく違う2つ（ふりがなと本文）は、近くに置くのが正しいので見ない
      const fa = parseFloat(getComputedStyle(tb[i].t).fontSize), fc = parseFloat(getComputedStyle(tb[j].t).fontSize);
      if (Math.min(fa, fc) / Math.max(fa, fc) < 0.7) continue;
      if (w > mw * 0.2 && h > mh * 0.4) {
        out.push([label, tb[i].t.textContent.trim().slice(0, 12) + ' × ' + tb[j].t.textContent.trim().slice(0, 12), '文字どうしが重なる']);
      }
    }
  });
  return out;
}
"""


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    args = sys.argv[1:]
    pad = 3.0
    if '--pad' in args:
        i = args.index('--pad'); pad = float(args[i + 1]); del args[i:i + 2]
    # 引数に .html を渡すと、そのページの中の SVG だけを調べる
    pages_arg = [os.path.relpath(os.path.abspath(f), ROOT) for f in args if f.endswith('.html')]
    args = [f for f in args if not f.endswith('.html')]
    files = args if (args or pages_arg) else sorted(glob.glob(os.path.join(ROOT, 'assets', 'thumbs', '*.svg')) + glob.glob(os.path.join(ROOT, 'assets', 'art', '*.svg'))
                           + [f for f in glob.glob(os.path.join(ROOT, 'assets', '*.svg'))])
    pages = pages_arg if (args or pages_arg) else sorted(os.path.basename(f) for f in glob.glob(os.path.join(ROOT, '*.html'))) + sorted('news/' + os.path.basename(f) for f in glob.glob(os.path.join(ROOT, 'news', '*.html')))
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    found = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1200, 'height': 900})
        # SVG ファイル: 1ページに並べて文字の箱を測る（<img> では中の文字が測れないので、中身をそのまま入れる）
        body = ''
        for f in files:
            src = open(f, encoding='utf-8').read()
            src = src.replace('<svg', f'<svg data-src="{os.path.relpath(f, ROOT)}"', 1)
            body += f'<div style="width:640px">{src}</div>'
        hp = os.path.join(ROOT, '_svgcheck.html')
        open(hp, 'w', encoding='utf-8').write(f'<!doctype html><html><head><meta charset="utf-8">{FONT_CSS}<style>body>div>svg{{width:640px;height:auto;display:block}}</style></head><body>{body}</body></html>')
        try:
            pg.goto(f'http://127.0.0.1:{PORT}/_svgcheck.html'); pg.evaluate(LOAD_JS); pg.wait_for_timeout(800)
            found += pg.evaluate(CHECK_JS, pad)
        finally:
            os.remove(hp)
        # ページの中の SVG（ブログの絵・LP の絵）
        for u in pages:
            pg.goto(f'http://127.0.0.1:{PORT}/{u}')
            pg.add_script_tag(content="document.head.insertAdjacentHTML('beforeend', " + repr(FONT_CSS) + ")")
            pg.evaluate(LOAD_JS); pg.wait_for_timeout(600)
            found += [[u + ' ' + a, t, w] for a, t, w in pg.evaluate(CHECK_JS, pad)]
        b.close()
    srv.shutdown()
    for a, t, w in found:
        print(f'NG  {a} 「{t}」 {w}')
    print(f'\n{len(found)} 件' + ('' if found else '（はみ出し・重なりなし）'))
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
