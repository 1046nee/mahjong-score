# -*- coding: utf-8 -*-
"""麻雀「鳴き（副露）のまとめ」（1枚・A4縦。SNSの投稿用。2026-11-20 ユーザーの依頼）。
初心者（オレンジ）・中級者（緑）・上級者（紫）に色分け。初心者の所は牌の絵で見せる。見た目は tools/rule_sheet.py（打つ前の確認リスト）と同じ型。
内容の正: チー・ポン・カン（暗槓・大明槓・加槓）／リーチできるか（暗槓だけ鳴きではない）／喰い替え（同一牌・スジ・赤五）／
リーチ後のカン（Mリーグ公式ルール 第4章第5条: 面子構成が変わらない暗槓なら可）／鳴いても役があるか／鳴きの損得。
出力: まじゃすこ素材/x/naki/naki-matome.png（1588×2246）
実行: python tools/naki_sheet.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
T = "file:///" + os.path.join(ROOT, "assets", "tiles").replace("\\", "/")
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "naki")
C1, C2, C3 = "#E75620", "#177083", "#6B4FA0"      # 初心者・中級者・上級者


def t(code, w=26, yoko=False, dim=False, mark=""):
    """牌1枚。yoko＝横向き（鳴いた牌）・dim＝伏せ（裏）・mark＝下に付ける小さな印（×など）"""
    src = f"{T}/{'back' if dim else code}{'-yoko' if yoko and not dim else ''}.svg"
    h = round(w * 1.33)
    st = f"width:{h}px" if yoko else f"height:{h}px"      # 横向きの絵は幅＝牌の高さ
    img = f'<img src="{src}" style="{st}">'
    return f'<span class="tl">{img}{f"<i>{mark}</i>" if mark else ""}</span>' if mark else img


def hand(*parts, w=26):
    """parts: 牌のコード（"m4"）・横（"y:m6"）・伏せ（"d"）・すき間（"|"）"""
    out = ""
    for p in parts:
        if p == "|": out += '<span class="gap"></span>'
        elif p == "d": out += t("back", w, dim=True)
        elif p.startswith("y:"): out += t(p[2:], w, yoko=True)
        elif p.startswith("x:"): out += t(p[2:], w, mark="✕")
        else: out += t(p, w)
    return f'<span class="hd">{out}</span>'


def sheet_html():
    calls = f"""
<div class="kans">
  <div class="call"><b>チー</b><small>上家（左の人）からだけ</small>{hand("m4", "m5", "y:m6", w=24)}<span>つながった3枚（順子）</span></div>
  <div class="call"><b>ポン</b><small>だれからでも</small>{hand("z6", "z6", "y:z6", w=24)}<span>同じ牌3枚（刻子）</span></div>
  <div class="kan"><b>暗槓<rt>アンカン</rt></b><small>自分で4枚そろえる</small>{hand("d", "z1", "z1", "d", w=24)}<span>両端を伏せて卓の右へ</span></div>
  <div class="kan"><b>大明槓<rt>ダイミンカン</rt></b><small>手の3枚＋人の4枚目</small>{hand("z2", "z2", "z2", "y:z2", w=22)}<span>人が切った牌は横向き</span></div>
  <div class="kan"><b>加槓<rt>カカン</rt></b><small>ポン＋自分の4枚目</small>{hand("z7", '<stack>', "z7", "z7")}<span>横向きの牌に重ねる</span></div>
</div>"""
    # 加槓は横向きの牌の上に横向きで重ねる絵
    calls = calls.replace(hand("z7", '<stack>', "z7", "z7"),
                          f'<span class="hd"><span class="stk">{t("z7", 24, yoko=True)}{t("z7", 24, yoko=True)}</span>{t("z7", 24)}{t("z7", 24)}</span>')
    riichi = """
<table class="ok">
<tr><th>チー</th><th>ポン</th><th>大明槓</th><th>加槓</th><th class="g">暗槓</th></tr>
<tr><td class="x">×</td><td class="x">×</td><td class="x">×</td><td class="x">×</td><td class="o">○</td></tr>
</table>
<p class="tip">暗槓は人の牌をもらっていないので<b>鳴きではない</b>。暗槓しても門前のまま＝リーチできる</p>"""
    kuikae = f"""
<div class="kk">
  <div><b>同じ牌</b>{hand("m4", "m5", "y:m6", w=24)}<em>→</em>{hand("x:m6", w=24)}<span class="cap">六萬をチーして、六萬を切る</span></div>
  <div><b>スジ</b>{hand("m4", "m5", "y:m6", w=24)}<em>→</em>{hand("x:m3", w=24)}<span class="cap">四五萬で六萬をチーして三萬を切る</span></div>
  <div><b>赤五</b>{hand("p4", "p6", "y:p5r", w=24)}<em>→</em>{hand("x:p5", w=24)}<span class="cap">赤五筒をチーして、黒い五筒を切る</span></div>
</div>
<p class="tip">鳴いた牌と同じ牌・スジの牌は切れない＝<b>喰い替え</b>（Mリーグはアガリ放棄）。赤も黒も同じ五筒なので、赤をもらって黒を切るのも喰い替え</p>"""
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>
@page {{ size: A4; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1123px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 18px 30px 20px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 8px 16px; margin-bottom: 8px; }}
header h1 {{ font-size: 30px; font-weight: 900; line-height: 1.1; letter-spacing: .03em; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; letter-spacing: 0; }}
.legend {{ font-size: 12px; font-weight: 800; line-height: 1.7; text-align: right; }}
.legend i {{ font-style: normal; display: inline-block; border-radius: 4px; padding: 0 7px; margin-left: 4px; color: #fff; border: 1.5px solid #fff; }}
{LOGO_CSS}
section {{ background: #fff; border: 2px solid var(--c); border-radius: 6px; margin-bottom: 7px; overflow: hidden; }}
section > h2 {{ background: var(--c); color: #fff; font-size: 15px; font-weight: 900; padding: 4px 12px; display: flex; align-items: center; gap: 8px; }}
section > h2 .lv {{ background: #fff; color: var(--c); border-radius: 4px; font-size: 11.5px; padding: 0 6px; }}
section > h2 small {{ font-size: 11px; font-weight: 700; opacity: .9; margin-left: auto; }}
.in {{ padding: 6px 12px 7px; }}
.row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
h3 {{ font-size: 13.5px; font-weight: 900; color: var(--c); margin: 2px 0 5px; }}
h3 small {{ color: #5E6B69; font-size: 11px; font-weight: 700; margin-left: 6px; }}
.calls {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 7px; }}
.kans {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; }}
.call, .kan {{ border: 1.5px solid #D5E2DF; border-radius: 6px; padding: 5px 6px; justify-content: space-between; display: flex; flex-direction: column; align-items: flex-start; gap: 3px; }}
.call b, .kan b {{ font-size: 16px; font-weight: 900; }}
.kan b rt, .call b rt {{ display: block; line-height: 1; font-size: 10px; color: #177083; margin-left: 4px; }}
.call small, .kan small {{ font-size: 10.5px; font-weight: 700; color: #5E6B69; }}
.call span:last-child, .kan span:last-child {{ font-size: 10.5px; font-weight: 800; color: #1F2A28; }}
.hd {{ display: inline-flex; align-items: flex-end; gap: 1px; }}
.hd img {{ display: block; }}
.gap {{ width: 7px; }}
.stk {{ display: inline-flex; flex-direction: column; gap: 1px; }}
.tl {{ position: relative; display: inline-block; }}
.tl i {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-style: normal; font-size: 26px; font-weight: 900; color: #C92F42; text-shadow: 0 0 3px #fff, 0 0 3px #fff; }}
table.ok {{ border-collapse: collapse; width: 100%; margin: 2px 0 5px; }}
table.ok th, table.ok td {{ border: 1.5px solid #1F2A28; text-align: center; font-weight: 900; }}
table.ok th {{ background: #F2F5F4; font-size: 12.5px; padding: 3px 0; }}
table.ok th.g {{ background: #E4F3EC; color: #177083; }}
table.ok td {{ font-size: 18px; line-height: 1.2; }}
td.x {{ color: #C92F42; }} td.o {{ color: #177083; background: #E4F3EC; }}
.tip {{ font-size: 11px; font-weight: 700; line-height: 1.45; color: #33403D; }}
.tip b {{ color: {C1}; }}
.kk {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; margin-bottom: 4px; }}
.kk > div {{ display: flex; flex-wrap: wrap; align-items: center; gap: 4px 5px; border: 1.5px solid #F2D3D8; border-radius: 6px; padding: 5px 6px; }} .kk > div > b, .kk > div > .cap {{ width: 100%; }} .kk .hd {{ flex: none; }}
.kk b {{ font-size: 12.5px; font-weight: 900; color: #C92F42; }}
.kk em {{ font-style: normal; font-weight: 900; color: #8A9A97; }}
.kk .cap {{ font-size: 10.5px; font-weight: 700; color: #33403D; }}
ul.li {{ list-style: none; }}
ul.li li {{ font-size: 11.5px; font-weight: 700; line-height: 1.45; padding: 2px 0 2px 16px; position: relative; border-top: 1px solid #E3ECEA; }}
ul.li li:first-child {{ border-top: 0; }}
ul.li li::before {{ content: ""; position: absolute; left: 2px; top: 9px; width: 8px; height: 8px; border-radius: 50%; background: var(--c); }}
ul.li li b {{ font-weight: 900; }}
ul.li li.ng::before {{ background: #C92F42; }} ul.li li.okk::before {{ background: #177083; }}
.grp {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }}
.grp div {{ border-radius: 6px; padding: 5px 7px; font-size: 10.5px; font-weight: 700; line-height: 1.45; }}
.grp div b {{ display: block; font-size: 12px; font-weight: 900; margin-bottom: 2px; }}
.g1 {{ background: #E4F3EC; }} .g1 b {{ color: #177083; }}
.g2 {{ background: #EAF0FB; }} .g2 b {{ color: #4261AA; }}
.g3 {{ background: #FFF1E8; }} .g3 b {{ color: {C1}; }}
.g4 {{ background: #FBE9EC; }} .g4 b {{ color: #C92F42; }}
.pm {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.pm h4 {{ font-size: 12.5px; font-weight: 900; margin-bottom: 2px; }}
footer {{ position: absolute; left: 30px; right: 30px; bottom: 12px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><h1>鳴き（副露）のまとめ<small>チー・ポン・カン／リーチできる？／喰い替え／リーチ後のカン</small></h1>
<div class="legend">覚える順<br><i style="background:{C1}">初心者</i><i style="background:{C2}">中級者</i><i style="background:{C3}">上級者</i></div>{logo_html()}</header>

<section style="--c:{C1}"><h2><span class="lv">初心者</span>鳴きは3種類＋カンは3つ<small>鳴き＝人が切った牌をもらって面子を作ること</small></h2>
<div class="in">{calls}</div></section>

<section style="--c:{C1}"><h2><span class="lv">初心者</span>鳴いたらリーチできない（暗槓だけはできる）</h2>
<div class="in">{riichi}</div></section>

<section style="--c:{C1}"><h2><span class="lv">初心者</span>喰い替えは禁止<small>鳴いたら、その牌で作り直せる牌は切れない</small></h2>
<div class="in">{kuikae}</div></section>

<section style="--c:{C2}"><h2><span class="lv">中級者</span>リーチのあとのカン</h2>
<div class="in"><div class="row">
<div><h3>できる</h3><ul class="li"><li class="okk"><b>待ちが変わらない暗槓</b>（例：東東東に4枚目の東をツモ）</li>
<li class="okk">Mリーグ：面子の組み方が変わらない暗槓ならOK（役の増減は問わない）</li></ul></div>
<div><h3>できない</h3><ul class="li"><li class="ng"><b>送りカン</b>：ツモった牌と別の暗刻をカンする</li>
<li class="ng"><b>待ちが変わる</b>：三三三四五で三をツモ→三・六待ちが六待ちに</li>
<li class="ng"><b>面子の組み方が変わる</b>：暗刻と順子のどちらにも取れる形</li>
<li class="ng"><b>役が変わる</b>カンはルールによって分かれる（打つ前に確認）</li></ul></div>
</div></div></section>

<section style="--c:{C2}"><h2><span class="lv">中級者</span>鳴いても、役は残る？<small>役が無いとアガれない</small></h2>
<div class="in"><div class="grp">
<div class="g1"><b>役牌のポン</b>白・發・中・場風・自風。鳴いた時点で役が決まる。いちばん安心</div>
<div class="g2"><b>二〜八だけの鳴き</b>喰いタン（タンヤオ）が残る。手牌も二〜八だけにする</div>
<div class="g3"><b>一・九を含む鳴き</b>タンヤオが消える。役なしになりやすい（チャンタ・一通・混一色など）</div>
<div class="g4"><b>大明槓</b>手は進まない。新しいドラは全員に乗る。門前からはほぼ損</div>
</div></div></section>

<section style="--c:{C3}"><h2><span class="lv">上級者</span>鳴きの得と損</h2>
<div class="in"><div class="pm">
<div><h4 style="color:#177083">得</h4><ul class="li" style="--c:#177083">
<li>手が確実に早く進む（大明槓はのぞく）</li><li>他家の一発を消す</li>
<li>対面・下家からのポンで、間の人のツモ番を飛ばす／チーをさせない（邪魔ポン）</li>
<li>同じ巡目のフリテンを解消・海底をずらす</li></ul></div>
<div><h4 style="color:#C92F42">損</h4><ul class="li" style="--c:#C92F42">
<li>狙いが読まれやすい（ポンした牌は3枚の壁に）</li><li>鳴いた牌は切れず、打牌の幅が減る</li>
<li>リーチできない・門前の役が消え点数が下がる（食い下がり）</li><li>下家（や対面）のツモ番が早くなる</li></ul></div>
</div></div></section>

<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>リーチ後のカン・喰い替えは Mリーグ公式ルールより（2026年11月）。牌のイラストは まじゃすこ オリジナル</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, "_sheet.html"); io.open(hp, "w", encoding="utf-8").write(sheet_html())
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
        pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        h = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - Math.max(...[...document.querySelectorAll('section')].map(s => s.getBoundingClientRect().bottom))")
        print("余白", round(h)); pg.screenshot(path=os.path.join(OUT, "naki-matome.png")); b.close()
    os.remove(hp)


if __name__ == "__main__":
    render()
