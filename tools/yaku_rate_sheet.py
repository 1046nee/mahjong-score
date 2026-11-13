# -*- coding: utf-8 -*-
"""役の出やすさランキング・役満の出やすさの1枚の表（2026-11-13〜）。見た目は役一覧表（hai_sheets.py）とそろえる。

数字の出どころ: 天鳳 鳳凰卓 東南戦 赤あり 2023年 168,778戦（あがり 1,511,570回）の和了役統計
  （koba::blog「天鳳鳳凰卓統計(2023年)」https://blog.kobalab.net/entry/2024/11/04/215201 の表の回数）。
  出現率＝その役がついたあがりの回数 ÷ あがりの回数。翻牌（役牌）はダブ東なら2回と数えた数字。四喜和は大四喜と小四喜の合計。
出力（assets/hai/）: mahjong-yaku-ranking.png / -web.png / .pdf、mahjong-yakuman-ranking.png / -web.png / .pdf
実行: python tools/yaku_rate_sheet.py
"""
import io, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hai_sheets import CSS, FONT, SHEET2_CSS, YAKU, ex_tiles, naki_chip, check, OUT, ROOT  # noqa: E402
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402

GAMES, WINS = 168778, 1511570
SRC = "天鳳 鳳凰卓 2023年 168,778半荘・あがり1,511,570回の集計（koba::blog）"
# 役の名前（hai_sheets の YAKU と同じ字）→ あがりの回数
COUNT = {"立直": 627241, "役牌": 593823, "門前清自摸和": 377504, "断么九": 332470, "平和": 306891, "一発": 120275,
         "混一色": 68803, "一盃口": 59460, "三色同順": 56173, "七対子": 43426, "対々和": 22370, "一気通貫": 21947,
         "混全帯么九": 12515, "三暗刻": 9329, "清一色": 7990, "海底摸月": 6963, "河底撈魚": 6457, "純全帯么九": 4274,
         "嶺上開花": 3657, "ダブル立直": 2956, "小三元": 1175, "二盃口": 519, "三色同刻": 402, "混老頭": 402, "槍槓": 265, "三槓子": 15}
YAKUMAN = {"四暗刻": 556, "国士無双": 289, "大三元": 243, "四喜和": 96, "字一色": 20, "地和": 15, "清老頭": 14,
           "緑一色": 10, "九蓮宝燈": 10, "天和": 6, "四槓子": 1}
INFO = {name: (yomi, m, n, ex) for _, items in YAKU for name, yomi, m, n, cond, ex in items}
INFO["四喜和"] = ("スーシーホー", 13, 13, INFO["小四喜"][3])
WHY = {"天和": "親が配牌の時点であがっている", "地和": "子が最初のツモであがる"}


def pct(c): return c / WINS * 100
def sig3(x):
    """有効数字3桁（2026-11-13 ユーザーの指定。低い確率も 0.0192% のように3桁で）"""
    d = 2 - math.floor(math.log10(abs(x)))
    v = round(x, d)
    return f"{v:,.{max(0, d)}f}"
def pct_s(c): return sig3(pct(c)) + "%"
def once(c, d=WINS):
    return f"{sig3(d / c)}回に1回"


GROUP_COLOR = {1: "#177083", 2: "#4261AA", 3: "#6A4BB0", 6: "#A8407F", 13: "#E25A1C"}      # 役一覧表（hai_sheets）の翻ごとの色と同じ
RANK_CSS = """
.cols2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; align-items: start; }
.rk { border: 2px solid #1F2A28; background: #fff; }
.rk .hd { display: grid; grid-template-columns: 26px 96px 38px 1fr; background: #177083; color: #fff; font-size: 10.5px; font-weight: 900; }
.rk .hd span { text-align: center; padding: 3px 0; }
.r { display: grid; grid-template-columns: 26px 96px 38px 1fr; align-items: stretch; min-height: 40px; border-top: 1px solid color-mix(in srgb, var(--c) 35%, #fff); }
.r:first-of-type { border-top: 0; }
.r .no { display: grid; place-items: center; font-size: 13px; font-weight: 900; color: var(--c); background: color-mix(in srgb, var(--c) 7%, #fff); border-right: 1px solid color-mix(in srgb, var(--c) 35%, #fff); }
.r .nm { display: flex; flex-direction: column; justify-content: center; padding: 2px 5px 2px 7px; background: color-mix(in srgb, var(--c) 13%, #fff); border-right: 1.5px solid #1F2A28; border-left: 4px solid var(--c); }
.r .nm b { display: block; font-size: 13px; font-weight: 900; white-space: nowrap; letter-spacing: -.03em; line-height: 1.15; }
.r .nm small { display: block; font-size: 8px; font-weight: 700; color: #55625F; white-space: nowrap; }
.r .hn { display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px; padding: 0 3px; border-right: 1px solid color-mix(in srgb, var(--c) 35%, #fff); }
.r .hn b { display: block; width: 100%; text-align: center; background: var(--c); color: #fff; font-size: 10.5px; font-weight: 900; border-radius: 4px; line-height: 16px; }
.r .hn small { font-size: 7.5px; font-weight: 800; color: #55625F; white-space: nowrap; line-height: 1.1; }
.r .rt { display: flex; flex-direction: column; justify-content: center; padding: 2px 7px; gap: 2px; }
.bar { display: flex; align-items: center; gap: 5px; }
.bar .b { height: 9px; border-radius: 2px; background: var(--c); min-width: 2px; flex: none; }
.bar .v { font-size: 13.5px; font-weight: 900; white-space: nowrap; color: var(--c); }
.r .o { font-size: 9px; font-weight: 800; color: #6B7A77; white-space: nowrap; }
.r.top .no { background: #E75620; color: #fff; } .r.top .v { color: #E75620; font-size: 15px; }
.note { margin-top: 7px; font-size: 9.5px; font-weight: 700; color: #6B7A77; line-height: 1.5; }
.pts { display: flex; gap: 8px; margin: 0 0 9px; }
.pts div { flex: 1; border-radius: 8px; padding: 5px 8px; text-align: center; font-size: 11px; font-weight: 800; line-height: 1.3; color: #fff; }
.pts div:nth-child(1) { background: #177083; } .pts div:nth-child(2) { background: #E25A1C; } .pts div:nth-child(3) { background: #4261AA; }
.pts b { display: block; font-size: 20px; font-weight: 900; color: #FFE68A; line-height: 1.15; }      /* 3つの札は色の地に白い字（2026-11-13 ユーザーの指定「Xでは色味がある方がウケがいい」） */
body { background: #EEF6F3 !important; }      /* 紙の地も薄い緑に（表の中は白のまま） */
.lg { display: flex; gap: 10px; justify-content: center; margin: 0 0 8px; font-size: 11px; font-weight: 800; }
.lg span { display: flex; align-items: center; gap: 4px; } .lg i { width: 26px; height: 14px; border-radius: 3px; background: var(--c); }
"""


def han_cell(name):
    yomi, m, n, ex = INFO[name]
    if m == 13:
        return "役満", ("門前のみ" if n is None else "鳴きOK")
    return f"{m}翻", ("門前のみ" if n is None else ("鳴きOK" if n == m else f"鳴くと{n}翻"))


def ranking_sheet(url):
    allv = dict(COUNT); allv.update(YAKUMAN)
    items = sorted(allv.items(), key=lambda kv: -kv[1])
    mx = items[0][1]
    def row(k, name, c):
        yomi, m, n, ex = INFO[name]; col = GROUP_COLOR[m]; h, sub = han_cell(name)
        w = max(1.5, (c / mx) ** .5 * 100) * .7       # 棒は平方根の長さ（低い役も見えるように）
        return (f'<div class="r{" top" if k <= 5 else ""}" style="--c:{col}"><div class="no">{k}</div><div class="nm"><b>{name}</b><small>{yomi}</small></div>'
                f'<div class="hn"><b>{h}</b><small>{sub}</small></div><div class="rt"><div class="bar"><div class="b" style="width:{w:.1f}%"></div>'
                f'<span class="v">{pct_s(c)}</span></div><span class="o">あがり{once(c)}</span></div></div>')
    half = (len(items) + 1) // 2
    hd = '<div class="hd"><span>順位</span><span>役</span><span>翻</span><span>出現率（あがりのうち）</span></div>'
    left = "".join(row(k, nm, c) for k, (nm, c) in enumerate(items[:half], 1))
    right = "".join(row(k, nm, c) for k, (nm, c) in enumerate(items[half:], half + 1))
    lg = "".join(f'<span style="--c:{GROUP_COLOR[g]}"><i></i>{"役満" if g == 13 else f"{g}翻"}</span>' for g in (1, 2, 3, 6, 13))
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}{LOGO_CSS}{SHEET2_CSS}{RANK_CSS}
body {{ padding: 24px 30px 20px; }} header {{ margin-bottom: 10px; padding: 9px 12px 9px 16px; }}
</style></head><body>
<header><h1>麻雀 役の出やすさランキング<small>あがりのうち、その役がつく割合（一般役26役＋役満11役）</small></h1>{logo_html()}</header>
<div class="pts"><div>いちばん出る役<b>リーチ</b>あがりの約4割</div><div>いちばん出る役満<b>四暗刻</b>あがり{once(YAKUMAN["四暗刻"])}</div><div>いちばん出ない役<b>四槓子</b>151万回のあがりで1回</div></div>
<div class="lg">{lg}</div>
<div class="cols2"><section class="rk">{hd}{left}</section><section class="rk">{hd}{right}</section></div>
<p class="note">出現率＝その役がついたあがりの回数 ÷ あがりの回数（有効数字3桁）。役牌はダブ東などを2回と数えた数字。四喜和は大四喜と小四喜の合計。ドラは役ではないので入れていない。<br>データ: {SRC}</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>翻数は一般的なルール</span></footer></body></html>"""


HAI_CSS = """
.rk3 { border: 2px solid #1F2A28; background: #fff; }
.rk3 .hd, .r3 { display: grid; grid-template-columns: 30px 100px 46px 232px 1fr; }
.rk3 .hd { background: #177083; color: #fff; font-size: 10.5px; font-weight: 900; } .rk3 .hd span { text-align: center; padding: 3px 0; }
.r3 { align-items: stretch; min-height: 24.2px; border-top: 1px solid color-mix(in srgb, var(--c) 35%, #fff); }
.r3 .no { display: grid; place-items: center; font-size: 12px; font-weight: 900; color: var(--c); background: color-mix(in srgb, var(--c) 7%, #fff); border-right: 1px solid color-mix(in srgb, var(--c) 35%, #fff); }
.r3.top .no { background: #E75620; color: #fff; }
.r3 .nm { display: flex; flex-direction: column; justify-content: center; padding: 0 4px 0 6px; background: color-mix(in srgb, var(--c) 13%, #fff); border-right: 1.5px solid #1F2A28; border-left: 4px solid var(--c); line-height: 1.05; }
.r3 .nm b { font-size: 11.5px; font-weight: 900; white-space: nowrap; letter-spacing: -.03em; } .r3 .nm small { font-size: 6.5px; font-weight: 700; color: #55625F; white-space: nowrap; overflow: hidden; }
.r3 .hn { display: flex; flex-direction: column; justify-content: center; align-items: center; padding: 0 3px; border-right: 1px solid color-mix(in srgb, var(--c) 35%, #fff); }
.r3 .hn b { width: 100%; text-align: center; background: var(--c); color: #fff; font-size: 9.5px; font-weight: 900; border-radius: 3px; line-height: 13px; } .r3 .hn small { font-size: 6.5px; font-weight: 800; color: #55625F; white-space: nowrap; line-height: 1.1; }
.r3 .tl { display: flex; align-items: center; padding: 0 4px; border-right: 1px solid color-mix(in srgb, var(--c) 35%, #fff); overflow: hidden; }
.r3 .tl .sit { font-size: 9.5px; font-weight: 800; color: #33403D; white-space: nowrap; }
.r3 .rt { display: flex; align-items: center; gap: 6px; padding: 0 7px; }
.r3 .b { height: 9px; border-radius: 2px; background: var(--c); min-width: 2px; flex: none; }
.r3 .v { font-size: 12.5px; font-weight: 900; color: var(--c); white-space: nowrap; } .r3.top .v { color: #E75620; font-size: 13.5px; }
.r3 .o { font-size: 8.5px; font-weight: 800; color: #6B7A77; white-space: nowrap; margin-left: auto; }
.r3 .ex .win { margin-left: 2px; padding: 1px; }
"""


def ranking_sheet_hai(url):
    """牌の並びつきの版（役一覧表のように、役ごとに牌の例）。1列に37役"""
    from hai_sheets import SHORT
    allv = dict(COUNT); allv.update(YAKUMAN)
    items = sorted(allv.items(), key=lambda kv: -kv[1]); mx = items[0][1]
    rows = ""
    for k, (name, c) in enumerate(items, 1):
        yomi, m, n, ex = INFO[name]; col = GROUP_COLOR[m]; h, sub = han_cell(name)
        tl = ex_tiles(ex, url, avail=222, wmax=11.5) if ex else f'<span class="sit">{WHY.get(name) or SHORT.get(name, "")}</span>'
        w = max(1.5, (c / mx) ** .5 * 100) * .55
        rows += (f'<div class="r3{" top" if k <= 5 else ""}" style="--c:{col}"><div class="no">{k}</div><div class="nm"><b>{name}</b><small>{yomi}</small></div>'
                 f'<div class="hn"><b>{h}</b><small>{sub}</small></div><div class="tl">{tl}</div>'
                 f'<div class="rt"><div class="b" style="width:{w:.1f}%"></div><span class="v">{pct_s(c)}</span><span class="o">あがり{once(c)}</span></div></div>')
    lg = "".join(f'<span style="--c:{GROUP_COLOR[g]}"><i></i>{"役満" if g == 13 else f"{g}翻"}</span>' for g in (1, 2, 3, 6, 13))
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}{LOGO_CSS}{SHEET2_CSS}{RANK_CSS}{HAI_CSS}
body {{ padding: 20px 28px 16px; }} header {{ margin-bottom: 7px; padding: 8px 12px 8px 16px; }} .lg {{ margin-bottom: 6px; }}
</style></head><body>
<header><h1>麻雀 役の出やすさランキング<small>あがりのうち、その役がつく割合（一般役26役＋役満11役・牌の例つき）</small></h1>{logo_html()}</header>
<div class="lg">{lg}<span><i style="background:#E75620;width:16px;border-radius:3px"></i>あがり牌</span></div>
<section class="rk3"><div class="hd"><span>順位</span><span>役</span><span>翻</span><span>形の例</span><span>出現率（あがりのうち）</span></div>{rows}</section>
<p class="note">出現率＝その役がついたあがりの回数 ÷ あがりの回数（有効数字3桁）。役牌はダブ東などを2回と数えた数字。四喜和は大四喜と小四喜の合計（例は小四喜）。データ: {SRC}</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>翻数は一般的なルール・牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


MAN_CSS = """
.r2 { display: grid; grid-template-columns: 34px 112px 250px 1fr; column-gap: 8px; align-items: center; min-height: 72px; border-top: 1px solid #F2C6A0; padding-right: 10px; }
.r2:first-of-type { border-top: 0; }
.r2 .no { align-self: stretch; display: grid; place-items: center; font-size: 16px; font-weight: 900; color: #fff; background: #E25A1C; border-right: 1.5px solid #1F2A28; }
.r2 .nm b { display: block; font-size: 18px; font-weight: 900; white-space: nowrap; line-height: 1.15; } .r2 .nm small { display: block; font-size: 9px; font-weight: 700; color: #55625F; }
.r2 .sit { font-size: 11.5px; font-weight: 800; color: #33403D; }
.r2 .fq { display: flex; align-items: baseline; gap: 8px; justify-content: flex-end; flex-wrap: wrap; text-align: right; }
.r2 .fq b { font-size: 24px; font-weight: 900; color: #E25A1C; white-space: nowrap; } .r2 .fq b small { font-size: 11px; color: #1F2A28; font-weight: 800; }
.r2 .fq span { display: block; width: 100%; font-size: 10px; font-weight: 800; color: #6B7A77; }
.mk { border: 2px solid #1F2A28; } .mk .hd { display: grid; grid-template-columns: 34px 112px 250px 1fr; column-gap: 8px; background: #E25A1C; color: #fff; font-size: 11px; font-weight: 900; padding: 4px 10px 4px 0; }
.mk .hd span { text-align: center; } .mk .hd span:last-child { text-align: right; }
.big { display: flex; gap: 8px; margin: 0 0 10px; }
.big div { flex: 1; border-radius: 8px; padding: 6px 8px; text-align: center; font-size: 11.5px; font-weight: 800; line-height: 1.35; color: #fff; background: #E25A1C; }
.big div:nth-child(2) { background: #C2410C; } .big div:nth-child(3) { background: #1F2A28; }
.big b { display: block; font-size: 22px; font-weight: 900; color: #FFE68A; line-height: 1.15; }
body { background: #FFF4EC !important; }
.note { margin-top: 8px; font-size: 10px; font-weight: 700; color: #6B7A77; line-height: 1.6; }
"""


def yakuman_sheet(url):
    items = sorted(YAKUMAN.items(), key=lambda kv: -kv[1])
    total = sum(YAKUMAN.values())
    rows = ""
    for k, (name, c) in enumerate(items, 1):
        yomi, m, n, ex = INFO[name]
        tiles = ex_tiles(ex, url, avail=236, wmax=16) if ex else f'<span class="sit">{WHY[name]}</span>'
        g = GAMES / c
        rows += (f'<div class="r2"><div class="no">{k}</div><div class="nm"><b>{name}</b><small>{yomi}</small></div><div>{tiles}</div>'
                 f'<div class="fq"><b>{round(g):,}<small>半荘に1回</small></b><span>あがり{once(c)}・{c:,}回</span></div></div>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}{LOGO_CSS}{SHEET2_CSS}{MAN_CSS}
body {{ padding: 24px 30px 20px; }} header {{ margin-bottom: 10px; padding: 9px 12px 9px 16px; background: #E25A1C; }} header h1 small {{ color: #FFE7D6; }}
</style></head><body>
<header><h1>麻雀 役満の出やすさランキング<small>卓のだれかが その役満をあがるのは 何半荘に1回か</small></h1>{logo_html()}</header>
<div class="big"><div>役満が出るのは<b>{round(GAMES / total):,}半荘に1回</b>（どれか1つ）</div><div>いちばん出る役満<b>四暗刻</b>{round(GAMES / YAKUMAN["四暗刻"]):,}半荘に1回</div><div>いちばん出ない役満<b>四槓子</b>16.8万半荘で1回だけ</div></div>
<section class="mk"><div class="hd"><span>順位</span><span>役満</span><span>形の例</span><span>出る回数</span></div>{rows}</section>
<p class="note">「○半荘に1回」＝4人の卓で、だれか1人がその役満をあがる目安。四喜和は大四喜と小四喜の合計（例は小四喜）。<br>データ: {SRC}</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


def render(names=None):
    from playwright.sync_api import sync_playwright
    url = "file:///" + os.path.join(ROOT, "assets", "tiles").replace("\\", "/")
    sheets = [("mahjong-yaku-ranking", ranking_sheet(url)), ("mahjong-yaku-ranking-hai", ranking_sheet_hai(url)), ("mahjong-yakuman-ranking", yakuman_sheet(url))]
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, html in sheets:
            hp = os.path.join(OUT, f"_{name}.html"); io.open(hp, "w", encoding="utf-8").write(html)
            u = "file:///" + hp.replace("\\", "/")
            for suffix, scale in [("", 2481 / 794), ("-web", 2)]:
                pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
                pg.goto(u); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1000)
                over = pg.evaluate("document.body.scrollHeight") > 1123
                if over: print("はみ出し:", name, pg.evaluate("document.body.scrollHeight"))
                pg.screenshot(path=os.path.join(OUT, f"{name}{suffix}.png"), clip={"x": 0, "y": 0, "width": 794, "height": 1123})
                pg.close()
            pg = b.new_page(); pg.goto(u); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1000)
            pg.pdf(path=os.path.join(OUT, f"{name}.pdf"), format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
            pg.close(); os.remove(hp)
        b.close()
    from PIL import Image
    for name, _ in sheets:
        for suffix in ("", "-web"):
            f = os.path.join(OUT, f"{name}{suffix}.png"); Image.open(f).save(f, optimize=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    bad = [f"{k}: {check(INFO[k][3])}" for k in list(COUNT) + list(YAKUMAN) if INFO[k][3] and check(INFO[k][3])]
    print("例の確認:", "すべてOK" if not bad else bad)
    if bad: sys.exit(1)
    render()
    print("ok")
