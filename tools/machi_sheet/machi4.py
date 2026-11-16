# 待ちの形の一覧: 案A（1枚・見出し2段・枚数の棒）と案B（基本8形／応用の2枚・応用は枚数の多い順）。2026-11-16
import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
import machi3 as M
import os as _os, re
DESC = _os.environ.get("DESC") is not None      # 説明の列は出さない（2026-11-16 ユーザーの判断。DESC=1 で出す）
PAT = _os.environ.get("NOPAT") is None       # 形の名前の下に枚数の並びを出すか（試し）
ALL = []
for t, sub, m, rows in M.SECS:
    for name, yomi, hand, txt in rows:
        w = M.waits(hand, m, 1); n = sum(x[1] for x in w)
        ALL.append(dict(name=name, yomi=yomi, hand=hand, txt=txt, m=m, w=[c for c, _ in w], n=n, kihon=name in M.KIHON,
                        honor=any(c[0] == "z" for c in hand), ank=M.n_ank(hand)))
MAXN = max(r["n"] for r in ALL)
def bar(n): return f'<div class="bar2"><i style="width:{n / MAXN * 100:.0f}%"></i></div>'
def pat(hand):
    """形を「数字ごとの枚数の並び」で（例: 三面張＝11111 XX・暗刻＋延べ単＝31111）。抜けている数字は 0、字牌は X（2026-11-16 ユーザーの案）"""
    ns = sorted(int(c[1]) for c in hand if c[0] != "z")
    t = "".join(str(ns.count(k)) for k in range(ns[0], ns[-1] + 1)) if ns else ""
    z = "X" * sum(1 for c in hand if c[0] == "z")
    if ns and (ns[0] == 1 or ns[-1] == 9) and len(ns) == 2 and ns[-1] - ns[0] == 1: t = "端" + t      # 辺張は端を付けて両面と見分ける（2026-11-16 ユーザーの案）
    return (t + (" " if t and z else "") + z)
def namecell(r):
    nm = f'<span class="ln">{r["name"]}</span>' if len(r["name"]) >= 10 else r["name"]
    lv = M.level(r["name"])
    return f'<th class="rh lvbg{lv}"><i class="st l{lv}">{M.LVN[lv]}</i>' + nm + (f'<small>{r["yomi"]}</small>' if r["yomi"] else "") + (f'<em class="pt">{pat(r["hand"])}</em>' if PAT else "") + "</th>"
def row(r, rank=None, tag=False, big=False, small=False):
    tw = (30 if len(r["hand"]) <= 5 else 25) if big else (((27 if len(r["hand"]) <= 5 else 25) if not DESC else (22 if len(r["hand"]) <= 5 else 19)) if small else (24 if len(r["hand"]) <= 5 else 21))
    tg = ""
    return ((f'<tr><td class="rk">{rank}</td>' if rank else "<tr>") + namecell(r) +
            f'<td class="hand">{M.row_tiles(r["hand"], tw)}</td><td class="wt">{M.row_tiles(r["w"], 22 if big else ((22 if not DESC else 16) if small else 19))}</td>'
            f'<td class="n"><b>{r["n"]}<i>枚</i></b>{bar(r["n"])}</td>' + (f'<td class="kd"><em class="tg t{r["m"]}">{r["m"] * 3 + 1}枚形</em></td>' if tag else "") + (f'<td class="tx">{r["txt"]}</td>' if DESC else "") + '</tr>')
def hero(cards):
    return '<div class="hero">' + "".join(f'<div class="hc" style="background:{c}"><small>{a}</small><b>{b}</b><span>{d}</span></div>' for a, b, d, c in cards) + "</div>"
CSS = M.PAT_CSS + """
td.hand, td.wt { text-align: center; white-space: nowrap; } .gap { display: inline-block; width: 7px; }
td.n { text-align: center; } td.n b { font-size: 18px; font-weight: 900; color: #E25A1C; } td.n b i { font-style: normal; font-size: 10px; color: #1F2A28; }
.bar2 { height: 6px; background: #E9EFEE; border-radius: 3px; margin: 2px 6px 0; overflow: hidden; } .bar2 i { display: block; height: 100%; background: #E25A1C; border-radius: 3px; }
td.tx { font-size: 11.5px; white-space: nowrap; letter-spacing: -.01em; } tbody tr { height: 44px; }
th.rh { font-size: 12.5px; position: relative; } th.rh .ln { font-size: 11px; letter-spacing: -.03em; white-space: nowrap; }
.st { position: absolute; left: 3px; top: 3px; font-style: normal; font-size: 8.5px; font-weight: 900; line-height: 1; color: #fff; border-radius: 3px; padding: 2px 4px; }
.st.l1 { background: #E25A1C; } .st.l2 { background: #E25A1C; } .st.l3 { background: #177083; } .st.l4 { background: #6A4BB0; }
th.rh em.pt { display: block; font-style: normal; font-family: "Roboto Mono", "Noto Sans JP", monospace; font-size: 10.5px; font-weight: 900; letter-spacing: .12em; color: #5E6B69; margin-top: 1px; }
.k47b { display: inline-block; font-size: 12px; font-weight: 900; color: #fff; background: #1F2A28; border-radius: 5px; padding: 3px 7px; line-height: 1.35; }
.k47 { display: inline-block; margin-top: 3px; font-size: 11.5px; font-weight: 900; color: #fff; background: #1F2A28; border-radius: 4px; padding: 1px 6px; }      /* 星は左上に横並び。名前はセルの真ん中のまま、上に少し余白をとって重ならない */
.lv { position: absolute; left: 5px; top: 50%; transform: translateY(-50%); width: 17px; height: 17px; border-radius: 4px; color: #fff; font-style: normal; font-size: 10.5px; font-weight: 900; line-height: 17px; text-align: center; }
.lvk { display: inline-block; width: 15px; height: 15px; border-radius: 3px; color: #fff; font-style: normal; font-size: 9.5px; font-weight: 900; line-height: 15px; text-align: center; vertical-align: 1px; margin: 0 2px 0 6px; }
th.rh.lvbg1, th.rh.lvbg2 { background: #FDE3D5; color: #B23A0E; } th.rh.lvbg1 small, th.rh.lvbg2 small { color: #B23A0E; }
th.rh.lvbg3 { background: #DCEFF1; color: #0F5A69; } th.rh.lvbg3 small { color: #0F5A69; }
th.rh.lvbg4 { background: #EDE6F7; color: #4E3591; } th.rh.lvbg4 small { color: #4E3591; } .fb { background: #FDE3D5; border-radius: 3px; padding: 1px 6px 1px 0; }
.st2 { font-style: normal; font-size: 10px; font-weight: 900; color: #fff; border-radius: 3px; padding: 1px 5px; margin: 0 3px; } .st2.l1 { background: #E25A1C; } .st2.l2 { background: #F08A4B; } .st2.l3 { background: #177083; } .st2.l4 { background: #6A4BB0; }
.fb3 { background: #DCEFF1; border-radius: 3px; padding: 1px 6px 1px 0; } .fb4 { background: #EDE6F7; border-radius: 3px; padding: 1px 6px 1px 0; }
.sk { color: #C9A227; font-weight: 900; margin-left: 6px; }
.ck { position: absolute; left: 6px; top: 50%; transform: translateY(-50%); width: 17px; height: 17px; border-radius: 50%; background: #177083; color: #fff; font-style: normal; font-size: 11px; font-weight: 900; line-height: 17px; text-align: center; }
.kh2 { display: inline-block; width: 15px; height: 15px; border-radius: 50%; background: #177083; color: #fff; font-style: normal; font-size: 10px; font-weight: 900; line-height: 15px; text-align: center; vertical-align: 1px; }
tr.gh td { background: #177083; color: #fff; font-size: 15px; font-weight: 900; padding: 3px 10px; border-top: 4px double #1F2A28; } tbody tr.gh:first-child td { border-top: 2px solid #1F2A28; }
tr.gh small { font-size: 11px; font-weight: 700; color: #DDF0EC; margin-left: 10px; }
tr.sh td { background: #E4F3EC; color: #177083; font-size: 12px; font-weight: 900; padding: 2px 12px; border-top: 1.5px solid #177083; } tr.sh small { font-size: 10.5px; font-weight: 700; color: #4C5B58; margin-left: 10px; }
tbody tr.gh, tbody tr.sh { height: auto; } thead th { border-bottom: 1.5px solid #fff; }
.hero { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 10px; } .hc { border-radius: 8px; color: #fff; text-align: center; padding: 6px 4px; }
.hc small { display: block; font-size: 11.5px; font-weight: 800; opacity: .92; } .hc b { display: block; font-size: 23px; font-weight: 900; color: #FFE68A; line-height: 1.25; } .hc span { font-size: 11.5px; font-weight: 800; }
td.kd { text-align: center; } td.rk { text-align: center; font-size: 17px; font-weight: 900; color: #fff; background: #177083; width: 34px; } tr.top td.rk { background: #E25A1C; }
.tg { display: inline-block; white-space: nowrap; font-style: normal; font-size: 9.5px; font-weight: 900; color: #fff; border-radius: 3px; padding: 0 5px; margin-right: 6px; } .tg.t1 { background: #4261AA; } .tg.t2 { background: #6A4BB0; }
"""
TEAL_, ORG, BLU = "#177083", "#E25A1C", "#4261AA"
top = max(ALL, key=lambda r: r["n"]); low = min(ALL, key=lambda r: r["n"])
def sheet_A(out):
    """カテゴリーは行を足さず、左の2列にまとめる（2026-11-16 ユーザーの指定）: 1列目＝何面子何雀頭（縦書き）・2列目＝形の分け方"""
    body = ""
    for t, sub, m, rows in M.SECS:
        rs = [r for r in ALL if r["m"] == m]
        sep = [r for r in rs if r["honor"]]
        blocks = [("面子と雀頭が<br>別々の形", "雀頭は字牌でも", sep, "sep")]
        for k, lab in ((0, "暗刻×0"), (1, "暗刻×1"), (2, "暗刻×2")):
            xs = [r for r in rs if not r["honor"] and r["ank"] == k]
            if not xs: continue
            if k == 1 and len(xs) > 3:      # 暗刻1つの中は、暗刻の位置・空・4枚で小分けの行を差し込む（2026-11-16 ユーザーの指定）
                ys = []
                for c_ in M.CAT1:
                    zs = [r for r in xs if M.cat1(r["hand"]) == c_]
                    if zs: ys += [("SUB", c_)] + zs
                xs = ys
            blocks.append((f"<span class='k47b'>{'4' if m == 1 else '7'}枚形<br>{lab}</span>", "", xs, "con" + str(k)))
        total = sum(len(b_[2]) for b_ in blocks); first = True
        for lab, sm, xs, kind in blocks:
            for j, r in enumerate(xs):
                cls = ["gtop"] if first else ((["btop"] if kind == "con0" or (kind.startswith("con") and not any(b_[3] == "con0" for b_ in blocks) and kind == blocks[1][3]) else ["ctop"]) if j == 0 else [])
                tr = f'<tr class="{" ".join(cls)}">'
                if first:
                    lab1 = re.sub(r"(\d)", r'<i class="tcu">\1</i>', t.replace("を作る形", ""))
                    tr += f'<td class="g1" rowspan="{total}"><span>{lab1}</span><small>を作る形</small></td>'
                if j == 0: tr += f'<td class="g2" rowspan="{len(xs)}">{lab}<small>{sm}</small></td>'
                if r[0] == "SUB" if isinstance(r, tuple) else False:
                    body += tr.replace('<tr class="', '<tr class="ssr ', 1) + f'<td class="ss2" colspan="5">{r[1]}</td></tr>'
                else:
                    body += row(r, small=True).replace("<tr>", tr, 1)
                first = False
    if DESC:
        cg = '<col style="width:28px"><col style="width:74px"><col style="width:140px"><col style="width:146px"><col style="width:98px"><col style="width:56px"><col>'
        hd = '<th colspan="2">分け方</th><th>形</th><th>牌の例</th><th>待ち</th><th>枚数</th><th>説明</th>'
    else:
        body = body.replace('colspan="5"', 'colspan="4"')
        cg = '<col style="width:30px"><col style="width:80px"><col style="width:140px"><col style="width:220px"><col style="width:150px"><col>'
        hd = '<th colspan="2">分け方</th><th>形</th><th>牌の例</th><th>待ち</th><th>枚数</th>'
    html = f"""<table><colgroup>{cg}</colgroup>
<thead><tr>{hd}</tr></thead><tbody>{body}</tbody></table>
<div class="tip"><b>左上の札＝覚える段階</b>　<span class="fb"><i class="st2 l1">初心者</i>まず覚える（8形）</span>　<span class="fb3"><i class="st2 l3">脱初心者</i>次に覚える（4形）</span>　<span class="fb4"><i class="st2 l4">中級者</i>余裕があれば（11形）</span><br>
<span class="k47">4枚形</span>・<span class="k47">7枚形</span>＝同じ色の牌だけでつながった形（アガると1面子＋1雀頭／2面子＋1雀頭）。<br>
名前の決まっていない形は、部品を左から「＋」でつないで表した（<b>空</b>＝1つ飛んだ数字。例: 暗刻＋空＋延べ単＝二二二・四五六七）。<br>
</div>"""
    css = CSS + """
td.g1 { background: #177083; color: #fff; text-align: center; padding: 4px 0; font-weight: 900; } td.g1 span { writing-mode: vertical-rl; font-size: 16px; letter-spacing: .06em; } td.g1 .tcu { font-style: normal; text-combine-upright: all; } td.g1 small { display: block; writing-mode: vertical-rl; margin: 4px auto 0; font-size: 10px; color: #DDF0EC; }
td.g2 { background: #E4F3EC; color: #177083; text-align: center; font-size: 11px; font-weight: 900; line-height: 1.35; padding: 3px 2px; } td.g2 b { font-size: 12.5px; } td.g2 small { display: block; font-size: 9.5px; color: #4C5B58; font-weight: 700; margin-top: 2px; }
td.tx { font-size: 10.5px; letter-spacing: -.03em; padding: 4px 5px; } th.rh { font-size: 12px; padding: 13px 2px 2px; } th.rh .ln { font-size: 10px; letter-spacing: -.05em; }
tr.gtop td, tr.gtop th { border-top: 5px double #1F2A28 !important; } tbody tr.gtop:first-child td, tbody tr.gtop:first-child th { border-top: 2px solid #1F2A28; } tr.btop td, tr.btop th { border-top: 2px solid #1F2A28 !important; } tr.ctop td, tr.ctop th { border-top: 1.5px solid #8FA29D !important; }      /* 別々の形とつながった形の境 */
tbody tr.ssr { height: 20px; } td.ss2 { background: #F4F7F6; color: #4C5B58; font-size: 11px; font-weight: 900; padding: 1px 10px; border-top: 1px dashed #8FA29D; }"""
    render(page("待ちの形の一覧", "1面子1雀頭（4枚形）・2面子1雀頭（7枚形）を作る形と、待ちの枚数", f"脱初心者の<br><span>{len(ALL)}形</span>", html, css), out)
def sheet_B1(out):
    ks = sorted([r for r in ALL if r["kihon"]], key=lambda r: -r["n"])
    body = "".join(row(r, big=True) for r in ks)
    html = f"""<table><colgroup><col style="width:150px"><col style="width:200px"><col style="width:116px"><col style="width:76px"><col></colgroup>
<thead><tr><th>形</th><th>牌の例</th><th>待ち</th><th>枚数</th><th>説明</th></tr></thead><tbody>{body}</tbody></table>
<div class="tip"><b>形をよくする</b>　嵌張・辺張は、となりの牌を引いて両面に変えると待ちが2倍（4枚→8枚）。リーチの前に形を整えるとアガりやすい。<br>
<b>亜両面</b>は両面と同じ待ちの種類でも、手の中に1枚使っているので、両面より2枚少ない。</div>
<p class="note">例は筒子と東。枚数は、形の中の牌を除いた残り（場に見えている牌は数えない）。応用の形は、もう1枚の「応用の形」で</p>"""
    render(page("待ちの形　基本の8形", "まずはこれだけ。待ちの枚数が多い順", "まず覚える<br><span>8形</span>", html, CSS.replace("tbody tr { height: 44px; }", "tbody tr { height: 54px; }")), out)
def sheet_B2(out):
    global ROWH
    os_ = sorted([r for r in ALL if not r["kihon"]], key=lambda r: (-r["n"], r["m"]))
    body = ""; prev = None; rank = 0
    for k, r in enumerate(os_):
        if r["n"] != prev: rank = k + 1; prev = r["n"]
        body += row(r, rank=rank, tag=True).replace("<tr>", '<tr class="top">', 1) if rank <= 3 else row(r, rank=rank, tag=True)
    html = f"""<table><colgroup><col style="width:30px"><col style="width:138px"><col style="width:164px"><col style="width:104px"><col style="width:62px"><col style="width:56px"><col></colgroup>
<thead><tr><th></th><th>形</th><th>牌の例</th><th>待ち</th><th>枚数</th><th>形</th><th>説明</th></tr></thead><tbody>{body}</tbody></table>
<div class="tip"><b>読み方</b>　名前は、部品を左から「＋」でつないだもの（<b>空</b>＝1つ飛んだ数字）。<em class="tg t1">4枚形</em>はアガると1面子＋1雀頭、<em class="tg t2">7枚形</em>はアガると2面子＋1雀頭になる形。</div>
<p class="note">例は筒子と東。枚数は、形の中の牌を除いた残り（場に見えている牌は数えない）。待ちと枚数は計算で出した</p>"""
    render(page("待ちの形　応用の15形", "暗刻が入ると待ちが広がる。待ちの枚数が多い順", "脱初心者の<br><span>15形</span>", html, CSS + "td.tx { font-size: 11px; letter-spacing: -.03em; }"), out)
k = sys.argv[2]
{"A": sheet_A, "B1": sheet_B1, "B2": sheet_B2}[k](sys.argv[1])
