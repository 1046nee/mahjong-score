# -*- coding: utf-8 -*-
"""表の列の寄せをそろえる（2026-10-30〜・ユーザーの依頼「表の形式・文字の大きさ・中央ぞろえや左揃えを場面ごとのルールで合わせる」）。
決まり（docs/blog-spec.md「表と図のそろえ方」）:
- 文字の列は左寄せ（assets/blog.css）
- 数字・点数・記号（○✕—）だけの列は中央寄せ＋数字の幅をそろえる → その列の td と、先頭行の th に class="c-n" を付ける
- 形が決まっている表（点数表・符の表・答えの表・回し方・指名の順）は対象外（それぞれの CSS で寄せている）
何度実行しても同じ結果。
実行: python tools/table_align.py            （blog-*.html をまとめて）
"""
import glob, io, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_CLASS = ("score-tbl", "fu-tbl", "ans-tbl", "rot", "snake", "kj-tbl")
NUM = re.compile(r"^[\s0-9０-９,.\-+−±×÷%％／/~〜～→＝=点符翻ptsPTS本枚人回位着倍局分秒年月日時歳約・：:（）()○◯〇✕✓—–△万千百半以上下前後第名組試合]+$")
HAS_DIGIT = re.compile(r"[0-9０-９○◯〇✕✓—–△]")


def cell_text(html):
    return re.sub(r"\s+", " ", re.sub(r"<rt>.*?</rt>|<[^>]+>", "", html)).strip()


def is_num(t):
    return bool(t) and len(t) <= 16 and bool(NUM.match(t)) and bool(HAS_DIGIT.search(t))


def set_cn(tag_open, on):
    """<td ...> の class に c-n を付ける／外す"""
    m = re.search(r'class="([^"]*)"', tag_open)
    cls = [c for c in (m.group(1).split() if m else []) if c != "c-n"]
    if on:
        cls.append("c-n")
    if m:
        new = tag_open[:m.start()] + (f'class="{" ".join(cls)}"' if cls else "") + tag_open[m.end():]
        return re.sub(r"\s+>", ">", re.sub(r"\s{2,}", " ", new))
    return tag_open[:-1] + ' class="c-n">' if on else tag_open


def fix_table(tbl):
    head = tbl[:tbl.find(">") + 1]
    if any(re.search(rf'class="[^"]*\b{c}\b', head) for c in SKIP_CLASS) or "rowspan" in tbl:
        return tbl
    rows = list(re.finditer(r"<tr[^>]*>(.*?)</tr>", tbl, re.S))
    grid = []  # 行ごとに [(列番号, 開始位置, 終了位置, タグ, 中身, thead?)]
    for r in rows:
        in_head = tbl.rfind("<thead", 0, r.start()) > tbl.rfind("</thead>", 0, r.start())
        col, cells = 0, []
        for c in re.finditer(r"(<(t[hd])\b[^>]*>)(.*?)</t[hd]>", r.group(1), re.S):
            span = int((re.search(r'colspan="(\d+)"', c.group(1)) or [0, 1])[1])
            cells.append((col, span, r.start(1) + c.start(1), r.start(1) + c.end(1), c.group(2), c.group(3), in_head))
            col += span
        grid.append(cells)
    ncol = max((c[0] + c[1] for row in grid for c in row), default=0)
    numcol = set()
    for k in range(ncol):
        vals = [cell_text(c[5]) for row in grid for c in row if c[0] == k and c[1] == 1 and c[4] == "td" and not c[6]]
        vals = [v for v in vals if v]
        if len(vals) >= 2 and sum(is_num(v) for v in vals) / len(vals) >= 0.8:
            numcol.add(k)
    edits = []
    for row in grid:
        for col, span, a, b, tag, inner, in_head in row:
            on = span == 1 and col in numcol and (tag == "td" or in_head)
            new = set_cn(tbl[a:b], on)
            if new != tbl[a:b]:
                edits.append((a, b, new))
    for a, b, new in sorted(edits, reverse=True):
        tbl = tbl[:a] + new + tbl[b:]
    return tbl


def process(path):
    s = io.open(path, encoding="utf-8").read()
    a = s.find('<article class="blog-post">'); b = s.find("</article>", a)
    if a < 0 or b < 0:
        return 0
    body = s[a:b]
    new = re.sub(r"<table\b.*?</table>", lambda m: fix_table(m.group(0)), body, flags=re.S)
    if new == body:
        return 0
    io.open(path, "w", encoding="utf-8", newline="").write(s[:a] + new + s[b:])
    return 1


if __name__ == "__main__":
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, "blog-*.html")))
    n = sum(process(f) for f in files)
    print(n, "ページの表の寄せを更新")
