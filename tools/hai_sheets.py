# -*- coding: utf-8 -*-
"""牌の一覧表・役の一覧表（1枚）と、記事に入れる牌の並びのHTMLを作る（2026-10-23〜）。牌の絵は assets/tiles/（tools/make_tiles.py）。

出力（assets/hai/）: hai-ichiran.png / hai-ichiran-web.png / hai-ichiran.pdf、yaku-ichiran.png / yaku-ichiran-web.png / yaku-ichiran.pdf
牌の書き方: "123m" = 一二三萬、"p"=筒子、"s"=索子、"z"=字牌（1東 2南 3西 4北 5白 6發 7中）、"0" = 赤五
実行: python tools/hai_sheets.py          （画像とPDFを作る。役の例があがりの形になっているかを先に確かめる）
      python tools/hai_sheets.py --check  （確かめるだけ）
"""
import io, os, sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "hai")

NAMES = {"m": "萬", "p": "筒", "s": "索"}
KANSU = "一二三四五六七八九"
# 9は牌の読みが「キュー」、役の名前（九蓮宝燈・么九牌）では「チュー」。6は「ロー」だけ。萬子は「マン」が基本（「ワン」とも）＝2026-10-24 ユーザーの指摘
YOMI_NUM = ["イー", "リャン", "サン", "スー", "ウー", "ロー", "チー", "パー", "キュー"]
YOMI_SUIT = {"m": "マン", "p": "ピン", "s": "ソー"}
Z = {1: ("東", "トン"), 2: ("南", "ナン"), 3: ("西", "シャー"), 4: ("北", "ペー"), 5: ("白", "ハク"), 6: ("發", "ハツ"), 7: ("中", "チュン")}


def parse(s):
    out, buf = [], []
    for ch in s.replace(" ", ""):
        if ch.isdigit():
            buf.append(ch)
        else:
            for d in buf:
                out.append(f"{ch}5r" if d == "0" else f"{ch}{d}")
            buf = []
    return out


def base(c):  # 赤五も同じ牌として数える
    return c[:2]


def tile_name(c):
    if c == "back":
        return "裏向きの牌"
    if c[0] == "z":
        return Z[int(c[1])][0]
    return ("赤" if c.endswith("r") else "") + KANSU[int(c[1]) - 1] + NAMES[c[0]]


# ---------------- 役のデータ ----------------
# (名前, 読み, 門前の翻, 鳴いたときの翻 or None, 条件, 例) 例 = None（状況で決まる役）か dict(hand=, win=, melds=[(種類, 牌)])
YAKU = [
 ("1翻", [
  ("立直", "リーチ", 1, None, "門前でテンパイしたら宣言する。1,000点を供託", dict(hand="123m456m789p23s55s", win="4s")),
  ("一発", "イッパツ", 1, None, "リーチから1巡以内（間に鳴きが入らない）にあがる", None),
  ("門前清自摸和", "メンゼンツモ", 1, None, "門前（鳴いていない）でツモあがり", None),
  ("断么九", "タンヤオ", 1, 1, "2〜8の数牌だけで作る", dict(hand="234m567m345p66s78s", win="6s")),
  ("平和", "ピンフ", 1, None, "順子4つ＋役牌でない雀頭＋両面待ち", dict(hand="123m456p789p23s99m", win="4s")),
  ("一盃口", "イーペーコー", 1, None, "同じ順子を2つ", dict(hand="112233m456p78s55p", win="9s")),
  ("役牌", "ヤクハイ", 1, 1, "三元牌・場風・自風の刻子（1つにつき1翻）", dict(hand="123m456p33s45s", win="6s", melds=[("pon", "777z")])),
  ("海底摸月", "ハイテイ", 1, 1, "最後の牌でツモあがり", None),
  ("河底撈魚", "ホウテイ", 1, 1, "最後に捨てられた牌でロンあがり", None),
  ("嶺上開花", "リンシャンカイホウ", 1, 1, "カンをして取った嶺上牌でツモあがり", None),
  ("槍槓", "チャンカン", 1, 1, "ほかの人の加槓の牌でロンあがり", None),
 ]),
 ("2翻", [
  ("ダブル立直", "ダブルリーチ", 2, None, "最初の打牌でリーチ（それまでに鳴きが無い）", None),
  ("七対子", "チートイツ", 2, None, "対子を7つ（同じ牌4枚は2対子にしない）", dict(hand="1199m3355p77s22z6z", win="6z")),
  ("三色同順", "サンショク", 2, 1, "萬・筒・索で同じ数の順子", dict(hand="123m123p123s789m5z", win="5z")),
  ("一気通貫", "イッツー", 2, 1, "同じ種類で123・456・789", dict(hand="123456789p234s5m", win="5m")),
  ("混全帯么九", "チャンタ", 2, 1, "全部の面子と雀頭に1・9か字牌", dict(hand="123m789p789s111z9m", win="9m")),
  ("対々和", "トイトイ", 2, 2, "刻子4つ＋雀頭", dict(hand="222m999s3z", win="3z", melds=[("pon", "555p"), ("pon", "777s")])),
  ("三暗刻", "サンアンコー", 2, 2, "鳴いていない刻子を3つ", dict(hand="222m555p888s34m66s", win="5m")),
  ("三色同刻", "サンショクドウコー", 2, 2, "萬・筒・索で同じ数の刻子", dict(hand="222m222p222s567m8s", win="8s")),
  ("三槓子", "サンカンツ", 2, 2, "カンを3回", dict(hand="456m9p", win="9p", melds=[("ankan", "3333m"), ("kan", "5555p"), ("kan", "7777s")])),
  ("小三元", "ショウサンゲン", 2, 2, "三元牌の刻子2つ＋三元牌の雀頭（役牌2つで実質4翻）", dict(hand="555z666z77z123m45p", win="3p")),
  ("混老頭", "ホンロウトウ", 2, 2, "1・9と字牌だけ（対々和か七対子と重なる）", dict(hand="111m999p999s111z2z", win="2z")),
 ]),
 ("3翻", [
  ("混一色", "ホンイツ", 3, 2, "1種類の数牌と字牌だけ", dict(hand="234m567m888m11z22z", win="2z")),
  ("純全帯么九", "ジュンチャン", 3, 2, "全部の面子と雀頭に1・9（字牌なし）", dict(hand="123m789m123p789s1p", win="1p")),
  ("二盃口", "リャンペーコー", 3, None, "一盃口を2つ", dict(hand="112233m445566p7s", win="7s")),
 ]),
 ("6翻", [
  ("清一色", "チンイツ", 6, 5, "1種類の数牌だけ", dict(hand="2233445566778s", win="8s")),
 ]),
 ("役満", [
  ("国士無双", "コクシムソウ", 13, None, "1・9と字牌の13種を1枚ずつ＋どれか1枚", dict(hand="119m19p19s123456z", win="7z")),
  ("四暗刻", "スーアンコー", 13, None, "鳴いていない刻子を4つ", dict(hand="111m333p555s777s9p", win="9p")),
  ("大三元", "ダイサンゲン", 13, 13, "白・發・中の刻子を3つ", dict(hand="555z666z777z12m33p", win="3m")),
  ("字一色", "ツーイーソー", 13, 13, "字牌だけ", dict(hand="111z222z333z555z7z", win="7z")),
  ("小四喜", "ショウスーシー", 13, 13, "風牌の刻子3つ＋風牌の雀頭", dict(hand="111z222z333z44z23m", win="1m")),
  ("大四喜", "ダイスーシー", 13, 13, "風牌の刻子を4つ", dict(hand="111z222z333z444z5m", win="5m")),
  ("緑一色", "リューイーソー", 13, 13, "2・3・4・6・8索と發だけ", dict(hand="223344s666s888s6z", win="6z")),
  ("清老頭", "チンロウトウ", 13, 13, "1と9の数牌だけ", dict(hand="111m999m111p999p1s", win="1s")),
  ("四槓子", "スーカンツ", 13, 13, "カンを4回", dict(hand="5p", win="5p", melds=[("ankan", "1111m"), ("kan", "4444p"), ("kan", "7777s"), ("ankan", "2222z")])),
  ("九蓮宝燈", "チューレンポウトウ", 13, None, "1種類で1112345678999＋同じ種類の1枚", dict(hand="1112345678999p", win="5p")),
  ("天和", "テンホー", 13, None, "親が配牌の時点であがっている", None),
  ("地和", "チーホー", 13, None, "子が最初のツモであがる（それまでに鳴きが無い）", None),
 ]),
]


# ---------------- あがりの形の確かめ ----------------
def _std(cnt, sets):
    """cnt（34種の数）を、sets 個の面子＋雀頭1つに分けられるか"""
    for t in sorted(cnt):
        if cnt[t] >= 2:
            c = cnt.copy(); c[t] -= 2
            if _sets(c, sets):
                return True
    return False


def _sets(c, n):
    c = +c
    if not c:
        return n == 0
    t = min(c)
    if c[t] >= 3:
        d = c.copy(); d[t] -= 3
        if _sets(d, n - 1):
            return True
    if t[0] != "z" and int(t[1]) <= 7:
        a, b = f"{t[0]}{int(t[1]) + 1}", f"{t[0]}{int(t[1]) + 2}"
        if c[a] and c[b]:
            d = c.copy(); d[t] -= 1; d[a] -= 1; d[b] -= 1
            if _sets(d, n - 1):
                return True
    return False


def check(ex):
    tiles = [base(x) for x in parse(ex["hand"])] + [base(x) for x in parse(ex["win"])]
    melds = ex.get("melds", [])
    allt = tiles + [base(x) for _, m in melds for x in parse(m)]
    over = [t for t, n in Counter(allt).items() if n > 4]
    if over:
        return f"5枚以上: {over}"
    if len(tiles) + 3 * len(melds) != 14:
        return f"枚数が合わない: 手{len(tiles)}＋鳴き{len(melds)}"
    cnt = Counter(tiles)
    if _std(cnt, 4 - len(melds)):
        return None
    if not melds and len(cnt) == 7 and all(v == 2 for v in cnt.values()):
        return None
    yaochu = {f"{s}{n}" for s in "mps" for n in (1, 9)} | {f"z{i}" for i in range(1, 8)}
    if not melds and set(cnt) == yaochu and sum(cnt.values()) == 14:
        return None
    return "あがりの形になっていない"


# ---------------- 待ちを調べる（待ち当て道場の答えを計算で出す・2026-10-23〜）----------------
ALL34 = [f"{s}{n}" for s in "mps" for n in range(1, 10)] + [f"z{i}" for i in range(1, 8)]


def _splits(c, n):
    """c（数）を n 個の面子に分ける分け方をすべて返す（各面子は牌の並び）"""
    c = +c
    if not c:
        return [[]] if n == 0 else []
    t = min(c)
    out = []
    if c[t] >= 3:
        d = c.copy(); d[t] -= 3
        out += [[[t] * 3] + r for r in _splits(d, n - 1)]
    if t[0] != "z" and int(t[1]) <= 7:
        a, b = f"{t[0]}{int(t[1]) + 1}", f"{t[0]}{int(t[1]) + 2}"
        if c[a] and c[b]:
            d = c.copy(); d[t] -= 1; d[a] -= 1; d[b] -= 1
            out += [[[t, a, b]] + r for r in _splits(d, n - 1)]
    return out


def splits(tiles14):
    """14枚（鳴きなし）を「面子4つ＋雀頭」に分ける分け方をすべて返す。七対子の形なら ["七対子"] も足す"""
    cnt = Counter(base(x) for x in tiles14)
    out = []
    for t in sorted(cnt):
        if cnt[t] >= 2:
            c = cnt.copy(); c[t] -= 2
            for r in _splits(c, 4):
                k = sorted(map(tuple, r)) + [(t, t)]
                if k not in out:
                    out.append(k)
    if len(cnt) == 7 and all(v == 2 for v in cnt.values()):
        out.append("七対子")
    return out


def waits(hand13):
    """13枚（鳴きなし・"123m456p..." の書き方）の待ちの牌を返す。手の中に4枚ある牌は待ちに数えない（5枚目は無い）"""
    tiles = [base(x) for x in parse(hand13)]
    assert len(tiles) == 13, len(tiles)
    cnt = Counter(tiles)
    return [t for t in ALL34 if cnt[t] < 4 and splits(tiles + [t])]


# ---------------- 牌の並びのHTML ----------------
def tile_img(code, url, w, yoko=False, cls=""):
    name = tile_name(code)
    src = f"{url}/{code}{'-yoko' if yoko else ''}.svg"
    ww = round(w * 80 / 60) if yoko else w
    return f'<img src="{src}" alt="{name}" width="{ww}" class="{cls}" loading="lazy" decoding="async">'


def meld_html(kind, s, url, w):
    t = parse(s)
    if kind == "chi":
        parts = [tile_img(t[0], url, w, True)] + [tile_img(x, url, w) for x in t[1:]]
    elif kind == "pon":
        parts = [tile_img(x, url, w) for x in t[:2]] + [tile_img(t[2], url, w, True)]
    elif kind == "kan":
        parts = [tile_img(t[0], url, w), tile_img(t[1], url, w, True)] + [tile_img(x, url, w) for x in t[2:]]
    else:  # ankan
        parts = [tile_img("back", url, w), tile_img(t[1], url, w), tile_img(t[2], url, w), tile_img("back", url, w)]
    label = {"chi": "チー", "pon": "ポン", "kan": "明槓", "ankan": "暗槓"}[kind]
    return f'<span class="meld" title="{label}">' + "".join(parts) + "</span>"


def hand_html(ex, url="/assets/tiles", w=26):
    h = "".join(tile_img(c, url, w) for c in parse(ex["hand"]))
    win = "".join(tile_img(c, url, w) for c in parse(ex["win"]))
    m = "".join(meld_html(k, s, url, w) for k, s in ex.get("melds", []))
    label = "、".join(tile_name(c) for c in parse(ex["hand"])) + "　あがり牌：" + tile_name(parse(ex["win"])[0])
    return (f'<span class="hand" role="img" aria-label="{label}"><span class="h-in">{h}</span>'
            f'<span class="h-win">{win}</span>' + (f'<span class="h-meld">{m}</span>' if m else "") + "</span>")


def han_label(m, n):
    if m == 13:
        return "役満" + ("" if n else "（門前のみ）")
    return f"{m}翻" + ("（門前のみ）" if n is None else ("" if n == m else f"（鳴くと{n}翻）"))


# ---------------- 1枚の表 ----------------
FONT = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">'
CSS = """@page { size: A4; margin: 0; } * { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 794px; height: 1123px; } body { font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #fff; padding: 28px 32px 20px; position: relative; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-feature-settings: "palt"; }
header { display: flex; align-items: flex-end; justify-content: space-between; border-bottom: 3px solid #1F2A28; padding-bottom: 8px; margin-bottom: 12px; }
header h1 { font-size: 30px; font-weight: 900; line-height: 1.1; } header h1 small { display: block; font-size: 12.5px; font-weight: 500; color: #55625F; margin-top: 5px; }
.legend { text-align: right; font-size: 10.5px; color: #55625F; line-height: 1.6; }
footer { position: absolute; left: 32px; right: 32px; bottom: 14px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; } footer b { color: #177083; font-weight: 900; }
img { display: inline-block; vertical-align: bottom; }"""


def hai_sheet(url):
    def suit_row(s, label, yomi):
        cells = "".join(f'<div class="c">{tile_img(f"{s}{n}", url, 64)}<b>{KANSU[n - 1] if s == "m" else n}{NAMES[s]}</b><span>{YOMI_NUM[n - 1]}{YOMI_SUIT[s]}</span></div>' for n in range(1, 10))
        return f'<section class="suit {s}"><h2><em>{label}</em><small>{yomi}・1〜9が4枚ずつ（36枚）</small></h2><div class="row">{cells}</div></section>'
    z = "".join(f'<div class="c">{tile_img(f"z{i}", url, 64)}<b>{Z[i][0]}</b><span>{Z[i][1]}</span></div>' for i in range(1, 8))
    aka = "".join(f'<div class="c">{tile_img(c, url, 52)}<b>赤{n}</b></div>' for c, n in [("m5r", "五萬"), ("p5r", "五筒"), ("s5r", "五索")])
    nums = "".join(f"<td>{n}<br><b>{y}</b></td>" for n, y in zip(range(1, 10), YOMI_NUM))
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}
.suit h2, .zi h2 {{ display: flex; align-items: baseline; gap: 8px; font-size: 11px; font-weight: 500; color: #55625F; margin: 0 0 6px; }}
.suit h2 em, .zi h2 em {{ font-style: normal; font-size: 15px; font-weight: 900; color: #fff; border-radius: 4px; padding: 1px 10px; }}
.m h2 em {{ background: #E25A1C; }} .p h2 em {{ background: #4261AA; }} .s h2 em {{ background: #177083; }} .zi h2 em {{ background: #1F2A28; }}
section {{ margin-bottom: 12px; }}
.row {{ display: flex; gap: 8px; }} .c {{ display: flex; flex-direction: column; align-items: center; width: 74px; }}
.c b {{ font-size: 12.5px; font-weight: 900; margin-top: 3px; }} .c span {{ font-size: 10.5px; color: #55625F; font-weight: 700; }}
.zi .c {{ width: 74px; }} .zi .grp {{ display: flex; gap: 8px; }} .zi .lbl {{ font-size: 10.5px; color: #8A9A97; font-weight: 700; margin: 0 0 3px; }}
.bottom {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 16px; margin-top: 4px; }}
h3 {{ font-size: 13px; font-weight: 900; border-left: 4px solid #1F2A28; padding-left: 7px; margin-bottom: 6px; }}
table {{ border-collapse: collapse; width: 100%; font-size: 11px; }} td, th {{ border: 1px solid #DFE6E3; padding: 4px 3px; text-align: center; }} th {{ background: #F3F6F5; }}
td b {{ font-size: 11.5px; }}
.aka {{ display: flex; gap: 10px; }} .aka .c {{ width: 64px; }} .note {{ font-size: 10.5px; line-height: 1.65; color: #33403D; }} .note b {{ color: #C2471A; }}
</style></head><body>
<header><h1>麻雀牌 一覧表<small>34種類・136枚の名前と読み方を1枚で</small></h1><div class="legend">数牌 27種（萬子・筒子・索子）＋字牌 7種（風牌・三元牌）<br>どの牌も4枚ずつ ＝ 34種 × 4枚 ＝ <b>136枚</b></div></header>
{suit_row("m", "萬子（マンズ）", "漢数字＋萬")}{suit_row("p", "筒子（ピンズ）", "丸の数")}{suit_row("s", "索子（ソーズ）", "竹の棒の数・1索だけ鳥の絵")}
<section class="zi"><h2><em>字牌（ジハイ）</em><small>数字がない牌・7種が4枚ずつ（28枚）</small></h2><div class="grp"><div><p class="lbl">風牌（カゼハイ）</p><div class="grp">{"".join(f'<div class="c">{tile_img(f"z{i}", url, 64)}<b>{Z[i][0]}</b><span>{Z[i][1]}</span></div>' for i in range(1, 5))}</div></div>
<div><p class="lbl">三元牌（サンゲンパイ）</p><div class="grp">{"".join(f'<div class="c">{tile_img(f"z{i}", url, 64)}<b>{Z[i][0]}</b><span>{Z[i][1]}</span></div>' for i in range(5, 8))}</div></div></div></section>
<div class="bottom"><div><h3>数字の読み方</h3><table><tr>{nums}</tr></table>
<p class="note" style="margin-top:6px">読みは「数字＋種類」。萬子＝マン（ワンとも）、筒子＝ピン、索子＝ソー。<br>例：五萬＝ウーマン、七筒＝チーピン、二索＝リャンソー<br>9は役の名前では<b>チュー</b>（九蓮宝燈・么九牌）。7索は関西で<b>チャーソー</b>とも</p>
<h3 style="margin-top:10px">よく出る呼び名</h3><p class="note"><b>么九牌（ヤオチューハイ）</b>：1・9の数牌と字牌。<b>中張牌（チュンチャンパイ）</b>：2〜8の数牌（タンヤオに使う）。<b>役牌</b>：三元牌と、場風・自風の牌</p></div>
<div><h3>赤ドラ（赤五）</h3><div class="aka">{aka}</div><p class="note" style="margin-top:6px">ふつうの五と差し替えて使う牌。持っているだけで<b>ドラ1枚</b>として数える（使うかどうかはルールで決める）。</p>
<h3 style="margin-top:10px">三麻（3人麻雀）</h3><p class="note">萬子の2〜8（28枚）を抜いた108枚で打つのが一般的。</p></div></div>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


def yaku_sheet(url):
    blocks = ""
    for grp, items in YAKU:
        rows = ""
        for name, yomi, m, n, cond, ex in items:
            tiles = hand_html(ex, url, 12) if ex else f'<span class="cond">{cond}</span>'
            big = "役満" if m == 13 else f"{m}翻"
            sub = "門前のみ" if n is None else ("" if n == m else f"鳴き{n}翻")
            rows += f'<tr><th><b>{name}</b><small>{yomi}</small></th><td class="h"><b>{big}</b>' + (f'<small>{sub}</small>' if sub else "") + f'</td><td class="t">{tiles}</td></tr>'
        blocks += f'<section class="g"><h2>{grp}</h2><table>{rows}</table></section>'
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}
.cols {{ column-count: 2; column-gap: 14px; }} .g {{ break-inside: avoid; margin-bottom: 6px; }}
.g h2 {{ font-size: 12.5px; font-weight: 900; color: #fff; background: #177083; padding: 2px 8px; border-radius: 3px; margin-bottom: 2px; }}
.g:last-child h2 {{ background: #E25A1C; }}
table {{ width: 100%; border-collapse: collapse; }} tr {{ border-bottom: 1px solid #E3E9E7; }}
th {{ text-align: left; width: 78px; padding: 3px 2px; line-height: 1.15; }} th b {{ display: block; font-size: 11.5px; font-weight: 900; }} th small {{ font-size: 8.5px; color: #6B7A77; font-weight: 700; }}
td.h {{ width: 42px; line-height: 1.15; }} td.h b {{ display: block; font-size: 11px; font-weight: 900; color: #136070; }} td.h small {{ display: block; font-size: 8px; font-weight: 700; color: #8A9A97; white-space: nowrap; }}
td.t {{ padding: 3px 0; }} .hand {{ display: inline-flex; align-items: flex-end; gap: 0; }} .hand img {{ margin-right: .5px; }}
.h-win {{ margin-left: 3px; padding: 1px; border-radius: 2px; background: #FFE2D3; }} .h-meld {{ margin-left: 3px; display: inline-flex; gap: 2px; }} .hand {{ white-space: nowrap; }}
.meld {{ display: inline-flex; align-items: flex-end; }} .cond {{ font-size: 9.5px; color: #55625F; }}
.notes {{ font-size: 9.5px; color: #55625F; line-height: 1.55; margin-top: 4px; }}
</style></head><body>
<header><h1>麻雀 役一覧表<small>1翻〜役満まで全38役・翻数と牌の並びの例</small></h1><div class="legend">オレンジの枠の牌 ＝ あがり牌　右の横向きの牌 ＝ 鳴いた面子<br>鳴き○翻 ＝ チー・ポン・カンをしたときの翻数<br>文字だけの役 ＝ あがったときの状況で決まる役</div></header>
<div class="cols">{blocks}</div>
<p class="notes">あがるには役が1つ以上必要（ドラだけではあがれない）。役は重ねて数える。ドラ・赤ドラ・裏ドラは役ではなく、役があるときに1枚1翻を足す。流し満貫・人和・数え役満などはルールで決める。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    url = "file:///" + os.path.join(ROOT, "assets", "tiles").replace("\\", "/")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, html in [("hai-ichiran", hai_sheet(url)), ("yaku-ichiran", yaku_sheet(url))]:
            hp = os.path.join(OUT, f"_{name}.html")
            io.open(hp, "w", encoding="utf-8").write(html)
            u = "file:///" + hp.replace("\\", "/")
            for suffix, scale in [("", 2481 / 794), ("-web", 2)]:
                pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
                pg.goto(u); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1000)
                pg.screenshot(path=os.path.join(OUT, f"{name}{suffix}.png"))
                pg.close()
            pg = b.new_page(); pg.goto(u); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1000)
            pg.pdf(path=os.path.join(OUT, f"{name}.pdf"), format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            pg.close()
            os.remove(hp)
        b.close()
    try:
        from PIL import Image
        for f in os.listdir(OUT):
            if f.endswith(".png"):
                Image.open(os.path.join(OUT, f)).save(os.path.join(OUT, f), optimize=True)
    except ImportError:
        pass


if __name__ == "__main__":
    bad = []
    for grp, items in YAKU:
        for name, yomi, m, n, cond, ex in items:
            if ex:
                r = check(ex)
                if r:
                    bad.append(f"{name}: {r}")
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    print("役の数:", sum(len(i) for _, i in YAKU), "／例の確認:", "すべてOK" if not bad else bad)
    if bad:
        sys.exit(1)
    if "--check" not in sys.argv:
        render()
        for f in sorted(os.listdir(OUT)):
            print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, "KB")
