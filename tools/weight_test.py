# -*- coding: utf-8 -*-
"""ページの重さ（1回開いたときに送る量）の点検。Firebase Hosting の転送量を増やしすぎないための見張り。
  python tools/weight_test.py          … 全ページを調べて、上限を超えたページ・ファイルがあれば 1 で終わる（CI で毎回動く）
  python tools/weight_test.py --top 20 … 重い順に一覧を出す

なぜ（2026-11-14）: 1ページで 1〜1.6MB の PNG を3枚読ませる記事がXで広まり、1日で約6GB＝月の無料枠（10GB）を超えた。
有料（Blaze）に切りかえたので止まりはしないが、送った分だけ費用になる。重いページを公開する前に気づけるようにする。
数え方: HTML（gzip した大きさ）＋そのページが読みこむ自分のサイトのファイル（img の src・video の src/poster・source・script・css）。
  - <a href> の先（押したときだけ開く大きな PNG・PDF）は数えない
  - loading="lazy" の画像も数える（下まで読む人には送るので、広まったときの最悪の量として見る）
  - preload="none" の動画は数えない（再生した人にだけ送る）
"""
import glob, gzip, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE_MAX = 1200 * 1024      # 1ページの上限（これを超えるなら、画像を WebP にする・小さくする・押した先に回す）
FILE_MAX = 600 * 1024       # ページが読みこむ1ファイルの上限（動画は VIDEO_MAX）
VIDEO_MAX = 1600 * 1024
# 上限をこえてよいページ（理由を書く）。ここを増やす前に、軽くできないかを先に考える
ALLOW = {
    "index.html": 2600 * 1024,   # アプリ本体（HTML が約400KB）＋使い方の動画（約1.3MB。画面に入ったら再生）。動画は preload="metadata"
    "blog.html": 1700 * 1024,    # 全記事の一覧。サムネは lazy（下まで見た人にだけ送る）。1記事ふえるごとに約25KB。上限に近づいたら、サムネを軽くするか一覧を分ける
}
SKIP_DIRS = ("tools", "docs", "node_modules", "まじゃすこ素材")
TAG = re.compile(r'<(img|source|video|script|link)\b[^>]*>', re.I)
ATTR = lambda t, k: (re.search(r'\b' + k + r'="([^"]*)"', t) or [None, None])[1]
GZ = (".js", ".css", ".svg", ".json", ".html")


def size(path):
    if not os.path.isfile(path): return None
    if path.endswith(GZ): return len(gzip.compress(open(path, "rb").read(), 6))
    return os.path.getsize(path)


def local(url, page_dir):
    if not url or url.startswith(("data:", "http:", "https:", "//", "#", "mailto:")): return None
    url = url.split("?")[0].split("#")[0]
    p = os.path.join(ROOT, url.lstrip("/")) if url.startswith("/") else os.path.join(page_dir, url)
    return os.path.normpath(p)


def page_files(path):
    s = io.open(path, encoding="utf-8").read()
    out = {}
    for m in TAG.finditer(s):
        t = m.group(0); tag = m.group(1).lower(); urls = []
        if tag == "link":
            if "stylesheet" in (ATTR(t, "rel") or ""): urls.append(ATTR(t, "href"))
        elif tag == "video":
            urls.append(ATTR(t, "poster"))
            if ATTR(t, "preload") != "none": urls.append(ATTR(t, "src"))
        else:
            urls.append(ATTR(t, "src"))
            ss = ATTR(t, "srcset")
            if ss:      # srcset は、いちばん大きいものが選ばれることがあるので、いちばん重いものを数える
                c = [local(u.strip().split(" ")[0], os.path.dirname(path)) for u in ss.split(",")]
                c = [(size(x) or 0, x) for x in c if x]
                if c: out[max(c)[1]] = max(c)[0]
        for u in urls:
            p = local(u, os.path.dirname(path))
            if p and size(p) is not None: out[p] = size(p)
    return len(gzip.compress(s.encode("utf-8"), 6)), out


def main():
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 0
    rows, bad = [], []
    for p in sorted(glob.glob(os.path.join(ROOT, "**", "*.html"), recursive=True)):
        rel = os.path.relpath(p, ROOT).replace(os.sep, "/")
        if rel.split("/")[0] in SKIP_DIRS or rel == "tests.html": continue
        h, files = page_files(p)
        total = h + sum(files.values())
        rows.append((total, rel, h, files))
        lim_p = ALLOW.get(rel, PAGE_MAX)
        if total > lim_p:
            bad.append(f"ページが重い: {rel} {total // 1024}KB（上限 {lim_p // 1024}KB）")
        for f, n in files.items():
            lim = VIDEO_MAX if f.endswith((".mp4", ".webm")) else FILE_MAX
            if n > lim:
                bad.append(f"ファイルが重い: {os.path.relpath(f, ROOT)} {n // 1024}KB（{rel} が読みこむ。上限 {lim // 1024}KB）")
    rows.sort(reverse=True)
    for total, rel, h, files in rows[:top or 5]:
        print(f"{total // 1024:6d}KB  {rel}（HTML {h // 1024}KB＋{len(files)}ファイル）")
        if top:
            for f, n in sorted(files.items(), key=lambda x: -x[1])[:4]: print(f"          {n // 1024:5d}KB {os.path.relpath(f, ROOT)}")
    bad = sorted(set(bad))
    for b in bad: print("NG", b)
    print(f"{len(rows)}ページ・", "ALL PASS" if not bad else f"{len(bad)}件 NG")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
