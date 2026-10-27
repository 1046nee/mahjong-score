# -*- coding: utf-8 -*-
"""add_ruby.py のテスト（2026-10-27〜）。手で付けたルビ（READ に無い語）が消えないこと、何度実行しても同じ結果になることを確かめる。
実行: python tools/add_ruby_test.py   （ALL PASS と出ればよい。記事のファイルには触らない）
"""
import io, os, sys, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import add_ruby

HTML = ('<html><body><article class="blog-post">'
        '<h3><ruby>大車輪<rt>ダイシャリン</rt></ruby></h3>'                       # 手で付けたルビ（READ に無い）
        '<p><ruby>一色三順<rt>イーソーサンシュン</rt></ruby><span class="yomi">（イッショクサンジュン）</span>と面子と面子</p>'
        '<p>あとの<ruby>雀頭<rt>ジャントウ</rt></ruby>と、前に出てこなかった花牌</p>'   # READ の語は付け直される
        '</article></body></html>')

d = tempfile.mkdtemp()
try:
    p = os.path.join(d, "blog-test.html")
    io.open(p, "w", encoding="utf-8").write(HTML)
    add_ruby.process(p)
    s1 = io.open(p, encoding="utf-8").read()
    add_ruby.process(p)
    s2 = io.open(p, encoding="utf-8").read()
    checks = [
        ("手で付けたルビが残る（大車輪）", "<ruby>大車輪<rt>ダイシャリン</rt></ruby>" in s1),
        ("手で付けたルビが残る（一色三順）", "<ruby>一色三順<rt>イーソーサンシュン</rt></ruby>" in s1),
        ("READ の語は最初の1回だけ（面子）", s1.count("<ruby>面子") == 1),
        ("READ の語に付く（花牌）", "<ruby>花牌<rt>ファパイ</rt></ruby>" in s1),
        ("何度実行しても同じ", s1 == s2),
    ]
finally:
    shutil.rmtree(d)
bad = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(("ok   " if ok else "FAIL ") + n)
print("ALL PASS" if not bad else f"{len(bad)} FAIL")
sys.exit(1 if bad else 0)
