# -*- coding: utf-8 -*-
"""まじゃすこの麻雀の道具のイラスト（SVG）: 点棒・サイコロ・起家マーク・全自動卓・卓を上から見た図（山・王牌・ツモの順）（2026-10-23〜・見本）
色は牌と同じ（緑・青・オレンジ＋墨）。牌の絵は assets/tiles/ を使う。
"""
GREEN, BLUE, ORANGE, INK = "#177083", "#4261AA", "#E25A1C", "#1F2A28"
CREAM, EDGE = "#FFFDF6", "#A79E87"
BACK_FACE, BACK_EDGE = "#4FA3AE", "#2E8794"
F = 'font-family="Noto Sans JP, sans-serif"'


def svg(w, h, body, label=""):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">{body}</svg>'


# ---------------- 点棒 ----------------
def _dots(cx, cy, n, r, gap, col):
    xs = [cx + (i - (n - 1) / 2) * gap for i in range(n)]
    return "".join(f'<circle cx="{x:.1f}" cy="{cy}" r="{r}" fill="{col}"/>' for x in xs)


def tenbo(value, x=0, y=0, L=180, H=16):
    """点棒（横向き）。模様は日本の白い点棒と同じ（Wikimedia Commons「Mahjong japan fiches」で確認。赤い点はまじゃすこのオレンジ、黒い点は墨）
    100点＝真ん中に黒い点8つ（2段×4）、1,000点＝真ん中に赤い点1つ、5,000点＝赤い点1つのまわりに小さな赤い点4つ、
    10,000点＝5,000点の模様の左右に小さな赤い点を1つずつ＋両端寄りに大きな黒い点1つずつ"""
    cy = y + H / 2
    c = x + L / 2
    g = f'<rect x="{x}" y="{y + 2}" width="{L}" height="{H}" rx="{H / 2}" fill="#D9D2BE"/>'  # 厚み
    g += f'<rect x="{x}" y="{y}" width="{L}" height="{H}" rx="{H / 2}" fill="{CREAM}" stroke="{EDGE}" stroke-width="1.2"/>'
    dot = lambda dx, dy, r, col: f'<circle cx="{c + dx:.1f}" cy="{cy + dy:.1f}" r="{r}" fill="{col}"/>'
    if value == 100:
        g += "".join(dot(dx, dy, 1.9, INK) for dx in (-7.5, -2.5, 2.5, 7.5) for dy in (-2.6, 2.6))
    elif value == 1000:
        g += dot(0, 0, 3.6, ORANGE)
    elif value in (5000, 10000):
        g += dot(0, 0, 3.6, ORANGE) + "".join(dot(dx, dy, 1.9, ORANGE) for dx in (-6.5, 6.5) for dy in (-3.6, 3.6))
        if value == 10000:
            g += dot(-12, 0, 1.9, ORANGE) + dot(12, 0, 1.9, ORANGE) + dot(-24, 0, 3.4, INK) + dot(24, 0, 3.4, INK)
    return g


def tenbo_set():
    g = ""
    for i, v in enumerate((10000, 5000, 1000, 100)):
        y = 14 + i * 34
        g += tenbo(v, 20, y)
        g += f'<text x="214" y="{y + 12.5}" font-size="13" font-weight="900" fill="{INK}" {F}>{v:,}点</text>'
    return svg(300, 150, g, "点棒（10,000点・5,000点・1,000点・100点）")


# ---------------- サイコロ・起家マーク・リーチ棒 ----------------
PIPS = {1: [(0, 0)], 2: [(-1, -1), (1, 1)], 3: [(-1, -1), (0, 0), (1, 1)], 4: [(-1, -1), (1, -1), (-1, 1), (1, 1)],
        5: [(-1, -1), (1, -1), (0, 0), (-1, 1), (1, 1)], 6: [(-1, -1), (1, -1), (-1, 0), (1, 0), (-1, 1), (1, 1)]}


def die(n, x, y, s=40):
    g = f'<rect x="{x}" y="{y + 3}" width="{s}" height="{s}" rx="{s * .22}" fill="#D9D2BE"/>'
    g += f'<rect x="{x}" y="{y}" width="{s}" height="{s}" rx="{s * .22}" fill="#fff" stroke="{EDGE}" stroke-width="1.2"/>'
    for dx, dy in PIPS[n]:
        col = ORANGE if n == 1 else INK
        r = s * (.14 if n == 1 else .085)
        g += f'<circle cx="{x + s / 2 + dx * s * .26:.1f}" cy="{y + s / 2 + dy * s * .26:.1f}" r="{r:.1f}" fill="{col}"/>'
    return g


def chiicha(x, y, kanji="東", w=46, h=30):
    """起家マーク（親を最初にした人の前に置く札）。オレンジの札に白い字"""
    g = f'<rect x="{x}" y="{y + 4}" width="{w}" height="{h}" rx="5" fill="#A63E12"/>'
    g += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="5" fill="{ORANGE}"/>'
    g += f'<text x="{x + w / 2}" y="{y + h / 2 + 6}" text-anchor="middle" font-size="18" font-weight="900" fill="#fff" {F}>{kanji}</text>'
    return g


def small_parts():
    g = die(3, 16, 18) + die(5, 64, 18) + die(1, 112, 18)
    g += chiicha(180, 22, "東") + chiicha(236, 22, "南")
    g += f'<text x="88" y="84" text-anchor="middle" font-size="10" font-weight="700" fill="#55625F" {F}>サイコロ（1はオレンジ）</text>'
    g += f'<text x="236" y="84" text-anchor="middle" font-size="10" font-weight="700" fill="#55625F" {F}>起家マーク（東・南）</text>'
    return svg(300, 96, g, "サイコロと起家マーク")


# ---------------- 全自動卓（斜め上から） ----------------
def jidou_taku():
    """全自動卓を斜め上から見た形。天板は緑のマット、まわりはオレンジの枠（オレンジの枠の業務用卓を参考に）、真ん中にサイコロの窓と4つの点数表示"""
    W, H = 360, 268
    cx, cy = 180, 96
    def P(u, v, z=0):  # 卓の上の (u, v)（-1〜1）を、斜めから見た画面の座標に
        return (cx + (u - v) * 84, cy + (u + v) * 36 - z)
    def poly(pts, fill, extra=""):
        return f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for x, y in pts)}" fill="{fill}" {extra}/>'
    g = f'<ellipse cx="{cx}" cy="{cy + 142}" rx="100" ry="12" fill="#000" opacity=".08"/>'
    # 台（天板の下の箱）
    g += poly([(cx - 64, cy + 56), (cx, cy + 82), (cx, cy + 140), (cx - 64, cy + 114)], "#2B3634")
    g += poly([(cx, cy + 82), (cx + 64, cy + 56), (cx + 64, cy + 114), (cx, cy + 140)], "#3A4744")
    # 天板の厚み
    t = 16
    g += poly([P(-1, 1), P(1, 1), (P(1, 1)[0], P(1, 1)[1] + t), (P(-1, 1)[0], P(-1, 1)[1] + t)], "#B8461A")
    g += poly([P(1, 1), P(1, -1), (P(1, -1)[0], P(1, -1)[1] + t), (P(1, 1)[0], P(1, 1)[1] + t)], "#CF5420")
    # 天板（枠）とマット
    g += poly([P(-1, -1), P(1, -1), P(1, 1), P(-1, 1)], ORANGE)
    g += poly([P(-1, -1), P(1, -1), P(.94, -.94), P(-.94, -.94)], "#fff", 'opacity=".18"')
    g += poly([P(-.86, -.86), P(.86, -.86), P(.86, .86), P(-.86, .86)], GREEN)
    g += poly([P(-.86, -.86), P(.86, -.86), P(.86, -.72), P(-.86, -.72)], "#fff", 'opacity=".07"')
    # 真ん中のサイコロの窓と点数表示
    g += poly([P(-.2, -.2), P(.2, -.2), P(.2, .2), P(-.2, .2)], "#0F4F5C")
    x0, y0 = P(0, 0)
    g += f'<ellipse cx="{x0}" cy="{y0}" rx="18" ry="7.5" fill="#cfe3e6" opacity=".55"/><ellipse cx="{x0 - 4}" cy="{y0 - 2}" rx="6" ry="2.4" fill="#fff" opacity=".6"/>'
    for u, v in ((0, .3), (.3, 0), (0, -.3), (-.3, 0)):
        x, y = P(u, v)
        g += f'<rect x="{x - 10}" y="{y - 4}" width="20" height="8" rx="1.5" fill="{INK}"/><text x="{x}" y="{y + 2.6}" text-anchor="middle" font-size="5.6" font-weight="900" fill="{ORANGE}" font-family="monospace">25000</text>'
    # 山（4辺に並んだ牌の背）
    for side in range(4):
        for i in range(17):
            a = -.62 + i * (1.24 / 16)
            u, v = {0: (a, .62), 1: (.62, -a), 2: (-a, -.62), 3: (-.62, a)}[side]
            x, y = P(u, v)
            g += f'<rect x="{x - 2.6}" y="{y - 4}" width="5.2" height="4.6" rx="1" fill="{BACK_FACE}" stroke="{BACK_EDGE}" stroke-width=".5"/>'
    return svg(W, H, g, "全自動卓を斜め上から見た図")


# ---------------- 卓を上から見た図: 山・開門・王牌・ツモの順 ----------------
def wall_top(break_at=9, show_labels=True):
    """4人の山（17幢×2段）を上から。下（東家）の山を右から break_at 幢目で開門。
    王牌＝開門位置の右の7幢（開門位置から3幢目の上段がドラ表示牌、反対の端の2幢が嶺上牌）。
    配牌とツモは開門位置の左から取っていく（山は時計回りに減る）。手番は反時計回り（東→南→西→北）"""
    import os
    T = "/assets/tiles"
    S = 400
    # 卓: オレンジの枠に緑のマット（全自動卓の絵と同じ色）
    g = f'<rect width="{S}" height="{S}" rx="20" fill="{ORANGE}"/><rect x="3" y="3" width="{S - 6}" height="{S - 6}" rx="18" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="2"/>'
    g += f'<rect x="14" y="14" width="{S - 28}" height="{S - 28}" rx="10" fill="{GREEN}"/>'
    w, d = 13, 17  # 1幢の幅（山に沿った長さ）と奥行き
    L = 17 * w
    x0 = 200 - L / 2

    def stack(px, py, mode):
        # mode: "live"（ふつうの山）/ "dead"（王牌）/ "dora"（ドラ表示牌）/ "rinshan"（嶺上牌）
        if mode == "dora":
            return f'<image href="{T}/m8.svg" x="{px + .5}" y="{py - 1}" width="{w - 1}" height="{(w - 1) * 89 / 62:.1f}"/>'
        fill, st = (BACK_FACE, BACK_EDGE) if mode == "live" else ("#7FC1C9", "#2E8794")
        s = f'<rect x="{px + .5}" y="{py}" width="{w - 1}" height="{d}" rx="2" fill="{fill}" stroke="{st}" stroke-width=".8"/>'
        if mode == "rinshan":
            s += f'<rect x="{px + .5}" y="{py}" width="{w - 1}" height="{d}" rx="2" fill="none" stroke="{ORANGE}" stroke-width="1.6"/>'
        return s

    walls = ""
    for side, rot in ((0, 0), (1, 270), (2, 180), (3, 90)):
        body = ""
        for i in range(17):  # 左から i 番目（自分から見て）
            px = x0 + i * w
            py = 313
            mode = "live"
            if side == 0:
                k = 17 - i  # 右から k 幢目
                if break_at - 7 < k <= break_at:  # 開門位置の右の7幢＝王牌（右から break_at-6 .. break_at）
                    pos = break_at - k + 1  # 開門位置から数えて pos 幢目（1〜7）
                    mode = "dora" if pos == 3 else ("rinshan" if pos >= 6 else "dead")
                if k == break_at + 1:
                    px -= 6  # 開門位置（すき間）
            body += stack(px, py, mode)
        walls += f'<g transform="rotate({rot} 200 200)">{body}</g>'
    g += walls
    # 席の名前（手番は反時計回り）
    for x, y, name in ((200, 362, "東家（親）"), (366, 200, "南家"), (200, 40, "西家"), (34, 200, "北家")):
        g += f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" font-size="12" font-weight="900" fill="#fff" {F}>{name}</text>'
    # 手番の矢印（反時計回り）
    g += f'<path d="M262 250 A88 88 0 0 0 250 138" fill="none" stroke="#fff" stroke-width="3" stroke-dasharray="1 0" marker-end="url(#ah)" opacity=".85"/>'
    g = f'<defs><marker id="ah" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#fff"/></marker></defs>' + g
    if show_labels:
        g += f'<rect x="130" y="166" width="140" height="68" rx="8" fill="#fff" opacity=".95"/>'
        g += f'<text x="200" y="186" text-anchor="middle" font-size="11" font-weight="900" fill="{INK}" {F}>手番は反時計回り</text>'
        g += f'<text x="200" y="204" text-anchor="middle" font-size="9.5" font-weight="700" fill="#55625F" {F}>山は開門位置の左から取る</text>'
        g += f'<text x="200" y="220" text-anchor="middle" font-size="9.5" font-weight="700" fill="#55625F" {F}>王牌＝右の7幢（14枚）</text>'
    return svg(S, S, g, "卓を上から見た図。4人の山と開門位置、王牌・ドラ表示牌・嶺上牌、手番の向き")
