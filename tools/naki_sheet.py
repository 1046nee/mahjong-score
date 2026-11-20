# -*- coding: utf-8 -*-
"""麻雀「鳴き（副露）のまとめ」（A4縦2枚。SNSの投稿用。2026-11-20 ユーザーの依頼）。
1枚目＝きほん（鳴きの種類・リーチできるか・役は残るか・鳴く？鳴かない？）、2枚目＝ルールと駆け引き（喰い替え・リーチ後のカン・鳴きの得と損）。
覚える段階は、まとまりごとではなく項目ごとに札を付ける（初心者＝オレンジ・中級者＝緑・上級者＝紫。2026-11-20 ユーザーの指定）。
牌の並べ方（2026-11-20 ユーザーの指定）: チーは鳴いた牌を一番左に横向き。ポンは対面から＝真ん中、大明槓は下家から＝右を横向き。加槓は横向きの牌に重ねる。
リーチ後のカンの例は、待ちを tools/machi_sheet/machi3.py の waits で確かめた手（できる1つ・できない4つ）。
出力: まじゃすこ素材/x/naki/naki-1.png・naki-2.png（1588×2246）
実行: python tools/naki_sheet.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
T = "file:///" + os.path.join(ROOT, "assets", "tiles").replace("\\", "/")
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "naki")
LV = {1: ("初心者", "#E75620"), 2: ("中級者", "#177083"), 3: ("上級者", "#6B4FA0")}


def lv(n): return f'<i class="lv" style="background:{LV[n][1]}">{LV[n][0]}</i>'


def t(code, w=24, yoko=False, mark="", hl=False):
    """牌1枚。yoko＝横向き（鳴いた牌）・mark＝重ねる印（✕・○）・hl＝ツモった牌の枠"""
    h = round(w * 1.33)
    src = f"{T}/{code}{'-yoko' if yoko else ''}.svg"
    img = f'<img src="{src}" style="{f"width:{h}px" if yoko else f"height:{h}px"}">'
    cls = "tl" + (" hl" if hl else "")
    return f'<span class="{cls}">{img}{f"<i class=m{1 if mark == chr(10005) else 2}>{mark}</i>" if mark else ""}</span>'


def hand(spec, w=24):
    """spec: 空白区切り。m4＝牌・y:m6＝横向き・d＝伏せ・x:m6＝✕・o:m7＝○・t:z1＝ツモ（枠）・|＝すき間・k:z7＝横向き2枚を重ねる"""
    out = ""
    for p in spec.split():
        if p == "|": out += '<span class="gap"></span>'
        elif p == "d": out += t("back", w)
        elif p.startswith("y:"): out += t(p[2:], w, yoko=True)
        elif p.startswith("x:"): out += t(p[2:], w, mark="✕")
        elif p.startswith("o:"): out += t(p[2:], w, mark="○")
        elif p.startswith("t:"): out += t(p[2:], w, hl=True)
        elif p.startswith("k:"): out += f'<span class="stk">{t(p[2:], w, yoko=True)}{t(p[2:], w, yoko=True)}</span>'
        else: out += t(p, w)
    return f'<span class="hd">{out}</span>'


def seq(s, suit):
    return " ".join(suit + ch for ch in s)


CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1123px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 18px 28px 20px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 8px 16px; margin-bottom: 9px; }}
header h1 {{ font-size: 28px; font-weight: 900; line-height: 1.1; }}
header h1 em {{ font-style: normal; display: inline-block; background: #E75620; border-radius: 6px; font-size: 15px; padding: 1px 8px; margin-left: 8px; vertical-align: 5px; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; }}
.legend {{ font-size: 11.5px; font-weight: 800; line-height: 1.8; text-align: right; }}
.legend .lv {{ border: 1.5px solid #fff; }}
{LOGO_CSS}
i.lv {{ font-style: normal; display: inline-block; color: #fff; font-size: 10.5px; font-weight: 900; border-radius: 4px; padding: 0 5px; line-height: 1.6; margin-right: 5px; vertical-align: 1px; white-space: nowrap; }}
section {{ background: #fff; border: 2px solid #177083; border-radius: 6px; margin-bottom: 8px; overflow: hidden; }}
section > h2 {{ background: #177083; color: #fff; font-size: 15.5px; font-weight: 900; padding: 4px 12px; display: flex; align-items: baseline; gap: 8px; }}
section > h2 small {{ font-size: 11px; font-weight: 700; opacity: .92; margin-left: auto; }}
.in {{ padding: 7px 12px 8px; }}
.hd {{ display: inline-flex; align-items: flex-end; gap: 1px; flex: none; }}
.hd img {{ display: block; }}
.gap {{ width: 8px; }}
.stk {{ display: inline-flex; flex-direction: column; gap: 1px; }}
.tl {{ position: relative; display: inline-block; }}
.tl.hl img {{ outline: 3px solid #E75620; outline-offset: 1px; border-radius: 3px; }}
.tl i {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-style: normal; font-size: 24px; font-weight: 900; text-shadow: 0 0 3px #fff, 0 0 3px #fff; }}
.tl i.m1 {{ color: #C92F42; }} .tl i.m2 {{ color: #177083; }}
/* 鳴きの種類 */
.kinds {{ display: grid; grid-template-columns: 1fr 1fr 2.55fr; gap: 7px; }}
.kind {{ border: 1.5px solid #D5E2DF; border-radius: 6px; padding: 6px 8px; }}
.kind > b {{ font-size: 18px; font-weight: 900; display: block; }}
.kind > .d {{ font-size: 11px; font-weight: 800; margin: 2px 0 5px; }}
.kind > .who {{ font-size: 10.5px; font-weight: 700; color: #5E6B69; display: block; margin-top: 4px; }}
.kans {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 6px; }}
.kan {{ background: #F4F8F7; border-radius: 6px; padding: 5px 6px; }}
.kan b {{ font-size: 14px; font-weight: 900; display: block; }}
.kan b small {{ font-size: 9.5px; color: #177083; margin-left: 3px; }}
.kan > span.cap {{ font-size: 10px; font-weight: 700; color: #4F5C5A; display: block; margin-top: 3px; line-height: 1.35; }}
.kan .lvl {{ margin-bottom: 3px; }}
table.ok {{ border-collapse: collapse; width: 100%; }}
table.ok th, table.ok td {{ border: 1.5px solid #1F2A28; text-align: center; font-weight: 900; }}
table.ok th {{ background: #F2F5F4; font-size: 13px; padding: 3px 0; }}
table.ok th.g {{ background: #E4F3EC; color: #177083; }}
table.ok td {{ font-size: 19px; line-height: 1.2; }}
td.x {{ color: #C92F42; }} td.o {{ color: #177083; background: #E4F3EC; }}
.tip {{ font-size: 11px; font-weight: 700; line-height: 1.5; color: #33403D; margin-top: 5px; }}
.tip b {{ color: #E75620; }}
.grp {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; }}
.grp div {{ border-radius: 6px; padding: 5px 7px; font-size: 10.5px; font-weight: 700; line-height: 1.45; }}
.grp div b {{ display: block; font-size: 12.5px; font-weight: 900; margin: 2px 0; }}
.g1 {{ background: #E4F3EC; }} .g1 b {{ color: #177083; }}
.g2 {{ background: #EAF0FB; }} .g2 b {{ color: #4261AA; }}
.g3 {{ background: #FFF1E8; }} .g3 b {{ color: #E75620; }}
.g4 {{ background: #FBE9EC; }} .g4 b {{ color: #C92F42; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
h3 {{ font-size: 14px; font-weight: 900; margin-bottom: 3px; }}
h3.ok {{ color: #177083; }} h3.ng {{ color: #C92F42; }}
ul.li {{ list-style: none; }}
ul.li li {{ font-size: 11.5px; font-weight: 700; line-height: 1.45; padding: 4px 0; border-top: 1px solid #E3ECEA; }}
ul.li li:first-child {{ border-top: 0; }}
ul.li li b {{ font-weight: 900; }}
.lead {{ font-size: 12px; font-weight: 800; line-height: 1.5; margin-bottom: 6px; background: #FFF5EF; border-left: 4px solid #E75620; padding: 4px 8px; }}
.lead b {{ color: #E75620; }}
/* 喰い替え */
.kk {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.kkc {{ border: 1.5px solid #D5E2DF; border-radius: 6px; padding: 6px 8px; }}
.kkc > b {{ font-size: 14px; font-weight: 900; color: #C92F42; display: block; margin-bottom: 4px; }}
.kkr {{ display: flex; align-items: center; gap: 6px; padding: 7px 0; border-top: 1px dashed #D5E2DF; }}
.kkr:first-of-type {{ border-top: 0; }}
.kkr em {{ font-style: normal; font-weight: 900; color: #8A9A97; }}
.kkr span {{ font-size: 10.5px; font-weight: 700; line-height: 1.4; color: #33403D; }}
/* リーチ後のカン */
.rk {{ display: grid; grid-template-columns: 92px auto 1fr; align-items: center; gap: 8px; padding: 9px 0; border-top: 1px solid #E3ECEA; }}
.rk:first-child {{ border-top: 0; }}
.rk > b {{ font-size: 12.5px; font-weight: 900; text-align: center; border-radius: 5px; padding: 3px 0; color: #fff; }}
.rk > b.o {{ background: #177083; }} .rk > b.x {{ background: #C92F42; }}
.rk > span {{ font-size: 11px; font-weight: 700; line-height: 1.45; }}
.rk > span strong {{ font-weight: 900; display: block; font-size: 12px; }}
footer {{ position: absolute; left: 28px; right: 28px; bottom: 12px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
"""


def page(no, sub, body):
    legend = f'<div class="legend">覚える段階<br>{lv(1)}{lv(2)}{lv(3)}</div>'
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><h1>鳴き（副露）のまとめ<em>{no}/2</em><small>{sub}</small></h1>{legend}{logo_html()}</header>
{body}
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer>
</body></html>"""


def page1():
    kinds = f"""
<div class="kinds">
  <div class="kind">{lv(1)}<b>チー</b><div class="d">つながった3枚（順子）</div>{hand("y:m6 m4 m5")}<span class="who">上家（左の人）からだけ。鳴いた牌は左に横向き</span></div>
  <div class="kind">{lv(1)}<b>ポン</b><div class="d">同じ牌3枚（刻子）</div>{hand("z6 y:z6 z6")}<span class="who">だれからでも。対面からは真ん中を横向き</span></div>
  <div class="kind"><b>カン</b><div class="d">同じ牌4枚（槓子）。カンしたら、カンドラをめくって嶺上牌を1枚ツモる</div>
    <div class="kans">
      <div class="kan">{lv(1)}<b>暗槓<small>アンカン</small></b>{hand("d z1 z1 d", 20)}<span class="cap">自分で4枚そろえる。両端を伏せる</span></div>
      <div class="kan">{lv(2)}<b>大明槓<small>ダイミンカン</small></b>{hand("z2 z2 z2 y:z2", 19)}<span class="cap">手の3枚＋人が切った4枚目。下家からは右を横向き</span></div>
      <div class="kan">{lv(1)}<b>加槓<small>カカン</small></b>{hand("z7 k:z7 z7", 20)}<span class="cap">ポンした3枚に、自分で引いた4枚目を横向きで重ねる</span></div>
    </div></div>
</div>"""
    riichi = f"""{lv(1)}<span style="font-size:12px;font-weight:900">鳴いたあとに、リーチできる？</span>
<table class="ok" style="margin-top:5px">
<tr><th>チー</th><th>ポン</th><th class="g">暗槓</th><th>大明槓</th><th>加槓</th></tr>
<tr><td class="x">×</td><td class="x">×</td><td class="o">○</td><td class="x">×</td><td class="x">×</td></tr>
</table>
<p class="tip">暗槓は人の牌をもらっていないので<b>鳴きではない</b>。暗槓しても門前（メンゼン）のまま＝リーチできる。加槓はポンのあとなので、もう門前ではない</p>"""
    yaku = f"""<p class="lead">鳴くと、リーチやピンフなど<b>門前でしかつかない役</b>が無くなる。<b>役が1つも無いとアガれない</b>ので、鳴く前に「鳴いたあとも役があるか」を確かめる</p>
<div class="grp">
<div class="g1">{lv(1)}<b>役牌のポン</b>白・發・中・場風・自風。ポンした時点で役が1つ決まる。いちばん安心</div>
<div class="g2">{lv(1)}<b>二〜八だけの鳴き</b>タンヤオ（喰いタン）が残る。手牌も二〜八だけでそろえる</div>
<div class="g3">{lv(2)}<b>一・九・字牌を含む鳴き</b>タンヤオが消える。チャンタ・一通・混一色・対々和などを狙わないと役なしに</div>
<div class="g4">{lv(2)}<b>大明槓</b>手は1枚も進まない。新しいドラは全員に乗る。門前からの大明槓はほぼ損</div>
</div>"""
    naku = f"""<p class="lead">鳴くと<b>アガリまでが早くなる</b>。でも<b>点数が下がり、役が無くなることもある</b>。「早さ」と「点数・役」をくらべて決める</p>
<div class="two">
<div><h3 class="ok">鳴いた方がいい</h3><ul class="li">
<li>{lv(1)}<b>役牌の対子がある</b>：ポンするだけで役が1つつく</li>
<li>{lv(1)}<b>あと1〜2回の鳴きでテンパイ</b>：タンヤオ・混一色など、役がはっきり見える</li>
<li>{lv(1)}<b>鳴いても満貫（8,000点）以上</b>：役＋ドラが多い手は、鳴いてでもアガり切る</li>
<li>{lv(2)}<b>局の終盤・他家の親や大きい手を流したい</b>：残りのツモが少ないなら早さを優先</li>
<li>{lv(2)}<b>オーラスでトップを守りたい</b>：安くても早くアガって終わらせる</li></ul></div>
<div><h3 class="ng">鳴かない方がいい</h3><ul class="li">
<li>{lv(1)}<b>鳴いたら役が無くなる</b>：役が決まらないまま鳴くと、アガれない</li>
<li>{lv(1)}<b>門前でも十分アガれそう</b>：リーチした方が点数が高い・待ちがいい</li>
<li>{lv(2)}<b>守りが苦しくなる</b>：手牌が短くなり、他家のリーチから降りにくい</li></ul></div>
</div>"""
    body = f"""
<section><h2>鳴きは3種類（チー・ポン・カン）<small>鳴き＝人が切った牌をもらって面子を作ること</small></h2><div class="in">{kinds}</div></section>
<section><h2>鳴いたらリーチできない（暗槓だけはできる）</h2><div class="in">{riichi}</div></section>
<section><h2>鳴いても、役は残る？</h2><div class="in">{yaku}</div></section>
<section><h2>鳴く？　鳴かない？</h2><div class="in">{naku}</div></section>"""
    return page(1, "鳴きのきほん：種類・リーチ・役・鳴くか鳴かないか", body)


def page2():
    kuikae = f"""<p class="lead">鳴いたあとに、鳴いた形のまま<b>同じ面子をもう一度作れる牌</b>は切れない＝<b>喰い替え</b>（違反するとアガれなくなるルールが多い）</p>
<div class="kk">
<div class="kkc">{lv(1)}<b>同じ牌</b>
  <div class="kkr">{hand("y:m6 m4 m5", 21)}<em>→</em>{hand("x:m6", 21)}<span>六萬をチーして、六萬を切る</span></div>
  <div class="kkr">{hand("y:m6 m4 m5", 21)}<em>→</em>{hand("o:m7", 21)}<span>七萬は切れる（四五萬と面子にならない）</span></div>
  <div class="kkr">{hand("y:p5r p4 p6", 21)}<em>→</em>{hand("x:p5", 21)}<span>赤五筒をチーして黒い五筒を切るのも、同じ牌</span></div>
</div>
<div class="kkc">{lv(1)}<b>スジ</b>
  <div class="kkr">{hand("y:m6 m4 m5", 21)}<em>→</em>{hand("x:m3", 21)}<span>四五萬で六萬をチーして、三萬を切る（三四五萬も作れる）</span></div>
  <div class="kkr">{hand("y:m5 m4 m6", 21)}<em>→</em>{hand("o:m3", 21)}<span>四六萬で五萬をチー（嵌張）なら、三萬・七萬は切れる</span></div>
  <div class="kkr">{hand("y:m3 m4 m5", 21)}<em>→</em>{hand("x:m6", 21)}<span>四五萬で三萬をチーして、六萬を切るのもスジ</span></div>
</div></div>"""
    W = 18
    base = f'{seq("123", "m")} {seq("789", "s")}'
    rk = [
        ("o", "できる", f'{seq("123", "m")} {seq("456", "p")} {seq("789", "s")} z1 z1 z1 z2 | t:z1', "<strong>待ちが変わらない暗槓</strong>東東東に4枚目の東をツモ。カンしても南の単騎待ちのまま"),
        ("x", "送りカン", f'{base} {seq("55556", "p")} z1 z1 | t:m9', "<strong>ツモった牌と別の牌でカン</strong>ツモった九萬を手に残して、前からある五筒4枚をカン"),
        ("x", "待ちが変わる", f'{base} z1 z1 {seq("2223", "p")} p4 | t:p2', "<strong>カンで待ちが減る</strong>二・五筒と東の待ち。二筒をカンすると東では待てなくなる"),
        ("x", "面子が変わる", f'{base} {seq("1112444", "p")} | t:p4', "<strong>面子の組み方が変わる</strong>待ちは二・三筒のまま。でも四筒を二三四の順子や雀頭に使う取り方ができなくなる"),
        ("x", "役が変わる", f'{seq("111222333", "m")} {seq("789", "s")} z1 | t:m1', "<strong>役が変わる</strong>一二三萬×3（一盃口）とも取れる形。一萬をカンすると一盃口の取り方が消える（ルールによっては可）"),
    ]
    rkh = "".join(f'<div class="rk"><b class="{k}">{lab}</b>{hand(h, W)}<span>{tx}</span></div>' for k, lab, h, tx in rk)
    ok = f"""<div class="two">
<div><h3 class="ok">得</h3><ul class="li">
<li>{lv(1)}手が確実に早く進む（大明槓はのぞく）</li>
<li>{lv(2)}他家の一発を消す</li>
<li>{lv(2)}同じ巡目のフリテンを解消できる</li>
<li>{lv(2)}海底（最後のツモ）の人をずらす</li>
<li>{lv(3)}対面・下家からのポンで、ツモ番を飛ばす／チーをさせない（邪魔ポン）</li>
<li>{lv(3)}安全牌に困っていそうな人に、ツモ番を回す</li>
<li>{lv(3)}親のテンパイの確率を上げるために、ツモ番を回す</li></ul></div>
<div><h3 class="ng">損</h3><ul class="li">
<li>{lv(1)}リーチできない。門前の役が消えて、点数が下がる（食い下がり）</li>
<li>{lv(1)}鳴いた牌は切れず、打牌の幅が減る</li>
<li>{lv(1)}手牌が短くなり、他家のリーチから降りにくい</li>
<li>{lv(1)}狙いを読まれやすい（ポンした牌は3枚見えた壁に）</li></ul></div>
</div>"""
    body = f"""
<section><h2>喰い替えは禁止</h2><div class="in">{kuikae}</div></section>
<section><h2>リーチのあとのカン<small>リーチしたら、待ちが変わらない暗槓だけできる</small></h2><div class="in"><div style="margin-bottom:2px">{lv(2)}</div>{rkh}</div></section>
<section><h2>鳴きの得と損</h2><div class="in">{ok}</div></section>"""
    return page(2, "ルールと駆け引き：喰い替え・リーチ後のカン・得と損", body)


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for no, html in ((1, page1()), (2, page2())):
            hp = os.path.join(OUT, "_p.html"); io.open(hp, "w", encoding="utf-8").write(html)
            pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
            pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
            h = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - Math.max(...[...document.querySelectorAll('section')].map(s => s.getBoundingClientRect().bottom))")
            print(no, "余白", round(h)); pg.screenshot(path=os.path.join(OUT, f"naki-{no}.png")); pg.close(); os.remove(hp)
        b.close()


if __name__ == "__main__":
    render()
