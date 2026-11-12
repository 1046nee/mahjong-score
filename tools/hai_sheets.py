# -*- coding: utf-8 -*-
"""牌の一覧表・役の一覧表（1枚）と、記事に入れる牌の並びのHTMLを作る（2026-10-23〜）。牌の絵は assets/tiles/（tools/make_tiles.py）。

出力（assets/hai/）: hai-ichiran.png / hai-ichiran-web.png / hai-ichiran.pdf、mahjong-yaku-ichiran.png / -web.png / .pdf、mahjong-local-yaku-ichiran.png / -web.png / .pdf
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
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}{LOGO_CSS}
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
<header><h1>麻雀牌 一覧表<small>全34種類の名前と読み方</small></h1><div class="legend">どの牌も <b>4枚</b>ずつ<br>34種 × 4枚 ＝ <span>136枚</span></div>{logo_html()}</header>
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


from sheet_logo import LOGO_CSS, logo_html  # noqa: E402  見出しの右上のロゴ（2026-11-12〜）


def ex_tiles(ex, url, avail=206, wmax=13.5):
    """牌の例を1行に。手牌 → すき間 → あがり牌（オレンジの下地）→ すき間 → 鳴いた面子。幅に入るように牌の幅を決める"""
    hand = parse(ex["hand"]); win = parse(ex["win"]); melds = ex.get("melds", [])
    units = len(hand) + 1 + .5
    for k, t in melds:
        units += .45 + (3 + 80 / 60 if k in ("pon", "chi") else (3 + 80 / 60 if k == "kan" else 4))
        if k in ("pon", "chi"): units -= 1
    w = min(wmax, avail / units)
    def im(c, yoko=False):
        return tile_img(c, url, round(w, 2), yoko)
    h = "".join(im(c) for c in hand)
    wn = "".join(im(c) for c in win)
    m = "".join(meld_html(k, t, url, round(w, 2)) for k, t in melds)
    return f'<span class="ex"><span>{h}</span><span class="win">{wn}</span>' + (f'<span class="ml">{m}</span>' if m else "") + "</span>"


def naki_chip(m, n):
    if n is None:
        return '<i class="c-mz">門前<br>のみ</i>'
    if n == m:
        return '<i class="c-ok">鳴き<br>OK</i>'
    return f'<i class="c-dn">鳴くと<br><b>{n}翻</b></i>'


SHEET2_CSS = """
.cols { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.g { border: 2px solid #1F2A28; border-radius: 0; overflow: hidden; margin-bottom: 9px; background: #fff; } /* 表は点数早見表と同じ四角・濃い枠（2026-11-12 ユーザーの指定）。見出しの帯・凡例は丸角のまま */
.g > h2 { background: var(--c); color: #fff; display: flex; align-items: baseline; gap: 8px; padding: 2px 10px 3px; font-size: 17px; font-weight: 900; line-height: 1.2; }
.g > h2 small { font-size: 11px; font-weight: 700; opacity: .9; }
.row { display: grid; grid-template-columns: 94px 32px 1fr; align-items: center; column-gap: 6px; padding: 0 6px 0 0; border-top: 1px solid color-mix(in srgb, var(--c) 30%, #fff); min-height: 34px; }
/* 役の名前の列は、点数早見表の左の列と同じ作り: 薄い色の地＋右に濃い線（2026-11-12 ユーザーの指定）。色は表の見出しの色を薄めたもの */
.row .nm { align-self: stretch; display: flex; flex-direction: column; justify-content: center; padding: 3px 6px 3px 8px; background: color-mix(in srgb, var(--c) 11%, #fff); border-right: 1.5px solid #1F2A28; }
.row:first-of-type { border-top: 0; }
.row .nm b { display: block; font-size: 14px; font-weight: 900; letter-spacing: -.03em; white-space: nowrap; line-height: 1.15; }
.row .nm small { display: block; font-size: 8.5px; font-weight: 700; color: #55625F; white-space: nowrap; letter-spacing: -.02em; }
.row i { display: grid; place-items: center; font-style: normal; font-size: 8px; font-weight: 900; line-height: 1.12; text-align: center; border-radius: 6px; height: 27px; }
.c-mz { background: #1F2A28; color: #fff; } .c-ok { background: #E4F3EC; color: #177083; border: 1.5px solid #9FC3BD; }
.c-dn { background: #EAF0FB; color: #22397A; border: 1.5px solid #B9C6E4; } .c-dn b { font-size: 10px; }
.c-na { background: #F1F4F3; color: #8A9A97; } .c-loc { background: #FFF3E0; color: #B4561B; border: 1.5px solid #F2C6A0; }
.row .bd { min-width: 0; }
.ex { display: flex; align-items: flex-end; gap: 0; white-space: nowrap; }
.ex > span { display: flex; align-items: flex-end; }
.ex .win { margin-left: 3px; background: #E75620; border-radius: 3px; padding: 1.5px; }
.ex .ml { margin-left: 5px; gap: 3px; } .ex .meld { display: inline-flex; align-items: flex-end; }
.ex img { display: block; }
.row .t { font-size: 9.5px; font-weight: 700; color: #33403D; margin-top: 1px; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.row .t b { color: var(--c); font-weight: 900; }
.row.sit .t { font-size: 11.5px; font-weight: 800; margin-top: 0; color: #1F2A28; white-space: normal; }
.row.sit { min-height: 30px; }
.legend2 { display: flex; gap: 6px; align-items: center; justify-content: center; margin: 0 0 9px; padding: 5px 8px; background: #EEF5F3; border-radius: 8px; }
.legend2 span { display: flex; align-items: center; gap: 5px; padding: 0 6px; font-size: 11px; font-weight: 800; color: #1F2A28; white-space: nowrap; }
.legend2 i { width: 30px; height: 22px; display: grid; place-items: center; font-style: normal; font-size: 7.5px; font-weight: 900; line-height: 1.05; border-radius: 4px; text-align: center; }
.legend2 .win-k { width: 16px; height: 16px; background: #E75620; border-radius: 3px; }
.box { border: 2px solid #177083; border-radius: 8px; overflow: hidden; background: #fff; }
.box h3 { background: #177083; color: #fff; font-size: 13.5px; font-weight: 900; padding: 4px 10px; }
.box ul { list-style: none; padding: 6px 10px 7px; font-size: 11.5px; font-weight: 800; line-height: 1.7; }
.box li::before { content: ""; display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #E75620; margin-right: 6px; vertical-align: 2px; }
.box li b { color: #E75620; }
"""


def _nm(name, yomi):
    """役の名前の列。長い名前・読みは、線をはみ出さないように字を小さく（門前清自摸和・トウホクシンカンセン）"""
    bs = ' style="font-size:11px"' if len(name) >= 7 else (' style="font-size:12.5px"' if len(name) >= 6 else "")
    ys = ' style="font-size:7.6px"' if len(yomi) >= 10 else ""
    return f'<div class="nm"><b{bs}>{name}</b><small{ys}>{yomi}</small></div>'


def _rows(items, url, color):
    out = ""
    for name, yomi, m, n, cond, ex in items:
        if ex:
            body = f'{ex_tiles(ex, url)}<p class="t">{SHORT[name]}</p>'
            cls = "row"
        else:
            body = f'<p class="t">{SHORT_SIT.get(name, SHORT[name])}</p>'
            cls = "row sit"
        out += f'<div class="{cls}">{_nm(name, yomi)}{naki_chip(m, n)}<div class="bd">{body}</div></div>'
    return out


# 状況で決まる役（牌の例が無い）は、大事な語を色で
SHORT_SIT = {
 "一発": "リーチから<b>1巡以内</b>にあがる（鳴きが入ると消える）", "門前清自摸和": "鳴かずに<b>自分で引いて</b>あがる",
 "海底摸月": "<b>最後の牌</b>でツモ", "河底撈魚": "<b>最後の捨て牌</b>でロン", "嶺上開花": "<b>カンのあとに引いた牌</b>でツモ",
 "槍槓": "ほかの人の<b>加槓の牌</b>でロン", "ダブル立直": "<b>最初の打牌</b>でリーチ", "天和": "親が<b>配牌の時点</b>であがっている",
 "地和": "子が<b>最初のツモ</b>であがる",
}


def legend2():
    return ('<div class="legend2"><span><i class="c-mz">門前<br>のみ</i>鳴くとつかない</span><span><i class="c-dn">鳴くと<br>1翻</i>鳴くと下がる</span>'
            '<span><i class="c-ok">鳴き<br>OK</i>そのまま</span><span><i class="win-k"></i>あがり牌</span></div>')


def yaku_sheet(url):
    assert all(name in SHORT for _, items in YAKU for name, *_ in items)
    G = dict(YAKU)
    def grp(k, sub=""):
        c = GROUP_COLOR[k]
        return f'<section class="g" style="--c:{c}"><h2>{k}<small>{len(G[k])}役{sub}</small></h2>{_rows(G[k], url, c)}</section>'
    left = grp("1翻") + grp("2翻")
    right = (grp("3翻") + grp("6翻") + grp("役満", "・数え役満は13翻〜") +
             '<div class="box"><h3>役のきまり</h3><ul><li>あがるには<b>役が1つ以上</b>いる（ドラだけではあがれない）</li>'
             '<li>役は<b>重ねて数える</b>（リーチ＋タンヤオ＋ドラ1で3翻）</li><li>ドラは役ではない。役があるとき<b>1枚1翻</b></li></ul></div>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}{LOGO_CSS}{SHEET2_CSS}
body {{ padding: 24px 30px 20px; }} header {{ margin-bottom: 10px; padding: 9px 12px 9px 16px; }}
</style></head><body>
<header><h1>麻雀 役一覧表<small>1翻〜役満 全38役・牌の例つき</small></h1>{logo_html()}</header>{legend2()}
<div class="cols"><div>{left}</div><div>{right}</div></div>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>翻数は一般的なルール・牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


# ---------------- ローカル役の一覧表（2026-11-12〜・blog-local-yaku と同じ中身） ----------------
# (名前, 読み, 鳴き: 'mz'=門前のみ / 'ok'=鳴きOK / 'loc'=卓で決める / 'na'=形でない, 条件, 例)
LOCAL_YAKUMAN = [
 ("八連荘", "パーレンチャン", "na", "親が<b>8回続けて</b>あがる（8回目を役満に）", None),
 ("大車輪", "ダイシャリン", "mz", "<b>二〜八筒を2枚ずつ</b>", dict(hand="2233445566778p", win="8p")),
 ("四連刻", "スーレンコー", "loc", "同じ種類で<b>数が続いた刻子</b>4つ", dict(hand="2223334445559p", win="9p")),
 ("一色四順", "イーソースーシュン", "loc", "<b>同じ順子</b>を4つ", dict(hand="1111222233335p", win="5p")),
 ("紅孔雀", "ベニクジャク", "ok", "<b>一・五・七・九索と中</b>だけ", dict(hand="1115559997777sz"[:0] + "111555999s777z7s", win="7s")),
 ("紅一点", "コウイッテン", "loc", "緑一色の<b>發を中</b>に（中が雀頭）", dict(hand="2233446668887zs"[:0] + "223344666888s7z", win="7z")),
 ("黒一色", "ヘイイーソー", "loc", "<b>二・四・八筒と風牌</b>だけ", dict(hand="222444888p1112z"[:0] + "222444888p1112z", win="2z")),
 ("百万石", "ヒャクマンゴク", "ok", "萬子だけで<b>数字の合計100以上</b>", dict(hand="9998887776665m", win="5m")),
 ("東北新幹線", "トウホクシンカンセン", "mz", "<b>東・北</b>＋一気通貫", dict(hand="11144z12345678m", win="9m")),
 ("金門橋", "キンモンキョウ", "loc", "<b>123・345・567・789</b>（同じ種類）", dict(hand="1233455677895s"[:0] + "123345567789p5s", win="5s")),
 ("大七星", "ダイチーシン", "mz", "<b>字牌7種</b>の七対子", dict(hand="1122334455667z", win="7z")),
 ("パッチリ", "パッチギ", "mz", "<b>4枚使いの対子2組</b>の七対子", dict(hand="2222m5555p77s11z9m", win="9m")),
 ("十三不塔", "シーサンプーター", "mz", "配牌で<b>面子も搭子もなく</b>対子が1つ", None),
]
LOCAL_YAKU = [
 ("人和", "レンホー", "子が<b>最初のツモより前</b>にロン", "役満・倍満・跳満・満貫"),
 ("流し満貫", "ナガシマンガン", "流局で<b>捨て牌が全部么九牌</b>・鳴かれていない", "満貫（まれに倍満・三倍満）"),
 ("三連刻", "サンレンコー", "<b>数が続いた刻子3つ</b>", "2翻"),
 ("オープン立直", "オープンリーチ", "リーチで<b>手牌を全部見せる</b>", "2翻（振り込むと役満の払い）"),
 ("五門斉", "ウーメンサイ", "<b>萬・筒・索・風・三元</b>を全部使う", "2翻・5翻・役満など"),
 ("燕返し", "ツバメガエシ", "<b>リーチ宣言の牌</b>でロン", "扱いに揺れがある"),
 ("十二落抬", "シーアルラオタイ", "<b>4つ全部鳴いて</b>単騎であがる", "1翻"),
 ("金鶏独立", "チンチードクリツ", "十二落抬で<b>一索の単騎</b>", "満貫"),
]
# ルールで2倍になる役満（形によるダブル役満）。Mリーグ・天鳳は1倍、雀魂は2倍（blog-yakuman-rules と同じ中身・2026-11-12 ユーザーの依頼）
DOUBLE_YAKUMAN = [
 ("四暗刻単騎", "スーアンコータンキ", "四暗刻を<b>単騎待ち</b>（雀頭の1枚待ち）であがる", dict(hand="111m333p555s222z4z", win="4z")),
 ("国士無双十三面", "コクシジュウサンメン", "<b>13種どれでも</b>あがれる国士無双", dict(hand="19m19p19s1234567z", win="1m")),
 ("純正九蓮宝燈", "ジュンセイチューレン", "<b>1112345678999</b>の形で9種待ち", dict(hand="1112345678999m", win="5m")),
 ("大四喜", "ダイスーシー", "<b>風牌4種</b>を全部刻子に", dict(hand="111222333444z5m", win="5m")),
]
# いちばん大きい形: 字一色＋大四喜（2倍）＋四暗刻単騎（2倍）＋四槓子＝6倍
MAX6 = dict(hand="7z", win="7z", melds=[("ankan", "1111z"), ("ankan", "2222z"), ("ankan", "3333z"), ("ankan", "4444z")])
LOCAL_CHIP = {"mz": '<i class="c-mz">門前<br>のみ</i>', "ok": '<i class="c-ok">鳴き<br>OK</i>', "loc": '<i class="c-loc">卓で<br>決める</i>', "na": '<i class="c-na">回数<br>で決定</i>'}


def local_sheet(url):
    c = "#E25A1C"
    rows = ""
    for name, yomi, nk, cond, ex in LOCAL_YAKUMAN:
        body = (f'{ex_tiles(ex, url)}<p class="t">{cond}</p>' if ex else f'<p class="t">{cond}</p>')
        rows += f'<div class="row{"" if ex else " sit"}">{_nm(name, yomi)}{LOCAL_CHIP[nk]}<div class="bd">{body}</div></div>'
    half = 7
    parts = rows.split('<div class="row')[1:]
    left_rows = "".join('<div class="row' + p for p in parts[:half]); right_rows = "".join('<div class="row' + p for p in parts[half:])
    yrow = lambda n, y, cd, v: f'<tr><th><b>{n}</b><small>{y}</small></th><td class="tc">{cd}</td><td class="tv">{v}</td></tr>'
    yk1 = "".join(yrow(*x) for x in LOCAL_YAKU[:4]); yk2 = "".join(yrow(*x) for x in LOCAL_YAKU[4:])
    dchip = '<i class="c-dbl">ルール<br>で2倍</i>'
    drow = lambda n, y, cd, ex: f'<div class="row">{_nm(n, y)}{dchip}<div class="bd">{ex_tiles(ex, url, avail=232)}<p class="t">{cd}</p></div></div>'
    d1 = "".join(drow(*x) for x in DOUBLE_YAKUMAN[:2]); d2 = "".join(drow(*x) for x in DOUBLE_YAKUMAN[2:])
    # 最大の形は、ローカル役満の左の列の下（右の列より短くて空いていた所）に置く
    max6 = (f'<section class="g dbl m6" style="--c:#A8407F"><h2>いちばん大きい形<small>6倍役満</small></h2><div class="m6b">{ex_tiles(MAX6, url, avail=330, wmax=19)}'
            f'<p class="t"><b>字一色</b>＋<b>大四喜</b>（2倍）＋<b>四暗刻単騎</b>（2倍）＋<b>四槓子</b>＝<b>6倍</b><br>子192,000点・親288,000点（形の2倍がないルールでは4倍）</p></div></section>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}{LOGO_CSS}{SHEET2_CSS}
body {{ padding: 24px 30px 20px; }} header {{ margin-bottom: 10px; padding: 9px 12px 9px 16px; background: #B4561B; }}
/* 画像の大きさは役一覧表と同じ A4 にそろえる（下に余白が出てもよい。2026-11-12 ユーザーの指定） */
.lt {{ width: 100%; border-collapse: collapse; table-layout: fixed; border: 0; }}
.lt th {{ text-align: left; background: #FFF3E0; padding: 4px 8px; border-top: 1px solid #F2D9C2; border-right: 1.5px solid #1F2A28; width: 92px; line-height: 1.15; }}
.lt th b {{ display: block; font-size: 13.5px; font-weight: 900; white-space: nowrap; letter-spacing: -.03em; }} .lt th small {{ display: block; font-size: 8.5px; font-weight: 700; color: #6B5A4C; white-space: nowrap; }}
.lt td {{ border-top: 1px solid #F2D9C2; padding: 4px 7px; font-size: 10.5px; font-weight: 700; line-height: 1.3; }}
.lt td b {{ color: #B4561B; font-weight: 900; }} .lt td.tv {{ width: 104px; font-size: 10px; font-weight: 800; color: #1F2A28; border-left: 1px solid #F2D9C2; }}
.lt tr:first-child th, .lt tr:first-child td {{ border-top: 0; }}
.box {{ border-color: #B4561B; }} .box h3 {{ background: #B4561B; }}
/* 行の高さは役一覧表と同じにそろえる（2026-11-12 ユーザーの指定。前は70pxで間延びしていた） */
.lt2 {{ display: grid; grid-template-columns: 1fr 1fr; }} .lt2 .lt + .lt {{ border-left: 2px solid #F2D9C2; }}
.dbl .lt2 > div + div {{ border-left: 2px solid #1F2A28; }} .dbl .row:first-child {{ border-top: 0; }}
.c-dbl {{ background: #F7E6EF; color: #A8407F; border: 1.5px solid #E0B4CB; }}
.m6 .m6b {{ padding: 6px 10px 6px; background: #FBF2F7; }} .m6 .ex {{ justify-content: center; }}
.m6 .t {{ font-size: 11px; font-weight: 800; white-space: normal; text-align: center; margin-top: 4px; line-height: 1.45; }} .m6 .t b {{ color: #A8407F; }}
.lt td, .lt th {{ height: 34px; padding-top: 3px; padding-bottom: 3px; }} .lt td {{ font-size: 11px; }} .lt td.tv {{ font-size: 10.5px; width: 98px; }}
</style></head><body>
<header><h1>麻雀 ローカル役一覧表<small>ローカル役満13・ローカル役8・ダブル役満・牌の例つき</small></h1>{logo_html()}</header>{legend2().replace('<span><i class="c-dn">鳴くと<br>1翻</i>鳴くと下がる</span>', '<span><i class="c-loc">卓で<br>決める</i>ルールしだい</span>')}
<div class="cols loc">
<div><section class="g" style="--c:{c}"><h2>ローカル役満<small>13役</small></h2>{left_rows}</section>{max6}</div>
<div><section class="g" style="--c:{c}"><h2>ローカル役満<small>つづき</small></h2>{right_rows}</section>
<div class="box"><h3>ローカル役は打つ前に決める</h3><ul><li><b>あるか・ないか</b>（Mリーグなど競技のルールでは使わない）</li><li>あるなら<b>何点か</b>・<b>鳴いてもいいか</b></li><li>扱いは場所で違う。<b>初めての相手とは必ず確かめる</b></li></ul></div></div>
</div>
<section class="g" style="--c:#B4561B"><h2>ローカル役<small>役満より下の扱いが多い・右は扱いの例</small></h2><div class="lt2"><table class="lt"><tbody>{yk1}</tbody></table><table class="lt"><tbody>{yk2}</tbody></table></div></section>
<section class="g dbl" style="--c:#A8407F"><h2>ルールで2倍になる役満<small>雀魂などはダブル役満・Mリーグ・天鳳は役満のまま</small></h2><div class="lt2"><div>{d1}</div><div>{d2}</div></div></section>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>扱いは一例（卓・雀荘・地域で違う）・牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    url = "file:///" + os.path.join(ROOT, "assets", "tiles").replace("\\", "/")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, html in [("hai-ichiran", hai_sheet(url)), ("mahjong-yaku-ichiran", yaku_sheet(url)), ("mahjong-local-yaku-ichiran", local_sheet(url))]:   # 役の表は 2026-11-12 に作り直したので名前を変えた（画像検索の見本を新しくするため。docs/image-tools.md）
            hp = os.path.join(OUT, f"_{name}.html")
            io.open(hp, "w", encoding="utf-8").write(html)
            u = "file:///" + hp.replace("\\", "/")
            for suffix, scale in [("", 2481 / 794), ("-web", 2)]:
                pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
                pg.goto(u); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1000)
                h = pg.evaluate("Math.ceil(document.body.getBoundingClientRect().height)")      # 中身が A4 より短い表は、その高さで切る
                pg.screenshot(path=os.path.join(OUT, f"{name}{suffix}.png"), clip={"x": 0, "y": 0, "width": 794, "height": min(1123, h)})
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
