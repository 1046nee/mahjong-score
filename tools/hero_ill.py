# -*- coding: utf-8 -*-
# テーマの一覧ページの見出しの右に出す絵（200×120）。文字は入れない（端末で字形が変わるため）
O = "#E75620"; INK = "#1F2A28"
def sp(x, y, s=1, c=O):  # 4つの角の星
    return f'<path d="M{x} {y-7*s} L{x+2*s} {y-2*s} L{x+7*s} {y} L{x+2*s} {y+2*s} L{x} {y+7*s} L{x-2*s} {y+2*s} L{x-7*s} {y} L{x-2*s} {y-2*s} Z" fill="{c}"/>'
def tile(x, y, c, w=26, h=36, inner=''):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" fill="#fff" stroke="{c}" stroke-width="2.5"/>'
            f'<rect x="{x}" y="{y+h-5}" width="{w}" height="5" rx="2.5" fill="{c}"/>' + inner)
def svg(body): return f'<svg viewBox="0 0 200 120" xmlns="http://www.w3.org/2000/svg">{body}</svg>'
def beginner(c="#16A34A"):  # 開いた本と、芽（はじめて）
    return svg(f'<path d="M36 40 Q68 30 100 42 V100 Q68 90 36 100 Z" fill="#fff" stroke="{c}" stroke-width="2.5" stroke-linejoin="round"/>'
               f'<path d="M164 40 Q132 30 100 42 V100 Q132 90 164 100 Z" fill="#fff" stroke="{c}" stroke-width="2.5" stroke-linejoin="round"/>'
               f'<g stroke="{c}" stroke-width="2.5" stroke-linecap="round" opacity=".45"><path d="M48 54 Q66 48 88 56"/><path d="M48 66 Q66 60 88 68"/><path d="M48 78 Q66 72 88 80"/></g>'
               + tile(118, 52, c, 22, 30, f'<circle cx="129" cy="62" r="4.5" fill="{O}"/><circle cx="129" cy="72" r="3" fill="{c}"/>')
               + f'<path d="M100 42 V20" stroke="{c}" stroke-width="3" stroke-linecap="round"/><path d="M100 28 Q86 26 82 14 Q96 14 100 26 Z" fill="{c}"/><path d="M100 24 Q112 18 118 8 Q104 8 100 22 Z" fill="#7BD39A"/>'
               + sp(160, 22, .9) + sp(28, 28, .7, c))
def rules(c="#0E95A3"):  # 決まりの紙と虫めがね（深掘り）
    return svg(f'<rect x="40" y="14" width="74" height="94" rx="7" fill="#fff" stroke="{c}" stroke-width="2.5"/>'
               + ''.join(f'<rect x="52" y="{30+i*18}" width="10" height="10" rx="2.5" fill="{c if i!=2 else O}"/><rect x="68" y="{32+i*18}" width="34" height="5" rx="2.5" fill="{c}" opacity=".35"/>' for i in range(4))
               + f'<circle cx="128" cy="62" r="24" fill="#fff" fill-opacity=".85" stroke="{INK}" stroke-width="5"/><circle cx="128" cy="62" r="16" fill="none" stroke="{c}" stroke-width="2" opacity=".5"/>'
               f'<path d="M145 79 L166 100" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>' + sp(170, 26, .9) + sp(28, 96, .7, c))
def score(c="#C2410C"):  # 成績のグラフと表彰台（集計）
    return svg(f'<rect x="28" y="16" width="96" height="78" rx="8" fill="#fff" stroke="{c}" stroke-width="2.5"/>'
               f'<path d="M40 78 L62 60 L80 68 L110 34" fill="none" stroke="{c}" stroke-width="3.5" stroke-linecap="round" stroke-linejoin="round"/><circle cx="110" cy="34" r="5" fill="{O}"/>'
               f'<g stroke="{c}" stroke-width="1.5" opacity=".25"><path d="M38 40 H116"/><path d="M38 58 H116"/><path d="M38 76 H116"/></g>'
               f'<rect x="132" y="70" width="18" height="34" rx="3" fill="#fff" stroke="{c}" stroke-width="2.5"/><rect x="150" y="54" width="18" height="50" rx="3" fill="{c}"/><rect x="168" y="80" width="18" height="24" rx="3" fill="#fff" stroke="{c}" stroke-width="2.5"/>'
               f'<circle cx="159" cy="42" r="7" fill="#FFD23F" stroke="{INK}" stroke-width="2"/>' + sp(182, 24, .8))
def pro(c="#7C3AED"):  # トロフィーとスポットライト（Mリーグ・プロ）
    return svg(f'<path d="M100 4 L60 112 H140 Z" fill="{c}" opacity=".12"/>'
               f'<path d="M78 26 H122 V44 A22 22 0 0 1 78 44 Z" fill="#FFD23F" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
               f'<path d="M78 32 H66 A10 10 0 0 0 80 52" fill="none" stroke="{INK}" stroke-width="2.5"/><path d="M122 32 H134 A10 10 0 0 1 120 52" fill="none" stroke="{INK}" stroke-width="2.5"/>'
               f'<rect x="95" y="66" width="10" height="14" fill="{INK}"/><rect x="82" y="80" width="36" height="9" rx="2" fill="{c}"/><rect x="76" y="89" width="48" height="12" rx="3" fill="{c}"/>'
               f'<circle cx="100" cy="40" r="5" fill="#fff" opacity=".7"/>' + sp(46, 30, 1) + sp(156, 22, .8, c) + sp(152, 84, .7))
def ai(c="#0284C7"):  # ロボットと牌譜（AI・ゲーム）
    return svg(f'<path d="M66 18 V28" stroke="{INK}" stroke-width="3" stroke-linecap="round"/><circle cx="66" cy="15" r="5" fill="{O}"/>'
               f'<rect x="34" y="28" width="64" height="50" rx="14" fill="#fff" stroke="{c}" stroke-width="2.5"/><circle cx="54" cy="52" r="6" fill="{INK}"/><circle cx="78" cy="52" r="6" fill="{INK}"/>'
               f'<rect x="54" y="64" width="24" height="5" rx="2.5" fill="{c}"/><rect x="44" y="82" width="44" height="22" rx="8" fill="{c}"/>'
               f'<rect x="110" y="20" width="62" height="80" rx="7" fill="#fff" stroke="{c}" stroke-width="2.5"/>'
               + ''.join(f'<rect x="120" y="{32+i*14}" width="{42 if i%2==0 else 30}" height="5" rx="2.5" fill="{c}" opacity=".35"/>' for i in range(5))
               + f'<rect x="146" y="58" width="16" height="8" rx="2" fill="{O}"/>' + sp(182, 18, .8))
def culture(c="#DB2777"):  # 本と動画（漫画・アニメ・YouTube）
    return svg(f'<rect x="30" y="34" width="20" height="70" rx="3" fill="{c}"/><rect x="52" y="26" width="20" height="78" rx="3" fill="#fff" stroke="{c}" stroke-width="2.5"/><rect x="74" y="40" width="18" height="64" rx="3" fill="#FFD23F" stroke="{INK}" stroke-width="2"/>'
               f'<path d="M26 104 H98" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
               f'<rect x="106" y="30" width="72" height="50" rx="10" fill="#fff" stroke="{c}" stroke-width="2.5"/><path d="M135 44 L135 66 L154 55 Z" fill="{O}"/>'
               f'<rect x="114" y="88" width="56" height="6" rx="3" fill="{c}" opacity=".35"/><rect x="114" y="88" width="24" height="6" rx="3" fill="{c}"/>' + sp(178, 18, .8) + sp(110, 14, .6, c))
ILL = {"beginner": beginner(), "rules": rules(), "score": score(), "pro": pro(), "ai": ai(), "culture": culture()}
if __name__ == "__main__":
    import os
    d = os.path.dirname(os.path.abspath(__file__))
    html = '<html><body style="margin:0;display:grid;grid-template-columns:repeat(3,320px);gap:12px;padding:12px;background:#eee">' + ''.join(f'<div style="background:#fff;padding:8px">{k}<br>{v.replace("<svg ", "<svg width=300 ")}</div>' for k, v in ILL.items()) + '</body></html>'
    open(os.path.join(d, 'ill.html'), 'w').write(html)
