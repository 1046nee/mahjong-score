# -*- coding: utf-8 -*-
"""麻雀「打つ前の確認リスト」（1枚・A4）を作る（2026-11-11〜・ユーザーの依頼）。
点数早見表（tools/score_sheet.py）と同じ見た目。基本の10項目（blog-house-rules）＋上級の20項目（blog-rule-joukyu）を、
□・項目・決め方（選択肢）の形で全部並べる。中身を変えたら記事の本文とそろえる。

出力（assets/rules/）:
- rule-checklist.png      … A4・約300dpi（2481×3508px）
- rule-checklist-web.png  … 記事に出す版（1588px幅）
- rule-checklist.pdf      … 印刷用（A4・文字はベクター）
実行: python tools/rule_sheet.py
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "rules")

# (見出し, 色, 添え書き, [(項目, 決め方), ...])
LEFT = [
    ("基本｜必ず決める", "#177083", "決めていないと、その日の集計が止まる", [
        ("試合形式", "四麻／三麻 ・ 東風戦／半荘戦 ・ 今日は何試合やるか"),
        ("持ち点・返し点", "25,000／30,000（オカあり）・ 30,000／30,000 ・ 三麻 35,000／35,000"),
        ("ウマ", "10-30 ／ 10-20 ／ 5-15 ／ 5-10 ／ なし（三麻は3人用のウマ）"),
        ("同点のとき", "山分け ／ 起家に近い人が上 ／ 再戦・じゃんけん"),
        ("終わったときの供託", "トップが総取り ／ 誰も取らない ／ 出した人に返す"),
    ]),
    ("基本｜必要なら決める", "#3F8F8A", "", [
        ("チョンボ", "罰符なし（印だけ）／ 満貫払い相当 ・ 場から消すか配るか"),
        ("チップ・焼き鳥", "持ちチップの枚数 ・ 動く条件（一発・裏・赤・役満）・ 焼き鳥の罰"),
        ("途中参加・途中抜け", "抜け番の回し方 ・ 成績は合計か平均か ・ 帰る人の扱い"),
        ("赤ドラ・喰いタンなど", "赤の枚数 ・ 喰いタン ・ 後づけ ・ ダブロンか頭ハネか"),
        ("記録", "誰が付けるか ・ 全員が見られるか ・ あとで見返せるか"),
    ]),
    ("ローカル役｜あるか・何点か", "#6E8CA8", "", [
        ("流し満貫", "なし ／ 満貫"),
        ("十三不塔", "なし ／ 満貫 ／ 役満"),
        ("四風連打", "流局にする ／ そのまま続ける"),
        ("人和", "なし ／ 満貫 ／ 役満"),
    ]),
]
RIGHT = [
    ("トビ｜トビ終了ありの卓", "#E75620", "0点を下回ったらトビとして", [
        ("0点・マイナスになるリーチ", "0点：できる ／ できない ・ マイナス：できる（局が終わってマイナスならトビ）／ できない"),
        ("トビ賞", "なし ／ 飛ばした人 ／ その時の1着 ・ 点数かチップか"),
        ("ツモ番がないリーチ", "できる（ロンだけ待つ）／ できない（四麻は山の残り4枚未満）"),
    ]),
    ("上級｜玄人の卓", "#0B4D5A", "", [
        ("ダブル役満", "四暗刻単騎・国士13面・純正九蓮：ダブル ／ ふつう ・ 役満の重なり"),
        ("国士の暗槓ロン", "できる ／ できない（搶槓は加槓だけ）"),
        ("カンドラ", "すぐめくる ／ 捨ててから（暗槓はすぐ・明槓は捨ててから が多い）"),
        ("パオ（責任払い）", "なし ／ 大三元・大四喜 ／ 四槓子まで"),
        ("リーチ後のカン", "待ちが変わらない暗槓だけ ・ 違反は取り消しかチョンボか"),
        ("あがりやめ・テンパイやめ", "あり ／ なし（親は続ける）"),
        ("数え役満", "あり（13翻以上）／ なし（三倍満まで）"),
    ]),
    ("三麻｜3人で打つとき", "#4261AA", "", [
        ("北の扱い", "北抜き（ドラ1枚）／ 手の中で使う"),
        ("花牌", "入れない ／ 入れて抜きドラ"),
        ("赤ドラの枚数", "筒子・索子に1枚ずつ ／ 2枚ずつ"),
        ("嶺上牌の数", "抜く北・花の数に足りるように"),
        ("ツモり切り", "王牌14枚を残す ／ ドラ表示牌の横まで"),
        ("ツモの払い", "ツモ損 ／ 北家の分を2人で折半"),
    ]),
]
assert sum(len(x[3]) for x in LEFT + RIGHT) == 30  # 基本10・トビ3・玄人7・ローカル役4・三麻6（記事とそろえる）


def col_html(sections):
    out = ""
    for title, color, note, rows in sections:
        items = "".join(f'<li><i></i><b>{n}</b><span>{d}</span></li>' for n, d in rows)
        out += (f'<section style="--c:{color}"><h2>{title}{f"<small>{note}</small>" if note else ""}</h2>'
                f'<ul>{items}</ul></section>')
    return out


def sheet_html():
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1123px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #fff; padding: 30px 34px 22px; position: relative; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 10px 16px; margin-bottom: 12px; }}
header h1 {{ font-size: 31px; font-weight: 900; letter-spacing: .04em; line-height: 1.1; }}
header h1 small {{ display: block; font-size: 13px; font-weight: 700; color: #DDF0EC; letter-spacing: 0; margin-top: 4px; }}
.legend {{ text-align: right; font-size: 12px; font-weight: 700; line-height: 1.6; background: rgba(255,255,255,.14); border-radius: 6px; padding: 5px 10px; }}
.legend b {{ display: inline-block; width: 13px; height: 13px; border: 2px solid #fff; border-radius: 3px; vertical-align: -2px; margin-right: 4px; }}
.legend span {{ color: #FFE68A; font-weight: 900; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
section {{ border: 2px solid var(--c); border-radius: 6px; overflow: hidden; margin-bottom: 10px; }}
section h2 {{ background: var(--c); color: #fff; font-size: 14px; font-weight: 900; padding: 4px 10px; line-height: 1.35; display: flex; align-items: baseline; gap: 8px; }}
section h2 small {{ font-size: 10.5px; font-weight: 700; opacity: .9; }}
ul {{ list-style: none; }}
li {{ display: grid; grid-template-columns: 18px 1fr; column-gap: 7px; padding: 5px 9px 5px 8px; border-top: 1px solid #D5E2DF; }}
li:first-child {{ border-top: 0; }}
li i {{ grid-row: 1 / span 2; width: 15px; height: 15px; border: 2px solid var(--c); border-radius: 3px; margin-top: 2px; background: #fff; }}
li b {{ font-size: 13px; font-weight: 900; line-height: 1.35; }}
li span {{ font-size: 10.5px; font-weight: 700; color: #3B4A47; line-height: 1.45; }}
.foot-note {{ font-size: 11px; font-weight: 700; color: #1F2A28; line-height: 1.6; border-top: 2px solid #177083; padding-top: 6px; margin-top: 2px; }}
.foot-note b {{ color: #E75620; }}
footer {{ position: absolute; left: 34px; right: 34px; bottom: 16px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><h1>麻雀 打つ前の確認リスト<small>基本の10項目 ＋ 上級の20項目 ／ 決め方の選択肢つき</small></h1>
<div class="legend"><b></b>決めたら チェック<br><span>正解は1つではない</span></div></header>
<div class="grid"><div>{col_html(LEFT)}</div><div>{col_html(RIGHT)}</div></div>
<p class="foot-note">いつものメンバーなら一度決めて、LINEなどに残しておけば次からは聞かずに済む。初めての相手と打つ日は、上から読み上げて確かめる。<br>
<b>どれを選んでも、集計で入れるのは最後の持ち点だけ</b>。ウマ・オカを付けたスコアと通算の成績は、まじゃすこで自動に。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>くわしくは「打つ前に決める10項目」「上級ルール20項目」の記事で</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, "_sheet.html")
    io.open(hp, "w", encoding="utf-8").write(sheet_html())
    url = "file:///" + hp.replace("\\", "/")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for name, scale in [("rule-checklist.png", 2481 / 794), ("rule-checklist-web.png", 2)]:
            pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
            pg.goto(url); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
            h = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - Math.max(...[...document.querySelectorAll('.grid > div')].map(d => d.getBoundingClientRect().bottom)) - document.querySelector('.foot-note').getBoundingClientRect().height")
            assert h > 0, f"A4に入りきらない（{h:.0f}px）"
            pg.screenshot(path=os.path.join(OUT, name), full_page=False)
            pg.close()
        pg = b.new_page()
        pg.goto(url); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(800)
        pg.pdf(path=os.path.join(OUT, "rule-checklist.pdf"), format="A4", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        b.close()
    os.remove(hp)
    try:
        from PIL import Image
        for name in ("rule-checklist.png", "rule-checklist-web.png"):
            f = os.path.join(OUT, name)
            Image.open(f).save(f, optimize=True)
    except ImportError:
        pass


if __name__ == "__main__":
    render()
    for f in sorted(os.listdir(OUT)):
        print(f, os.path.getsize(os.path.join(OUT, f)) // 1024, "KB")
