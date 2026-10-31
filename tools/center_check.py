# -*- coding: utf-8 -*-
"""丸・小さな札の中の短い文字（順位の数字・番号・バッジ）が、真ん中からずれていないかを調べる（2026-10-31〜）。
きっかけ: ブログのおすすめ記事の順位の丸で、親の行間（line-height）が残って数字が1.5px下にずれていた（ユーザー指摘）。

調べるもの: 幅・高さが40px以下で、角が丸い（border-radius）か幅と高さがほぼ同じ要素のうち、中身が3字以内の文字だけのもの。
文字の箱（Range）の真ん中と、要素の中身の箱（枠と余白を除く）の真ん中の差が 1px を超えたら報告する。
幅 390・1280px で、ブログ一覧・テーマ一覧・記事・トップページ・アプリの画面を見る。
使い方: python tools/center_check.py [ページ...]   （1件でも見つかれば終了コード1）
"""
import functools
import http.server
import os
import sys
import threading

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORT = 8833
PAGES = ['blog.html', 'rules/index.html', 'blog-score-table.html', 'blog-yaku-list.html', 'blog-mleague-2026.html', 'index.html', 'score-basics.html', 'faq.html']
JS = r"""
() => {
  const out = [];
  document.querySelectorAll('body *').forEach(e => {
    if (e.children.length || e.tagName === 'TD' || e.tagName === 'TH') return; // 表のセルは見ない（寄せは table_align.py）
    const t = (e.textContent || '').trim();
    if (!t || [...t].length > 3) return;
    const r = e.getBoundingClientRect();
    if (r.width < 8 || r.width > 40 || r.height < 8 || r.height > 40) return;
    const c = getComputedStyle(e);
    if (c.visibility === 'hidden' || c.display === 'none' || c.display === 'inline') return;
    const round = parseFloat(c.borderTopLeftRadius) >= Math.min(r.width, r.height) / 3;
    const square = Math.abs(r.width - r.height) <= 2;
    if (!round && !square) return;
    const bg = c.backgroundColor, bd = parseFloat(c.borderTopWidth);
    if ((bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && !bd) return; // 形の無いものは見ない
    const g = document.createRange(); g.selectNodeContents(e); const tr = g.getBoundingClientRect();
    if (!tr.width) return;
    const pl = parseFloat(c.paddingLeft) + parseFloat(c.borderLeftWidth), pr = parseFloat(c.paddingRight) + parseFloat(c.borderRightWidth);
    const pt = parseFloat(c.paddingTop) + parseFloat(c.borderTopWidth), pb = parseFloat(c.paddingBottom) + parseFloat(c.borderBottomWidth);
    const cx = r.left + pl + (r.width - pl - pr) / 2, cy = r.top + pt + (r.height - pt - pb) / 2;
    const dx = tr.left + tr.width / 2 - cx, dy = tr.top + tr.height / 2 - cy;
    if (Math.abs(dx) > 1 || Math.abs(dy) > 1) out.push([(e.className && e.className.toString()) || e.tagName.toLowerCase(), t, Math.round(dx * 10) / 10, Math.round(dy * 10) / 10]);
  });
  return out;
}
"""


class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def main():
    pages = sys.argv[1:] or PAGES
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', PORT), functools.partial(Q, directory=ROOT))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    found = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        for w in (390, 1280):
            pg = b.new_page(viewport={'width': w, 'height': 900})
            for u in pages:
                pg.goto(f'http://127.0.0.1:{PORT}/{u}'); pg.wait_for_timeout(900)
                seen = set()
                for cls, t, dx, dy in pg.evaluate(JS):
                    if (cls, dx, dy) in seen:
                        continue
                    seen.add((cls, dx, dy))
                    found.append((w, u, cls, t, dx, dy))
            pg.close()
        b.close()
    srv.shutdown()
    for w, u, cls, t, dx, dy in found:
        print(f'NG  {w}px {u} .{cls} 「{t}」 横{dx:+}px 縦{dy:+}px')
    print(f'\n{len(found)} 件' + ('' if found else '（ずれなし）'))
    sys.exit(1 if found else 0)


if __name__ == '__main__':
    main()
