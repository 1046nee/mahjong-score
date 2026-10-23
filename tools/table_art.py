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


# カラーの点棒（雀荘に多い色つきの点棒。Wikimedia Commons「Mahjong japan fiches」の左の列と同じ色と模様。原色でよい＝2026-10-23 ユーザーの判断）
COLOR_TENBO = {100: ("#F2F2EE", "#9EA3A3", "#CFCFC8"), 500: ("#16A05A", "#fff", "#0E7A43"), 1000: ("#1F6FD1", "#fff", "#1555A3"),
               5000: ("#F5C400", "#fff", "#C99E00"), 10000: ("#E02424", "#fff", "#AC1717"), "tobi": ("#222", "#fff", "#000")}


def tenbo_color(value, x=0, y=0, L=180, H=16):
    """カラーの点棒。100＝白に灰色の点8つ、500＝緑に白い点5つ、1,000＝青に白い点1つ、5,000＝黄に白い点（1つ＋まわりに4つ）、
    10,000＝赤に白い点（5,000の模様＋左右に1つずつ＋両端寄りに大きな点）、トビ点棒＝黒に10,000と同じ模様（持ち点が0点を下回ったときに使う）"""
    body, dc, shade = COLOR_TENBO[value]
    cy, c = y + H / 2, x + L / 2
    g = f'<rect x="{x}" y="{y + 2}" width="{L}" height="{H}" rx="{H / 2}" fill="{shade}"/>'
    g += f'<rect x="{x}" y="{y}" width="{L}" height="{H}" rx="{H / 2}" fill="{body}"' + (f' stroke="{EDGE}" stroke-width="1"' if value == 100 else "") + "/>"
    g += f'<rect x="{x + 8}" y="{y + 2.5}" width="{L - 16}" height="2.4" rx="1.2" fill="#fff" opacity=".22"/>'
    dot = lambda dx, dy, r: f'<circle cx="{c + dx:.1f}" cy="{cy + dy:.1f}" r="{r}" fill="{dc}"/>'
    if value == 100:
        g += "".join(dot(dx, dy, 1.9) for dx in (-7.5, -2.5, 2.5, 7.5) for dy in (-2.6, 2.6))
    elif value == 500:
        g += "".join(dot(dx, 0, 1.9) for dx in (-12, -6, 0, 6, 12))
    elif value == 1000:
        g += dot(0, 0, 3.6)
    else:
        g += dot(0, 0, 3.6) + "".join(dot(dx, dy, 1.9) for dx in (-6.5, 6.5) for dy in (-3.6, 3.6))
        if value in (10000, "tobi"):
            g += dot(-12, 0, 1.9) + dot(12, 0, 1.9) + dot(-24, 0, 3.4) + dot(24, 0, 3.4)
    return g


def tenbo_color_set():
    g = ""
    for i, (v, label) in enumerate(((100, "100点"), (500, "500点"), (1000, "1,000点"), (5000, "5,000点"), (10000, "10,000点"), ("tobi", "トビ点棒"))):
        y = 12 + i * 32
        g += tenbo_color(v, 20, y)
        g += f'<text x="214" y="{y + 12.5}" font-size="13" font-weight="900" fill="{INK}" {F}>{label}</text>'
    return svg(310, 206, g, "カラーの点棒（100点・500点・1,000点・5,000点・10,000点・トビ点棒）")


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


# ---------------- 卓を上から見た図（場面ごと）----------------
# 席: 0=東家（下）1=南家（右）2=西家（上）3=北家（左）。手番は反時計回り（東→南→西→北）。
# 山の幢は、その席の人から見て右から数えて k=1〜17。開門は東家の山を右から BREAK 幢目で割る（サイコロの合計9の例）。
# 王牌＝開門位置の右の7幢（開門位置から3幢目の上段がドラ表示牌、反対の端の2幢＝嶺上牌）。
# 配牌とツモは開門位置の左から取る（山は時計回りに減る）。最後のツモ（海底牌）は王牌のすぐ手前の幢。
# 出典: Wikipedia「壁牌」（開門・王牌・幢）「ドラ (麻雀)」「麻雀のルール」（席の呼び方）
import math

BREAK = 9
SEATS = ["東家", "南家", "西家", "北家"]
SEAT_COL = {0: ORANGE, 1: BLUE, 2: "#2E9C8A", 3: "#55625F"}
ROT = {0: 0, 1: 270, 2: 180, 3: 90}
W_, D_ = 13, 17          # 1幢の幅と奥行き
WALL_Y = 313             # 下の山の位置（4辺が重ならない）
X0 = 200 - 17 * W_ / 2


def live_order():
    """配牌・ツモで取っていく順の (席, k) の並び（開門位置の左から時計回り）"""
    out = [(0, k) for k in range(BREAK + 1, 18)]
    for side in (3, 2, 1):
        out += [(side, k) for k in range(1, 18)]
    out += [(0, k) for k in range(1, BREAK - 6)]
    return out


def dead_pos(side, k):
    """王牌なら開門位置から数えた番号（1〜7）、ちがえば None"""
    if side == 0 and BREAK - 6 <= k <= BREAK:
        return BREAK - k + 1
    return None


def stack_xy(side, k):
    """（回す前の）下の山での左上の座標"""
    x = X0 + (17 - k) * W_
    if side == 0 and k > BREAK:
        x -= 6  # 開門のすき間
    return x, WALL_Y


def center_of(side, k):
    x, y = stack_xy(side, k)
    cx, cy = x + W_ / 2, y + D_ / 2
    a = math.radians(ROT[side])
    dx, dy = cx - 200, cy - 200
    return 200 + dx * math.cos(a) - dy * math.sin(a), 200 + dx * math.sin(a) + dy * math.cos(a)


def _stack(px, py, fill, stroke):
    return f'<rect x="{px + .5:.1f}" y="{py}" width="{W_ - 1}" height="{D_}" rx="2" fill="{fill}" stroke="{stroke}" stroke-width=".8"/>'


def _callout(xy, label, dx, dy, col=ORANGE):
    x, y = xy
    tx, ty = x + dx, y + dy
    wd = len(label) * 11 + 14
    return (f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="#fff" stroke-width="1.4"/>'
            f'<rect x="{tx - wd / 2:.1f}" y="{ty - 9:.1f}" width="{wd:.1f}" height="18" rx="9" fill="{col}"/>'
            f'<text x="{tx:.1f}" y="{ty + 4:.1f}" text-anchor="middle" font-size="10.5" font-weight="900" fill="#fff" {F}>{label}</text>')


def _box(lines, y0=160):
    h = 18 + 16 * len(lines)
    out = f'<rect x="94" y="{y0}" width="212" height="{h}" rx="8" fill="#fff" opacity=".96"/>'
    for n, (t, big) in enumerate(lines):
        out += (f'<text x="200" y="{y0 + 20 + n * 16}" text-anchor="middle" font-size="{11.5 if big else 8.8}" '
                f'font-weight="{900 if big else 700}" fill="{INK if big else "#55625F"}" {F}>{t}</text>')
    return out


SCENE_LABEL = {
    "yama": "麻雀の卓を上から見た図。4人の山（壁牌）と開門位置、王牌・ドラ表示牌・嶺上牌の場所",
    "kaimon": "サイコロで開門位置を決める図。合計9なら東家の山を右から9幢目で割る",
    "haipai": "配牌の取り方の図。開門位置の左から東南西北の順に2幢ずつ3回取る",
    "tsumo": "ツモの順と山の減り方の図。手番は反時計回り、山は時計回りに減り、最後の1枚が海底牌",
    "kaze": "席と風の図。場風と自風、上家・下家・対面、起家マーク",
}


def table_scene(scene="yama", T="/assets/tiles"):
    """scene: yama（山と王牌）/ kaimon（サイコロと開門）/ haipai（配牌の取り方）/ tsumo（ツモの順と海底牌）/ kaze（席と風）"""
    S = 400
    g = '<defs><marker id="ah" markerWidth="8" markerHeight="8" refX="4" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8 Z" fill="#fff"/></marker></defs>'
    g += f'<rect width="{S}" height="{S}" rx="20" fill="{ORANGE}"/><rect x="3" y="3" width="{S - 6}" height="{S - 6}" rx="18" fill="none" stroke="#fff" stroke-opacity=".25" stroke-width="2"/>'
    g += f'<rect x="14" y="14" width="{S - 28}" height="{S - 28}" rx="10" fill="{GREEN}"/>'
    order = live_order()
    idx = {sk: n for n, sk in enumerate(order)}
    haitei = order[-1]
    show_dead = scene in ("yama", "tsumo")
    for side in range(4):
        body = ""
        for k in range(1, 18):
            px, py = stack_xy(side, k)
            dp = dead_pos(side, k)
            if dp and scene in ("yama", "kaimon", "tsumo"):
                if show_dead and dp == 3:
                    body += f'<image href="{T}/m8.svg" x="{px + .5:.1f}" y="{py - 1}" width="{W_ - 1}" height="{(W_ - 1) * 89 / 62:.1f}"/>'
                    continue
                body += _stack(px, py, "#8FCAD1", BACK_EDGE)
                if show_dead and dp >= 6:
                    body += f'<rect x="{px + .5:.1f}" y="{py}" width="{W_ - 1}" height="{D_}" rx="2" fill="none" stroke="{ORANGE}" stroke-width="1.8"/>'
                continue
            fill, st = BACK_FACE, BACK_EDGE
            if scene == "haipai":
                n = idx.get((side, k))
                if n is not None and n < 24:
                    fill, st = SEAT_COL[(n // 2) % 4], "#fff"
            if scene == "tsumo" and (side, k) == haitei:
                fill, st = "#FFE2D3", ORANGE
            body += _stack(px, py, fill, st)
        g += f'<g transform="rotate({ROT[side]} 200 200)">{body}</g>'
    pos = {0: (200, 362), 1: (366, 200), 2: (200, 40), 3: (34, 200)}
    for side, (x, y) in pos.items():
        g += (f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="middle" font-size="12" font-weight="900" fill="#fff" {F}>'
              f'{SEATS[side]}{"（親）" if side == 0 else ""}</text>')
    bx, by = center_of(0, BREAK)
    if scene == "yama":
        g += _box([("山（壁牌）と王牌", True), ("1人17幢（2段＝34枚）×4人＝136枚", False), ("王牌＝開門位置の右の7幢（14枚）", False), ("王牌からはカンのときしか取らない", False)])
        g += _callout(center_of(0, BREAK - 2), "ドラ表示牌", -24, -46)
        g += _callout(center_of(0, BREAK - 6), "嶺上牌", 40, -46)
        g += _callout((bx + 9, by), "開門位置", -70, -30, INK)
    elif scene == "kaimon":
        g += die(4, 162, 168, 34) + die(5, 204, 168, 34)
        g += f'<text x="200" y="226" text-anchor="middle" font-size="12" font-weight="900" fill="#fff" {F}>合計 9 → 東家の山</text>'
        g += f'<text x="200" y="242" text-anchor="middle" font-size="9" font-weight="700" fill="#fff" {F}>東家から反時計回りに数える</text>'
        g += f'<text x="200" y="256" text-anchor="middle" font-size="9" font-weight="700" fill="#fff" {F}>（1・5・9＝東家、2・6・10＝南家…）</text>'
        g += _callout((bx + 9, by), "右から9幢目で割る", -64, -36, INK)
        g += _callout(center_of(0, BREAK - 3), "右の7幢が王牌", 40, -34)
    elif scene == "haipai":
        g += _box([("配牌の取り方", True), ("開門位置の左から、東→南→西→北の順に", False), ("2幢（4枚）ずつを3回まわる", False), ("最後に親は2枚・子は1枚（親14枚・子13枚）", False)])
        for n in range(0, 24, 2):
            (x, y), (x2, y2) = center_of(*order[n]), center_of(*order[n + 1])
            g += (f'<text x="{(x + x2) / 2:.1f}" y="{(y + y2) / 2 + 3.5:.1f}" text-anchor="middle" font-size="8.5" font-weight="900" fill="#fff" {F}>'
                  f'{SEATS[(n // 2) % 4][0]}</text>')
    elif scene == "tsumo":
        g += _box([("ツモの順と山の減り方", True), ("手番は反時計回り（東→南→西→北）", False), ("山は開門位置の左から時計回りに減る", False), ("王牌の手前の最後の1枚＝海底牌", False)], 150)
        g += '<path d="M300 250 A100 100 0 0 0 300 150" fill="none" stroke="#fff" stroke-width="3" marker-end="url(#ah)" opacity=".9"/>'
        g += _callout(center_of(*haitei), "海底牌", 40, -44)
        g += _callout(center_of(0, BREAK - 6), "嶺上牌", -8, -66)
    elif scene == "kaze":
        g += _box([("東場（場風＝東）", True), ("自風は席で決まる（東家＝東・南家＝南…）", False), ("東家から見て右が下家・正面が対面・左が上家", False), ("親は局ごとに反時計回りに移る", False)], 150)
        g += chiicha(236, 326, "東", 34, 22)
        g += f'<text x="253" y="361" text-anchor="middle" font-size="8.5" font-weight="900" fill="#fff" {F}>起家マーク</text>'
        for side, rel in ((1, "下家"), (2, "対面"), (3, "上家")):
            x, y = pos[side]
            g += (f'<rect x="{x - 22}" y="{y + 10}" width="44" height="16" rx="8" fill="{ORANGE}"/>'
                  f'<text x="{x}" y="{y + 21.5}" text-anchor="middle" font-size="9.5" font-weight="900" fill="#fff" {F}>{rel}</text>')
    return svg(S, S, g, SCENE_LABEL[scene])


def dead_wall_zoom(T="/assets/tiles"):
    """王牌（7幢×2段）を手前から見た拡大図。右端が開門位置の側。開門位置から3幢目の上段がドラ表示牌、その下が裏ドラ表示牌、
    カンをすると隣（開門位置から4幢目）の上段が槓ドラ表示牌になる。反対の端の2幢（4枚）が嶺上牌"""
    w = 38
    h = w * 89 / 62
    y_up, y_lo = 78, 78 + h - 12
    g = f'<rect width="400" height="250" rx="16" fill="{GREEN}"/>'
    xs = {pos: 352 - pos * (w + 3) for pos in range(1, 8)}
    for pos, x in xs.items():
        g += f'<image href="{T}/back.svg" x="{x}" y="{y_lo:.1f}" width="{w}" height="{h:.1f}"/>'
    for pos, x in xs.items():
        g += f'<image href="{T}/{"m8" if pos == 3 else "back"}.svg" x="{x}" y="{y_up}" width="{w}" height="{h:.1f}"/>'
    xl = xs[7] - 3
    g += f'<rect x="{xl}" y="{y_up - 4}" width="{2 * (w + 3) + 3}" height="{y_lo + h - y_up + 8:.0f}" rx="7" fill="none" stroke="{ORANGE}" stroke-width="2.6"/>'

    def lab(x, y, t, col=ORANGE):
        wd = len(t) * 11 + 14
        return (f'<rect x="{x - wd / 2:.1f}" y="{y - 9}" width="{wd:.1f}" height="18" rx="9" fill="{col}"/>'
                f'<text x="{x:.1f}" y="{y + 4}" text-anchor="middle" font-size="10.5" font-weight="900" fill="#fff" {F}>{t}</text>')
    xd, xk = xs[3] + w / 2, xs[4] + w / 2
    g += lab(xd + 18, 46, "ドラ表示牌") + f'<line x1="{xd:.1f}" y1="55" x2="{xd:.1f}" y2="{y_up}" stroke="#fff" stroke-width="1.4"/>'
    g += lab(xk - 30, 20, "カンをすると槓ドラ表示牌", BLUE) + f'<line x1="{xk:.1f}" y1="29" x2="{xk:.1f}" y2="{y_up}" stroke="#fff" stroke-width="1.4"/>'
    g += lab(xs[7] + w + 1, 52, "嶺上牌（4枚）")
    g += lab(xd, 232, "ドラ表示牌の下＝裏ドラ表示牌", INK) + f'<line x1="{xd:.1f}" y1="{y_lo + h:.0f}" x2="{xd:.1f}" y2="223" stroke="#fff" stroke-width="1.4"/>'
    g += (f'<line x1="372" y1="{y_up}" x2="372" y2="{y_lo + h:.0f}" stroke="#fff" stroke-width="2" stroke-dasharray="4 3"/>'
          f'<text x="386" y="{(y_up + y_lo + h) / 2:.0f}" text-anchor="middle" font-size="10" font-weight="900" fill="#fff" {F} writing-mode="tb">開門位置</text>')
    return svg(400, 250, g, "王牌の拡大図。開門位置の側から3幢目の上段がドラ表示牌、下段が裏ドラ表示牌、カンをすると隣が槓ドラ表示牌、反対の端の2幢が嶺上牌")
