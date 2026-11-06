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
  ("断么九", "タンヤオ", 1, 1, "二〜八の数牌だけで作る", dict(hand="234m567m345p66s78s", win="6s")),
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
  ("混全帯么九", "チャンタ", 2, 1, "全部の面子と雀頭に一・九か字牌", dict(hand="123m789p789s111z9m", win="9m")),
  ("対々和", "トイトイ", 2, 2, "刻子4つ＋雀頭", dict(hand="222m999s3z", win="3z", melds=[("pon", "555p"), ("pon", "777s")])),
  ("三暗刻", "サンアンコー", 2, 2, "鳴いていない刻子を3つ", dict(hand="222m555p888s34m66s", win="5m")),
  ("三色同刻", "サンショクドウコー", 2, 2, "萬・筒・索で同じ数の刻子", dict(hand="222m222p222s567m8s", win="8s")),
  ("三槓子", "サンカンツ", 2, 2, "カンを3回", dict(hand="456m9p", win="9p", melds=[("ankan", "3333m"), ("kan", "5555p"), ("kan", "7777s")])),
  ("小三元", "ショウサンゲン", 2, 2, "三元牌の刻子2つ＋三元牌の雀頭（役牌2つで実質4翻）", dict(hand="555z666z77z123m45p", win="3p")),
  ("混老頭", "ホンロウトウ", 2, 2, "一・九と字牌だけ（対々和か七対子と重なる）", dict(hand="111m999p999s111z2z", win="2z")),
 ]),
 ("3翻", [
  ("混一色", "ホンイツ", 3, 2, "1種類の数牌と字牌だけ", dict(hand="234m567m888m11z22z", win="2z")),
  ("純全帯么九", "ジュンチャン", 3, 2, "全部の面子と雀頭に一・九（字牌なし）", dict(hand="123m789m123p789s1p", win="1p")),
  ("二盃口", "リャンペーコー", 3, None, "一盃口を2つ", dict(hand="112233m445566p7s", win="7s")),
 ]),
 ("6翻", [
  ("清一色", "チンイツ", 6, 5, "1種類の数牌だけ", dict(hand="2233445566778s", win="8s")),
 ]),
 ("役満", [
  ("国士無双", "コクシムソウ", 13, None, "一・九と字牌の13種を1枚ずつ＋どれか1枚", dict(hand="119m19p19s123456z", win="7z")),
  ("四暗刻", "スーアンコー", 13, None, "鳴いていない刻子を4つ", dict(hand="111m333p555s777s9p", win="9p")),
  ("大三元", "ダイサンゲン", 13, 13, "白・發・中の刻子を3つ", dict(hand="555z666z777z12m33p", win="3m")),
  ("字一色", "ツーイーソー", 13, 13, "字牌だけ", dict(hand="111z222z333z555z7z", win="7z")),
  ("小四喜", "ショウスーシー", 13, 13, "風牌の刻子3つ＋風牌の雀頭", dict(hand="111z222z333z44z23m", win="1m")),
  ("大四喜", "ダイスーシー", 13, 13, "風牌の刻子を4つ", dict(hand="111z222z333z444z5m", win="5m")),
  ("緑一色", "リューイーソー", 13, 13, "二・三・四・六・八索と發だけ", dict(hand="223344s666s888s6z", win="6z")),
  ("清老頭", "チンロウトウ", 13, 13, "一と九の数牌だけ", dict(hand="111m999m111p999p1s", win="1s")),
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
# 見た目は点数早見表（score_sheet.py）とそろえる: 色の帯の見出し・色の札・太い枠の表・大きい字。説明の文はのせない（2026-11-06 ユーザーの指定）
FONT = '<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">'
CSS = """@page { size: A4; margin: 0; } * { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 794px; height: 1123px; } body { font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #fff; padding: 30px 34px 22px; position: relative; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-feature-settings: "palt"; }
header { display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 10px 16px; margin-bottom: 14px; }
header h1 { font-size: 32px; font-weight: 900; letter-spacing: .04em; line-height: 1.1; } header h1 small { display: block; font-size: 13px; font-weight: 700; color: #DDF0EC; letter-spacing: 0; margin-top: 4px; }
.legend { text-align: right; font-size: 12px; font-weight: 700; color: #fff; line-height: 1.7; background: rgba(255,255,255,.14); border-radius: 6px; padding: 5px 10px; } .legend b { font-size: 15px; } .legend span { color: #FFE68A; font-weight: 900; }
.blk h2 { display: flex; align-items: center; gap: 8px; font-size: 12px; font-weight: 800; color: #1F2A28; margin-bottom: 5px; }
.blk h2 em { font-style: normal; font-size: 18px; font-weight: 900; color: #fff; border-radius: 4px; padding: 0 12px; line-height: 28px; }
table { width: 100%; border-collapse: collapse; table-layout: fixed; border: 2px solid #1F2A28; }
footer { position: absolute; left: 34px; right: 34px; bottom: 16px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; } footer b { color: #177083; font-weight: 900; }
img { display: inline-block; vertical-align: bottom; }"""

SUIT_COLOR = {"m": "#E25A1C", "p": "#4261AA", "s": "#177083", "z": "#1F2A28"}


def hai_sheet(url):
    def cell(code, name, yomi, w=52):
        return f'<td>{tile_img(code, url, w)}<b>{name}</b><span>{yomi}</span></td>'

    def suit(s, label, sub):
        head = "".join(f"<th>{n}</th>" for n in range(1, 10))
        cells = "".join(cell(f"{s}{n}", f"{KANSU[n - 1]}{NAMES[s]}", f"{YOMI_NUM[n - 1]}{YOMI_SUIT[s]}") for n in range(1, 10))
        return (f'<section class="blk {s}"><h2><em>{label}</em>{sub}</h2>'
                f'<table><thead><tr>{head}</tr></thead><tbody><tr>{cells}</tr></tbody></table></section>')
    kaze = "".join(cell(f"z{i}", Z[i][0], Z[i][1]) for i in range(1, 5))
    sangen = "".join(cell(f"z{i}", Z[i][0], Z[i][1]) for i in range(5, 8))
    nums = "".join(f"<td><b>{n}</b><span>{y}</span></td>" for n, y in zip(range(1, 10), YOMI_NUM))
    aka = "".join(cell(c, n, "赤ドラ", 40) for c, n in [("m5r", "赤五萬"), ("p5r", "赤五筒"), ("s5r", "赤五索")])
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}
section {{ margin-bottom: 10px; }}
thead th {{ font-size: 13px; font-weight: 900; color: #fff; padding: 3px 0; border-left: 1px solid rgba(255,255,255,.35); }}
.m thead th, .m h2 em {{ background: #E25A1C; }} .p thead th, .p h2 em {{ background: #4261AA; }} .s thead th, .s h2 em {{ background: #177083; }} .z thead th, .z h2 em, .x thead th, .x h2 em {{ background: #1F2A28; }}
td {{ text-align: center; border-left: 1px solid #8FA29D; padding: 6px 0 5px; line-height: 1.2; }}
td b {{ display: block; font-size: 15px; font-weight: 900; margin-top: 4px; }} td span {{ display: block; font-size: 12.5px; font-weight: 800; }}
.m td span {{ color: #B23A0E; }} .p td span {{ color: #22397A; }} .s td span {{ color: #0B4D5A; }} .z td span {{ color: #33403D; }}
.z table {{ width: auto; }} .z td {{ width: 76px; }} .z .row {{ display: flex; gap: 14px; }}
.bottom {{ display: grid; grid-template-columns: 1.25fr 1fr; gap: 14px; }}
.x td {{ padding: 6px 0; }} .x td b {{ margin-top: 0; font-size: 17px; }} .x td span {{ color: #177083; }}
.aka td span {{ color: #B23A0E; }} .aka td {{ padding: 5px 0 4px; }} .aka td b {{ font-size: 13px; margin-top: 2px; }}
.total {{ margin-top: 2px; border: 2px solid #1F2A28; border-radius: 6px; display: flex; align-items: center; justify-content: center; gap: 10px; padding: 9px 0; font-size: 16px; font-weight: 900; background: #FFF2B8; }}
.total b {{ font-size: 26px; color: #B23A0E; }}
</style></head><body>
<header><h1>麻雀牌 一覧表<small>全34種類の名前と読み方</small></h1><div class="legend">どの牌も <b>4枚</b>ずつ<br>34種 × 4枚 ＝ <span>136枚</span></div></header>
{suit("m", "萬子", "マンズ")}{suit("p", "筒子", "ピンズ")}{suit("s", "索子", "ソーズ")}
<section class="blk z"><h2><em>字牌</em>ジハイ</h2><div class="row">
<table><thead><tr><th colspan="4">風牌（カゼハイ）</th></tr></thead><tbody><tr>{kaze}</tr></tbody></table>
<table><thead><tr><th colspan="3">三元牌（サンゲンパイ）</th></tr></thead><tbody><tr>{sangen}</tr></tbody></table></div></section>
<div class="bottom"><section class="blk x"><h2><em>数字の読み方</em></h2><table><tbody><tr>{nums}</tr></tbody></table></section>
<section class="blk x aka"><h2><em>赤ドラ</em>持つだけでドラ1枚</h2><table><tbody><tr>{aka}</tr></tbody></table></section></div>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


# 役の一覧表に出す短い条件（表の1マスに収まる長さ）
SHORT = {
 "立直": "門前でテンパイして宣言", "一発": "リーチから1巡以内にあがる", "門前清自摸和": "門前でツモあがり", "断么九": "二〜八の数牌だけ",
 "平和": "順子4つ・両面待ち", "一盃口": "同じ順子が2つ", "役牌": "三元牌・場風・自風の刻子", "海底摸月": "最後の牌でツモ",
 "河底撈魚": "最後の捨て牌でロン", "嶺上開花": "嶺上牌でツモ", "槍槓": "加槓の牌でロン",
 "ダブル立直": "最初の打牌でリーチ", "七対子": "対子が7つ", "三色同順": "萬筒索で同じ数の順子", "一気通貫": "1種類で123・456・789",
 "混全帯么九": "全部の面子に一九・字牌", "対々和": "刻子が4つ", "三暗刻": "暗刻が3つ", "三色同刻": "萬筒索で同じ数の刻子",
 "三槓子": "カンが3回", "小三元": "三元牌の刻子2つ＋雀頭", "混老頭": "一九と字牌だけ",
 "混一色": "1種類の数牌＋字牌", "純全帯么九": "全部の面子に一九（字牌なし）", "二盃口": "一盃口が2つ", "清一色": "1種類の数牌だけ",
 "国士無双": "一九字牌13種＋1枚", "四暗刻": "暗刻が4つ", "大三元": "三元牌の刻子が3つ", "字一色": "字牌だけ",
 "小四喜": "風牌の刻子3つ＋雀頭", "大四喜": "風牌の刻子が4つ", "緑一色": "二三四六八索と發だけ", "清老頭": "一と九の数牌だけ",
 "四槓子": "カンが4回", "九蓮宝燈": "1112345678999＋1枚", "天和": "親が配牌であがり", "地和": "子が最初のツモであがり",
}
GROUP_COLOR = {"1翻": "#177083", "2翻": "#4261AA", "3翻": "#6A4BB0", "6翻": "#A8407F", "役満": "#E25A1C"}


def yaku_sheet(url):
    def block(grp, items):
        c = GROUP_COLOR[grp]
        rows = ""
        for name, yomi, m, n, cond, ex in items:
            big = "役満" if m == 13 else f"{m}翻"
            if n is None:
                naki = '<i class="mz">門前のみ</i>'
            elif n == m:
                naki = '<i class="ok">そのまま</i>'
            else:
                naki = f'<i class="dn">{n}翻</i>'
            rows += f'<tr><th><b>{name}</b><small>{yomi}</small></th><td class="h" style="color:{c}">{big}</td><td class="n">{naki}</td><td class="t">{SHORT[name]}</td></tr>'
        return (f'<section class="g" style="--c:{c}"><table><thead><tr><th class="gh">{grp}<small>{len(items)}役</small></th><th>翻</th><th>鳴き</th><th>形・条件</th></tr></thead>'
                f'<tbody>{rows}</tbody></table></section>')
    assert all(name in SHORT for _, items in YAKU for name, *_ in items)
    G = dict(YAKU)
    left = block("1翻", G["1翻"]) + block("2翻", G["2翻"])
    right = block("3翻", G["3翻"]) + block("6翻", G["6翻"]) + block("役満", G["役満"])
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}
.cols {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }} .g {{ margin-bottom: 10px; }}
thead th {{ background: var(--c); color: #fff; font-size: 11px; font-weight: 800; padding: 4px 0; border-left: 1px solid rgba(255,255,255,.35); }}
thead th.gh {{ font-size: 18px; font-weight: 900; text-align: left; padding: 3px 9px; border-left: 0; }} thead th.gh small {{ font-size: 11px; font-weight: 700; margin-left: 6px; opacity: .85; }}
thead th:nth-child(1) {{ width: 112px; }} thead th:nth-child(2) {{ width: 44px; }} thead th:nth-child(3) {{ width: 58px; }}
tbody th {{ text-align: left; background: #E3ECE9; padding: 4px 7px; border-bottom: 1px solid #8FA29D; border-right: 1.5px solid #1F2A28; line-height: 1.15; }}
tbody th b {{ display: block; font-size: 14px; font-weight: 900; white-space: nowrap; letter-spacing: -.02em; }} tbody th small {{ display: block; font-size: 9px; font-weight: 700; color: #55625F; white-space: nowrap; }}
td {{ border-bottom: 1px solid #8FA29D; border-left: 1px solid #8FA29D; text-align: center; height: 37px; }}
td.h {{ font-size: 15px; font-weight: 900; }} td.t {{ text-align: left; font-size: 11.5px; font-weight: 700; padding: 0 6px; line-height: 1.3; }}
td.n i {{ font-style: normal; font-size: 10.5px; font-weight: 900; border-radius: 3px; padding: 2px 4px; white-space: nowrap; }}
i.mz {{ background: #1F2A28; color: #fff; }} i.dn {{ color: #22397A; font-size: 13px !important; }} i.ok {{ color: #6B7A77; }}
.rule {{ border: 2px solid #1F2A28; border-radius: 6px; overflow: hidden; }} .rule h3 {{ background: #1F2A28; color: #fff; font-size: 14px; font-weight: 900; padding: 4px 10px; }}
.rule ul {{ list-style: none; padding: 7px 10px 8px; font-size: 12px; font-weight: 800; line-height: 1.75; }} .rule li::before {{ content: "●"; color: #E25A1C; font-size: 8px; margin-right: 6px; vertical-align: 2px; }}
</style></head><body>
<header><h1>麻雀 役一覧表<small>1翻〜役満 全38役</small></h1><div class="legend"><span>鳴き</span>＝チー・ポン・カンをしたとき<br>門前のみ＝鳴くとつかない</div></header>
<div class="cols"><div>{left}</div><div>{right}<div class="rule"><h3>役のきまり</h3><ul><li>あがるには役が1つ以上いる</li><li>役は重ねて数える</li><li>ドラは役ではない（役があるとき1枚1翻）</li></ul></div></div></div>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>翻数は一般的なルール</span></footer></body></html>"""


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
