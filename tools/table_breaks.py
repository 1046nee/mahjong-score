# -*- coding: utf-8 -*-
"""記事の表のセルを読みやすく改行する（2026-10-27〜・ユーザーの依頼「（）などで表しているものは適切な所で改行」）。
何度実行しても同じ結果になる（もう直したセルは変えない）。

  1. セルの最後の「（…）」の補足 → <span class="tp">（…）</span>（CSS で次の行に小さく出す。assets/blog.css）
     前の文字が2字以上・補足の中身が3字以上（「6月3日（水）」のような曜日は変えない）。括弧が2つ以上あるセルは変えない
  2. 文が2つ以上ある長いセル（30字以上） → 「。」のあとで改行
  3. 「／」で3つ以上並べた長いセル（28字以上） → 「／」を改行に
表の中の絵（牌の並びの表など）は変えない（セルの中身に <img> がある・決まった表）。
使い方: python tools/table_breaks.py [ファイル...]   （省略で blog-*.html 全部）
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_TABLE = re.compile(r'class="[^"]*\b(kj-num|kj-pair|kj-hayami|dj-tbl|ans-tbl|rot|snake)\b')
CELL = re.compile(r'(<t[dh]\b[^>]*>)(.*?)(</t[dh]>)', re.S)


def plain(h):
    return re.sub(r'<[^>]+>', '', re.sub(r'<rt>.*?</rt>', '', h, flags=re.S)).strip()


def on_text(h, fn):
    """タグの外の文字だけに fn をかける"""
    return ''.join(t if t.startswith('<') else fn(t) for t in re.split(r'(<[^>]+>)', h))


def fix_cell(inner):
    if '<img' in inner or 'class="tp"' in inner or '<br' in inner:
        return inner
    p = plain(inner)
    # 1. 最後の（…）
    m = re.match(r'^(.*\S)\s*(（[^（）]*）)\s*$', inner, re.S)
    if m and '（' not in m.group(1) and len(plain(m.group(1))) >= 2 and len(plain(m.group(2))) - 2 >= 3:  # 括弧が2つ以上のセルは変えない
        # 短い本体（名前など）と短い補足は、途中で折り返さない（「佐々木寿／人」「（81,700／点）」にならないように）
        main = f'<span class="tm">{m.group(1)}</span>' if len(plain(m.group(1))) <= 10 else m.group(1)
        return f'{main}<span class="tp{" nw" if len(plain(m.group(2))) <= 11 else ""}">{m.group(2)}</span>'
    # 2. 文が2つ以上
    if len(p) >= 30 and re.search(r'。.', p):  # 途中に「。」がある＝文が2つ以上
        out = on_text(inner, lambda t: t.replace('。', '。<br>'))
        return re.sub(r'(<br>)+(\s*)$', r'\2', out)
    # 3. 「／」で並べたもの
    if len(p) >= 28 and p.count('／') >= 2:
        return on_text(inner, lambda t: t.replace('／', '<br>'))
    return inner


def fix_table(t):
    if SKIP_TABLE.search(t[:300]):
        return t
    return CELL.sub(lambda m: m.group(1) + fix_cell(m.group(2)) + m.group(3), t)


def main():
    files = sys.argv[1:] or sorted(glob.glob(os.path.join(ROOT, 'blog-*.html')))
    total = 0
    for f in files:
        s = open(f, encoding='utf-8').read()
        new = re.sub(r'<table\b.*?</table>', lambda m: fix_table(m.group(0)), s, flags=re.S)
        n = sum(1 for a, b in zip(re.findall(r'<t[dh]\b[^>]*>.*?</t[dh]>', s, re.S), re.findall(r'<t[dh]\b[^>]*>.*?</t[dh]>', new, re.S)) if a != b)
        if new != s:
            open(f, 'w', encoding='utf-8').write(new)
            print(f'{os.path.basename(f)}: {n} セル')
            total += n
    print(f'合計 {total} セル')


if __name__ == '__main__':
    main()
