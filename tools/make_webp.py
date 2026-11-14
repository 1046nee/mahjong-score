# -*- coding: utf-8 -*-
"""記事にのせる1枚の表（点数早見表・役一覧・牌の一覧・確認リスト…）の、軽い画像（WebP・ロスレス）を作り、記事の <img> をそれに差しかえる。
  python tools/make_webp.py          … 作る＋記事を書きかえる（何度実行しても同じ結果）
  python tools/make_webp.py --check  … 作り直しが要る画像・書きかえが要る記事があれば一覧を出して 1 で終わる

なぜ（2026-11-14）: Firebase Hosting の無料枠（月10GB）を使い切った。役の出やすさランキングがXで広まった日に、
1ページで1〜1.6MBの PNG を3枚読ませていて、1日で約6GB。見た目は同じまま、送る量を3分の1ほどにする。
  - 記事の中で見せるのは WebP（ロスレス＝PNG と同じ見た目）を1つだけ（幅 1588 まで）。1080 幅も作ってみたが、縮めると色の中間が増えて、
    ロスレスでは 1588 幅より重くなった（ロッシーでも同じくらい）ので、作らない
  - 拡大したい人のための大きな PNG・PDF は、画像を押したときのリンク先にだけ残す（今までどおり）
  - og:image・sitemap の image:image・JSON-LD は PNG のまま（X や画像検索は PNG を読む）
元の PNG を作り直したら（hai_sheets.py・score_sheet.py・rule_sheet.py・yaku_rate_sheet.py）、このスクリプトも実行する。
"""
import glob, io, os, re, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# 記事の <img src="/assets/(hai|score|rules)/X.png" srcset="...X-web.png 1588w, ...X.png 2481w"...> の形を探す
IMG = re.compile(r'<img src="/assets/((?:hai|score|rules)/[a-z0-9-]+?)(?:\.png|-web\.webp)"(?: srcset="[^"]*")?')


def webp_paths(base):
    return (os.path.join(ROOT, "assets", base + "-web.webp"),)


def build(base):
    """base（例 hai/mahjong-yaku-ichiran）の WebP を2つ作る。元は -web.png（無ければ大きい PNG を 1588 幅に縮める）"""
    src = os.path.join(ROOT, "assets", base + "-web.png")
    if not os.path.exists(src): src = os.path.join(ROOT, "assets", base + ".png")
    im = Image.open(src).convert("RGB")
    if im.width > 1588: im = im.resize((1588, round(im.height * 1588 / im.width)), Image.LANCZOS)
    im.save(webp_paths(base)[0], "WEBP", lossless=True, quality=100, method=6)
    return src


def stale(base):
    src = os.path.join(ROOT, "assets", base + "-web.png")
    if not os.path.exists(src): src = os.path.join(ROOT, "assets", base + ".png")
    return any(not os.path.exists(w) or os.path.getmtime(w) < os.path.getmtime(src) for w in webp_paths(base))


def rewrite(html):
    def rep(m):
        b = m.group(1)
        return f'<img src="/assets/{b}-web.webp"'
    return IMG.sub(rep, html)


def main():
    check = "--check" in sys.argv
    bad = []
    bases = set()
    for p in sorted(glob.glob(os.path.join(ROOT, "*.html"))):
        s = io.open(p, encoding="utf-8").read()
        found = IMG.findall(s)
        bases |= set(found)
        t = rewrite(s)
        if t != s:
            bad.append("記事: " + os.path.basename(p))
            if not check: io.open(p, "w", encoding="utf-8", newline="").write(t)
    # 書きかえ済みの記事からも、使っている WebP を拾う
    for p in glob.glob(os.path.join(ROOT, "*.html")):
        bases |= set(re.findall(r'/assets/((?:hai|score|rules)/[a-z0-9-]+)-web\.webp', io.open(p, encoding="utf-8").read()))
    for b in sorted(bases):
        if stale(b):
            bad.append("画像: " + b)
            if not check:
                build(b)
                print("作った:", b, *[f"{os.path.getsize(w) // 1024}KB" for w in webp_paths(b)])
    if check:
        print("要対応:", bad or "なし"); sys.exit(1 if bad else 0)
    print("記事:", [x for x in bad if x.startswith("記事")] or "変更なし")


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
