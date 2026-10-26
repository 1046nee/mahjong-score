# -*- coding: utf-8 -*-
"""記事の一覧の絵（assets/thumbs/）を、記事の中にも出す（2026-10-26〜・ユーザーの依頼）。
タイトルと日付（.post-meta）のすぐ下に <figure class="eyecatch"> を入れる。すでにあれば入れ直さない（何度実行しても同じ）。
そのすぐ下にあった飾りの絵（.post-illust の大きい方）は、絵が2つ続くので外す。
実行: python tools/add_eyecatch.py   （新しい記事は make_thumbs.py で絵を作ってから）
"""
import glob, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = sorted(glob.glob(os.path.join(ROOT, "blog-*.html")) + glob.glob(os.path.join(ROOT, "news", "*.html")))
files = [f for f in files if not f.endswith(os.sep + "index.html")]
n = 0
for f in files:
    slug = os.path.basename(f)[:-5]
    thumb = os.path.join(ROOT, "assets", "thumbs", slug + ".svg")
    if not os.path.exists(thumb):
        print("絵がない（make_thumbs.py に足す）:", slug)
        continue
    s = io.open(f, encoding="utf-8").read()
    if 'class="eyecatch"' in s:
        continue
    m = re.search(r'<article class="blog-post">.*?<h1>(.*?)</h1>\s*<p class="post-meta">.*?</p>\n', s, re.S)
    if not m:
        print("見出しと日付が見つからない:", slug)
        continue
    title = re.sub(r"<rt>.*?</rt>|<[^>]+>", "", m.group(1)).split("｜")[0]
    fig = (f'\n  <figure class="eyecatch"><img src="/assets/thumbs/{slug}.svg" alt="{title}のイメージ" width="320" height="240" fetchpriority="high"></figure>\n')
    rest = s[m.end():]
    # すぐ下の大きい飾りの絵（.post-illust で small ではないもの）は外す
    rest = re.sub(r'^\s*<div class="post-illust" aria-hidden="true">.*?</svg></div>\n', "", rest, count=1, flags=re.S)
    s = s[:m.end()] + fig + rest
    io.open(f, "w", encoding="utf-8", newline="").write(s)
    n += 1
print(n, "ページに絵を入れた")
