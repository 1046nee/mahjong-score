# -*- coding: utf-8 -*-
"""麻雀の点数早見表（1枚）を作る（2026-10-23〜）。点数は式から計算する（手で写さない）。

出力（assets/score/）:
- tensu-hayamihyo.png        … A4・約300dpi（2481×3508px）。画像検索・保存用の高画質版
- tensu-hayamihyo-web.png    … 記事に表示する版（1588px幅。スマホの拡大でも荒れない）
- tensu-hayamihyo.pdf        … 印刷用（A4・文字と線はベクター＝いくら拡大しても荒れない）
- score_table.json           … 記事のHTMLの表を作るためのデータ
記事（blog-score-table.html）の表は、このデータから作り直す（tools/score_sheet.py --html で表のHTMLを出す）。
実行: python tools/score_sheet.py   （playwright と Google Fonts の Noto Sans JP を使う）
"""
import io, json, math, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "score")
FUS = [20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 110]
HANS = [1, 2, 3, 4]


def up100(x):
    return int(math.ceil(x / 100.0) * 100)


def exists(fu, han, tsumo):
    """実際には出ない組み合わせ（表では「—」）"""
    if fu == 20:            # 20符はピンフのツモだけ（ピンフ＋ツモで2翻から）
        return tsumo and han >= 2
    if fu == 25:            # 25符は七対子だけ（2翻から。ツモは門前ツモが付くので3翻から）
        return han >= 3 or (han == 2 and not tsumo)
    return True


def score(fu, han):
    """基本点＝符×2^(翻+2)。2,000をこえたら満貫"""
    base = fu * 2 ** (han + 2)
    mangan = base > 2000
    if mangan:
        base = 2000
    return {
        "mangan": mangan,
        "ko_ron": up100(base * 4), "ko_tsumo": [up100(base), up100(base * 2)],
        "oya_ron": up100(base * 6), "oya_tsumo": up100(base * 2),
    }


LIMITS = [  # 名称, 翻, 基本点
    ("満貫", "5翻", 2000), ("跳満", "6〜7翻", 3000), ("倍満", "8〜10翻", 4000),
    ("三倍満", "11〜12翻", 6000), ("役満", "13翻〜", 8000),
]


def table_data():
    rows = []
    for fu in FUS:
        r = {"fu": fu, "cells": []}
        for han in HANS:
            s = score(fu, han)
            s["ron_ok"] = exists(fu, han, False)
            s["tsumo_ok"] = exists(fu, han, True)
            r["cells"].append(s)
        rows.append(r)
    lim = [{"name": n, "han": h, "ko_ron": b * 4, "ko_tsumo": [b, b * 2], "oya_ron": b * 6, "oya_tsumo": b * 2} for n, h, b in LIMITS]
    return {"rows": rows, "limits": lim}


def n(x):
    return f"{x:,}"


# ---------------- 1枚の早見表（A4縦・794×1123 CSS px） ----------------
def sheet_html(d):
    def block(side):
        ko = side == "ko"
        head = "".join(f"<th>{h}翻</th>" for h in HANS)
        body = ""
        for r in d["rows"]:
            tds = ""
            for c in r["cells"]:
                if not (c["ron_ok"] or c["tsumo_ok"]):
                    tds += '<td class="na">—</td>'; continue
                if c["mangan"]:
                    tds += '<td class="mg"><b>満貫</b></td>'; continue
                ron = f'<b>{n(c["ko_ron"] if ko else c["oya_ron"])}</b>' if c["ron_ok"] else '<b class="x">—</b>'
                ts = (f'{n(c["ko_tsumo"][0])}-{n(c["ko_tsumo"][1])}' if ko else f'{n(c["oya_tsumo"])}<i>∀</i>') if c["tsumo_ok"] else "—"
                tds += f'<td>{ron}<span>{ts}</span></td>'
            body += f'<tr><th>{r["fu"]}符</th>{tds}</tr>'
        title = "子" if ko else "親"
        sub = "ロン ／ ツモ（子の払い-親の払い）" if ko else "ロン ／ ツモ（∀＝全員が同じ額＝オール）"
        return (f'<section class="blk {side}"><h2><em>{title}</em><small>{sub}</small></h2>'
                f'<table><thead><tr><th>符＼翻</th>{head}</tr></thead><tbody>{body}</tbody></table></section>')

    lim = "".join(f'<tr><th>{l["name"]}</th><td class="h">{l["han"]}</td><td><b>{n(l["ko_ron"])}</b><span>{n(l["ko_tsumo"][0])}-{n(l["ko_tsumo"][1])}</span></td>'
                  f'<td><b>{n(l["oya_ron"])}</b><span>{n(l["oya_tsumo"])}<i>∀</i></span></td></tr>' for l in d["limits"])
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1123px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #fff; padding: 30px 34px 22px; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: flex-end; justify-content: space-between; border-bottom: 3px solid #1F2A28; padding-bottom: 8px; margin-bottom: 12px; }}
header h1 {{ font-size: 30px; font-weight: 900; letter-spacing: .02em; line-height: 1.1; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 500; color: #55625F; letter-spacing: 0; margin-top: 5px; }}
.legend {{ text-align: right; font-size: 10.5px; color: #55625F; line-height: 1.6; }}
.legend b {{ font-size: 13px; color: #1F2A28; }}
.legend span {{ color: #4F6B88; font-weight: 700; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.blk h2 {{ display: flex; align-items: baseline; gap: 8px; font-size: 11px; font-weight: 500; color: #55625F; margin-bottom: 5px; }}
.blk h2 em {{ font-style: normal; font-size: 19px; font-weight: 900; color: #fff; border-radius: 4px; padding: 0 10px; line-height: 28px; }}
.ko h2 em {{ background: #177083; }} .oya h2 em {{ background: #4261AA; }}
table {{ width: 100%; border-collapse: collapse; table-layout: fixed; }}
thead th {{ font-size: 12px; font-weight: 900; color: #fff; padding: 4px 0; }}
.ko thead th {{ background: #177083; }} .oya thead th {{ background: #4261AA; }}
thead th:first-child {{ width: 52px; font-size: 10px; }}
tbody th {{ font-size: 13px; font-weight: 900; text-align: center; background: #F3F6F5; border-bottom: 1px solid #DFE6E3; }}
.ko tbody th {{ color: #136070; }} .oya tbody th {{ color: #2F4A86; }}
td {{ text-align: center; border-bottom: 1px solid #DFE6E3; border-left: 1px solid #EDF1EF; height: 50px; padding: 2px 0; line-height: 1.15; }}
td b {{ display: block; font-size: 16px; font-weight: 900; letter-spacing: -.01em; font-variant-numeric: tabular-nums; }}
td span {{ display: block; font-size: 10.5px; font-weight: 700; color: #4F6B88; margin-top: 2px; font-variant-numeric: tabular-nums; }}
td i {{ font-style: normal; font-size: 9px; margin-left: 1px; }}
td b.x {{ color: #C9D2CF; font-weight: 400; font-size: 13px; }}
td.na {{ color: #B4C0BD; font-size: 13px; background: #FAFBFB; }}
td.mg {{ background: #FFF3EC; }} td.mg b {{ color: #C2471A; font-size: 14px; }}
.blk tbody tr:nth-child(3) td, .blk tbody tr:nth-child(3) th {{ background-image: linear-gradient(#FFFBEA, #FFFBEA); }}
.bottom {{ display: grid; grid-template-columns: 1.15fr 1fr; gap: 14px; margin-top: 14px; }}
.box h3 {{ font-size: 13px; font-weight: 900; border-left: 4px solid #1F2A28; padding-left: 7px; margin-bottom: 6px; line-height: 1.3; }}
.lim thead th {{ background: #1F2A28; font-size: 11px; }}
.lim tbody th {{ font-size: 12.5px; color: #C2471A; background: #FFF3EC; }}
.lim td {{ height: 43px; }} .lim td b {{ font-size: 14.5px; }} .lim td.h {{ font-size: 11px; font-weight: 700; color: #55625F; }}
.fu {{ font-size: 10.5px; line-height: 1.55; }}
.fu table td, .fu table th {{ height: auto; font-size: 10.5px; padding: 3px 4px; border: 1px solid #DFE6E3; background: none; }}
.fu table th {{ background: #F3F6F5; color: #1F2A28; font-weight: 700; }}
.fu ul {{ list-style: none; margin-top: 5px; }}
.fu li {{ padding-left: 10px; text-indent: -10px; }}
.fu li::before {{ content: "・"; }}
.fu b {{ color: #C2471A; }}
.notes {{ margin-top: 10px; font-size: 10px; color: #55625F; line-height: 1.6; border-top: 1px solid #DFE6E3; padding-top: 6px; }}
footer {{ position: absolute; left: 34px; right: 34px; bottom: 16px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><h1>麻雀 点数早見表<small>子・親 × ロン・ツモ ／ 20符〜110符・満貫以上・符の数え方を1枚で</small></h1>
<div class="legend">上の大きい数字 <b>ロン</b><br>下の小さい数字 <span>ツモ</span>（子：子の払い-親の払い ／ 親：∀＝オール）<br>— は実際には出ない組み合わせ</div></header>
<div class="grid">{block("ko")}{block("oya")}</div>
<div class="bottom">
<div class="box"><h3>満貫以上（符に関係なく決まる）</h3>
<table class="lim"><thead><tr><th>名前</th><th>翻</th><th>子</th><th>親</th></tr></thead><tbody>{lim}</tbody></table></div>
<div class="box fu"><h3>符の数え方（足して、10の位で切り上げ）</h3>
<table><tr><th>あがりの基本（副底）</th><td>20符</td></tr><tr><th>門前でロン</th><td>+10符</td></tr><tr><th>ツモ（ピンフのツモは除く）</th><td>+2符</td></tr>
<tr><th>待ち（カンチャン・ペンチャン・単騎）</th><td>+2符</td></tr><tr><th>雀頭が役牌</th><td>+2符</td></tr></table>
<table style="margin-top:5px"><tr><th>刻子・槓子</th><th>明刻</th><th>暗刻</th><th>明槓</th><th>暗槓</th></tr>
<tr><th>2〜8の数牌</th><td>2</td><td>4</td><td>8</td><td>16</td></tr><tr><th>1・9・字牌</th><td>4</td><td>8</td><td>16</td><td>32</td></tr></table>
<ul><li><b>ピンフのツモは20符</b>、<b>七対子は25符</b>（切り上げない）</li><li>鳴いて符が20符のままのロンは30符にする</li></ul></div>
</div>
<p class="notes">本場（積み棒）：1本につきロンは+300点、ツモは1人あたり+100点。　黄色の行（30符）は実戦でいちばんよく出る符。<br>
「切り上げ満貫」ありのルールでは、子の7,700（4翻30符・3翻60符）を8,000、親の11,600を12,000にする。点数は 符×2の(翻+2)乗×4（親は×6）を100点未満切り上げで計算。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>対局後のスコア（ウマ・オカ）の計算は、まじゃすこで自動に</span></footer>
</body></html>"""


def render(d):
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    html_path = os.path.join(OUT, "_sheet.html")
    io.open(html_path, "w", encoding="utf-8").write(sheet_html(d))
    url = "file:///" + html_path.replace("\\", "/")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, scale in [("tensu-hayamihyo.png", 2481 / 794), ("tensu-hayamihyo-web.png", 2)]:
            pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
            pg.goto(url); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
            pg.screenshot(path=os.path.join(OUT, name), full_page=False)
            pg.close()
        pg = b.new_page()
        pg.goto(url); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
        pg.pdf(path=os.path.join(OUT, "tensu-hayamihyo.pdf"), format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        b.close()
    os.remove(html_path)
    try:  # PNG を最適化（見た目は変えない・可逆）
        from PIL import Image
        for name in ["tensu-hayamihyo.png", "tensu-hayamihyo-web.png"]:
            f = os.path.join(OUT, name)
            Image.open(f).save(f, optimize=True)
    except ImportError:
        pass


# ---------------- 記事のHTMLの表 ----------------
def article_tables(d):
    def tbl(side):
        ko = side == "ko"
        out = '  <table class="score-tbl">\n    <thead><tr><th>符＼翻</th>' + "".join(f"<th>{h}翻</th>" for h in HANS) + "</tr></thead>\n    <tbody>\n"
        for r in d["rows"]:
            out += f'      <tr><th>{r["fu"]}符</th>'
            for c in r["cells"]:
                if not (c["ron_ok"] or c["tsumo_ok"]):
                    out += '<td class="na">—</td>'; continue
                if c["mangan"]:
                    out += '<td class="mg">満貫</td>'; continue
                ron = f'<b>{n(c["ko_ron"] if ko else c["oya_ron"])}</b>' if c["ron_ok"] else '<b class="x">—</b>'
                ts = (f'{n(c["ko_tsumo"][0])}-{n(c["ko_tsumo"][1])}' if ko else f'{n(c["oya_tsumo"])}オール') if c["tsumo_ok"] else "—"
                out += f'<td>{ron}<small>{ts}</small></td>'
            out += "</tr>\n"
        return out + "    </tbody>\n  </table>\n"
    lim = '  <table class="score-tbl lim">\n    <thead><tr><th>名前</th><th>翻</th><th>子（ロン／ツモ）</th><th>親（ロン／ツモ）</th></tr></thead>\n    <tbody>\n'
    for l in d["limits"]:
        lim += (f'      <tr><th>{l["name"]}</th><td>{l["han"]}</td><td><b>{n(l["ko_ron"])}</b><small>{n(l["ko_tsumo"][0])}-{n(l["ko_tsumo"][1])}</small></td>'
                f'<td><b>{n(l["oya_ron"])}</b><small>{n(l["oya_tsumo"])}オール</small></td></tr>\n')
    lim += "    </tbody>\n  </table>\n"
    return {"ko": tbl("ko"), "oya": tbl("oya"), "limits": lim}


if __name__ == "__main__":
    d = table_data()
    os.makedirs(OUT, exist_ok=True)
    io.open(os.path.join(OUT, "score_table.json"), "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
    if "--html" in sys.argv:
        t = article_tables(d)
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        print(t["ko"], t["oya"], t["limits"], sep="\n")
    else:
        render(d)
        for f in sorted(os.listdir(OUT)):
            print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, "KB")
