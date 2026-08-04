# -*- coding: utf-8 -*-
"""麻雀の牌姿図をインラインSVGとして生成するツール。

ブログ記事に牌姿図を入れるときに使う（-> docs/image-tools.md）。
牌コード: m1..m9=萬子 / p1..p9=筒子 / s1..s9=索子 /
          E,S,W,N=東南西北 / Wh=白 / Gr=發 / Rd=中
使い方（例）:
    from make_tile_svg import hand_svg, dora_map_svg
    svg = hand_svg([["m2","m3","m4"], ["E","E"]])   # グループごとに間隔が空く
    svg = dora_map_svg([("p3","p4"), ("m9","m1")])  # 表示牌→ドラの対応図
"""

TILE_W, TILE_H, GAP, GROUP_GAP = 44, 60, 4, 12
KANJI = {1: "一", 2: "二", 3: "三", 4: "四", 5: "五", 6: "六", 7: "七", 8: "八", 9: "九"}
WINDS = {"E": "東", "S": "南", "W": "西", "N": "北"}
FONT = "'Hiragino Kaku Gothic ProN','Noto Sans JP',sans-serif"

# 筒子の丸配置（1〜9）: (cx, cy, r)
PIN = {
    1: [(22, 30, 11)],
    2: [(22, 17, 7), (22, 43, 7)],
    3: [(12, 14, 6.5), (22, 30, 6.5), (32, 46, 6.5)],
    4: [(13, 17, 6.5), (31, 17, 6.5), (13, 43, 6.5), (31, 43, 6.5)],
    5: [(13, 16, 6), (31, 16, 6), (22, 30, 6), (13, 44, 6), (31, 44, 6)],
    6: [(13, 14, 6), (31, 14, 6), (13, 30, 6), (31, 30, 6), (13, 46, 6), (31, 46, 6)],
    7: [(9, 12, 5.2), (22, 16, 5.2), (35, 20, 5.2), (13, 34, 5.2), (31, 34, 5.2), (13, 48, 5.2), (31, 48, 5.2)],
    8: [(13, 11, 5.2), (31, 11, 5.2), (13, 24, 5.2), (31, 24, 5.2), (13, 37, 5.2), (31, 37, 5.2), (13, 50, 5.2), (31, 50, 5.2)],
    9: [(11, 14, 5), (22, 14, 5), (33, 14, 5), (11, 30, 5), (22, 30, 5), (33, 30, 5), (11, 46, 5), (22, 46, 5), (33, 46, 5)],
}
# 索子の棒配置（2〜9）: (cx, cy, 高さ)。1索は鳥柄のため図では使わない
SOU = {
    2: [(22, 16, 15), (22, 44, 15)],
    3: [(22, 14, 15), (14, 44, 15), (30, 44, 15)],
    4: [(14, 16, 15), (30, 16, 15), (14, 44, 15), (30, 44, 15)],
    5: [(14, 15, 14), (30, 15, 14), (22, 30, 12), (14, 45, 14), (30, 45, 14)],
    6: [(12, 16, 15), (22, 16, 15), (32, 16, 15), (12, 44, 15), (22, 44, 15), (32, 44, 15)],
    7: [(22, 11, 12), (12, 30, 12), (22, 30, 12), (32, 30, 12), (12, 49, 12), (22, 49, 12), (32, 49, 12)],
    8: [(14, 12, 11), (30, 12, 11), (14, 25, 11), (30, 25, 11), (14, 38, 11), (30, 38, 11), (14, 51, 11), (30, 51, 11)],
    9: [(12, 13, 12), (22, 13, 12), (32, 13, 12), (12, 30, 12), (22, 30, 12), (32, 30, 12), (12, 47, 12), (22, 47, 12), (32, 47, 12)],
}


def _face(code):
    """牌の絵柄部分のSVG要素を返す"""
    kind, out = code[0], []
    if kind == "m":
        n = int(code[1])
        out.append(f'<text x="22" y="27" text-anchor="middle" font-size="17" font-weight="700" fill="#1a1a1a" font-family="{FONT}">{KANJI[n]}</text>')
        out.append(f'<text x="22" y="50" text-anchor="middle" font-size="19" font-weight="700" fill="#b71c1c" font-family="{FONT}">萬</text>')
    elif kind == "p":
        n = int(code[1])
        if n == 1:
            out.append('<circle cx="22" cy="30" r="11" fill="#177083"/><circle cx="22" cy="30" r="6" fill="#E4F3EC"/><circle cx="22" cy="30" r="2.5" fill="#177083"/>')
        else:
            for cx, cy, r in PIN[n]:
                out.append(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="#177083"/>')
    elif kind == "s":
        n = int(code[1])
        for cx, cy, h in SOU[n]:
            out.append(f'<rect x="{cx - 3}" y="{cy - h / 2}" width="6" height="{h}" rx="2.5" fill="#177083"/>')
    elif code in WINDS:
        out.append(f'<text x="22" y="39" text-anchor="middle" font-size="26" font-weight="700" fill="#1a1a1a" font-family="{FONT}">{WINDS[code]}</text>')
    elif code == "Wh":
        out.append('<rect x="9" y="11" width="26" height="38" rx="4" fill="none" stroke="#4261AA" stroke-width="2.2"/>')
    elif code == "Gr":
        out.append(f'<text x="22" y="39" text-anchor="middle" font-size="26" font-weight="700" fill="#00796b" font-family="{FONT}">發</text>')
    elif code == "Rd":
        out.append(f'<text x="22" y="39" text-anchor="middle" font-size="26" font-weight="700" fill="#b71c1c" font-family="{FONT}">中</text>')
    else:
        raise ValueError("unknown tile code: " + code)
    return "".join(out)


def tile_svg(code, x, y=4):
    return (f'<g transform="translate({x},{y})">'
            f'<rect x="0" y="0" width="{TILE_W}" height="{TILE_H}" rx="7" fill="#ffffff" stroke="#c9d4d1" stroke-width="1.5"/>'
            + _face(code) + "</g>")


def hand_svg(groups, max_width=560, min_width=520):
    """グループ（面子・雀頭）ごとに間隔を空けた1列の牌姿図。

    13〜14枚の手牌はスマホ幅だと潰れるためmin-widthを持たせている。
    記事に入れるときは必ず <div style="overflow-x:auto"> で包むこと（横スクロールで見せる）。
    """
    parts, x = [], 4
    for gi, group in enumerate(groups):
        if gi > 0:
            x += GROUP_GAP
        for code in group:
            parts.append(tile_svg(code, x))
            x += TILE_W + GAP
    w, h = x - GAP + 4, TILE_H + 8
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'style="width:100%;min-width:{min_width}px;max-width:{max_width}px;height:auto">' + "".join(parts) + "</svg>")


def dora_map_svg(pairs, max_width=440):
    """表示牌→ドラの対応図（矢印つき・下にラベル）"""
    parts, x = [], 4
    for pi, (ind, dora) in enumerate(pairs):
        if pi > 0:
            x += 26
        parts.append(tile_svg(ind, x))
        parts.append(f'<text x="{x + 22}" y="82" text-anchor="middle" font-size="11" fill="#8a9997" font-family="{FONT}">表示牌</text>')
        ax = x + TILE_W + 4
        parts.append(f'<path d="M{ax + 2} 34 h14 m-5 -5 l5 5 -5 5" stroke="#E75620" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>')
        x = ax + 22
        parts.append(tile_svg(dora, x))
        parts.append(f'<text x="{x + 22}" y="82" text-anchor="middle" font-size="11" fill="#8a9997" font-family="{FONT}">ドラ</text>')
        x += TILE_W + GAP
    w, h = x - GAP + 4, 90
    return (f'<svg viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg" role="img" '
            f'style="width:100%;max-width:{max_width}px;height:auto">' + "".join(parts) + "</svg>")


if __name__ == "__main__":
    print(hand_svg([["m2", "m3", "m4"], ["m5", "m6", "m7"], ["p3", "p4", "p5"], ["s7", "s8"], ["E", "E"]]))
