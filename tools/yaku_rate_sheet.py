# -*- coding: utf-8 -*-
"""役の出やすさランキング・役満の出やすさの1枚の表（2026-11-13〜）。見た目は役一覧表（hai_sheets.py）とそろえる。

数字の出どころ: 天鳳 鳳凰卓 東南戦 赤あり 2023年 168,778戦（あがり 1,511,570回）の和了役統計
  （koba::blog「天鳳鳳凰卓統計(2023年)」https://blog.kobalab.net/entry/2024/11/04/215201 の表の回数）。
  出現率＝その役がついたあがりの回数 ÷ あがりの回数。翻牌（役牌）はダブ東なら2回と数えた数字。四喜和は大四喜と小四喜の合計。
出力（assets/hai/）: mahjong-yaku-ranking.png / -web.png / .pdf、mahjong-yakuman-ranking.png / -web.png / .pdf
実行: python tools/yaku_rate_sheet.py
"""
import io, os, sys
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
def pct_s(c):
    p = pct(c)
    return f"{p:.1f}%" if p >= 1 else (f"{p:.2f}%" if p >= .01 else f"{p:.3f}%")
def once(c, d=WINS):
    n = d / c
    if n < 10: return f"{n:.1f}回に1回"
    if n < 1000: return f"{round(n):,}回に1回"
    return f"{round(n, -2 if n < 100000 else -3):,.0f}回に1回"


RANK_CSS = """
.rk { border: 2px solid #1F2A28; }
.rk .hd { display: grid; grid-template-columns: 34px 104px 32px 222px 1fr; column-gap: 6px; background: #177083; color: #fff; font-size: 11px; font-weight: 900; padding: 4px 8px 4px 0; }
.rk .hd span { text-align: center; } .rk .hd span:nth-child(5) { text-align: left; padding-left: 4px; }
.r { display: grid; grid-template-columns: 34px 104px 32px 222px 1fr; column-gap: 6px; align-items: center; min-height: 31.5px; border-top: 1px solid #CFE0DC; padding-right: 8px; }
.r .no { align-self: stretch; display: grid; place-items: center; font-size: 15px; font-weight: 900; color: #177083; background: #E4F3EC; border-right: 1.5px solid #1F2A28; }
.r.top .no { background: #177083; color: #fff; font-size: 17px; }
.r .nm { padding: 2px 0; } .r .nm b { display: block; font-size: 13.5px; font-weight: 900; white-space: nowrap; letter-spacing: -.03em; line-height: 1.15; }
.r .nm small { display: block; font-size: 8.5px; font-weight: 700; color: #55625F; white-space: nowrap; }
.r i { display: grid; place-items: center; font-style: normal; font-size: 8px; font-weight: 900; line-height: 1.12; text-align: center; border-radius: 6px; height: 27px; }
.r .sit { font-size: 10.5px; font-weight: 800; color: #33403D; }
.bar { display: flex; align-items: center; gap: 6px; }
.bar .b { height: 14px; border-radius: 3px; background: var(--bc, #177083); min-width: 3px; }
.bar .v { font-size: 14px; font-weight: 900; white-space: nowrap; color: #1F2A28; } .bar .o { font-size: 9.5px; font-weight: 800; color: #6B7A77; white-space: nowrap; }
.r.top .bar .v { font-size: 16px; color: #E75620; }
  .note { margin-top: 6px; font-size: 9.5px; font-weight: 700; color: #6B7A77; line-height: 1.5; }
.pts { display: flex; gap: 8px; margin: 0 0 9px; }
.pts div { flex: 1; border: 2px solid #177083; border-radius: 8px; padding: 5px 8px; text-align: center; font-size: 11px; font-weight: 800; line-height: 1.35; }
.pts b { display: block; font-size: 20px; font-weight: 900; color: #E75620; line-height: 1.15; }
"""


def ranking_sheet(url):
    items = sorted(COUNT.items(), key=lambda kv: -kv[1])
    mx = items[0][1]
    rows = ""
    for k, (name, c) in enumerate(items, 1):
        yomi, m, n, ex = INFO[name]
        tiles = ex_tiles(ex, url, avail=200, wmax=13) if ex else f'<span class="sit">{WHY.get(name, "状況で決まる役")}</span>'
        if not ex:
            from hai_sheets import SHORT_SIT, SHORT
            tiles = f'<span class="sit">{SHORT.get(name, "")}</span>'
        w = max(1.0, c / mx * 100)
        bc = "#E75620" if k <= 5 else "#177083"
        rows += (f'<div class="r{" top" if k <= 5 else ""}"><div class="no">{k}</div><div class="nm"><b>{name}</b><small>{yomi}</small></div>'
                 f'{naki_chip(m, n)}<div>{tiles}</div><div class="bar"><div class="b" style="width:{w * .55:.1f}%;--bc:{bc}"></div>'
                 f'<span class="v">{pct_s(c)}</span><span class="o">{once(c)}</span></div></div>')
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">{FONT}<style>{CSS}{LOGO_CSS}{SHEET2_CSS}{RANK_CSS}
body {{ padding: 24px 30px 20px; }} header {{ margin-bottom: 10px; padding: 9px 12px 9px 16px; }}
</style></head><body>
<header><h1>麻雀 役の出やすさランキング<small>あがり100回のうち、その役が何回つくか（一般役26役）</small></h1>{logo_html()}</header>
<div class="pts"><div>いちばん出る役<b>リーチ</b>あがりの約4割</div><div>上位5役は<b>どれも2割超</b>5回に1回以上つく</div><div>出ない役<b>三槓子</b>約10万回に1回</div></div>
<section class="rk"><div class="hd"><span>順位</span><span>役</span><span>鳴き</span><span>形の例</span><span>出現率（あがりのうち）</span></div>{rows}</section>
<p class="note">出現率＝その役がついたあがりの回数 ÷ あがりの回数。役牌はダブ東などを2回と数えた数字。ドラは役ではないので入れていない。<br>データ: {SRC}</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer></body></html>"""


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
.big div { flex: 1; border: 2px solid #E25A1C; border-radius: 8px; padding: 6px 8px; text-align: center; font-size: 11.5px; font-weight: 800; line-height: 1.35; background: #FFF6F0; }
.big b { display: block; font-size: 22px; font-weight: 900; color: #E25A1C; line-height: 1.15; }
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
    sheets = [("mahjong-yaku-ranking", ranking_sheet(url)), ("mahjong-yakuman-ranking", yakuman_sheet(url))]
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
