# -*- coding: utf-8 -*-
"""世界の麻雀の記事などで使う、国旗の小さな絵（SVG・2026-10-27〜）。
国旗は 30×20 の枠で、細部を省いた形で描く（星の向きなどは簡略）。
国ではない地域（香港・台湾）は国旗を使わず、地図のピンの印にする（政治的に扱いが分かれる旗を避ける）。
  flag_svg(code, w)      … 記事に置く <svg>（幅 w px）
  flag_g(code, x, y, w)  … サムネイルなど大きなSVGの中に置く <g>
code: jp（日本）・cn（中国）・us（アメリカ）・vn（ベトナム）・pin（地域の印）
"""
import math


def star(cx, cy, r, fill, rot=0):
    pts = []
    for i in range(10):
        a = math.radians(rot - 90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.382
        pts.append(f"{cx + rr * math.cos(a):.2f},{cy + rr * math.sin(a):.2f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def body(code):
    if code == "jp":
        return '<rect width="30" height="20" fill="#fff"/><circle cx="15" cy="10" r="6" fill="#BC002D"/>'
    if code == "cn":
        s = '<rect width="30" height="20" fill="#DE2910"/>' + star(5, 5, 3, "#FFDE00")
        for x, y in ((10, 2), (12, 4), (12, 7), (10, 9)):
            s += star(x, y, 1, "#FFDE00", rot=math.degrees(math.atan2(5 - y, 5 - x)) + 90)
        return s
    if code == "us":
        sh = 20 / 13
        s = '<rect width="30" height="20" fill="#fff"/>'
        s += "".join(f'<rect y="{i * sh:.2f}" width="30" height="{sh:.2f}" fill="#B22234"/>' for i in range(0, 13, 2))
        s += f'<rect width="12" height="{sh * 7:.2f}" fill="#3C3B6E"/>'
        s += "".join(f'<circle cx="{1.5 + c * 2.25:.2f}" cy="{1.4 + r * 2.1:.2f}" r=".45" fill="#fff"/>' for r in range(5) for c in range(5))
        return s
    if code == "vn":
        return '<rect width="30" height="20" fill="#DA251D"/>' + star(15, 10.5, 6, "#FFFF00")
    # pin: 地域の印（青い地に白い地図のピン）
    return ('<rect width="30" height="20" fill="#EAF0FB"/>'
            '<path d="M15 3.2 a4.6 4.6 0 0 1 4.6 4.6 c0 3.4 -4.6 8.6 -4.6 8.6 s-4.6 -5.2 -4.6 -8.6 a4.6 4.6 0 0 1 4.6 -4.6 Z" fill="#4261AA"/>'
            '<circle cx="15" cy="7.8" r="1.8" fill="#fff"/>')


def flag_svg(code, w=30, label=""):
    h = round(w * 2 / 3, 1)
    # label なし（見出しの飾りなど）は読み上げない。<title> を入れないので、見出しの文字（目次）にも混ざらない
    attr = f'role="img" aria-label="{label}"><title>{label}</title>' if label else 'aria-hidden="true">'
    return (f'<svg class="flag" viewBox="0 0 30 20" width="{w}" height="{h}" {attr}'
            f'<clipPath id="fc-{code}-{w}"><rect width="30" height="20" rx="2"/></clipPath>'
            f'<g clip-path="url(#fc-{code}-{w})">{body(code)}</g>'
            f'<rect x=".25" y=".25" width="29.5" height="19.5" rx="2" fill="none" stroke="#1F2A28" stroke-opacity=".18" stroke-width=".5"/></svg>')


def flag_g(code, x, y, w):
    k = w / 30
    return (f'<g transform="translate({x} {y}) scale({k:.4f})">'
            f'<rect x="-1" y="1.2" width="32" height="20" rx="3" fill="#000" opacity=".12"/>'
            f'<rect width="30" height="20" rx="2" fill="#fff"/><g>{body(code)}</g>'
            f'<rect x=".25" y=".25" width="29.5" height="19.5" rx="2" fill="none" stroke="#1F2A28" stroke-opacity=".18" stroke-width=".5"/></g>')
