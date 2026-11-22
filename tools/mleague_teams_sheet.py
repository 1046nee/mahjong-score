# -*- coding: utf-8 -*-
"""Mリーグ 2026-27 の全10チームと選手の1枚（SNSの投稿用。2026-11-22 ユーザーの依頼）。
チームごとにロゴ・紹介（オーナー企業・参入・優勝回数）・4人の選手。選手の所属団体は、文字と色でひと目で分かるように札にする。
団体の色は記事 blog-mleague-2026 の「選手の所属団体」と同じ（連盟＝緑・最高位戦＝青・協会＝オレンジ・RMU＝紫）。
チームと選手・団体は tools/video_topics2.py の TEAMS（Mリーグ公式サイト・2026年10月に確認）。参入と優勝は blog-mleague-history と同じ。
ロゴはユーザーから受け取った画像（2026-11-22 ユーザーの判断で使う）。元の画像は非公開の素材リポジトリ まじゃすこ素材/x/mleague-teams/src/ だけに置く。
ロゴが無いチームは、チーム名の頭文字の丸で代わりにする（受け取ったら src/ に置けば出る）。
出力: まじゃすこ素材/x/mleague-teams/mleague-teams.png
実行: python3.13 tools/mleague_teams_sheet.py
"""
import base64, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402
from video_topics2 import TEAMS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "mleague-teams"); SRC = os.path.join(OUT, "src")
DANTAI = {"連盟": ("#177083", "日本プロ麻雀連盟"), "最高位戦": ("#4261AA", "最高位戦日本プロ麻雀協会"), "協会": ("#E25A1C", "日本プロ麻雀協会"), "RMU": ("#6B46C1", "")}
# チーム名 → (ロゴのファイル, オーナー企業, 参入シーズン, 優勝したシーズン)
INFO = {
    "EARTH JETS": ("earthjets", "アース製薬", "2025-26", []),
    "赤坂ドリブンズ": ("drivens", "博報堂", "2018-19", ["2018-19"]),
    "EX風林火山": ("furinkazan", "テレビ朝日", "2018-19", ["2020-21", "2025-26"]),
    "KADOKAWAサクラナイツ": ("sakura", "KADOKAWA", "2019-20", ["2021-22"]),
    "KONAMI麻雀格闘倶楽部": ("konami", "コナミグループ", "2018-19", []),
    "渋谷ABEMAS": ("abemas", "サイバーエージェント", "2018-19", ["2022-23"]),
    "セガサミーフェニックス": ("phoenix", "セガサミーグループ", "2018-19", ["2024-25"]),
    "TEAM RAIDEN / 雷電": ("raiden", "電通", "2018-19", []),
    "BEAST X": ("beastx", "ジャパネット", "2023-24", []),
    "U-NEXT Pirates": ("pirates", "U-NEXT", "2018-19", ["2019-20", "2023-24"]),
}


def logo(key, name):
    for ext in ("png", "jpg", "webp"):
        p = os.path.join(SRC, f"{key}.{ext}")
        if os.path.exists(p):
            from PIL import Image
            im = Image.open(p).convert("RGBA")
            px = im.load(); w, h = im.size      # 白い地は透かして、余白を切る
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    if a and min(r, g, b) > 246: px[x, y] = (255, 255, 255, 0)
            bb = im.getbbox(); im = im.crop(bb) if bb else im
            buf = io.BytesIO(); im.save(buf, "PNG")
            return f'<img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">'
    ini = "".join(w[0] for w in name.replace("/", " ").split()[:2]).upper()
    return f'<span class="ph">{ini}</span>'


def card(team, players):
    key, owner, since, wins = INFO[team]
    win = f'<span class="win">優勝 {len(wins)}回</span>' if wins else ""
    pls = "".join(f'<span class="pl" style="--c:{DANTAI[d][0]}"><b>{n}</b><i>{d}</i></span>' for n, d in players)
    return (f'<div class="tm"><div class="lg">{logo(key, team)}</div><div class="bd"><h2>{team}</h2>'
            f'<p class="in">{owner}<em>・</em>{since[:4]}年から{win}</p><div class="pls">{pls}</div></div></div>')


def html():
    cnt = {k: sum(1 for _, ps in TEAMS for _, d in ps if d == k) for k in DANTAI}
    leg = "".join(f'<span class="dl" style="--c:{c}"><i>{k}</i>{full}<b>{cnt[k]}人</b></span>' for k, (c, full) in DANTAI.items())
    cards = "".join(card(t, ps) for t, ps in TEAMS)
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&display=block" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1123px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 14px 22px 18px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 9px 16px; }}
header .ml {{ flex: none; background: #fff; border-radius: 8px; width: 74px; height: 62px; display: flex; align-items: center; justify-content: center; margin-right: 14px; }} header .ml img {{ max-height: 54px; max-width: 64px; display: block; }}
header h1 {{ flex: 1; font-size: 27px; font-weight: 900; line-height: 1.15; }} header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; }}
{LOGO_CSS}
.legend {{ display: flex; flex-wrap: nowrap; gap: 9px; align-items: center; background: #fff; border: 2px solid #177083; border-radius: 8px; padding: 7px 10px; margin: 8px 0; font-size: 10.5px; white-space: nowrap; font-weight: 800; }}
.legend > b {{ font-size: 12.5px; font-weight: 900; color: #177083; margin-right: 2px; }}
.dl {{ display: inline-flex; align-items: center; gap: 5px; }} .dl i {{ font-style: normal; color: #fff; background: var(--c); border-radius: 4px; padding: 1px 7px; font-weight: 900; }} .dl b {{ color: var(--c); font-weight: 900; }}
.grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 10px; }}
.tm {{ display: flex; gap: 8px; min-width: 0; align-items: center; background: #fff; border: 2px solid #C5D6D2; border-radius: 10px; padding: 22px 10px; }}
.lg {{ flex: none; width: 84px; height: 96px; display: flex; align-items: center; justify-content: center; }}
.lg img {{ max-width: 84px; max-height: 96px; display: block; }}
.ph {{ width: 78px; height: 78px; border-radius: 50%; background: #E3ECEA; color: #5E6B69; font-size: 20px; font-weight: 900; display: flex; align-items: center; justify-content: center; }}
.bd {{ flex: 1; min-width: 0; }}
h2 {{ font-size: 17.5px; font-weight: 900; line-height: 1.2; white-space: nowrap; }}
.in {{ font-size: 11px; font-weight: 700; color: #5E6B69; margin: 3px 0 8px; white-space: nowrap; display: flex; align-items: center; }} .in em {{ font-style: normal; margin: 0 2px; }}
.win {{ margin-left: 6px; font-size: 10px; font-weight: 900; color: #8A6A00; background: #FFF1C2; border: 1.5px solid #D4A017; border-radius: 9px; padding: 0 6px; }}
.pls {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 6px 5px; }}
.pl {{ display: flex; align-items: center; justify-content: space-between; gap: 4px; border: 2px solid var(--c); border-radius: 6px; overflow: hidden; background: #fff; }}
.pl b {{ font-size: 13.5px; font-weight: 900; padding: 4px 0 4px 6px; white-space: nowrap; }}
.pl i {{ font-style: normal; font-size: 9.5px; font-weight: 900; color: #fff; background: var(--c); padding: 4px 4px; white-space: nowrap; letter-spacing: -.04em; align-self: stretch; display: flex; align-items: center; }}
.note {{ font-size: 10.5px; font-weight: 700; color: #4F5C5A; line-height: 1.55; margin-top: 8px; }}
footer {{ position: absolute; left: 22px; right: 22px; bottom: 7px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }} footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><span class="ml">{logo("mleague", "M")}</span><h1>Mリーグ 2026-27 全10チーム40人<small>チームと選手、選手の所属するプロ団体</small></h1>{logo_html()}</header>
<div class="legend"><b>選手の所属団体</b>{leg}</div>
<div class="grid">{cards}</div>
<p class="note">チームと選手・所属団体は Mリーグ公式サイト（2026年10月時点）による。並びは公式サイトのチーム一覧の順。団体の色は見分けやすくするためにまじゃすこで付けたもの。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>全チームの紹介は「Mリーグ2026-27 完全ガイド」</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, "_p.html"); io.open(hp, "w", encoding="utf-8").write(html())
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
        pg.goto("file:///" + hp.replace("\\", "/").lstrip("/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        gap = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - document.querySelector('.note').getBoundingClientRect().bottom")
        over = pg.evaluate("[...document.querySelectorAll('.tm h2, .in, .pl, .pl b')].filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > e.closest('.tm').getBoundingClientRect().right - 2).map(e => e.textContent)")
        over += pg.evaluate("[...document.querySelectorAll('.tm, .legend')].filter(e => e.getBoundingClientRect().right > document.body.clientWidth - 21 || e.scrollWidth > e.clientWidth + 1).map(e => '右へ:' + e.textContent.slice(0, 8))")
        print("余白", round(gap), "はみ出し", over); pg.screenshot(path=os.path.join(OUT, "mleague-teams.png")); b.close()
    os.remove(hp)
    assert gap > 0 and not over


if __name__ == "__main__":
    render()
