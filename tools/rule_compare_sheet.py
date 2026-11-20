# -*- coding: utf-8 -*-
"""打つ前に決めるルールのチェックシート（A4縦1枚。SNSの投稿用。2026-11-20 ユーザーの依頼）。
2列に、事前に決めておきたい項目を並べ、選択肢ごとにMリーグのロゴと雀魂のアイコンの印で、どちらがどれを選んでいるかを見せる。
比べる表ではなく、チェックシート。文字・選択肢はぎゅっと詰めてよい（ユーザーの指定）。
出典: Mリーグ＝公式サイト m-league.jp/about の公式戦ルール（2026-11-20 に確認）。雀魂＝Wikipedia「雀魂」の段位戦のルールと、blog-yakuman-rules の表。
確かめられなかったもの・規定がないものは札を付けず、項目の右に小さく書く。
出力: まじゃすこ素材/x/rule-hikaku/rule-check.png（1588×2246）
実行: python tools/rule_compare_sheet.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "rule-hikaku")

# 選択肢の印: "M"＝Mリーグ・"J"＝雀魂。項目は (名前, [(選択肢, 印), ...], 補足)
LEFT = [
    ("##", "試合と点数"),
    ("試合形式", [("半荘", "MJ"), ("東風", "J"), ("今日は何試合", "")], "雀魂は東風・半荘を選ぶ"),
    ("持ち点／返し点", [("25,000／30,000", "M"), ("25,000／25,000", "J"), ("30,000／30,000", "")], ""),
    ("ウマ", [("10-30", "M"), ("10-20", ""), ("5-15", "J"), ("なし", "")], "Mはオカ込み+50/+10/−10/−30"),
    ("同点のとき", [("分け合う", "M"), ("上家取り", "J"), ("再戦", "")], "上家取り＝起家に近い人が上"),
    ("終わったときの供託", [("トップ", "MJ"), ("誰も取らない", ""), ("出した人に", "")], "流局で終わったとき"),
    ("チョンボ", [("罰符なし", ""), ("スコアから引く", "M"), ("満貫払い", ""), ("2,000オール", ""), ("供託1,000点", "")], "M＝−20pt。雀魂はゲームが止める"),
    ("チップ・祝儀", [("なし", "MJ"), ("一発・裏・赤", ""), ("役満", "")], ""),
    ("焼き鳥", [("なし", "MJ"), ("あり", "")], ""),
    ("##", "鳴き・アガリ"),
    ("赤ドラ", [("なし", ""), ("3枚", "MJ"), ("4枚", "")], ""),
    ("喰いタン", [("あり", "MJ"), ("なし", "")], ""),
    ("後付け", [("あり", "MJ"), ("なし", "")], ""),
    ("喰い替え", [("禁止", "MJ"), ("あり", "")], "同じ牌・スジ"),
    ("2人が同時にロン", [("頭ハネ", "M"), ("ダブロン", "J")], ""),
    ("3人が同時にロン", [("頭ハネ", "M"), ("トリロン", "J"), ("流局", "")], ""),
    ("連荘", [("テンパイ連荘", "MJ"), ("アガリ連荘だけ", "")], ""),
    ("アガリやめ・テンパイやめ", [("あり", "J"), ("なし", "")], "Mは規定なし"),
]
RIGHT = [
    ("##", "リーチとトビ"),
    ("ツモ番がないリーチ", [("できる", "M"), ("できない", "")], "雀魂は確かめられず"),
    ("0点・マイナスのリーチ", [("できる", ""), ("1,000点未満は不可", "J")], "Mは規定なし"),
    ("トビ", [("なし", "M"), ("0点未満で終了", "J"), ("0点で終了", "")], ""),
    ("トビ賞", [("なし", "M"), ("あり", "")], "雀魂は確かめられず"),
    ("##", "ローカル役・途中流局"),
    ("流し満貫", [("なし", "M"), ("満貫", "J")], ""),
    ("途中流局", [("なし", "M"), ("あり", "J")], "九種九牌・四風連打・四家立直・四開槓"),
    ("人和", [("なし", "MJ"), ("満貫", ""), ("役満", "")], "雀魂は友人戦で設定"),
    ("##", "役満"),
    ("形でダブル役満", [("なし", "M"), ("あり", "J")], "四暗刻単騎・国士13面・純正九蓮・大四喜"),
    ("役満が2つ重なる", [("2倍", "MJ"), ("1倍", "")], ""),
    ("数え役満", [("なし", "M"), ("あり", "")], "雀魂は確かめられず"),
    ("国士で暗槓をロン", [("できない", "M"), ("できる", "J")], ""),
    ("##", "カン"),
    ("カンドラをめくる時", [("すぐ", "M"), ("暗槓すぐ・明槓は打牌後", "J")], ""),
    ("パオ", [("なし", ""), ("大三元・大四喜", "J"), ("＋四槓子", "M")], ""),
    ("リーチ後のカン", [("面子が変わらない暗槓のみ", "M"), ("待ちが変わらない暗槓のみ", "")], "雀魂は確かめられず"),
]


# 印は本物のロゴ・アイコン（2026-11-20 ユーザーの判断で使う。元の画像は非公開の素材リポジトリ まじゃすこ素材/x/rule-hikaku/src/ だけに置く）。
# Mリーグ＝公式ロゴのマーク部分（文字は切る）。雀魂＝アプリのアイコンの顔の部分を丸く切る
SRC = os.path.join(OUT, "src")
def _uri(im):
    import base64; buf = io.BytesIO(); im.save(buf, "PNG"); return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
def _icons():
    from PIL import Image
    m = Image.open(os.path.join(SRC, "mleague.png")).convert("RGBA").crop((338, 28, 689, 474))
    px = m.load()                                                     # 白い地は透かす（色の札の上に白い四角が出ないように）
    for y in range(m.height):
        for x in range(m.width):
            r, g, b_, al = px[x, y]
            if min(r, g, b_) > 235: px[x, y] = (255, 255, 255, 0)
    m = m.resize((round(m.width * 96 / m.height), 96), Image.LANCZOS)
    j = Image.open(os.path.join(SRC, "jantama.jpg")).convert("RGB").crop((125, 125, 405, 405)).resize((96, 96), Image.LANCZOS)
    return _uri(m), _uri(j)
ICON_M, ICON_J = _icons()
def badge(k): return {"M": f'<i class="bm" title="Mリーグ"><img src="{ICON_M}"></i>', "J": f'<i class="bj" title="雀魂"><img src="{ICON_J}"></i>'}[k]
SEC_COLS = ["#177083", "#4261AA", "#6B4FA0", "#C2416B", "#2E8B57"]      # 区分ごとに見出しの色を変える（少しポップに。2026-11-20 ユーザーの指定）


_sec = iter(range(100))


def col(items):
    out, c = "", SEC_COLS[0]
    for it in items:
        if it[0] == "##":
            c = SEC_COLS[next(_sec) % len(SEC_COLS)]
            out += f'<h2 style="background:{c}">{it[1]}</h2>'; continue
        name, opts, note = it
        # 選んでいる方で色を分ける（Mリーグだけ＝金・雀魂だけ＝紫・両方＝半分ずつ）
        chips = "".join(f'<span class="op{" m" * ("M" in m and "J" not in m)}{" j" * ("J" in m and "M" not in m)}{" mj" * ("M" in m and "J" in m)}">{t}{"".join(badge(k) for k in m)}</span>' for t, m in opts)
        out += f'<div class="it"><b><i class="cb" style="border-color:{c}"></i>{name}</b><div class="ops">{chips}</div>{f"<small>{note}</small>" if note else ""}</div>'
    return out


def html():
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1123px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 14px 24px 18px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 9px 16px; margin-bottom: 8px; }}
header h1 {{ font-size: 25px; font-weight: 900; line-height: 1.15; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; }}
.legend {{ font-size: 11.5px; font-weight: 800; line-height: 1.9; white-space: nowrap; margin-left: auto; margin-right: 10px; }}
.legend i {{ margin-right: 3px; }}
{LOGO_CSS}
i.bm, i.bj {{ font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: 17px; height: 17px; margin-left: 3px; flex: none; }}
i.bm img {{ height: 16px; width: auto; display: block; }}
i.bj {{ border-radius: 50%; overflow: hidden; box-shadow: 0 0 0 1.5px #fff; }} i.bj img {{ width: 17px; height: 17px; display: block; }}
.legend i.bm, .legend i.bj {{ width: 22px; height: 22px; vertical-align: -6px; }} .legend i.bm {{ background: #fff; border-radius: 50%; }} .legend i.bm img {{ height: 16px; }} .legend i.bj img {{ width: 22px; height: 22px; }}
.grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.colw {{ background: #fff; border: 2px solid #177083; border-radius: 6px; padding: 2px 8px 6px; }}
h2 {{ font-size: 14.5px; font-weight: 900; color: #fff; background: #177083; margin: 8px -8px 2px; padding: 3px 10px; }}
.colw h2:first-child {{ margin-top: -2px; border-radius: 4px 4px 0 0; }}
.it {{ display: grid; grid-template-columns: 124px 1fr; column-gap: 6px; align-items: center; padding: 6px 0; border-top: 1.5px solid #DCE7E4; }}
h2 + .it {{ border-top: 0; }}
.it > b {{ font-size: 13px; font-weight: 900; line-height: 1.25; display: flex; align-items: flex-start; gap: 5px; }}
i.cb {{ flex: none; width: 13px; height: 13px; border: 2.2px solid #177083; border-radius: 4px; margin-top: 1px; background: #fff; }}
.ops {{ display: flex; flex-wrap: wrap; gap: 3px; }}
.op {{ font-size: 11.5px; font-weight: 800; border: 1.5px solid #CAD8D5; border-radius: 12px; padding: 1px 7px 1px 8px; color: #4F5C5A; background: #fff; white-space: nowrap; display: inline-flex; align-items: center; }}
.op.m {{ border-color: #E07A7F; color: #1F2A28; background: #FDECEC; }}
.op.j {{ border-color: #A47FE6; color: #1F2A28; background: #F1E8FD; }}
.op.mj {{ border-color: #8C7BC0; color: #1F2A28; background: linear-gradient(90deg, #FDECEC 50%, #F1E8FD 50%); }}
.it > small {{ grid-column: 2; font-size: 10.5px; font-weight: 700; color: #6B7A77; margin-top: 2px; }}
.note {{ font-size: 11px; font-weight: 700; color: #4F5C5A; line-height: 1.55; margin-top: 7px; }}
.note b {{ color: #E75620; }}
footer {{ position: absolute; left: 24px; right: 24px; bottom: 7px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><h1>打つ前に決める ルールチェックシート<small>Mリーグと雀魂は、どれを選んでいる？</small></h1>
<div class="legend">{badge("M")} Mリーグ<br>{badge("J")} 雀魂（段位戦）</div>{logo_html()}</header>
<div class="grid"><div class="colw">{col(LEFT)}</div><div class="colw">{col(RIGHT)}</div></div>
<p class="note"><b>□にチェックして、仲間内のルールを決めよう。</b>Mリーグは公式サイトの公式戦ルール、雀魂はWikipedia「雀魂」の段位戦のルールなどによる（2026年11月）。印が無い所は、規定がないか確かめられなかった所。ゲームのルールは変わることがある。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>決めたルールで打ったら、スコアはまじゃすこで</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, "_p.html"); io.open(hp, "w", encoding="utf-8").write(html())
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
        pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        h = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - document.querySelector('.note').getBoundingClientRect().bottom")
        print("余白", round(h)); pg.screenshot(path=os.path.join(OUT, "rule-check.png")); b.close()
    os.remove(hp)


if __name__ == "__main__":
    render()
