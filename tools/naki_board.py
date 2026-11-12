# -*- coding: utf-8 -*-
"""鳴きの手順の、上から見た卓の図（記事 blog-naki-tejun と動画 t-naki で同じ絵を使う）。
BASE を差しかえると、牌の絵の場所を変えられる（動画は file:// で読む）。"""
BASE = "/assets/tiles/"

def T(code, x, y, w, rot=0, op=1.0):
    """卓の図の牌（まじゃすこの牌の絵）。rot=90 で横向き"""
    yoko = rot in (90, 270)
    f = f"{code}-yoko" if yoko else code
    ww = w * (82 / 62) if yoko else w
    h = ww * 69 / 82 if yoko else w * 89 / 62     # 横向きは 82:69。高さを w×69/82 にすると枠が横長すぎて、絵が枠の中で縮む（小さく見えていた）
    return f'<image href="{BASE}{f}.svg" x="{x:.1f}" y="{y:.1f}" width="{ww:.1f}" height="{h:.1f}" opacity="{op}"/>'

def board(step):
    """上から見た卓。自分は下。上家（左の人）の河の最後の六萬をチーする。step=1〜5"""
    W = 320
    g = [f'<rect x="6" y="6" width="{W-12}" height="{W-12}" rx="22" fill="#E4F3EC" stroke="#9fc3bd" stroke-width="2"/>']
    tw = 20
    th = tw * 89 / 62
    # 上家の河（左。牌は上家の向き＝90度回す）。最後が六萬
    riv_left = ["z1", "m9", "p2", "s8", "z3", "m6"]
    lx, ly = 62, 52
    for i, c in enumerate(riv_left):
        hl = (i == 5)
        if hl and step >= 3:
            continue
        cx, cy = lx + th / 2, ly + i * (tw + 2) + tw / 2
        g.append(f'<g transform="rotate(90 {cx:.1f} {cy:.1f})">' + T(c, cx - tw / 2, cy - th / 2, tw, op=1 if hl else .5) + "</g>")
    hy = ly + 5 * (tw + 2)
    if step < 3:
        g.append(f'<rect x="{lx-3}" y="{hy-3}" width="{th+6:.0f}" height="{tw+6}" rx="5" fill="none" stroke="#E75620" stroke-width="3"/>')
    else:
        g.append(f'<rect x="{lx-1}" y="{hy-1}" width="{th+2:.0f}" height="{tw+2}" rx="4" fill="none" stroke="#9fc3bd" stroke-width="1.5" stroke-dasharray="3 3"/>')
    # 自分の河
    my_riv = ["z2", "m1", "p8"] + (["s3"] if step >= 5 else [])
    rx, ry = 122, 196
    for i, c in enumerate(my_riv):
        g.append(T(c, rx + i * (tw + 2), ry, tw, op=1 if (step >= 5 and i == 3) else .5))
    if step >= 5:
        g.append(f'<rect x="{rx + 3 * (tw + 2) - 3}" y="{ry - 3}" width="{tw + 6}" height="{th + 6:.0f}" rx="5" fill="none" stroke="#E75620" stroke-width="3"/>')
    # 自分の手牌
    hand = ["m4", "m5", "p3", "p4", "p6", "p7", "s3", "s5", "s6", "s7", "z7", "z7", "p9"]
    hw = 16; hx = 14; hyy = 272; k = 0
    for c in hand:
        if step >= 2 and c in ("m4", "m5"): continue
        if step >= 5 and c == "s3": continue
        g.append(T(c, hx + k * (hw + 1), hyy, hw)); k += 1
    if step == 1:
        g.append(f'<rect x="{hx-3}" y="{hyy-4}" width="{2*(hw+1)+4}" height="31" rx="5" fill="none" stroke="#177083" stroke-width="2.5" stroke-dasharray="4 3"/>')
    # 晒した牌・副露（右下の隅）
    mx, my = 246, 272
    if step >= 2:
        if step >= 3:
            g.append(T("m6", mx - 22, my + 5.2, hw, rot=90))
        g.append(T("m4", mx, my, hw)); g.append(T("m5", mx + hw + 1, my, hw))
        x0 = mx - (26 if step >= 3 else 4)
        dash = "" if step >= 4 else 'stroke-dasharray="4 3"'
        g.append(f'<rect x="{x0}" y="{my-5}" width="{mx + 2*(hw+1) + 3 - x0}" height="33" rx="6" fill="none" stroke="#E75620" stroke-width="2.5" {dash}/>')
    def arrow(x1, y1, x2, y2, col="#E75620", lift=34):
        return (f'<path d="M{x1} {y1} Q {(x1+x2)/2} {min(y1,y2)-lift} {x2} {y2}" fill="none" stroke="{col}" stroke-width="3.5" stroke-linecap="round" marker-end="url(#ah{col[1:]})"/>')
    if step == 2: g.append(arrow(32, 266, 262, 264, "#177083", 40))
    if step == 3: g.append(arrow(lx + th + 6, hy + 14, mx - 12, my - 6, lift=10))
    if step == 5: g.append(arrow(120, 268, rx + 3 * (tw + 2) + 4, ry + th + 8, lift=-6))
    defs = ("<defs>" + "".join(f'<marker id="ah{c}" viewBox="0 0 10 10" refX="7" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#{c}"/></marker>' for c in ("E75620", "177083")) + "</defs>")
    seats = ('<text x="160" y="26" text-anchor="middle" font-size="12" font-weight="800" fill="#5F6E6B">対面</text>'
             '<text x="26" y="150" text-anchor="middle" font-size="12" font-weight="800" fill="#5F6E6B">上家</text>'
             '<text x="294" y="150" text-anchor="middle" font-size="12" font-weight="800" fill="#5F6E6B">下家</text>'
             '<text x="160" y="312" text-anchor="middle" font-size="11" font-weight="800" fill="#177083">自分</text>')
    call = ('<rect x="104" y="232" width="112" height="28" rx="14" fill="#E75620"/><text x="160" y="251" text-anchor="middle" font-size="15" font-weight="900" fill="#fff">チー！</text>') if step == 1 else ""
    return f'<svg viewBox="0 0 {W} {W}" xmlns="http://www.w3.org/2000/svg" role="img" class="nk-board">{defs}{"".join(g)}{seats}{call}</svg>'
