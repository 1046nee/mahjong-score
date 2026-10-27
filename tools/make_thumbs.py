# -*- coding: utf-8 -*-
"""ブログの一覧のカードに出す、記事ごとの絵（サムネイル）を作る（2026-10-26〜・ユーザーの依頼「中身が少し分かる絵で、記事ごとの違いがひと目で分かるように。カラフルでよい」）。
1記事＝1枚の SVG（assets/thumbs/{記事のファイル名}.svg・320×240）。色の地＋中身を表す絵。牌は assets/tiles/ の絵をそのまま埋め込む。
新しい記事を足したら THUMBS に1行足して実行: python tools/make_thumbs.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_art import inline_tiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "assets", "thumbs")
W, H = 320, 240
INK = "#1F2A28"
F = 'font-family="Hiragino Sans, Noto Sans JP, Yu Gothic, Meiryo, sans-serif"'


# ---------------- 部品 ----------------
def tiles(codes, x0, y0, w=44, gap=4, hl=None):
    h = w * 89 / 62
    out = ""
    for i, c in enumerate(codes):
        x = x0 + i * (w + gap)
        if hl is not None and i == hl:
            out += f'<rect x="{x - 4}" y="{y0 - 4}" width="{w + 8}" height="{h + 4}" rx="9" fill="#fff" opacity=".55"/>'
        out += f'<image href="/assets/tiles/{c}.svg" x="{x}" y="{y0}" width="{w}" height="{h:.1f}"/>'
    return out


def row_center(codes, y0, w=44, gap=4, hl=None):
    total = len(codes) * w + (len(codes) - 1) * gap
    return tiles(codes, (W - total) / 2, y0, w, gap, hl)


def sparkle(x, y, r=10, c="#fff"):
    return f'<path d="M{x} {y - r} Q{x + r * .18} {y - r * .18} {x + r} {y} Q{x + r * .18} {y + r * .18} {x} {y + r} Q{x - r * .18} {y + r * .18} {x - r} {y} Q{x - r * .18} {y - r * .18} {x} {y - r} Z" fill="{c}"/>'


def phone(x, y, w, h, screen):
    """スマホの枠（docs/image-tools.md「スマホの枠」の決まり：高さ＝幅×2.06・枠3.5%・角15%/11.5%・ノッチ幅30%×高さ7%）。
    高さ h と中心はそのままにして、幅を決まりに合わせる"""
    w2 = round(h / 2.06, 1)
    x2 = round(x + (w - w2) / 2, 1)
    b = round(w2 * 0.035, 1)
    return (f'<rect x="{x2}" y="{y}" width="{w2}" height="{h}" rx="{round(w2 * .15, 1)}" fill="{INK}"/>'
            f'<rect x="{x2 + b}" y="{y + b}" width="{round(w2 - 2 * b, 1)}" height="{round(h - 2 * b, 1)}" rx="{round(w2 * .115, 1)}" fill="#fff"/>'
            f'<rect x="{round(x2 + w2 * .35, 1)}" y="{round(y + b + w2 * .015, 1)}" width="{round(w2 * .3, 1)}" height="{round(w2 * .07, 1)}" rx="{round(w2 * .035, 1)}" fill="{INK}"/>' + screen)


def bars(x, y, vals, bw=20, gap=10, maxh=90, c="#fff", last=None):
    out = ""
    m = max(vals)
    for i, v in enumerate(vals):
        h = v / m * maxh
        col = last if (last and i == len(vals) - 1) else c
        out += f'<rect x="{x + i * (bw + gap)}" y="{y - h:.1f}" width="{bw}" height="{h:.1f}" rx="4" fill="{col}"/>'
    return out


def trophy(cx, cy, s=1.0, c="#FFD23F"):
    return (f'<g transform="translate({cx} {cy}) scale({s})">'
            f'<path d="M-34 -50 H34 V-20 A34 32 0 0 1 -34 -20 Z" fill="{c}"/>'
            f'<path d="M-34 -42 H-52 A18 18 0 0 0 -32 -12" stroke="{c}" stroke-width="7" fill="none"/>'
            f'<path d="M34 -42 H52 A18 18 0 0 1 32 -12" stroke="{c}" stroke-width="7" fill="none"/>'
            f'<rect x="-8" y="10" width="16" height="16" fill="{c}"/><rect x="-28" y="26" width="56" height="12" rx="4" fill="{c}"/>'
            f'<circle cx="0" cy="-28" r="10" fill="#fff" opacity=".7"/></g>')


def person(cx, cy, c, r=16):
    return (f'<circle cx="{cx}" cy="{cy - r * .9}" r="{r * .62}" fill="{c}"/>'
            f'<path d="M{cx - r} {cy + r * .9} A{r} {r} 0 0 1 {cx + r} {cy + r * .9} Z" fill="{c}"/>')


def bubble(x, y, w, h, text, fs=40, c="#fff", tc=INK):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{c}"/>'
            f'<path d="M{x + 22} {y + h - 2} L{x + 16} {y + h + 16} L{x + 40} {y + h - 2} Z" fill="{c}"/>'
            f'<text x="{x + w / 2}" y="{y + h / 2 + fs * .36}" text-anchor="middle" font-size="{fs}" font-weight="900" fill="{tc}" {F}>{text}</text>')


def card(x, y, w, h, c="#fff", r=10):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{c}"/>'


def lines(x, y, n, w, gap=14, c="#DCE6E3", first=None):
    out = ""
    for i in range(n):
        ww = w * (0.55 if i % 3 == 2 else 1)
        out += f'<rect x="{x}" y="{y + i * gap}" width="{ww}" height="6" rx="3" fill="{first if (first and i == 0) else c}"/>'
    return out


def check(x, y, c="#2BB673", s=1):
    return f'<path d="M{x} {y} l{6 * s} {6 * s} l{12 * s} {-14 * s}" stroke="{c}" stroke-width="{4 * s}" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'


def grid(x, y, cols, rows, cw, rh, head="#2F6BFF", vals=None):
    out = card(x, y, cols * cw, rows * rh, "#fff", 8)
    out += f'<rect x="{x}" y="{y}" width="{cols * cw}" height="{rh}" rx="8" fill="{head}"/><rect x="{x}" y="{y + rh - 8}" width="{cols * cw}" height="8" fill="{head}"/>'
    for r in range(1, rows):
        out += f'<line x1="{x}" y1="{y + r * rh}" x2="{x + cols * cw}" y2="{y + r * rh}" stroke="#E6EAF2" stroke-width="1.5"/>'
    for c in range(1, cols):
        out += f'<line x1="{x + c * cw}" y1="{y + rh}" x2="{x + c * cw}" y2="{y + rows * rh}" stroke="#E6EAF2" stroke-width="1.5"/>'
    if vals:
        for (cc, rr, t, col) in vals:
            out += f'<text x="{x + cc * cw + cw / 2}" y="{y + rr * rh + rh * .68}" text-anchor="middle" font-size="{rh * .52:.0f}" font-weight="900" fill="{col}" {F}>{t}</text>'
    return out


def podium(cx, y, cols=("#C9D6D3", "#FFD23F", "#F6A04D")):
    return (f'<rect x="{cx - 75}" y="{y - 34}" width="48" height="34" rx="4" fill="{cols[0]}"/>'
            f'<rect x="{cx - 24}" y="{y - 56}" width="48" height="56" rx="4" fill="{cols[1]}"/>'
            f'<rect x="{cx + 27}" y="{y - 24}" width="48" height="24" rx="4" fill="{cols[2]}"/>'
            f'<text x="{cx}" y="{y - 22}" text-anchor="middle" font-size="22" font-weight="900" fill="{INK}" {F}>1</text>')


def tenbo(x, y, w, c, dots="#E75620"):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="14" rx="7" fill="{c}" stroke="#00000022"/>'
            f'<circle cx="{x + w / 2}" cy="{y + 7}" r="4" fill="{dots}"/>')


def bg(c, c2="#ffffff"):
    return (f'<rect width="{W}" height="{H}" fill="{c}"/>'
            f'<circle cx="286" cy="28" r="70" fill="{c2}" opacity=".14"/><circle cx="24" cy="226" r="56" fill="{c2}" opacity=".12"/>')


# ---------------- 記事ごと ----------------
def T(name, color, body):
    return name, color, body


THUMBS = [
 T("blog-pao", "#0F9D8A", lambda: row_center(["z5", "z6", "z7"], 40, 50, 6) + bubble(40, 140, 110, 52, "ポン！", 26) + bubble(170, 140, 110, 52, "包", 30, "#FFD23F") + sparkle(270, 44, 13) + sparkle(54, 50, 9)),
 T("blog-yakuman-rules", "#E8505B", lambda: row_center(["m1", "s9", "z1", "z7"], 44, 44, 4) + bubble(46, 146, 104, 52, "役満", 28) + bubble(170, 146, 104, 52, "×2?", 28) + sparkle(266, 46, 13) + sparkle(54, 54, 9)),
 T("blog-mahjong-manga", "#F28C28", lambda: card(62, 34, 92, 130, "#fff", 8) + card(166, 34, 92, 130, "#fff", 8) + lines(74, 62, 4, 68, 16) + tiles(["z7", "z6"], 180, 66, 30, 8) + bubble(150, 168, 120, 48, "ロン！", 26, "#FFD23F") + sparkle(272, 40, 12)),
 T("blog-mahjong-anime", "#2F6BFF", lambda: card(56, 30, 208, 140, "#1F2A28", 12) + card(66, 40, 188, 120, "#fff", 6) + row_center(["m1", "p1", "z5"], 70, 34, 6) + '<path d="M150 176 L170 176 L160 194 Z" fill="#fff"/>' + '<rect x="110" y="196" width="100" height="8" rx="4" fill="#fff"/>' + sparkle(276, 46, 13)),
 T("blog-rule-wakareme", "#7C5CFF", lambda: row_center(["z1", "z1"], 44, 54, 6) + bubble(54, 150, 92, 52, "2符", 30) + bubble(174, 150, 92, 52, "4符", 30) + '<text x="160" y="186" text-anchor="middle" font-size="30" font-weight="900" fill="#fff" ' + F + '>?</text>' + sparkle(262, 48, 13) + sparkle(56, 52, 9)),
 T("blog-local-yaku", "#FF5C8A", lambda: row_center(["p2", "p3", "p4", "p5", "p6"], 70, 46, 3) + sparkle(250, 50, 14) + sparkle(64, 196, 9) + '<text x="160" y="214" text-anchor="middle" font-size="22" font-weight="900" fill="#fff" ' + F + '>ローカル役満</text>'),
 T("blog-mahjong-kanji", "#FFC233", lambda: bubble(40, 46, 104, 96, "混", 64) + bubble(176, 46, 104, 96, "清", 64, "#1F2A28", "#fff") + '<text x="160" y="206" text-anchor="middle" font-size="22" font-weight="900" fill="#1F2A28" ' + F + '>字でつながる</text>'),
 T("blog-machi-dojo", "#22B573", lambda: row_center(["s2", "s3", "s4", "s5"], 92, 46, 3) + bubble(214, 18, 72, 62, "?", 44, "#fff", "#E75620")),
 T("blog-mahjong-yougoshu", "#8A5CF6", lambda: card(74, 36, 172, 168, "#fff", 12) + '<rect x="74" y="36" width="24" height="168" rx="10" fill="#6D3FE0"/>' + "".join(f'<rect x="246" y="{52 + i * 30}" width="22" height="24" rx="5" fill="{c}"/><text x="257" y="{70 + i * 30}" text-anchor="middle" font-size="13" font-weight="900" fill="#fff" {F}>{t}</text>' for i, (t, c) in enumerate([("あ", "#FF5C8A"), ("か", "#FFC233"), ("さ", "#22B573"), ("た", "#2F6BFF"), ("な", "#E75620")])) + lines(114, 70, 7, 112, 18)),
 T("blog-dantai-rekishi", "#29B6F6", lambda: '<line x1="40" y1="120" x2="280" y2="120" stroke="#fff" stroke-width="6" stroke-linecap="round"/>' + "".join(f'<circle cx="{x}" cy="120" r="16" fill="{c}" stroke="#fff" stroke-width="5"/><text x="{x}" y="{88 if i % 2 == 0 else 168}" text-anchor="middle" font-size="15" font-weight="900" fill="#fff" {F}>{y}</text>' for i, (x, c, y) in enumerate([(52, "#4261AA", "1976"), (108, "#177083", "1981"), (164, "#B7791F", "1997"), (220, "#E25A1C", "2001"), (272, "#6B46C1", "2007")]))),
 T("blog-mahjong-yougo", "#14B8A6", lambda: row_center(["z1", "z2", "z3", "z4"], 50, 44, 4) + card(70, 140, 180, 56, "#fff", 12) + '<text x="160" y="178" text-anchor="middle" font-size="26" font-weight="900" fill="#0F766E" ' + F + '>正式名称</text>'),
 T("blog-mleague-kansen", "#EF4444", lambda: card(60, 30, 200, 150, "#1F2A28", 14) + '<rect x="72" y="42" width="176" height="126" rx="8" fill="#177083"/>' + "".join(f'<rect x="{110 + i * 12}" y="58" width="10" height="13" rx="2" fill="#fff"/><rect x="{110 + i * 12}" y="139" width="10" height="13" rx="2" fill="#fff"/>' for i in range(9)) + '<rect x="150" y="182" width="20" height="18" fill="#1F2A28"/><rect x="118" y="198" width="84" height="8" rx="4" fill="#1F2A28"/><circle cx="160" cy="104" r="20" fill="#E75620"/><path d="M154 94 L170 104 L154 114 Z" fill="#fff"/>'),
 T("blog-yaku-ichiran", "#F97316", lambda: row_center(["m1", "m2", "m3", "p7", "p8", "p9"], 64, 40, 3) + card(96, 150, 128, 50, "#fff", 12) + '<text x="160" y="185" text-anchor="middle" font-size="28" font-weight="900" fill="#C2410C" ' + F + '>全38役</text>'),
 T("blog-mahjong-game-apps", "#6366F1", lambda: phone(110, 16, 100, 208, tiles(["m5", "p5", "s5"], 122, 120, 24, 2) + '<rect x="122" y="40" width="76" height="62" rx="8" fill="#177083"/><circle cx="160" cy="71" r="14" fill="#FFC233"/>') + sparkle(250, 70, 14) + sparkle(64, 170, 10)),
 T("blog-mahjong-youtube", "#EF4444", lambda: card(70, 50, 180, 124, "#fff", 26) + '<path d="M146 88 L188 112 L146 136 Z" fill="#EF4444"/>' + "".join(f'<rect x="{82 + i * 40}" y="190" width="34" height="14" rx="7" fill="{c}"/>' for i, c in enumerate(["#fff", "#FFD23F", "#FF9F6E", "#1F2A28"]))),
 T("blog-mahjong-books", "#84CC16", lambda: "".join(f'<rect x="{70 + i * 46}" y="{60 - h}" width="40" height="{130 + h}" rx="5" fill="{c}"/><rect x="{78 + i * 46}" y="{80 - h}" width="24" height="6" rx="3" fill="#fff" opacity=".8"/>' for i, (c, h) in enumerate([("#1F2A28", 10), ("#2F6BFF", 26), ("#E75620", 0), ("#FFC233", 18)])) + '<rect x="56" y="190" width="208" height="10" rx="5" fill="#3F6212"/>'),
 T("blog-meet-mleaguer", "#EC4899", lambda: '<path d="M160 10 L250 200 H70 Z" fill="#fff" opacity=".22"/>' + person(120, 168, "#1F2A28", 22) + person(160, 150, "#FFD23F", 26) + person(200, 168, "#1F2A28", 22) + sparkle(110, 70, 14) + sparkle(220, 60, 10)),
 T("blog-mahjong-pro", "#0EA5E9", lambda: card(60, 40, 200, 140, "#fff", 12) + '<circle cx="160" cy="96" r="30" fill="#FFD23F"/><path d="M146 122 L140 160 L160 148 L180 160 L174 122" fill="#E75620"/>' + check(146, 96, "#fff", 1.2) + lines(84, 196 - 12, 1, 152, 0, "#ffffff99")),
 T("blog-mahjong-titles", "#EAB308", lambda: '<path d="M88 80 L112 120 L160 66 L208 120 L232 80 L222 170 H98 Z" fill="#fff"/>' + "".join(f'<circle cx="{x}" cy="{y}" r="9" fill="{c}"/>' for x, y, c in [(88, 74, "#E75620"), (160, 58, "#2F6BFF"), (232, 74, "#22B573")]) + '<rect x="98" y="180" width="124" height="20" rx="6" fill="#fff"/>'),
 T("blog-mleague-2026", "#22C55E", lambda: trophy(160, 120, 1.25, "#FFD23F") + "".join(f'<circle cx="{40 + i * 26.7:.0f}" cy="214" r="8" fill="{c}"/>' for i, c in enumerate(["#fff", "#1F2A28", "#EF4444", "#2F6BFF", "#FFC233", "#8A5CF6", "#fff", "#1F2A28", "#EC4899", "#06B6D4"]))),
 T("blog-mleague-history", "#F43F5E", lambda: bars(64, 200, [80, 90, 90, 90, 94, 96, 96, 120], 20, 6, 150, "#fff", "#FFD23F")),
 T("blog-pro-dantai-rules", "#8B5CF6", lambda: "".join(f'<rect x="{46 + i * 48}" y="{70}" width="40" height="110" rx="8" fill="#fff"/><rect x="{46 + i * 48}" y="70" width="40" height="22" rx="8" fill="{c}"/>' + check(56 + i * 48, 128 + (0 if i % 2 else 20), c, 1) for i, c in enumerate(["#177083", "#4261AA", "#E25A1C", "#6B46C1", "#B7791F"]))),
 T("blog-mahjong-ai", "#06B6D4", lambda: '<rect x="96" y="60" width="128" height="104" rx="22" fill="#fff"/><circle cx="134" cy="106" r="13" fill="#1F2A28"/><circle cx="186" cy="106" r="13" fill="#1F2A28"/><circle cx="138" cy="102" r="4" fill="#fff"/><circle cx="190" cy="102" r="4" fill="#fff"/><rect x="138" y="136" width="44" height="8" rx="4" fill="#E75620"/><line x1="160" y1="60" x2="160" y2="36" stroke="#fff" stroke-width="6"/><circle cx="160" cy="30" r="9" fill="#FFC233"/>' + tiles(["p1", "p9"], 238, 150, 28, 4)),
 T("nakama-page", "#2F6BFF", lambda: phone(100, 14, 120, 212, '<g transform="translate(160 160) scale(.62) translate(-160 -160)">' + podium(160, 160) + '</g>' +lines(118, 176, 3, 84, 12) + '<text x="160" y="66" text-anchor="middle" font-size="16" font-weight="900" fill="#1F2A28" ' + F + '>通算順位</text>') + sparkle(258, 60, 14)),
 T("mypage-stats", "#3B82F6", lambda: phone(100, 14, 120, 212, '<path d="M116 150 L140 130 L162 140 L184 104 L204 92" stroke="#2F6BFF" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="204" cy="92" r="6" fill="#E75620"/>' + card(116, 160, 88, 40, "#EAF0FB", 8) + '<text x="160" y="188" text-anchor="middle" font-size="18" font-weight="900" fill="#2F4A86" ' + F + '>+124.4</text>' + '<circle cx="160" cy="58" r="14" fill="#C9D6EE"/>')),
 T("kiroku-kakutei", "#6366F1", lambda: '<rect x="108" y="96" width="104" height="92" rx="14" fill="#fff"/><path d="M128 96 V72 A32 32 0 0 1 192 72 V96" stroke="#fff" stroke-width="14" fill="none"/>' + check(144, 140, "#22B573", 1.4) + '<circle cx="246" cy="68" r="24" fill="#FFC233"/><path d="M246 54 V68 L256 74" stroke="#1F2A28" stroke-width="4" fill="none" stroke-linecap="round"/>'),
 T("blog-season-ranking", "#10B981", lambda: card(40, 40, 240, 150, "#fff", 12) + '<path d="M60 160 L100 140 L140 150 L180 104 L220 92 L256 62" stroke="#10B981" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/><path d="M60 170 L100 160 L140 130 L180 140 L220 128 L256 112" stroke="#FFC233" stroke-width="6" fill="none" stroke-linecap="round" stroke-linejoin="round"/><circle cx="256" cy="62" r="8" fill="#E75620"/>'),
 T("blog-score-examples", "#F59E0B", lambda: '<rect x="96" y="30" width="128" height="180" rx="16" fill="#1F2A28"/><rect x="108" y="44" width="104" height="40" rx="6" fill="#E4F3EC"/><text x="204" y="74" text-anchor="end" font-size="24" font-weight="900" fill="#1F2A28" ' + F + '>+61.3</text>' + "".join(f'<rect x="{108 + c * 27}" y="{96 + r * 27}" width="22" height="22" rx="5" fill="{"#E75620" if (r, c) == (3, 3) else "#fff"}"/>' for r in range(4) for c in range(4))),
 T("blog-house-rules", "#22C55E", lambda: card(80, 30, 160, 184, "#fff", 12) + "".join(check(98, 66 + i * 34, "#22C55E", 1) + f'<rect x="126" y="{60 + i * 34}" width="{90 - (i % 2) * 24}" height="8" rx="4" fill="#DCE6E3"/>' for i in range(5))),
 T("blog-score-mismatch", "#FB7185", lambda: tenbo(56, 70, 150, "#fff") + tenbo(56, 98, 150, "#FFD23F") + tenbo(56, 126, 150, "#2F6BFF", "#fff") + '<circle cx="214" cy="140" r="40" fill="none" stroke="#fff" stroke-width="12"/><line x1="242" y1="170" x2="272" y2="202" stroke="#fff" stroke-width="14" stroke-linecap="round"/>'),
 T("blog-mawashi-uchi", "#14B8A6", lambda: '<circle cx="160" cy="120" r="70" fill="none" stroke="#fff" stroke-width="5" stroke-dasharray="10 9"/>' + "".join(person(160 + 70 * __import__("math").sin(i * 1.2566), 120 - 70 * __import__("math").cos(i * 1.2566) + 6, c, 15) for i, c in enumerate(["#FFC233", "#fff", "#1F2A28", "#fff", "#E75620"]))),
 T("hikitsugi-url", "#0EA5E9", lambda: phone(36, 40, 88, 160, lines(52, 80, 5, 56, 14)) + phone(196, 40, 88, 160, lines(212, 80, 5, 56, 14)) + '<path d="M132 120 H188" stroke="#fff" stroke-width="7" stroke-linecap="round"/><path d="M176 108 L190 120 L176 132" stroke="#fff" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>'),
 T("blog-shukei-gakari", "#F28C28", lambda: '<g transform="rotate(-6 160 120)">' + card(70, 36, 180, 170, "#FFFDF6", 8) + "".join(f'<line x1="86" y1="{70 + i * 22}" x2="234" y2="{70 + i * 22}" stroke="#E3DCCB" stroke-width="2"/>' for i in range(6)) + '<text x="100" y="88" font-size="18" font-weight="900" fill="#1F2A28" ' + F + '>+12.3</text><text x="100" y="132" font-size="18" font-weight="900" fill="#C92F42" ' + F + '>-8.0</text></g><rect x="214" y="96" width="16" height="110" rx="3" fill="#FFC233" transform="rotate(28 222 150)"/>'),
 T("blog-team-tournament", "#A855F7", lambda: '<path d="M60 60 H110 V100 H150 M60 140 H110 V100 M210 60 H160 M150 100 H170" stroke="#fff" stroke-width="6" fill="none"/><path d="M260 60 H210 V100 H170 M260 140 H210 V100" stroke="#fff" stroke-width="6" fill="none"/>' + "".join(f'<rect x="{x}" y="{y}" width="40" height="22" rx="6" fill="{c}"/>' for x, y, c in [(30, 49, "#FFC233"), (30, 129, "#22B573"), (250, 49, "#2F6BFF"), (250, 129, "#EF4444")]) + trophy(160, 170, .7, "#FFD23F")),
 T("csv-export", "#22C55E", lambda: grid(70, 50, 4, 5, 45, 28, "#15803D", [(1, 0, "A", "#fff"), (2, 0, "B", "#fff"), (3, 0, "C", "#fff")]) + '<rect x="214" y="160" width="58" height="34" rx="8" fill="#fff"/><text x="243" y="183" text-anchor="middle" font-size="16" font-weight="900" fill="#15803D" ' + F + '>CSV</text>'),
 T("update-2026-07", "#3B82F6", lambda: '<rect x="100" y="96" width="120" height="96" rx="10" fill="#fff"/><rect x="92" y="78" width="136" height="28" rx="8" fill="#FFC233"/><rect x="152" y="78" width="16" height="114" fill="#E75620"/><path d="M160 78 C140 50 116 60 132 76 M160 78 C180 50 204 60 188 76" stroke="#E75620" stroke-width="7" fill="none"/>' + sparkle(70, 60, 14) + sparkle(256, 100, 12)),
 T("blog-manner", "#F472B6", lambda: '<rect x="70" y="120" width="180" height="70" rx="12" fill="#177083"/>' + tiles(["z5", "z6", "z7"], 104, 70, 34, 4) + '<path d="M222 110 h34 v24 a17 17 0 0 1 -34 0 Z" fill="#fff"/><path d="M256 116 a8 8 0 0 1 0 14" stroke="#fff" stroke-width="4" fill="none"/>'),
 T("blog-rule-basics", "#0EA5E9", lambda: row_center(["m1", "p1", "s1", "z1"], 60, 48, 6) + card(80, 160, 160, 44, "#fff", 12) + '<text x="160" y="190" text-anchor="middle" font-size="20" font-weight="900" fill="#0369A1" ' + F + '>はじめての麻雀</text>'),
 T("blog-app-guide", "#10B981", lambda: phone(48, 24, 96, 192, lines(62, 70, 6, 66, 16)) + "".join(check(170, 70 + i * 40, "#fff", 1.2) + f'<rect x="200" y="{62 + i * 40}" width="{70 - (i % 2) * 16}" height="10" rx="5" fill="#fff"/>' for i in range(4))),
 T("blog-sanma-yonma", "#6366F1", lambda: '<rect x="30" y="60" width="110" height="110" rx="12" fill="#3730A3"/><rect x="180" y="60" width="110" height="110" rx="12" fill="#177083"/>' + "".join(person(x, y, "#fff", 12) for x, y in [(85, 54), (36, 120), (134, 120)]) + "".join(person(x, y, "#fff", 12) for x, y in [(235, 54), (186, 120), (284, 120), (235, 184)]) + '<text x="85" y="128" text-anchor="middle" font-size="34" font-weight="900" fill="#fff" ' + F + '>3</text><text x="235" y="128" text-anchor="middle" font-size="34" font-weight="900" fill="#fff" ' + F + '>4</text>'),
 T("blog-yaku-list", "#F59E0B", lambda: row_center(["m2", "m3", "m4", "p5", "p5"], 56, 44, 4, 4) + tenbo(70, 150, 180, "#fff") + '<text x="160" y="206" text-anchor="middle" font-size="22" font-weight="900" fill="#fff" ' + F + '>リーチ・ドラ</text>'),
 T("blog-score-table", "#2563EB", lambda: grid(40, 40, 5, 5, 48, 30, "#1E3A8A", [(1, 0, "1翻", "#fff"), (2, 0, "2翻", "#fff"), (3, 0, "3翻", "#fff"), (4, 0, "4翻", "#fff"), (0, 1, "30", "#1E3A8A"), (1, 1, "1,000", "#1F2A28"), (2, 1, "2,000", "#1F2A28"), (3, 1, "3,900", "#1F2A28"), (4, 1, "7,700", "#E75620"), (0, 2, "40", "#1E3A8A"), (1, 2, "1,300", "#1F2A28"), (2, 2, "2,600", "#1F2A28"), (3, 2, "5,200", "#1F2A28"), (4, 2, "満貫", "#E75620")])),
 T("blog-uma-oka", "#EC4899", lambda: podium(160, 196, ("#fff", "#FFD23F", "#FFB4CF")) + '<text x="160" y="108" text-anchor="middle" font-size="40" font-weight="900" fill="#fff" ' + F + '>+30</text><text x="88" y="150" text-anchor="middle" font-size="26" font-weight="900" fill="#fff" ' + F + '>+10</text><text x="236" y="160" text-anchor="middle" font-size="26" font-weight="900" fill="#fff" ' + F + '>−10</text>'),
 T("blog-why-majasco", "#F28C28", lambda: '<circle cx="110" cy="104" r="46" fill="#FFD23F"/><rect x="94" y="148" width="32" height="26" rx="5" fill="#fff"/><path d="M98 104 l10 12 l14 -22" stroke="#E75620" stroke-width="7" fill="none" stroke-linecap="round" stroke-linejoin="round"/>' + phone(186, 40, 86, 170, '<text x="229" y="130" text-anchor="middle" font-size="40" font-weight="900" fill="#E75620" ' + F + '>M</text>') + sparkle(160, 46, 12)),
 # ブログ以外の読みもの（トップページの「もっと詳しく」）
 T("score-basics", "#0E95A3", lambda: card(48, 54, 224, 132, "#fff", 14) + '<text x="160" y="104" text-anchor="middle" font-size="22" font-weight="900" fill="#1F2A28" ' + F + '>素点＋ウマ＋オカ</text><rect x="74" y="122" width="172" height="4" rx="2" fill="#0E95A3"/><text x="160" y="164" text-anchor="middle" font-size="30" font-weight="900" fill="#E75620" ' + F + '>＝スコア</text>'),
 T("faq", "#2F6BFF", lambda: bubble(40, 44, 110, 84, "Q", 50, "#fff", "#2F6BFF") + bubble(170, 104, 110, 84, "A", 50, "#FFC233", "#1F2A28")),
 # フッターのページ（2026-10-26〜）
 T("about", "#0E95A3", lambda: person(160, 138, "#fff", 48) + '<circle cx="160" cy="88" r="30" fill="#FFC233"/><text x="160" y="99" text-anchor="middle" font-size="30" font-weight="900" fill="#1F2A28" ' + F + '>む</text>' + sparkle(240, 60, 14) + sparkle(78, 170, 10)),
 T("contact", "#2F6BFF", lambda: '<rect x="70" y="62" width="180" height="120" rx="12" fill="#fff"/><path d="M74 70 L160 132 L246 70" stroke="#2F6BFF" stroke-width="7" fill="none" stroke-linejoin="round"/><circle cx="244" cy="66" r="18" fill="#E75620"/><text x="244" y="73" text-anchor="middle" font-size="20" font-weight="900" fill="#fff" ' + F + '>!</text>'),
 T("terms", "#8A5CF6", lambda: card(92, 30, 136, 180, "#fff", 12) + "".join(check(108, 70 + i * 32, "#8A5CF6", 1) + f'<rect x="136" y="{64 + i * 32}" width="{70 - (i % 2) * 18}" height="8" rx="4" fill="#E3D7FF"/>' for i in range(4)) + '<circle cx="222" cy="186" r="26" fill="#E75620"/><circle cx="222" cy="186" r="18" fill="none" stroke="#fff" stroke-width="3"/>'),
 T("privacy", "#22B573", lambda: '<path d="M160 36 L226 60 V112 C226 156 196 188 160 204 C124 188 94 156 94 112 V60 Z" fill="#fff"/><rect x="136" y="110" width="48" height="40" rx="7" fill="#22B573"/><path d="M144 110 V98 A16 16 0 0 1 176 98 V110" stroke="#22B573" stroke-width="7" fill="none"/><circle cx="160" cy="128" r="5" fill="#fff"/>'),
]


def build():
    os.makedirs(OUT, exist_ok=True)
    for name, color, body in THUMBS:
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">'
               + bg(color) + body() + "</svg>")
        svg = inline_tiles(svg)
        assert "/assets/tiles/" not in svg, name
        io.open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8", newline="\n").write(svg)
    print(len(THUMBS), "枚")


if __name__ == "__main__":
    build()
