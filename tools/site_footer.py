# -*- coding: utf-8 -*-
"""全ページのフッターの中身を同じにする（2026-10-27〜）。見た目は assets/site-foot.css。
- 静的HTMLの <footer class="site-foot">…</footer>（記事・固定ページ・お知らせ）と、LP（index.html）の <footer class="site-footer">…</footer> の中身を FOOT に置きかえる
- それぞれの <head> に site-foot.css の <link> を入れる（無ければ）
- assets/blog-site.js の renderChrome も同じ中身を描く（FOOT を変えたら blog-site.js の FOOT_HTML も直す。下の assert で確かめる）
何度実行しても同じ結果。実行: python tools/site_footer.py
"""
import io, os, re, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
X_ICON = "https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/21/99/a9/2199a9db-0dc2-305f-7b8f-a5bc80258dbf/ProductionAppIcon-0-0-1x_U007emarketing-0-8-0-0-0-85-220.png/128x128bb.jpg"
IG_ICON = "https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/01/2d/b1/012db1a7-249a-86e8-f025-72491c2a6475/Prod-0-0-1x_U007epad-0-0-0-1-0-0-sRGB-85-220.png/128x128bb.jpg"
FOOT = (
    '<div class="ft">'
    '<a class="ft-brand" href="/"><img src="/assets/favicon.png" alt="" width="40" height="40"><span><b>まじゃすこ</b><small>麻雀のスコア記録を、スマホでかんたんに</small></span></a>'
    '<div class="ft-sns">'
    f'<a href="https://x.com/majasco_jp" target="_blank" rel="noopener" aria-label="まじゃすこ公式X（@majasco_jp）"><img src="{X_ICON}" alt="X" width="40" height="40" loading="lazy"></a>'
    f'<a href="https://www.instagram.com/majasco_jp/" target="_blank" rel="noopener" aria-label="まじゃすこ公式Instagram（@majasco_jp）"><img src="{IG_ICON}" alt="Instagram" width="40" height="40" loading="lazy"></a>'
    '</div>'
    '<nav class="ft-cols" aria-label="サイトのリンク">'
    '<div><b>使う</b><a href="/">トップ</a><a href="/score-basics.html">スコア計算の基本</a><a href="/faq.html">よくある質問</a></div>'
    '<div><b>読む</b><a href="/blog.html">ブログ</a><a href="/news/">お知らせ</a><a href="/news/feed.xml">お知らせRSS</a></div>'
    '<div><b>このサイトについて</b><a href="/about.html">運営者について</a><a href="/contact.html">お問い合わせ</a><a href="/terms.html">利用規約</a><a href="/privacy.html">プライバシーポリシー</a></div>'
    '</nav>'
    '<div class="ft-copy">© 2026 まじゃすこ</div>'
    '</div>'
)
LINK = '<link rel="stylesheet" href="/assets/site-foot.css">'
PAT = re.compile(r'(<footer class="(?:site-foot|site-footer)"[^>]*>)(.*?)(</footer>)', re.S)


def main():
    js = io.open(os.path.join(ROOT, "assets", "blog-site.js"), encoding="utf-8").read()
    assert ("const FOOT_HTML = '" + FOOT + "';") in js, "blog-site.js の FOOT_HTML が FOOT と違う"
    files = [f for f in glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)
             if "まじゃすこ素材" not in f and os.sep + "tools" + os.sep not in f]
    changed = []
    for f in files:
        s = io.open(f, encoding="utf-8").read()
        if not PAT.search(s):
            continue
        t = PAT.sub(lambda m: m.group(1) + "\n  " + FOOT + "\n" + m.group(3), s, count=1)
        if LINK not in t:
            t = t.replace("</head>", "  " + LINK + "\n</head>", 1)
        if t != s:
            io.open(f, "w", encoding="utf-8", newline="").write(t)
            changed.append(os.path.relpath(f, ROOT))
    print(len(changed), "ページ", changed[:5], "…" if len(changed) > 5 else "")


if __name__ == "__main__":
    main()
