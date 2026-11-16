import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
import machi3 as M3
from functools import lru_cache
CODES = M3.CODES
def cnt(hand):
    c = [0] * 34
    for h in hand: c[CODES.index(h)] += 1
    return c
def decomp(c, m, p):
    """1つの分け方（面子・雀頭のリスト）を返す"""
    c = list(c)
    if sum(c) == 0: return []
    i = next(k for k in range(34) if c[k])
    if c[i] >= 3 and m:
        c[i] -= 3; r = decomp(c, m - 1, p) if M3.dec(tuple(c), m - 1, p) else None
        if r is not None: return [("k", [i] * 3)] + r
        c[i] += 3
    if c[i] >= 2 and p:
        c[i] -= 2; r = decomp(c, m, p - 1) if M3.dec(tuple(c), m, p - 1) else None
        if r is not None: return [("j", [i] * 2)] + r
        c[i] += 2
    if m and i < 27 and i % 9 <= 6 and c[i + 1] and c[i + 2]:
        c[i] -= 1; c[i + 1] -= 1; c[i + 2] -= 1
        r = decomp(c, m - 1, p) if M3.dec(tuple(c), m - 1, p) else None
        if r is not None: return [("s", [i, i + 1, i + 2])] + r
    return None
TYPES = [("両面", "#E02424"), ("嵌張", "#1F6FD1"), ("辺張", "#8E3FD0"), ("双碰", "#16A05A"), ("単騎", "#E8730C")]      # 待ち方は原色で分ける（2026-11-16 ユーザーの指定）
TCOL = dict(TYPES)
def all_decomps(c, m, p):
    """すべての分け方（面子・雀頭のリスト）"""
    c = list(c)
    if sum(c) == 0: yield []; return
    i = next(k for k in range(34) if c[k])
    if c[i] >= 3 and m:
        c[i] -= 3
        for r in all_decomps(c, m - 1, p): yield [("k", [i] * 3)] + r
        c[i] += 3
    if c[i] >= 2 and p:
        c[i] -= 2
        for r in all_decomps(c, m, p - 1): yield [("j", [i] * 2)] + r
        c[i] += 2
    if m and i < 27 and i % 9 <= 6 and c[i + 1] and c[i + 2]:
        c[i] -= 1; c[i + 1] -= 1; c[i + 2] -= 1
        for r in all_decomps(c, m - 1, p): yield [("s", [i, i + 1, i + 2])] + r
def kinds(hand, w, m):
    """待ちの牌 w が、どの待ち方（両面・嵌張・辺張・双碰・単騎）でアガれるか"""
    c = cnt(hand); wi = CODES.index(w); c[wi] += 1; out = set()
    for d in all_decomps(c, m, 1):
        for k, g in d:
            if wi not in g: continue
            if k == "j": out.add("単騎")
            elif k == "k": out.add("双碰")
            else:
                a_ = g[0]
                if wi == a_ + 1: out.add("嵌張")
                elif wi == a_: out.add("辺張" if (a_ + 2) % 9 == 8 else "両面")
                else: out.add("辺張" if a_ % 9 == 0 else "両面")
    return [t for t, _ in TYPES if t in out]
def tl2(code, w, ks=None):
    """ks＝待ち方のリスト。点線の枠を待ち方の色に（2つあるときは左右で色を分ける）"""
    if ks:
        a = TCOL[ks[0]]; b = TCOL[ks[-1]]
        return f'<span class="dt" style="width:{w}px;height:{round(w * 1.36)}px;border-color:{a} {b} {b} {a}">{tl(code, w - 6)}</span>'
    return tl(code, w)
def top_view(hand, ws, km):
    """手の牌を並べ、手に無い数字（隙間）に来る待ちだけを点線で差し込む（端の外の待ちは横の図で見せる。2026-11-16 ユーザーの指定: 点線が多いと見づらい）"""
    have = {CODES.index(h) for h in hand}; lo = min(CODES.index(h) for h in hand if h[0] != "z"); hi = max(CODES.index(h) for h in hand if h[0] != "z")
    gaps = []      # 間に点線の牌を差し込む表示はやめた（2026-11-16 ユーザーの指定）。待ちは横から見た図とラベルで見せる
    items = sorted([(CODES.index(h), 0, h) for h in hand] + gaps, key=lambda x: (x[0], x[1]))
    out = ""; prev = None
    for idx, d, code in items:
        if prev is not None and idx >= 27 and prev < 27: out += '<span class="gap"></span>'
        out += tl2(code, 30, km[code] if d else None); prev = idx
    return out
import os as _os, itertools as _it
_CNT = _it.count()
BOX = _os.environ.get("BOX", "solid")      # 点線なし・薄めの塗りに決定（2026-11-16 ユーザーの判断）
K47 = _os.environ.get("K47", "#1F2A28")      # 4枚形・7枚形の札と、解説のその枠の色
HAND = _os.environ.get("HAND", "#1F2A28")      # 横から見た図の手にある牌は黒（2026-11-16 ユーザーの指定）
DUAL = _os.environ.get("DUAL", "half"); NUM = _os.environ.get("NUM", "split")      # 2つの待ち方を持つ数字は、数字そのものを左右で2色に（2026-11-16 ユーザーの判断）
SW = _os.environ.get("SW", "1.2"); DA = _os.environ.get("DA", "2.5 1.5")      # 点線の太さと、点と間の長さ（点線の版のとき）
def box(x, y, w, h, cols):
    """待ちの1枚分の箱（丸い角）。cols が2色なら左右で塗り分ける"""
    cid = "c%d_%d" % (round(x * 10), round(y * 10))
    clip = f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5"/></clipPath>'
    op = _os.environ.get("OP") or (".35" if BOX == "dash" else ".45")
    if len(cols) == 1: fill = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{cols[0]}" opacity="{op}"/>'
    elif DUAL == "diag":     # 斜めに2色
        fill = f'<path d="M{x} {y} H{x + w} L{x} {y + h} Z" fill="{cols[0]}" opacity="{op}"/><path d="M{x + w} {y} V{y + h} H{x} Z" fill="{cols[1]}" opacity="{op}"/>'
    elif DUAL == "stripe":   # 2色の縞
        n = 6; sw_ = w / n
        fill = "".join(f'<rect x="{x + k * sw_}" y="{y}" width="{sw_}" height="{h}" fill="{cols[k % 2]}" opacity="{op}"/>' for k in range(n))
    else: fill = f'<rect x="{x}" y="{y}" width="{w / 2}" height="{h}" fill="{cols[0]}" opacity="{op}"/><rect x="{x + w / 2}" y="{y}" width="{w / 2}" height="{h}" fill="{cols[1]}" opacity="{op}"/>'
    out = clip + f'<g clip-path="url(#{cid})">{fill}</g>'
    if BOX == "dash":
        if len(cols) == 1: out += f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5" fill="none" stroke="{cols[0]}" stroke-width="{SW}" stroke-dasharray="{DA}"/>'
        else: out += (f'<path d="M{x + w / 2} {y} H{x + 2.5} Q{x} {y} {x} {y + 2.5} V{y + h - 2.5} Q{x} {y + h} {x + 2.5} {y + h} H{x + w / 2}" fill="none" stroke="{cols[0]}" stroke-width="{SW}" stroke-dasharray="{DA}"/>'
                      f'<path d="M{x + w / 2} {y} H{x + w - 2.5} Q{x + w} {y} {x + w} {y + 2.5} V{y + h - 2.5} Q{x + w} {y + h} {x + w - 2.5} {y + h} H{x + w / 2}" fill="none" stroke="{cols[1]}" stroke-width="{SW}" stroke-dasharray="{DA}"/>')
    return out
HSTY = _os.environ.get("HSTY", "hatch")      # 横から見た図の手にある牌＝白地に黒の斜め線（2026-11-16 ユーザーの判断・案B）
def hand_box(x, y, w, h):
    base = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="2.5"'
    if HSTY == "solid": return base + f' fill="{HAND}"/>'
    if HSTY == "outline": return base + f' fill="#fff" stroke="{HAND}" stroke-width="1.6"/>'
    pat = {"hatch": "hp1", "hatch2": "hp2", "stripe": "hp3", "dots": "hp4"}[HSTY]
    return base + f' fill="url(#{pat})" stroke="{HAND}" stroke-width="1.2"/>'
PATDEF = ('<defs>'
  '<pattern id="hp1" width="3.2" height="3.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3.2" height="3.2" fill="#fff"/><rect width="1.4" height="3.2" fill="#1F2A28"/></pattern>'
  '<pattern id="hp2" width="3.2" height="3.2" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="3.2" height="3.2" fill="#5E6B69"/><rect width="1.4" height="3.2" fill="#1F2A28"/></pattern>'
  '<pattern id="hp3" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#fff"/><rect width="1.3" height="3" fill="#1F2A28"/></pattern>'
  '<pattern id="hp4" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#fff"/><circle cx="1.5" cy="1.5" r=".8" fill="#1F2A28"/></pattern>'
  '</defs>')
def side_view(hand, ws, km):
    """横から見た図: 横＝数字（1〜9。字牌があれば東も）・縦＝枚数（0〜4）。手の牌は灰色の実線、待ちの残りは待ち方の色の点線"""
    c = cnt(hand); wset = {CODES.index(w): w for w, n in ws}
    cols = [9 + k for k in range(9)] + ([27] if any(h[0] == "z" for h in hand) or any(w[0] == "z" for w, _ in ws) else [])
    CW, RH, X0, Y0 = 24, 8, 16, 4      # 縦を低く（カードの縦幅を詰める。2026-11-16 ユーザーの指定）
    W = X0 + CW * 10 + 8 + 4; H = Y0 + RH * 4 + 15      # 東の列が無い形も同じ幅（図の位置をそろえる）
    XE = X0 + CW * len(cols) + (8 if len(cols) > 9 else 0)
    g = ""
    for r in range(5):
        y = Y0 + RH * 4 - r * RH; g += f'<line x1="{X0}" y1="{y}" x2="{XE}" y2="{y}" stroke="#DDE5E3" stroke-width="1"/><text x="{X0 - 5}" y="{y + 3}" font-size="7" font-weight="800" fill="#8A9A97" text-anchor="end">{r}</text>'
    for k, t in enumerate(cols):
        x = X0 + CW * k + (8 if t == 27 else 0)
        lab = "東" if t == 27 else str(t - 8)
        ks = km[wset[t]] if t in wset else None; col = TCOL[ks[0]] if ks else None
        if ks:      # 待ちになる数字には、すべて下に待ち方の色の線（2つなら左右で2色。2026-11-16 ユーザーの指定）
            if len(ks) == 1: g += f'<rect x="{x + 3}" y="{H - 1.5}" width="{CW - 6}" height="2" fill="{TCOL[ks[0]]}"/>'
            else: g += f'<rect x="{x + 3}" y="{H - 1.5}" width="{CW / 2 - 3}" height="2" fill="{TCOL[ks[0]]}"/><rect x="{x + CW / 2}" y="{H - 1.5}" width="{CW / 2 - 3}" height="2" fill="{TCOL[ks[1]]}"/>'
        if ks and len(ks) > 1 and NUM == "dots":      # 数字は黒、右上に待ち方の色の点を2つ
            col = "#1F2A28"; g += f'<circle cx="{x + CW / 2 + 6}" cy="{H - 11}" r="1.8" fill="{TCOL[ks[0]]}"/><circle cx="{x + CW / 2 + 10}" cy="{H - 11}" r="1.8" fill="{TCOL[ks[1]]}"/>'
        if ks and len(ks) > 1 and NUM == "split":     # 数字の左半分と右半分を2色に
            cid = f"n{next(_CNT)}"; g += (f'<clipPath id="{cid}a"><rect x="{x}" y="{H - 14}" width="{CW / 2}" height="16"/></clipPath><clipPath id="{cid}b"><rect x="{x + CW / 2}" y="{H - 14}" width="{CW / 2}" height="16"/></clipPath>'
                                 f'<text x="{x + CW / 2}" y="{H - 3}" font-size="10" font-weight="900" fill="{TCOL[ks[0]]}" text-anchor="middle" clip-path="url(#{cid}a)">{lab}</text>'
                                 f'<text x="{x + CW / 2}" y="{H - 3}" font-size="10" font-weight="900" fill="{TCOL[ks[1]]}" text-anchor="middle" clip-path="url(#{cid}b)">{lab}</text>'); continue_lab = True
        else: continue_lab = False
        if not continue_lab: g += f'<text x="{x + CW / 2}" y="{H - 3}" font-size="10" font-weight="900" fill="{col or "#1F2A28"}" text-anchor="middle">{lab}</text>'
        for r in range(c[t]):
            y = Y0 + RH * 4 - (r + 1) * RH
            g += hand_box(x + 2, y + 1, CW - 4, RH - 2)
        if ks:
            for r in range(c[t], 4):
                y = Y0 + RH * 4 - (r + 1) * RH
                if len(ks) == 1:
                    g += box(x + 2.5, y + 1.5, CW - 5, RH - 3, [col])
                else:      # 左半分と右半分を、2つの待ち方の色に
                    hw = (CW - 5) / 2
                    g += box(x + 2.5, y + 1.5, CW - 5, RH - 3, [TCOL[ks[0]], TCOL[ks[1]]])
    return f'<svg viewBox="0 0 {W} {H}" style="width:{W * 1.25}px">{PATDEF}{g}</svg>'
def nm(i): return "東" if i == 27 else f"{i - 8}"
def explain(hand, ws, km):
    """待ち方ごとに、その待ち方でアガれる牌を並べる（例: 両面 2・5　双碰 2・東）。2つの待ち方を持つ牌は、両方の待ち方に出す（2026-11-16 ユーザーの指定）"""
    out = []
    for t, col in TYPES:
        xs = [nm(CODES.index(w)) for w, _ in ws if t in km[w]]
        if xs: out.append(f'<span class="ex" style="--c:{col}"><b>{t}</b>{"・".join(xs)}</span>')
    return "".join(out)
def sheet(sec_index, title, out, keep=(None, 0, 1, 2), cat1=None):
    """keep＝載せる区分（None＝面子と雀頭が別々の形・0/1/2＝つながった形の暗刻の数）。2面子1雀頭は2枚に分ける（2026-11-16 ユーザーの指定）"""
    t, sub, m, rows = M3.SECS[sec_index]
    cards = ""
    hz = [r for r in rows if any(c[0] == "z" for c in r[2])]; pu = [r for r in rows if r not in hz]
    seq = ([("SUB", "面子と雀頭が別々の形")] + hz) if None in keep else []
    _k = f"{'4' if m == 1 else '7'}枚形"
    for k_, lab_ in ((0, f"{_k}　暗刻×0"), (1, f"{_k}　暗刻×1"), (2, f"{_k}　暗刻×2")):
        xs = [r for r in pu if M3.n_ank(r[2]) == k_]
        if not (xs and k_ in keep): continue
        seq += [("SUB", lab_)]
        if k_ == 1 and len(xs) > 3:
            for c_ in M3.CAT1:
                if cat1 and c_ not in cat1: continue
                ys = [r for r in xs if M3.cat1(r[2]) == c_]
                if ys: seq += [("SUB2", c_)] + ys
        else: seq += xs
    rows = [r for r in seq if r[0] not in ("SUB", "SUB2")]
    open_ = False
    for row in seq:
        if row[0] == "SUB":
            if open_: cards += "</div>"
            dark = "枚形" in row[1]
            pips = f"<em class='pips'>{'<i></i>' * int(row[1][0])}</em>" if dark else ""     # 4枚形・7枚形の牌の数の目印（一覧の札と同じ）
            cards += f'<div class="grp{" dk" if dark else ""}"><div class="gh">{pips}{row[1]}</div>'; open_ = True; continue
        if row[0] == "SUB2":
            cards += f'<div class="sub2">{row[1]}</div>'; continue
        name, yomi, hand, txt = row
        ws = M3.waits(hand, m, 1); n = sum(x[1] for x in ws); km = {w: kinds(hand, w, m) for w, _ in ws}
        cards += (f'<div class="card"><div class="hd lvbg{M3.level(name)}">{f'<i class="lvl l{M3.level(name)}">{M3.LVN[M3.level(name)]}</i>'}' + (f'<b>{name}</b>' + (f'<small>{yomi}</small>' if yomi else "") + f'<em class="pt">{M4pat(hand)}</em>') +
                  f'<span class="cnt">{len(ws)}種 <em>{n}</em>枚</span><span class="tx">{txt}</span></div>'
                  f'<div class="bd"><div class="top"><div class="lb">手の形</div><div class="row">{top_view(hand, ws, km)}</div><div class="exs">{explain(hand, ws, km)}</div></div>'
                  f'<div class="side"><div class="lb">横から（縦＝枚数）</div>{side_view(hand, ws, km)}</div></div></div>')
    if open_: cards += "</div>"
    leg = "".join(f'<span class="ex" style="--c:{c}"><b>{t}</b></span>' for t, c in TYPES) + '　<span style="background:#FDE3D5;padding:0 4px">初心者＝まず覚える</span>'
    body = f"""<div class="leg"><span class="sol"></span>手にある牌　<span class="dot"></span>待ちの牌（残りの枚数。色は待ち方）　{leg}　例は筒子と東</div>{cards}"""
    solbg = {"hatch": "repeating-linear-gradient(45deg,#1F2A28 0 1.5px,#fff 1.5px 3.4px)", "hatch2": "repeating-linear-gradient(45deg,#1F2A28 0 1.5px,#5E6B69 1.5px 3.4px)"}.get(HSTY, "#1F2A28")
    css = f".leg .sol {{ background: {solbg} !important; border: 1.2px solid #1F2A28; }}" + M3.PAT_CSS + """ .hd small.nm { color: #6B7A77; font-size: 10.5px; }
.leg { font-size: 11px; font-weight: 800; color: #4C5B58; margin-bottom: 6px; display: flex; align-items: center; gap: 4px; } .leg .sol { width: 18px; height: 11px; background: #1F2A28; border-radius: 2px; display: inline-block; }
.leg .dot { width: 18px; height: 11px; background: #E9A3A3; border: 0; border-radius: 2px; display: inline-block; margin-left: 10px; }
.grp { border: 2px solid #177083; border-radius: 8px; background: #F4F9F8; padding: 0 6px 1px; margin-bottom: 10px; } .grp.dk { border-color: #1F2A28; background: #F3F4F4; }
.grp .gh { margin: 0 -6px 6px; background: #177083; color: #fff; font-size: 13.5px; font-weight: 900; padding: 3px 12px; border-radius: 6px 6px 0 0; } .grp.dk .gh { background: #1F2A28; display: flex; align-items: center; }
.grp .gh .pips { display: inline-flex; gap: 2px; margin-right: 8px; } .grp .gh .pips i { width: 6px; height: 9px; border-radius: 1.5px; background: #fff; }
.grp .card:last-child { margin-bottom: 5px; }
.k47 { display: inline-block; font-size: 11.5px; font-weight: 900; color: #fff; background: #1F2A28; border-radius: 4px; padding: 0 6px; margin: 0 2px; }
.sub2 { font-size: 11.5px; font-weight: 900; color: #1F2A28; margin: 6px 0 4px 2px; border-left: 4px solid #1F2A28; padding-left: 6px; }
.card { border: 1.5px solid #8FA29D; border-radius: 6px; margin-bottom: 6px; overflow: hidden; } .hd { display: flex; align-items: baseline; gap: 8px; background: #E9EFEE; padding: 3px 10px; }
.hd b { font-size: 15px; font-weight: 900; } .lvl { font-style: normal; font-size: 10px; font-weight: 900; color: #fff; border-radius: 3px; padding: 1px 5px; align-self: center; } .lvl.l1 { background: #E25A1C; } .lvl.l2 { background: #E25A1C; } .lvl.l3 { background: #177083; } .lvl.l4 { background: #6A4BB0; }
.hd.lvbg1, .hd.lvbg2 { background: #FDE3D5; } .hd.lvbg1 b, .hd.lvbg1 small, .hd.lvbg2 b, .hd.lvbg2 small { color: #B23A0E; }
.hd.lvbg3 { background: #DCEFF1; } .hd.lvbg3 b, .hd.lvbg3 small { color: #0F5A69; } .hd.lvbg4 { background: #EDE6F7; } .hd.lvbg4 b, .hd.lvbg4 small { color: #4E3591; } .hd em.pt { font-style: normal; font-family: "Roboto Mono", "Noto Sans JP", monospace; font-size: 11.5px; font-weight: 900; letter-spacing: .12em; color: #5E6B69; }
.stars { font-style: normal; color: #C9A227; font-size: 13px; letter-spacing: -1px; align-self: center; }
.ck { width: 18px; height: 18px; border-radius: 50%; background: #177083; color: #fff; font-style: normal; font-size: 11px; font-weight: 900; line-height: 18px; text-align: center; align-self: center; } .hd small { font-size: 10px; font-weight: 800; color: #177083; } .hd .cnt { font-size: 11px; font-weight: 800; color: #4C5B58; } .hd .cnt em { font-style: normal; font-size: 15px; font-weight: 900; color: #E25A1C; }
.hd .tx { margin-left: auto; font-size: 11px; font-weight: 700; color: #4C5B58; }
.bd { display: grid; grid-template-columns: 1fr auto; gap: 10px; padding: 3px 10px 4px; align-items: center; } .lb { font-size: 9.5px; font-weight: 900; color: #8A9A97; margin-bottom: 2px; }
.row { display: flex; align-items: flex-end; gap: 2px; } .gap { display: inline-block; width: 8px; } .dt { display: inline-flex; align-items: center; justify-content: center; border: 2px dashed; border-radius: 4px; background: #fff; }
.dt img { opacity: .75; } .exs { margin-top: 3px; display: flex; flex-wrap: wrap; gap: 4px 14px; } .ex { display: inline-flex; align-items: center; gap: 5px; font-size: 13px; font-weight: 900; color: var(--c); } .ex b { background: var(--c); color: #fff; font-size: 11px; padding: 1px 7px; border-radius: 3px; }
.ex.two span { color: #1F2A28; } .ex.two em { font-style: normal; font-size: 10px; font-weight: 700; color: #6B7A77; } .leg .ex { font-size: 10px; } .leg .ex b { font-size: 10px; padding: 0 5px; }"""
    render(page(title, f"アガると{m}面子＋1雀頭 ／ 待ちの牌がどこに来るか", f"{len(rows)}形を<br><span>図で解説</span>", body, css + f".grp.dk {{ border-color: {K47}; }} .grp.dk .gh {{ background: {K47}; }} .sub2 {{ border-left-color: {K47}; }}"), out)
M3_KIHON = M3.KIHON
def M4pat(hand):
    """数字ごとの枚数の並び（一覧と同じ。抜けた数字は0・字牌はX・辺張は端を付ける）"""
    ns = sorted(int(c[1]) for c in hand if c[0] != "z")
    t = "".join(str(ns.count(k)) for k in range(ns[0], ns[-1] + 1)) if ns else ""
    if ns and (ns[0] == 1 or ns[-1] == 9) and len(ns) == 2 and ns[-1] - ns[0] == 1: t = "端" + t
    z = "X" * sum(1 for c in hand if c[0] == "z")
    return t + (" " if t and z else "") + z
if sys.argv[2] == "1": sheet(0, "1面子1雀頭を作る形（4枚形）", sys.argv[1])
elif sys.argv[2] == "2a": sheet(1, "2面子1雀頭を作る形（7枚形）①", sys.argv[1], keep=(None, 0, 2))
elif sys.argv[2] == "2b": sheet(1, "2面子1雀頭を作る形（7枚形）②", sys.argv[1], keep=(1,))
# Instagram（1080×1350）用: 1枚に入るよう、区分ごとに分けて描く（2026-11-16）
elif sys.argv[2] == "ig1a": sheet(0, "1面子1雀頭を作る形（4枚形）①", sys.argv[1], keep=(None,))
elif sys.argv[2] == "ig1b": sheet(0, "1面子1雀頭を作る形（4枚形）②", sys.argv[1], keep=(0, 1))
elif sys.argv[2] == "ig2b": sheet(1, "2面子1雀頭を作る形（7枚形）②", sys.argv[1], keep=(1,), cat1=("空なし",))
elif sys.argv[2] == "ig2c": sheet(1, "2面子1雀頭を作る形（7枚形）③", sys.argv[1], keep=(1,), cat1=("空あり", "4枚を使う"))
