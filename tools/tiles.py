# -*- coding: utf-8 -*-
"""まじゃすこの牌のイラスト（SVG）を作る（2026-10-23〜）。決定: style="tokumin"（A の形・字は Kaisei Tokumin ExtraBold・太らせない）
牌の種類: m1〜m9（萬子）・p1〜p9（筒子）・s1〜s9（索子）・z1〜z7（東南西北白發中）・赤ドラは m5r / p5r / s5r
tile_svg(code, style) が1枚分のSVG文字列を返す。styles = STYLES のキー
"""
import io, json, math, os

_GLYPHS = json.load(io.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "tile_glyphs.json"), encoding="utf-8"))

# まじゃすこの3色だけで描く（赤の代わりにオレンジ。2026-10-23 ユーザーの依頼）。名前は役目（赤ドラ・中などの「赤い部分」）のまま RED
RED, GREEN, BLUE, INK = "#E25A1C", "#177083", "#4261AA", "#1F2A28"
KANJI = "一二三四五六七八九"
WIND = {"z1": "東", "z2": "南", "z3": "西", "z4": "北", "z6": "發", "z7": "中"}

STYLES = {
    # 牌の背（下の厚み）が まじゃすこの緑。表は少しクリーム。字は明朝の太字（本物の牌らしさ）
    "standard": dict(face="#FFFDF6", edge="#E3DCCB", back=GREEN, back_h=7, rx=7, serif=True, stroke=None),
    # 厚みなし・白・細い枠。字はゴシック（画面の中でいちばん読みやすい）
    "flat": dict(face="#FFFFFF", edge="#C9D3D0", back=None, back_h=0, rx=6, serif=False, stroke=1.4),
    # 厚みは緑＋上に白いつや。角を大きく丸め、字は極太ゴシック
    "pop": dict(face="#FFFFFF", edge="#D5DEDB", back=GREEN, back_h=8, rx=10, serif=False, stroke=None, gloss=True),
}
# 仕上げ候補（2026-10-23）: A の形に、字を図形にしたもの。glyphs＝tile_glyphs.json の名前、thick＝字を太らせる量
STYLES["tokumin"] = dict(STYLES["standard"], glyphs="tokumin", thick=0)     # Kaisei Tokumin ExtraBold（太らせない。2026-10-23 ユーザーの判断）
STYLES["boku"] = dict(STYLES["standard"], glyphs="boku", thick=0)           # Yuji Boku（太らせない）

W, H = 60, 80  # 牌の表の大きさ（厚みは下に足す）
EDGE, EDGE_W = "#A79E87", 1.3            # 牌の枠（少し濃くして見やすく。2026-10-23）
BACK_FACE, BACK_EDGE = "#4FA3AE", "#2E8794"  # 裏向きの面（下の厚みの緑 #177083 より明るい緑）


def _circle(cx, cy, r, col, big=False):
    # 筒子の丸: 外の輪＋内の輪＋中心の点（重ねて「筒」らしく）。一筒（big）は中心だけオレンジで、まわりは青
    center = RED if big else col
    if big:
        col = BLUE
    s = f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{col}" stroke-width="{r*0.28:.2f}"/>'
    s += f'<circle cx="{cx}" cy="{cy}" r="{r*0.42:.2f}" fill="{center}"/>'
    if big:
        s += f'<circle cx="{cx}" cy="{cy}" r="{r*0.72:.2f}" fill="none" stroke="{col}" stroke-width="{r*0.08:.2f}" stroke-dasharray="{r*0.18:.2f} {r*0.14:.2f}"/>'
    return s


P_LAYOUT = {  # 筒子の丸の位置（牌の表 60×80 の中）と色。筒子は青とオレンジだけ（緑は入れない。2026-10-23 ユーザーの判断）
    1: [(30, 40, 19, RED, True)],
    2: [(30, 24, 11, BLUE, False), (30, 56, 11, BLUE, False)],
    3: [(16, 18, 9, BLUE, False), (30, 40, 9, RED, False), (44, 62, 9, BLUE, False)],
    4: [(x, y, 10, BLUE, False) for y in (25, 55) for x in (18, 42)],
    5: [(17, 21, 9, BLUE, False), (43, 21, 9, BLUE, False), (30, 40, 9, RED, False), (17, 59, 9, BLUE, False), (43, 59, 9, BLUE, False)],
    6: [(19, 16, 8, BLUE, False), (41, 16, 8, BLUE, False)] + [(x, y, 8, RED, False) for y in (42, 64) for x in (19, 41)],
    7: [(15, 12, 7, BLUE, False), (30, 22, 7, BLUE, False), (45, 32, 7, BLUE, False)] + [(x, y, 7.5, RED, False) for y in (50, 68) for x in (19, 41)],
    8: [(x, y, 7, BLUE, False) for y in (13, 31, 49, 67) for x in (19, 41)],
    9: [(x, y, 7.5, col, False) for y, col in ((16, BLUE), (40, RED), (64, BLUE)) for x in (13, 30, 47)],
}


def _stick(x, y, h, col, ang=0):
    # 索子の棒: 角の丸い棒＋節（ふし）の線
    w = 7
    s = f'<g transform="rotate({ang} {x} {y + h / 2})"><rect x="{x - w / 2}" y="{y}" width="{w}" height="{h}" rx="3.5" fill="{col}"/>'
    s += f'<rect x="{x - w / 2 + 1.6}" y="{y + 1.5}" width="1.6" height="{h - 3}" rx=".8" fill="#fff" opacity=".35"/>'
    s += f'<line x1="{x - w / 2}" y1="{y + h / 2}" x2="{x + w / 2}" y2="{y + h / 2}" stroke="#fff" stroke-width="1.4" opacity=".8"/></g>'
    return s


S_LAYOUT = {
    2: [(30, 10, 27, GREEN), (30, 43, 27, GREEN)],
    3: [(30, 10, 27, GREEN), (19, 43, 27, GREEN), (41, 43, 27, GREEN)],
    4: [(x, y, 27, GREEN) for y in (10, 43) for x in (19, 41)],
    5: [(15, 10, 27, GREEN), (45, 10, 27, GREEN), (30, 26.5, 27, RED), (15, 43, 27, GREEN), (45, 43, 27, GREEN)],
    6: [(x, y, 27, GREEN) for y in (10, 43) for x in (13, 30, 47)],
    7: [(30, 6, 20, RED)] + [(x, y, 20, GREEN) for y in (30, 54) for x in (13, 30, 47)],
    9: [(x, y, 20, (RED if x == 30 else GREEN)) for y in (6, 30, 54) for x in (13, 30, 47)],
}


def _sou8():
    # 8索: 上はM字・下はW字（本物の並びに近い形）
    s = ""
    for y, sign in ((8, 1), (44, -1)):
        s += _stick(10, y, 28, GREEN) + _stick(50, y, 28, GREEN)
        s += _stick(23, y, 28, GREEN, 18 * sign) + _stick(37, y, 28, GREEN, -18 * sign)
    return s


def _bird():
    # 1索: まじゃすこのオリジナルの鳥（丸い体・羽・尾羽）
    return (f'<path d="M44 58 Q56 66 50 76 Q44 70 40 64 Z" fill="{BLUE}"/>'
            f'<path d="M40 60 Q54 58 56 70 Q48 68 38 66 Z" fill="{RED}"/>'
            f'<ellipse cx="30" cy="46" rx="17" ry="15" fill="{GREEN}"/>'
            f'<path d="M22 44 Q32 36 42 46 Q34 52 22 50 Z" fill="#fff" opacity=".35"/>'
            f'<circle cx="24" cy="28" r="10" fill="{GREEN}"/>'
            f'<path d="M14 27 L7 30 L14 32 Z" fill="#E75620"/>'
            f'<circle cx="21.5" cy="26" r="2.6" fill="#fff"/><circle cx="21" cy="26" r="1.4" fill="{INK}"/>'
            f'<path d="M26 18 Q30 10 36 14 Q32 16 30 20 Z" fill="{RED}"/>')


def _petals(cx, cy, n, r, pr, col, center):
    # 丸い花びら n 枚＋花の中心
    s = "".join(f'<circle cx="{cx + r * math.sin(2 * math.pi * i / n):.2f}" cy="{cy - r * math.cos(2 * math.pi * i / n):.2f}" r="{pr}" fill="{col}"/>' for i in range(n))
    return s + f'<circle cx="{cx}" cy="{cy}" r="{pr * 0.7:.2f}" fill="{center}"/>'


def _flower_pic(n):
    """花牌の絵（牌の上半分・中心 (30, 26)）。1〜4＝春夏秋冬、5〜8＝梅蘭菊竹。まじゃすこのオリジナルの絵"""
    cx, cy = 30, 26
    if n == 1:  # 春: 桜（5枚の花びら）
        return _petals(cx, cy, 5, 9, 7, RED, "#FFD23F")
    if n == 2:  # 夏: ひまわり（光のような花びら＋大きな中心）
        rays = "".join(f'<ellipse cx="{cx}" cy="{cy - 12}" rx="3.2" ry="6" fill="#F2B21C" transform="rotate({i * 30} {cx} {cy})"/>' for i in range(12))
        return rays + f'<circle cx="{cx}" cy="{cy}" r="8" fill="{GREEN}"/>'
    if n == 3:  # 秋: もみじ（5つの裂片＋ぎざぎざ＋葉脈＋柄）
        pts = []
        for ang, ln in ((0, 18), (52, 16), (-52, 16), (112, 11), (-112, 11)):
            for da, rr in ((-14, ln * 0.45), (-6, ln * 0.8), (0, ln), (6, ln * 0.8), (14, ln * 0.45)):
                a = math.radians(ang + da)
                pts.append((a, rr))
        pts.sort(key=lambda t: t[0])
        cy2 = cy + 2
        poly = " ".join(f"{cx + r * math.sin(a):.1f},{cy2 - r * math.cos(a):.1f}" for a, r in pts)
        veins = "".join(f'<line x1="{cx}" y1="{cy2}" x2="{cx + ln * 0.8 * math.sin(math.radians(ang)):.1f}" y2="{cy2 - ln * 0.8 * math.cos(math.radians(ang)):.1f}" stroke="#fff" stroke-width="1" opacity=".55"/>'
                        for ang, ln in ((0, 18), (52, 16), (-52, 16), (112, 11), (-112, 11)))
        return (f'<polygon points="{poly}" fill="{RED}" stroke="{RED}" stroke-width="1.5" stroke-linejoin="round"/>' + veins
                + f'<line x1="{cx}" y1="{cy2}" x2="{cx + 2}" y2="{cy2 + 18}" stroke="{RED}" stroke-width="2.2" stroke-linecap="round"/>')
    if n == 4:  # 冬: 雪の結晶
        s = ""
        for i in range(6):
            t = f'transform="rotate({i * 60} {cx} {cy})"'
            s += (f'<line x1="{cx}" y1="{cy}" x2="{cx}" y2="{cy - 17}" stroke="{BLUE}" stroke-width="2.6" stroke-linecap="round" {t}/>'
                  f'<path d="M{cx - 5} {cy - 14} L{cx} {cy - 9} L{cx + 5} {cy - 14}" fill="none" stroke="{BLUE}" stroke-width="2" stroke-linecap="round" {t}/>')
        return s
    if n == 5:  # 梅: 丸い5枚の花びら＋枝
        return (f'<path d="M8 44 Q22 36 30 28" fill="none" stroke="#8A5A2B" stroke-width="3" stroke-linecap="round"/>'
                + _petals(cx + 2, cy - 2, 5, 8, 7.5, "#E75A8C", "#FFD23F"))
    if n == 6:  # 蘭: 細長い葉と小さな花
        return (f'<path d="M30 46 Q18 28 10 10" fill="none" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>'
                f'<path d="M30 46 Q40 26 50 12" fill="none" stroke="{GREEN}" stroke-width="3" stroke-linecap="round"/>'
                f'<path d="M30 46 Q30 30 32 8" fill="none" stroke="{GREEN}" stroke-width="2.4" stroke-linecap="round"/>'
                + _petals(40, 22, 3, 4.5, 4, "#9B6AD6", "#FFD23F"))
    if n == 7:  # 菊: 細い花びらがたくさん
        p = "".join(f'<ellipse cx="{cx}" cy="{cy - 10}" rx="2.6" ry="8" fill="#F2B21C" transform="rotate({i * 22.5} {cx} {cy})"/>' for i in range(16))
        return p + f'<circle cx="{cx}" cy="{cy}" r="5" fill="{RED}"/>'
    # 8 竹: 節のある幹と葉
    return (f'<rect x="24" y="4" width="8" height="44" rx="3" fill="{GREEN}"/>'
            + "".join(f'<rect x="23" y="{y}" width="10" height="2.4" rx="1" fill="#0F5563"/>' for y in (16, 30))
            + f'<path d="M32 18 Q44 10 52 14 Q42 20 32 20 Z" fill="{GREEN}"/><path d="M24 32 Q12 26 6 30 Q16 36 24 34 Z" fill="{GREEN}"/>')


def _flower(n, st):
    """花牌: 上に絵、下に字、右下の角に番号（1〜4。座る席の番号）。番号は絵と字に重ならない場所に置く（2026-10-27 ユーザーの依頼で算用数字）"""
    ch = "春夏秋冬梅蘭菊竹"[n - 1]
    num = str((n - 1) % 4 + 1)
    col = {1: RED, 2: GREEN, 3: RED, 4: BLUE, 5: RED, 6: GREEN, 7: RED, 8: GREEN}[n]
    return _flower_pic(n) + _text(ch, 30, 62, 24, col, st) + _text(num, 52, 71, 11, INK, st)


def _text(ch, x, y, size, col, st):
    if st.get("glyphs"):
        return _glyph(ch, x, y, size, col, st)
    fam = st.get("font") or ("'Noto Serif JP', serif" if st["serif"] else "'Noto Sans JP', sans-serif")
    wt = st.get("weight", 900)
    # thick: 字のまわりに同じ色の線を足して太らせる（細い筆文字を、本物の牌の太い字に近づける）
    th = st.get("thick")
    extra = f' stroke="{col}" stroke-width="{th}" stroke-linejoin="round" paint-order="stroke"' if th else ""
    return f'<text x="{x}" y="{y}" font-family="{fam}" font-weight="{wt}" font-size="{size}" fill="{col}" text-anchor="middle" dominant-baseline="central"{extra}>{ch}</text>'


def _glyph(ch, x, y, size, col, st):
    """フォントから取り出した字の形（パス）を、(x, y) を中心に size の大きさで置く"""
    g = _GLYPHS[st["glyphs"]]
    d = g["glyphs"][ch]
    k = size / g["upm"]
    x0, y0, x1, y1 = d["bbox"]
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    th = st.get("thick")
    extra = f' stroke="{col}" stroke-width="{th / k:.1f}" stroke-linejoin="round"' if th else ""
    return (f'<path transform="translate({x - cx * k:.2f} {y + cy * k:.2f}) scale({k:.5f} {-k:.5f})" '
            f'd="{d["d"]}" fill="{col}"{extra}/>')


def face(code, st):
    suit, num = code[0], code[1]
    red = code.endswith("r")
    if suit == "m":
        n = int(num)
        return _text(KANJI[n - 1], 30, 24, 30, RED if red else INK, st) + _text("萬", 30, 56, 30, RED, st)
    if suit == "p":
        lay = P_LAYOUT[int(num)]
        if red:
            lay = [(x, y, r, RED, b) for x, y, r, c, b in lay]
        return "".join(_circle(x, y, r, c, b) for x, y, r, c, b in lay)
    if suit == "s":
        n = int(num)
        if n == 1:
            return _bird()
        if n == 8:
            return _sou8()
        lay = S_LAYOUT[n]
        return "".join(_stick(x, y, h, RED if red else c) for x, y, h, c in lay)
    if code == "z5":  # 白: 何も描かない（2026-10-23 ユーザーの判断。牌の枠を濃くしたので空白でも牌と分かる）
        return ""
    if code == "z5p":  # 白ぽっち: 白の真ん中に小さな赤い点（2026-10-27・三麻の記事用。赤はまじゃすこのオレンジ）
        return f'<circle cx="30" cy="40" r="5" fill="{RED}"/>'
    if suit == "f":
        return _flower(int(num), st)
    col = {"z6": GREEN, "z7": RED}.get(code, INK)
    return _text(WIND[code], 30, 40, 40, col, st)


def tile_svg(code, style="tokumin", px=None, yoko=False):
    """1枚分のSVG。yoko=True は鳴いた牌（チー・ポン・カンで横に倒した牌）。
    横向きでも絵だけを左に90度倒し、牌の背（緑の厚み）は常に下に置く（机に置いた牌を横から見た形）。
    code="back" は裏向きの牌（暗槓の両端など）。表の面がまじゃすこの緑になる"""
    st = STYLES[style]
    bh = st["back_h"]
    w, h = (H, W) if yoko else (W, H)
    total_h = h + bh
    out = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 {w + 2} {total_h + 2}"' + (f' width="{px}" height="{px * (total_h + 2) / (w + 2):.0f}"' if px else "") + ">"
    if st["back"]:
        out += f'<rect x="0" y="{bh}" width="{w}" height="{h}" rx="{st["rx"]}" fill="{st["back"]}"/>'
        if st.get("gloss"):
            out += f'<rect x="3" y="{h + bh - 4}" width="{w - 6}" height="2" rx="1" fill="#fff" opacity=".25"/>'
    if code == "back":
        # 裏向き: 面には何も描かない。面は明るい緑、下の厚みはいつもの緑（色の違いで面と厚みを見分ける）
        out += f'<rect x="0" y="0" width="{w}" height="{h}" rx="{st["rx"]}" fill="{BACK_FACE}" stroke="{BACK_EDGE}" stroke-width="{EDGE_W}"/>'
        return out + "</svg>"
    out += f'<rect x="0" y="0" width="{w}" height="{h}" rx="{st["rx"]}" fill="{st["face"]}"' + (f' stroke="{st["edge"]}" stroke-width="{st["stroke"]}"' if st["stroke"] else "") + "/>"
    if st["back"]:
        out += f'<rect x="0" y="{h - 3}" width="{w}" height="3" fill="{st["edge"]}" opacity=".9"/><rect x="0" y="0" width="{w}" height="{h}" rx="{st["rx"]}" fill="none" stroke="{EDGE}" stroke-width="{EDGE_W}"/>'
    body = face(code, st)
    if yoko:  # 縦の絵（60×80）を左に90度倒して、横の面（80×60）に入れる。上にあった部分が左に来る
        body = f'<g transform="translate(0 {W}) rotate(-90)">{body}</g>'
    return out + body + "</svg>"

ALL = ["back"] + [f"m{i}" for i in range(1, 10)] + [f"p{i}" for i in range(1, 10)] + [f"s{i}" for i in range(1, 10)] + [f"z{i}" for i in range(1, 8)] + ["m5r", "p5r", "s5r"] + ["z5p"] + [f"f{i}" for i in range(1, 9)]


PLATE_W, PLATE_H = 100, 50   # 卓に置く札（起家札・焼き鳥カード）の表の大きさ。横長で置く（2026-10-27 ユーザーの依頼「起家札と同じサイズ感・同じ向き」）


def _plate(face, edge, back, inner):
    """横長の札の土台（表の面・枠・内側の細い線・下の厚み）。厚みの高さは牌と同じ"""
    w, h, bh = PLATE_W, PLATE_H, STYLES["tokumin"]["back_h"]
    out = f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 {w + 2} {h + bh + 2}">'
    out += f'<rect x="0" y="{bh}" width="{w}" height="{h}" rx="6" fill="{back}"/>'
    out += f'<rect x="0" y="0" width="{w}" height="{h}" rx="6" fill="{face}" stroke="{edge}" stroke-width="1.6"/>'
    out += f'<rect x="4" y="4" width="{w - 8}" height="{h - 8}" rx="4" fill="none" stroke="{inner}" stroke-width="1" opacity=".75"/>'
    return out


def chicha_svg(ura=False):
    """起家札（2026-10-27）。表＝東、裏＝南（南場に入ったら裏返す）。牌と同じクリームの面・緑の厚み"""
    st = STYLES["tokumin"]
    out = _plate(STYLES["tokumin"]["face"], EDGE, GREEN, EDGE)
    col = BLUE if ura else RED
    out += f'<circle cx="50" cy="25" r="17" fill="none" stroke="{col}" stroke-width="2"/>'
    out += _text("南" if ura else "東", 50, 25, 24, col, st)
    return out + "</svg>"


def tenbo_svg():
    """1000点棒（2026-10-27・マイページのアイコン用）。白い棒の真ん中に赤い点、両端に小さな点"""
    out = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 102 22">'
    out += '<rect x="0" y="3" width="100" height="16" rx="8" fill="#C9D6D3"/><rect x="0" y="0" width="100" height="16" rx="8" fill="#fff" stroke="#A79E87" stroke-width="1.4"/>'
    out += f'<circle cx="50" cy="8" r="4" fill="{RED}"/>'
    return out + "</svg>"


def dice_svg():
    """サイコロ（2026-10-27・マイページのアイコン用）。5の目、真ん中だけ赤"""
    out = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-1 -1 62 68">'
    out += f'<rect x="0" y="6" width="60" height="60" rx="12" fill="{GREEN}"/><rect x="0" y="0" width="60" height="60" rx="12" fill="#fff" stroke="#A79E87" stroke-width="1.6"/>'
    for x, y in ((16, 16), (44, 16), (16, 44), (44, 44)):
        out += f'<circle cx="{x}" cy="{y}" r="5.5" fill="{INK}"/>'
    out += f'<circle cx="30" cy="30" r="7.5" fill="{RED}"/>'
    return out + "</svg>"


def yakitori_svg(ura=False):
    """焼き鳥カード（2026-10-27・三麻の記事用）。起家札と同じ大きさ・同じ横向きの札。表・裏ともオレンジ。
    表＝焼き鳥の絵だけ＋左上の角に小さく「表」（まだあがっていない人の前に置く）。ura=True は何も描かない裏＋左上に小さく「裏」（あがったら裏返す）。
    絵はまじゃすこのオリジナル"""
    st = STYLES["tokumin"]
    out = _plate("#F39A4E", RED, "#B8461A", "#FFF4E2")
    out += _text("裏" if ura else "表", 10, 11, 8, "#FFF4E2", st)
    if ura:
        return out + "</svg>"
    out += '<ellipse cx="52" cy="25" rx="36" ry="17" fill="#FFF4E2"/>'
    # 串（ほぼ横向き）と、肉・ねぎ・肉・ねぎ・肉。縦に描いた串を倒して札の真ん中に置く
    g = '<g transform="translate(52 25) rotate(-78) translate(-35 -52)">'
    g += '<rect x="33.6" y="19" width="2.8" height="66" rx="1.4" fill="#C9A26B"/>'
    y = 24
    for kind in ("niku", "negi", "niku", "negi", "niku"):
        if kind == "niku":
            g += f'<rect x="25" y="{y}" width="20" height="13" rx="6" fill="#B65A22"/>'
            g += f'<path d="M28 {y + 4} L42 {y + 4} M28 {y + 8.5} L42 {y + 8.5}" stroke="#7A3510" stroke-width="1.6" stroke-linecap="round" opacity=".7"/>'
            g += f'<rect x="28" y="{y + 1.5}" width="7" height="2" rx="1" fill="#fff" opacity=".3"/>'
            y += 13.5
        else:
            g += f'<rect x="27" y="{y}" width="16" height="8" rx="3" fill="#EFF3D6"/><rect x="27" y="{y}" width="16" height="3" rx="1.5" fill="#7DB346"/>'
            y += 8.5
    g += '</g>'
    out += g
    return out + "</svg>"
