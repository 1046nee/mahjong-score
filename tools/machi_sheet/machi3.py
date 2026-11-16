import os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from base import *
from functools import lru_cache
# 34種（萬0-8・筒9-17・索18-26・字27-33）で、ちょうど m面子 p雀頭 に分けられるか。字牌は順子にしない
CODES = [f"{s}{n}" for s in "mps" for n in range(1, 10)] + [f"z{n}" for n in range(1, 8)]
@lru_cache(None)
def dec(c, m, p):
    if sum(c) != 3 * m + 2 * p: return False
    if sum(c) == 0: return True
    i = next(k for k in range(34) if c[k]); l = list(c)
    if l[i] >= 3 and m:
        l[i] -= 3
        if dec(tuple(l), m - 1, p): return True
        l[i] += 3
    if l[i] >= 2 and p:
        l[i] -= 2
        if dec(tuple(l), m, p - 1): return True
        l[i] += 2
    if m and i < 27 and i % 9 <= 6 and l[i + 1] and l[i + 2]:
        l[i] -= 1; l[i + 1] -= 1; l[i + 2] -= 1
        if dec(tuple(l), m - 1, p): return True
    return False
def pattern(hand):
    """同じ色だけの形を「数字ごとの枚数の並び」で表す（2026-11-16 ユーザーの指定: 名前が決まっていない形の表し方）。
    例: 二二二三四五六 → 3 1 1 1 1 ／ 一一一三五五五 → 3 · 1 · 3（· ＝その数字が無い）"""
    ns = sorted(int(c[1]) for c in hand)
    return [ns.count(k) for k in range(ns[0], ns[-1] + 1)]
def pattern_html(hand):
    return '<span class="pat">' + "".join(f'<i class="{"z" if v == 0 else "v" + str(v)}">{v if v else "·"}</i>' for v in pattern(hand)) + "</span>"
PAT_CSS = """.pat { display: inline-flex; gap: 2px; vertical-align: middle; } .pat i { font-style: normal; width: 15px; height: 19px; border-radius: 3px; font-size: 12.5px; font-weight: 900; line-height: 19px; text-align: center; color: #fff; background: #5E6B69; }
.pat i.v1 { background: #8A9A97; } .pat i.v2 { background: #5E6B69; } .pat i.v3 { background: #1F2A28; } .pat i.v4 { background: #000; } .pat i.z { background: none; color: #8A9A97; border: 1.2px dashed #B4C0BD; width: 13px; height: 17px; line-height: 17px; }"""
CAT1 = ["空なし", "空あり", "4枚を使う"]      # 暗刻が端・すき間なしと、暗刻が真ん中は1つに（2026-11-16 ユーザーの指定）
def cat1(hand):
    """暗刻を1つ使う形の小分け"""
    ns = [int(c[1]) for c in hand]
    if max(ns.count(k) for k in ns) == 4: return CAT1[2]
    gap = any(k not in ns for k in range(min(ns), max(ns) + 1))
    return CAT1[1] if gap else CAT1[0]
# 覚える段階（2026-11-16 ユーザーの指定。一覧の上から5形＝初心者・12形まで＝脱初心者・残り＝中級者）
# ★の数＝覚える難しさ（大事さではない）。★と★★は「まず覚える」（2026-11-16 ユーザーの指定）
LV1 = ["両面", "嵌張", "辺張", "双碰", "単騎"]
LV2 = ["延べ単", "亜両面", "三面張"]
LV3 = ["暗刻＋1枚", "暗刻＋空＋1枚", "暗刻＋両面＋対子", "7枚つながり"]
def level(name): return 1 if name in LV1 else (2 if name in LV2 else (3 if name in LV3 else 4))
LVN = {1: "初心者", 2: "初心者", 3: "脱初心者", 4: "中級者"}      # 未経験者はやめて初心者に（2026-11-16 ユーザーの指定）      # 覚える段階の呼び名（★の代わり。2026-11-16 ユーザーの指定）
def n_ank(hand):
    """同じ牌3枚以上（暗刻）がいくつあるか"""
    return sum(1 for c in set(hand) if hand.count(c) >= 3)
def row_tiles(cs, w):
    """牌を並べる。字牌の前は少しあける（数牌と字牌の区切りが分かるように。2026-11-16 ユーザーの指定）"""
    out = ""
    for k, c in enumerate(cs):
        gap = k and c[0] == "z" and cs[k - 1][0] != "z"
        out += (f'<span class="gap"></span>' if gap else "") + tl(c, w)
    return out
def waits(hand, m, p):
    c = [0] * 34
    for h in hand: c[CODES.index(h)] += 1
    out = []
    for t in range(34):
        if c[t] >= 4: continue
        l = list(c); l[t] += 1
        if dec(tuple(l), m, p): out.append((CODES[t], 4 - c[t]))
    return out
P = lambda s: [f"p{ch}" for ch in s]
EAST = ["z1", "z1"]
SECS = [("1面子1雀頭を作る形", "4枚形", 1, [
  ("両面", "リャンメン", P("45") + EAST, "両側の2種を待つ。いちばんの基本"),
  ("嵌張", "カンチャン", P("46") + EAST, "1つ飛びの間の1種だけを待つ"),
  ("辺張", "ペンチャン", P("12") + EAST, "端の2枚。片側の1種だけを待つ"),
  ("双碰", "シャンポン", ["p2", "p2", "z1", "z1"], "対子2つのどちらかが刻子になる"),
  ("単騎", "タンキ", P("234") + ["z1"], "1枚で、同じ牌を雀頭として待つ"),
  ("延べ単", "ノベタン", P("3456"), "4枚つながり。両端が雀頭になる"),
  ("亜両面", "アリャンメン", P("3345"), "対子＋両面。両面より2枚少ない"),
  ("暗刻＋1枚", "", P("4445"), "両面と単騎が重なる"),
  ("暗刻＋空＋1枚", "", P("4446"), "嵌張と単騎が重なる")]),
 ("2面子1雀頭を作る形", "7枚形", 2, [
  ("三面張", "サンメンチャン", P("34567") + EAST, "両面が重なり、3種を待つ"),
  ("暗刻＋延べ単", "", P("2223456"), "延べ単・三面張・暗刻が重なる"),
  ("1枚＋暗刻＋順子", "", P("2333456"), "暗刻をはさみ、両面と単騎が重なる"),
  ("両面＋暗刻＋両面", "", P("2344456"), "暗刻を両側の両面がはさむ"),
  ("暗刻＋1枚＋暗刻", "", P("3334555"), "どこが雀頭かで待ちが変わる"),
  ("暗刻＋暗刻＋1枚", "", P("3334445"), "2つ続く暗刻のとなりに1枚"),
  ("暗刻＋亜両面", "", P("2223345"), "暗刻と亜両面が重なる"),
  ("1枚＋4枚＋両面", "", P("2333345"), "4枚使った牌は待ちにならない"),
  ("4枚＋順子", "", P("2222345"), "延べ単の片側が4枚使いで消える"),
  ("暗刻＋空＋1枚＋空＋暗刻", "", P("1113555"), "嵌張2つと単騎が重なる"),
  ("暗刻＋空＋延べ単", "", P("2224567"), "暗刻と4枚の間が1つ飛ぶ"),
  ("7枚つながり", "", P("1234567"), "延べ単が2つ重なる"),
  ("暗刻＋両面＋対子", "", P("22234") + EAST, "両面と双碰が重なる"),
  ("暗刻＋順子＋空＋1枚", "", P("2223457"), "最後の1枚だけが離れる")])]
KIHON = {"両面", "嵌張", "辺張", "双碰", "単騎", "延べ単", "亜両面", "三面張"}      # まず覚える基本の形（色を変える。2026-11-16 ユーザーの指定）
body_rows = ""; total = 0
for title, sub, m, rows in SECS:
    body_rows += f'<tr class="gh"><td colspan="5">{title}</td></tr>'
    # 同じグループの中で、雀頭が字牌でもよい形（東が入る）を上、同じ色の牌だけでできる形を下に分ける（2026-11-16 ユーザーの指定）
    hz = [r for r in rows if any(c[0] == "z" for c in r[2])]; pu = [r for r in rows if r not in hz]
    for part, lab in ((hz, "面子と雀頭が別々の形<small>雀頭は字牌や別の色の牌でもよい</small>"), (pu, f"同じ色の牌がつながった形<small>{sub}とも呼ぶ</small>")):
      body_rows += f'<tr class="sh {"lo" if part is pu else "up"}"><td colspan="5">{lab}</td></tr>'
      if part is pu:      # つながった形は、暗刻（同じ牌3枚以上）が入っていない形 → 入っている形 の順に分ける（2026-11-16 ユーザーの指定）
          part = []
          for k_, lab_ in ((0, "暗刻が入っていない"), (1, "暗刻を1つ使う"), (2, "暗刻を2つ使う")):      # 暗刻の数で分ける（2026-11-16 ユーザーの指定）
              xs = [r for r in pu if n_ank(r[2]) == k_]
              if not xs: continue
              part += [("SUB", lab_)]
              if k_ == 1 and len(xs) > 3:      # 暗刻を1つ使う形が多いときは、さらに小分け
                  for c_ in CAT1:
                      ys = [r for r in xs if cat1(r[2]) == c_]
                      if ys: part += [("SUB2", c_)] + ys
              else: part += xs
      for row in part:
        if row[0] == "SUB":
            body_rows += f'<tr class="ss"><td colspan="5">{row[1]}</td></tr>'; continue
        if row[0] == "SUB2":
            body_rows += f'<tr class="s2"><td colspan="5">{row[1]}</td></tr>'; continue
        name, yomi, hand, txt = row
        w = waits(hand, m, 1); assert w, name; n = sum(x[1] for x in w); total += 1
        tw = 24 if len(hand) <= 5 else 21
        named = True      # 名前のある形・字牌を含む形は名前で、それ以外は枚数の並びで表す
        lab = ((f'<span class="ln">{name}</span>' if len(name) >= 10 else name) + (f'<small>{yomi}</small>' if yomi else "")) if named else f'{pattern_html(hand)}<small class="nm">{name}</small>'
        body_rows += (f'<tr><th class="rh">' + ('<i class="ck">✓</i>' if name in KIHON else "") + lab + f'</th><td class="hand">{row_tiles(hand, tw)}</td>'
                      f'<td class="wt">{row_tiles([c_ for c_, _ in w], 19)}</td><td class="n">{n}<i>枚</i></td><td class="tx">{txt}</td></tr>')
        pass
body = f"""
<table><colgroup><col style="width:134px"><col style="width:190px"><col style="width:124px"><col style="width:60px"><col></colgroup>
<thead><tr><th>形</th><th>牌の例</th><th>待ち</th><th>枚数</th><th>説明</th></tr></thead><tbody>{body_rows}</tbody></table>
<div class="tip"><i class="kh2">✓</i> がついた形＝まず覚える基本の8つの形。名前の決まっていない形は、部品を左から「＋」でつないで表した（<b>空</b>＝1つ飛んだ数字。例: 暗刻＋1枚＋空＋順子＝二二二三・五六七）。<br><b>見方</b>　どの形も、アガリ牌が来ると「1面子＋1雀頭」か「2面子＋1雀頭」がそろう。上の段は、面子の部分と雀頭の部分が別々（例では雀頭を東にした）。下の段は、同じ色の牌がつながっていて、どこが雀頭になるかがアガリ牌で変わる。<br>
<b>亜両面</b>は両面と同じ待ちの種類でも、手の中に1枚使っているので、両面より2枚少ない。</div>
<p class="note">例は筒子と東。枚数は、形の中の牌を除いた残り（場に見えている牌は数えない）。待ちと枚数は計算で出した</p>"""
css = PAT_CSS + """
td.hand, td.wt { text-align: center; white-space: nowrap; } .gap { display: inline-block; width: 7px; } td.n { text-align: center; font-size: 18px; font-weight: 900; color: #E25A1C; } td.n i { font-style: normal; font-size: 10px; color: #1F2A28; }
td.tx { font-size: 11.5px; white-space: nowrap; letter-spacing: -.01em; } tr.gh td { background: #177083; color: #fff; font-size: 15px; font-weight: 900; padding: 3px 10px; } tr.sh td { background: #E4F3EC; color: #177083; font-size: 11.5px; font-weight: 900; padding: 2px 12px; }
tr.sh small { font-size: 10.5px; font-weight: 700; color: #4C5B58; margin-left: 10px; }       /* 上（字牌の雀頭でもよい）と下（同じ色だけ）の境は二重線 */
tr.gh td { border-top: 4px double #1F2A28; } tbody tr.gh:first-child td { border-top: 2px solid #1F2A28; } tr.sh.lo td { border-top: 1.5px solid #177083; }      /* 区切りの線は、グループの頭も段の境も同じ二重線にそろえる（2026-11-16 ユーザーの指定） */
tr.sh.up td { border-top: 1px solid #8FA29D; } thead th { border-bottom: 1.5px solid #fff; }      /* 見出し（形・牌の例…）の下にも線。二重線は2つのグループの上だけ（2026-11-16 ユーザーの指定） */ tr.gh small { font-size: 11px; font-weight: 700; color: #DDF0EC; margin-left: 10px; }
th.rh { font-size: 12.5px; } th.rh { position: relative; } th.rh .ln { font-size: 11px; letter-spacing: -.03em; white-space: nowrap; } th.rh small.nm { color: #6B7A77; font-size: 9.5px; margin-top: 2px; } .ck { position: absolute; left: 6px; top: 50%; transform: translateY(-50%); width: 17px; height: 17px; border-radius: 50%; background: #177083; color: #fff; font-style: normal; font-size: 11px; font-weight: 900; line-height: 17px; text-align: center; }
.kh2 { display: inline-block; width: 15px; height: 15px; border-radius: 50%; background: #177083; color: #fff; font-style: normal; font-size: 10px; font-weight: 900; line-height: 15px; text-align: center; vertical-align: 1px; } tbody tr { height: 42px; } tbody tr.gh, tbody tr.sh, tbody tr.ss, tbody tr.s2 { height: auto; }
tr.s2 td { font-size: 10px; font-weight: 800; color: #8A9A97; padding: 0 12px 0 26px; background: #fff; border-top: 1px dotted #B4C0BD; }
tr.ss td { font-size: 10.5px; font-weight: 900; color: #6B7A77; padding: 1px 12px; background: #F6F8F7; border-top: 1.5px dashed #6B7A77; }"""
if __name__ == "__main__": render(page("待ちの形の一覧", "1面子1雀頭・2面子1雀頭を作る形と、待ちの枚数", f"脱初心者の<br><span>{total}形</span>", body, css), sys.argv[1])
