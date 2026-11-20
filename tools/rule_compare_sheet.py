# -*- coding: utf-8 -*-
"""Mリーグと雀魂（段位戦）のルールの違い（A4縦2枚。SNSの投稿用。上級ルールの記事 blog-rule-joukyu をひねった版。2026-11-20 ユーザーの依頼）。
列: 項目／Mリーグ／雀魂（段位戦）／仲間内の決め方（例）。2つが違う行は、項目にオレンジの「違う」。
出典: Mリーグ＝公式サイト m-league.jp/about の公式戦ルール（2026-11-20 に確認）。雀魂＝Wikipedia「雀魂」のルール（四人麻雀・段位戦）と、
blog-yakuman-rules の表（国士の暗槓ロン・ダブル役満）。確かめられなかった所は「—」。ゲームのルールは更新されることがある。
出力: まじゃすこ素材/x/rule-hikaku/rule-hikaku-1.png・-2.png（1588×2246）
実行: python tools/rule_compare_sheet.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "rule-hikaku")

# (項目, Mリーグ, 雀魂, 仲間内の例, 違うか)。セクションは ("##", 見出し)
P1 = [
    ("##", "試合と点数"),
    ("試合形式", "半荘（東南戦）", "東風か半荘を選ぶ。トップが30,000点に届かなければ延長", "半荘／東風・今日は何試合", 1),
    ("持ち点／返し点", "25,000／30,000", "25,000／25,000（オカなし）", "25,000／30,000・30,000／30,000", 1),
    ("ウマ（順位点）", "+50／+10／−10／−30（オカ込み）", "5-15（+15／+5／−5／−15）", "10-30・10-20・5-10・なし", 1),
    ("同点のとき", "順位点を分け合う", "起家に近い人が上", "分け合う／上家取り", 1),
    ("終わったときの供託", "アガった人。流局で終わればトップ", "流局で終わればトップ", "トップ総取り／誰も取らない", 0),
    ("チョンボ", "−20ポイント・局はやり直し", "起きない（ゲームが止める）", "罰符なし／スコアから引く／満貫払い／親子なく2,000オール／供託に1,000点", 1),
    ("チップ・祝儀・焼き鳥", "なし", "段位戦はなし", "一発・裏・赤・役満で何枚／焼き鳥の罰", 0),
    ("##", "鳴き・アガリ・連荘"),
    ("赤ドラ", "3枚（五萬・五筒・五索）", "3枚（五萬・五筒・五索）", "なし／3枚／4枚", 0),
    ("喰いタン・後付け", "どちらもあり", "どちらもあり（アリアリ）", "アリアリ／喰いタンなし", 0),
    ("同じ牌で2人がロン", "頭ハネ（1人だけ）", "ダブロン（3人ならトリロン）", "ダブロン／頭ハネ", 1),
    ("連荘", "親のアガリ・テンパイ", "親のアガリ・テンパイ", "テンパイ連荘／アガリ連荘だけ", 0),
    ("アガリやめ・テンパイやめ", "規定なし", "あり（ラス親がトップで30,000点以上）", "あり／なし", 1),
    ("##", "リーチとトビ"),
    ("ツモ番がないリーチ", "できる（海底をツモった人はできない）", "—", "できる／できない", 0),
    ("トビ", "なし（マイナスでも最後まで）", "0点未満で終わり（0点は続行）", "あり（0点で続行か）／なし", 1),
    ("0点・マイナスになるリーチ", "規定なし", "1,000点未満はリーチできない", "できる／できない", 1),
    ("トビ賞", "なし", "—", "なし／飛ばした人に", 0),
]
P2 = [
    ("##", "ローカル役・途中流局"),
    ("流し満貫", "なし（役の一覧にない）", "あり", "なし／満貫", 1),
    ("途中流局（九種九牌・四風連打・四家立直・四開槓）", "なし", "あり", "種類ごとに決める", 1),
    ("3人が同時にロン（三家和）", "頭ハネ（1人だけ）", "トリロン（3人ともアガリ）", "流局／頭ハネ／トリロン", 1),
    ("人和", "なし", "段位戦はなし（友人戦で設定）", "なし／満貫／役満", 0),
    ("##", "役満"),
    ("ダブル役満（四暗刻単騎・国士13面・純正九蓮・大四喜）", "なし（ふつうの役満）", "ダブル役満", "ダブル／ふつう", 1),
    ("役満が2つ重なる", "2倍（3つなら3倍）", "2倍", "2倍／1倍", 0),
    ("数え役満（13翻以上）", "なし（三倍満まで）", "—", "あり／なし", 0),
    ("国士無双で暗槓をロン", "できない", "できる", "できる／できない", 1),
    ("##", "カン"),
    ("カンドラをめくる時", "どのカンもすぐ", "暗槓はすぐ・明槓と加槓は打牌のあと", "すぐ／打牌のあと（明槓だけ）", 1),
    ("パオ（責任払い）", "大三元・大四喜・四槓子", "大三元・大四喜", "なし／大三元・大四喜／四槓子まで", 1),
    ("リーチ後のカン", "面子の組み方が変わらない暗槓なら可（役の増減は問わない）", "—", "待ちが変わらない暗槓だけ・送りカンなし", 0),
    ("喰い替え", "禁止（アガリ放棄）", "禁止", "同じ牌・スジは禁止", 0),
]


def table(rows):
    out = ""
    for r in rows:
        if r[0] == "##":
            out += f'<tr class="sec"><td colspan="4">{r[1]}</td></tr>'; continue
        item, ml, js, ex, diff = r
        cell = lambda v: f'<td class="na">—</td>' if v == "—" else f"<td>{v}</td>"
        out += (f'<tr><th>{item}{"<i>違う</i>" if diff else ""}</th>{cell(ml)}{cell(js)}<td class="ex">{ex}</td></tr>')
    return out


def page_html(no, sub, rows, pad=9):
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1123px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 20px 28px 20px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 9px 16px; margin-bottom: 10px; }}
header h1 {{ font-size: 27px; font-weight: 900; line-height: 1.15; }}
header h1 em {{ font-style: normal; display: inline-block; background: #E75620; border-radius: 6px; font-size: 15px; padding: 1px 8px; margin-left: 8px; vertical-align: 5px; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; }}
{LOGO_CSS}
table {{ width: 100%; border-collapse: collapse; background: #fff; table-layout: fixed; }}
col.c0 {{ width: 160px; }} col.c3 {{ width: 170px; }}
thead th {{ background: #1F2A28; color: #fff; font-size: 14px; font-weight: 900; padding: 6px 4px; border: 2px solid #1F2A28; }}
thead th.js {{ background: #4261AA; border-color: #1F2A28; }} thead th.ex {{ background: #5E6B69; }}
tr.sec td {{ background: #177083; color: #fff; font-size: 14px; font-weight: 900; padding: 5px 10px; border: 2px solid #1F2A28; }}
tbody th {{ text-align: left; font-size: 13.5px; font-weight: 900; padding: {pad}px 8px; border: 2px solid #1F2A28; background: #F2F5F4; line-height: 1.35; }}
tbody th i {{ font-style: normal; display: inline-block; background: #E75620; color: #fff; font-size: 9.5px; border-radius: 3px; padding: 0 4px; margin-left: 4px; vertical-align: 1px; }}
tbody td {{ font-size: 13.5px; font-weight: 700; padding: {pad}px 8px; border: 2px solid #1F2A28; line-height: 1.4; }}
td.na {{ color: #A0ABA9; text-align: center; }}
td.ex {{ color: #4F5C5A; font-size: 12px; background: #FAFBFB; }}
.note {{ font-size: 10.5px; font-weight: 700; color: #4F5C5A; line-height: 1.55; margin-top: 8px; }}
.note b {{ color: #E75620; }}
footer {{ position: absolute; left: 28px; right: 28px; bottom: 12px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><h1>Mリーグと雀魂、ルールはここが違う<em>{no}/2</em><small>{sub}</small></h1>{logo_html()}</header>
<table><colgroup><col class="c0"><col><col><col class="c3"></colgroup>
<thead><tr><th>項目</th><th>Mリーグ</th><th class="js">雀魂（段位戦）</th><th class="ex">仲間内の決め方（例）</th></tr></thead>
<tbody>{table(rows)}</tbody></table>
<p class="note"><b>違う</b>＝Mリーグと雀魂で決まりが違う所。—＝確かめられなかった所。Mリーグは公式サイトの公式戦ルール、雀魂はWikipedia「雀魂」の段位戦のルールなどによる（2026年11月）。ゲームのルールは変わることがあるので、打つ前に確かめてください。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>仲間内で打つ日は、打つ前に決めておく</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for no, sub, rows, pad in ((1, "試合・点数・鳴き・リーチとトビ", P1, 8), (2, "ローカル役・途中流局・役満・カン", P2, 16)):
            hp = os.path.join(OUT, "_p.html"); io.open(hp, "w", encoding="utf-8").write(page_html(no, sub, rows, pad))
            pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
            pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
            h = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - document.querySelector('.note').getBoundingClientRect().bottom")
            print(no, "余白", round(h)); pg.screenshot(path=os.path.join(OUT, f"rule-hikaku-{no}.png")); pg.close(); os.remove(hp)
        b.close()


if __name__ == "__main__":
    render()
