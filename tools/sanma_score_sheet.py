# -*- coding: utf-8 -*-
"""三麻（3人麻雀）の点数早見表を作る（2026-11-11〜）。ツモ損あり・ツモ損なし（北家の分を折半）の2枚。

点数は score_sheet.py と同じ式から計算する（手で写さない）。
- ロンは四麻と同じ
- ツモ損あり : 四麻のツモの払いのまま、北家の分は誰も払わない
- ツモ損なし : 北家が払うはずだった分を、残りの2人が半分ずつ足して払う（半分は100点単位に切り上げ）
  （blog-sanma-rules.html の比べる表と同じ決め方）

出力（assets/score/）:
- sanma-tensu-tsumoson-ari.png / -web.png   … ツモ損あり（A4・高画質／記事用）
- sanma-tensu-tsumoson-nashi.png / -web.png … ツモ損なし
実行: python tools/sanma_score_sheet.py        （画像）
      python tools/sanma_score_sheet.py --html （記事の表のHTML）
"""
import io, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from score_sheet import FUS, HANS, LIMITS, OUT, exists, score, up100, n  # noqa: E402
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402


def pay(base, ari):
    """基本点から三麻のツモの払い。戻り値: (子のツモ=[子の払い, 親の払い], 親のツモ=1人の払い)"""
    ko, oya = up100(base), up100(base * 2)       # 四麻の子のツモ（子・親）
    oya_all = up100(base * 2)                     # 四麻の親のツモ（1人）
    if ari:
        return [ko, oya], oya_all
    h = up100(ko / 2)                             # 北家（子）の分の半分
    return [ko + h, oya + h], oya_all + up100(oya_all / 2)


VERSIONS = {
    "ari": {"file": "sanma-tensu-tsumoson-ari", "name": "ツモ損あり",
            "sub": "北家の分は誰も払わない（ツモはロンより少ない）"},
    "nashi": {"file": "sanma-tensu-tsumoson-nashi", "name": "ツモ損なし",
              "sub": "北家の分を2人で半分ずつ（100点未満は切り上げ）"},
}


def table_data(ari):
    rows = []
    for fu in FUS:
        cells = []
        for han in HANS:
            s = score(fu, han)
            base = 2000 if s["mangan"] else fu * 2 ** (han + 2)
            k, o = pay(base, ari)
            cells.append({"mangan": s["mangan"], "ko_ron": s["ko_ron"], "oya_ron": s["oya_ron"],
                          "ko_tsumo": k, "oya_tsumo": o,
                          "ron_ok": exists(fu, han, False), "tsumo_ok": exists(fu, han, True)})
        rows.append({"fu": fu, "cells": cells})
    lim = []
    for name, han, b in LIMITS:
        k, o = pay(b, ari)
        lim.append({"name": name, "han": han, "ko_ron": b * 4, "oya_ron": b * 6, "ko_tsumo": k, "oya_tsumo": o})
    return {"rows": rows, "limits": lim}


# 検算（四麻・既存の記事の表と同じになるか）
def _check():
    a, na = table_data(True), table_data(False)
    c30 = lambda d, h: d["rows"][2]["cells"][h - 1]
    assert c30(a, 1)["ko_tsumo"] == [300, 500] and c30(a, 1)["oya_tsumo"] == 500
    assert c30(na, 4)["ko_tsumo"] == [3000, 4900]          # blog-sanma-rules の表: 親4,900・子3,000
    m = {l["name"]: l for l in na["limits"]}
    assert m["満貫"]["ko_tsumo"] == [3000, 5000] and m["満貫"]["oya_tsumo"] == 6000
    assert m["跳満"]["ko_tsumo"] == [4500, 7500] and m["跳満"]["oya_tsumo"] == 9000
    ma = {l["name"]: l for l in a["limits"]}
    assert ma["満貫"]["ko_tsumo"] == [2000, 4000] and ma["満貫"]["oya_tsumo"] == 4000
    # ツモ損なしの合計は、ロン以上（切り上げのぶんだけ多くなることがある）
    for r in na["rows"]:
        for c in r["cells"]:
            assert sum(c["ko_tsumo"]) >= c["ko_ron"] and c["oya_tsumo"] * 2 >= c["oya_ron"]


def sheet_html(v):
    from score_sheet import sheet_html as yonma_html, table_data as yonma_data
    ver = VERSIONS[v]
    d = table_data(v == "ari")
    css = yonma_html(yonma_data()).split("<style>")[1].split("</style>")[0]

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
                ts = (f'{n(c["ko_tsumo"][0])}-{n(c["ko_tsumo"][1])}' if ko else f'{n(c["oya_tsumo"])}<i>ALL</i>') if c["tsumo_ok"] else "—"
                tds += f'<td>{ron}<span>{ts}</span></td>'
            body += f'<tr><th>{r["fu"]}符</th>{tds}</tr>'
        title = "子" if ko else "親"
        sub = "ツモは 子の払い-親の払い" if ko else "ツモは ALL（子2人が同じ額）"
        return (f'<section class="blk {side}"><h2><em>{title}</em><small>{sub}</small></h2>'
                f'<table><thead><tr><th>符＼翻</th>{head}</tr></thead><tbody>{body}</tbody></table></section>')

    lim = "".join(f'<tr><th>{l["name"]}</th><td class="h">{l["han"]}</td><td><b>{n(l["ko_ron"])}</b><span>{n(l["ko_tsumo"][0])}-{n(l["ko_tsumo"][1])}</span></td>'
                  f'<td><b>{n(l["oya_ron"])}</b><span>{n(l["oya_tsumo"])}<i>ALL</i></span></td></tr>' for l in d["limits"])
    if v == "ari":
        rule = ('<tr><th>子のツモ</th><td>親と子1人が、四麻と同じ額を払う</td></tr>'
                '<tr><th>親のツモ</th><td>子2人が、四麻と同じ額（ALL）を払う</td></tr>'
                '<tr><th>北家の分</th><td><b>誰も払わない</b>（受け取りはロンより少ない）</td></tr>')
    else:
        rule = ('<tr><th>子のツモ</th><td>四麻の払い ＋ 北家の分の半分</td></tr>'
                '<tr><th>親のツモ</th><td>四麻のALL ＋ その半分</td></tr>'
                '<tr><th>北家の分</th><td><b>2人で半分ずつ</b>（100点未満は切り上げ）</td></tr>')
    sanma_css = """
header { background: #4261AA; }
.ko h2 em, .ko thead th { background: #4261AA; } .ko tbody th { color: #22397A; }
.oya h2 em, .oya thead th { background: #22397A; } .oya tbody th { color: #22397A; }
tbody th { background: #EAF0FB; }
.ver { display: inline-block; background: #E75620; color: #fff; border-radius: 6px; padding: 0 10px; margin-left: 10px; font-size: 26px; vertical-align: 3px; }
.box h3 { background: #22397A; }
.lim thead th { background: #22397A; } .lim tbody th { background: #FFE2D2; }
.rule table { border: 2px solid #22397A; } .rule th, .rule td { height: 49px; font-size: 12px; font-weight: 800; padding: 4px 8px; border: 1px solid #B9C6E4; text-align: left; line-height: 1.4; }
.rule th { width: 76px; background: #EAF0FB; color: #22397A; text-align: center; }
.rule td b { display: inline; font-size: 12px; color: #E75620; }
.rule p { font-size: 11px; font-weight: 700; margin-top: 8px; line-height: 1.6; color: #1F2A28; }
.rule p b { color: #E75620; }
"""
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>{css}{sanma_css}{LOGO_CSS} .legend {{ white-space: nowrap; }} header h1 {{ font-size: 27px; white-space: nowrap; }} .ver {{ font-size: 21px; margin-left: 8px; }}</style></head><body>
<header><h1>三麻 点数早見表<span class="ver">{ver["name"]}</span><small>3人麻雀の子・親のロン・ツモ ／ 満貫以上</small></h1>
<div class="legend">上 <b>ロン</b>　下 <span>ツモ</span><br>— は出ない組み合わせ</div>{logo_html()}</header>
<div class="grid">{block("ko")}{block("oya")}</div>
<div class="bottom">
<div class="box"><h3>満貫以上（符に関係なく決まる）</h3>
<table class="lim"><thead><tr><th>名前</th><th>翻</th><th>子</th><th>親</th></tr></thead><tbody>{lim}</tbody></table></div>
<div class="box rule"><h3>{ver["name"]}のツモの払い方</h3><table>{rule}</table>
<p>ロンは四麻と同じ点数。<br>ツモの払い方は卓によって違うので、<b>打つ前に決めておく</b>。</p></div>
</div>
<p class="notes">黄色の行（30符）がいちばんよく出る。　本場1本：ロン+300点・ツモは1人+100点（ルールで違うことがある）。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>三麻のスコア（ウマ・オカ）の計算は、まじゃすこで自動に</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for v, ver in VERSIONS.items():
            hp = os.path.join(OUT, "_sanma.html")
            io.open(hp, "w", encoding="utf-8").write(sheet_html(v))
            for suf, scale in [("", 2481 / 794), ("-web", 2)]:
                pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
                pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
                pg.screenshot(path=os.path.join(OUT, ver["file"] + suf + ".png"), full_page=False)
                pg.close()
            os.remove(hp)
        b.close()
    try:
        from PIL import Image
        for ver in VERSIONS.values():
            for suf in ("", "-web"):
                f = os.path.join(OUT, ver["file"] + suf + ".png")
                Image.open(f).save(f, optimize=True)
    except ImportError:
        pass


def article_tables(v):
    """記事の表（子・親・満貫以上）。ツモの下に受け取る合計を小さく"""
    d = table_data(v == "ari")
    out = {}
    for side in ("ko", "oya"):
        ko = side == "ko"
        t = '  <table class="score-tbl">\n    <thead><tr><th>符＼翻</th>' + "".join(f"<th>{h}翻</th>" for h in HANS) + "</tr></thead>\n    <tbody>\n"
        for r in d["rows"]:
            t += f'      <tr><th>{r["fu"]}符</th>'
            for c in r["cells"]:
                if not (c["ron_ok"] or c["tsumo_ok"]):
                    t += '<td class="na">—</td>'; continue
                if c["mangan"]:
                    t += '<td class="mg">満貫</td>'; continue
                ron = f'<b>{n(c["ko_ron"] if ko else c["oya_ron"])}</b>' if c["ron_ok"] else '<b class="x">—</b>'
                if c["tsumo_ok"]:
                    ts = f'{n(c["ko_tsumo"][0])}-{n(c["ko_tsumo"][1])}' if ko else f'{n(c["oya_tsumo"])}オール'
                    tot = sum(c["ko_tsumo"]) if ko else c["oya_tsumo"] * 2
                    ts += f'<em>合計{n(tot)}</em>'
                else:
                    ts = "—"
                t += f'<td>{ron}<small>{ts}</small></td>'
            t += "</tr>\n"
        out[side] = t + "    </tbody>\n  </table>\n"
    t = '  <table class="score-tbl lim">\n    <thead><tr><th>名前</th><th>翻</th><th>子（ロン／ツモ）</th><th>親（ロン／ツモ）</th></tr></thead>\n    <tbody>\n'
    for l in d["limits"]:
        t += (f'      <tr><th>{l["name"]}</th><td>{l["han"]}</td><td><b>{n(l["ko_ron"])}</b><small>{n(l["ko_tsumo"][0])}-{n(l["ko_tsumo"][1])}<em>合計{n(sum(l["ko_tsumo"]))}</em></small></td>'
              f'<td><b>{n(l["oya_ron"])}</b><small>{n(l["oya_tsumo"])}オール<em>合計{n(l["oya_tsumo"] * 2)}</em></small></td></tr>\n')
    out["limits"] = t + "    </tbody>\n  </table>\n"
    return out


if __name__ == "__main__":
    _check()
    if "--html" in sys.argv:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        for v in VERSIONS:
            t = article_tables(v)
            print(f"<!-- {v} -->", t["ko"], t["oya"], t["limits"], sep="\n")
    else:
        render()
        for ver in VERSIONS.values():
            print(ver["file"], "ok")
