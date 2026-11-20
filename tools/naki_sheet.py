# -*- coding: utf-8 -*-
"""麻雀「鳴き（副露）のまとめ」（A4縦1枚。SNSの投稿用。2026-11-20 ユーザーの依頼・同日に1枚へまとめ直し）。
並び: 鳴きって、なに？（初心者向けの説明と、チー・ポン・暗槓・大明槓・加槓を1列）→ リーチできる？→できない／役は残る？ → 喰い替え（4例。赤五はポンの例）→ リーチ後のカン（できる1・できない3。待ちとツモ牌の札つき）→ 鳴く？鳴かない？かんたん判断表（一番下）。
覚える段階は項目ごとに札（初心者＝オレンジ・中級者＝緑・上級者＝紫）。文は1行に収まる短さにする（2026-11-20 ユーザーの指定）。
牌の並べ方: チーは鳴いた牌を一番左に横向き。ポンは対面から＝真ん中、大明槓は下家から＝右を横向き。加槓は横向きの牌に重ねる。
リーチ後のカン: 面子の組み方が変わる暗槓（送りカン・待ちが変わるを含む）はできない。役が変わるだけならよい（2026-11-20 ユーザーの指摘で「役が変わる」の禁止を消した）。
例の手は tools/machi_sheet/machi3.py の waits で待ちを確かめた。
出力: まじゃすこ素材/x/naki/naki-matome.png（1588×2246）
実行: python tools/naki_sheet.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
T = "file:///" + os.path.join(ROOT, "assets", "tiles").replace("\\", "/")
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "naki")
LV = {1: ("初心者", "#E75620"), 2: ("中級者", "#4261AA"), 3: ("上級者", "#6B4FA0")}      # 段階の色。中級者は青（緑はまじゃすこの地の色＝段階に関係ない所に使う。2026-11-20 ユーザーの指定）


def lv(n): return f'<i class="lv" style="background:{LV[n][1]}">{LV[n][0][0]}</i>'      # 頭文字1字（初・中・上）。色で段階を見せる（2026-11-20 ユーザーの指定）


def t(code, w=24, yoko=False, mark="", hl=False):
    """牌1枚。yoko＝横向き（鳴いた牌）・mark＝重ねる印（✕・○）・hl＝ツモった牌の枠"""
    h = round(w * 1.33)
    src = f"{T}/{code}{'-yoko' if yoko else ''}.svg"
    # 縦の絵は viewBox 62×89、横の絵は 82×69。縦は高さ h（89 の分）なので、横は幅を h×82/89 にすると同じ大きさになる
    # （幅を h にしていたら横向きの牌だけ約8%大きく見えた。2026-11-20 ユーザーの指摘）
    img = f'<img src="{src}" style="{f"width:{h * 82 / 89:.1f}px" if yoko else f"height:{h}px"}">'
    cls = "tl" + (" hl" if hl else "")
    cap = '<em class="cap">ツモ</em>' if hl else ""
    return f'<span class="{cls}">{cap}{img}{f"<i class=m{1 if mark == chr(10005) else 2}>{mark}</i>" if mark else ""}</span>'


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
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 15px 28px 20px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 8px 16px; margin-bottom: 9px; }}
header h1 {{ font-size: 28px; font-weight: 900; line-height: 1.1; }}
header h1 em {{ font-style: normal; display: inline-block; background: #E75620; border-radius: 6px; font-size: 15px; padding: 1px 8px; margin-left: 8px; vertical-align: 5px; }}
header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; }}
.legend {{ font-size: 11.5px; font-weight: 800; line-height: 1.8; text-align: right; white-space: nowrap; }}
.legend .lv {{ border: 1.5px solid #fff; margin: 0 2px 0 6px; vertical-align: -3px; }}
{LOGO_CSS}
i.lv {{ font-style: normal; display: inline-flex; align-items: center; justify-content: center; width: 17px; height: 17px; color: #fff; font-size: 11px; font-weight: 900; border-radius: 4px; padding: 0; line-height: 1; margin-right: 5px; vertical-align: 1px; white-space: nowrap; }}
section {{ background: #fff; border: 2px solid #177083; border-radius: 6px; margin-bottom: 5px; overflow: hidden; }}
section > h2 .lv {{ border: 1.5px solid #fff; }}
section > h2 {{ background: #177083; color: #fff; font-size: 15.5px; font-weight: 900; padding: 4px 12px; display: flex; align-items: baseline; gap: 8px; }}
section > h2 small {{ font-size: 11px; font-weight: 700; opacity: .92; margin-left: auto; }}
.in {{ padding: 6px 12px 7px; }}
.hd {{ display: inline-flex; align-items: flex-end; gap: 1px; flex: none; }}
.hd img {{ display: block; }}
.gap {{ width: 8px; }}
.stk {{ display: inline-flex; flex-direction: column; gap: 1px; }}
.tl {{ position: relative; display: inline-block; }}
.tl.hl img {{ outline: 2px solid #F2B08F; outline-offset: 1px; border-radius: 3px; }}
.tl i {{ position: absolute; top: -9px; right: -13px; width: 19px; height: 19px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-style: normal; font-size: 12px; font-weight: 900; color: #fff !important; border: 1.5px solid #fff; }}
.tl i.m1 {{ background: #C92F42; }} .tl i.m2 {{ background: #177083; }}
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
.grp div {{ border-radius: 6px; padding: 4px 7px; font-size: 10.5px; font-weight: 700; line-height: 1.5; }} 
.grp div b {{ display: inline; font-size: 12.5px; font-weight: 900; }} .grp div p {{ margin-top: 2px; }}
.g1 {{ background: #E4F3EC; }} .g1 b {{ color: #177083; }}
.g2 {{ background: #EAF0FB; }} .g2 b {{ color: #4261AA; }}
.g3 {{ background: #FFF1E8; }} .g3 b {{ color: #E75620; }}
.g4 {{ background: #FBE9EC; }} .g4 b {{ color: #C92F42; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
h3 {{ font-size: 14px; font-weight: 900; margin-bottom: 3px; }}
h3.ok {{ color: #177083; }} h3.ng {{ color: #C92F42; }}
ul.li {{ list-style: none; }}
ul.li li {{ font-size: 12px; font-weight: 700; line-height: 1.45; padding: 4px 0; white-space: nowrap; border-top: 1px solid #E3ECEA; }}
ul.li li:first-child {{ border-top: 0; }}
ul.li li b {{ font-weight: 900; }}
.lead {{ font-size: 12px; font-weight: 800; line-height: 1.5; margin-bottom: 6px; background: #EEF6F3; border-left: 4px solid #177083; padding: 4px 8px; }}
.lead b {{ color: #E75620; }}
/* 喰い替え */
.kk {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }}
.kkc {{ border: 1.5px solid #D5E2DF; border-radius: 6px; padding: 6px 8px; }}
.kkc > b {{ font-size: 14px; font-weight: 900; color: #C92F42; display: block; margin-bottom: 4px; }}
.kkr {{ display: flex; align-items: center; gap: 6px; padding: 7px 0; border-top: 1px dashed #D5E2DF; }}
.kkr:first-of-type {{ border-top: 0; }}
.kkr em {{ font-style: normal; font-weight: 900; color: #8A9A97; margin-right: 4px; }}
.kkr span {{ font-size: 10.5px; font-weight: 700; line-height: 1.4; color: #33403D; }}
/* リーチ後のカン */
.rk {{ display: grid; grid-template-columns: 98px auto 1fr; align-items: center; gap: 8px; padding: 6px 0; border-top: 1px solid #E3ECEA; }}
.rk:first-child {{ border-top: 0; }}
.rk > b {{ font-size: 12.5px; font-weight: 900; text-align: center; border-radius: 5px; padding: 3px 0; color: #fff; }}
.rk > b.o {{ background: #177083; }} .rk > b.x {{ background: #C92F42; }}
.rk > span {{ font-size: 11px; font-weight: 700; line-height: 1.45; }}
.rk > span strong {{ font-weight: 900; display: block; font-size: 12px; }}
.k5 {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 7px; }}
.kc {{ border: 1.5px solid #D5E2DF; border-radius: 6px; padding: 5px 6px; display: flex; flex-direction: column; gap: 3px; align-items: flex-start; }}
.kc > b {{ font-size: 15px; font-weight: 900; }}
.kc > span {{ font-size: 10px; font-weight: 700; color: #4F5C5A; }}
.two > section {{ margin-bottom: 7px; }}
.three {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 10px; }}
.kk4 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3px 12px; margin-top: 3px; }}
.kk4 .kkr {{ border-top: 0; padding: 3px 0 1px; }}
.kk4 .kkr span b {{ color: #C92F42; margin-right: 4px; }}
table.ok {{ table-layout: fixed; }}
.tl {{ vertical-align: bottom; }}
.tl em.cap {{ position: absolute; left: 50%; top: -13px; transform: translateX(-50%); font-style: normal; font-size: 9px; font-weight: 800; color: #C2622F; line-height: 1.2; white-space: nowrap; }}
.rk {{ padding-top: 10px !important; padding-bottom: 0 !important; }}
.rk > span.rtx {{ display: flex; flex-direction: column; align-items: flex-start; gap: 3px; }} .rk > span.rtx > span {{ font-size: 11.5px; }}
i.wt {{ font-style: normal; font-size: 10px; font-weight: 900; color: #5E6B69; display: inline-flex; align-items: center; gap: 4px; }}
.kk4 .kkr span b.okb {{ color: #177083; }}
.judge {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; align-items: start; }}
table.jt {{ width: 100%; border-collapse: collapse; }}
table.jt th {{ font-size: 13px; font-weight: 900; color: #fff; padding: 3px 8px; text-align: left; }}
table.jt th.o {{ background: #177083; }} table.jt th.x {{ background: #C92F42; }}
table.jt td {{ font-size: 11.5px; font-weight: 800; padding: 1px 6px; border-bottom: 1px solid #E3ECEA; white-space: nowrap; }}
table.jt td.why {{ font-size: 10px; font-weight: 700; color: #5E6B69; text-align: right; }}
.kc > span {{ line-height: 1.4; }}
.kc {{ position: relative; }}
.kt {{ display: flex; align-items: flex-start; gap: 4px; width: 100%; height: 42px; align-items: flex-end !important; }}
.kt .lv {{ margin-bottom: 5px; }}
.kn {{ background: #EEF6F3; border: 1.5px solid #9CC9C0; border-radius: 6px; padding: 6px 9px; font-size: 11px; font-weight: 700; line-height: 1.5; }}
.kn b {{ font-size: 13.5px; font-weight: 900; color: #C92F42; display: block; margin-bottom: 2px; }}
.kn em {{ font-style: normal; font-weight: 900; color: #E75620; }}
.kt > b ruby {{ ruby-align: start; }} .kt > b ruby rt {{ font-size: 9.5px; font-weight: 800; color: #177083; ruby-align: start; text-align: left; }}
.kt > b {{ font-size: 18px; font-weight: 900; white-space: nowrap; line-height: 1.2; padding-bottom: 2px; }}
.kt > .hd {{ margin-left: auto; align-self: flex-end; }}
.kc > span {{ font-size: 11.5px !important; line-height: 1.5 !important; color: #1F2A28 !important; font-weight: 800 !important; }}
.kc u {{ text-decoration: none; font-size: 10.5px; font-weight: 900; border-radius: 4px; padding: 0 6px; margin-top: 2px; }}
.kc u.rx {{ background: #FBE9EC; color: #C92F42; }} .kc u.ro {{ background: #E4F3EC; color: #177083; }}
/* 段階の色は札と細い線だけ（全面に色を敷くとカラフルすぎた。2026-11-20 ユーザーの指摘）。地は白、仕切りははっきりした線 */
.c1, .c2, .c3 {{ background: #fff !important; border: 1.5px solid #C5D6D2 !important; border-left-width: 5px !important; }}
.c1 {{ border-left-color: #E75620 !important; }} .c2 {{ border-left-color: #4261AA !important; }} .c3 {{ border-left-color: #6B4FA0 !important; }}
.c1 b, .c2 b, .c3 b {{ color: #1F2A28; }}
.grp > div {{ border-radius: 5px; }}
tr.c1 td, tr.c2 td, tr.c3 td {{ background: #fff; }}
table.jt td {{ border-bottom: 1.5px solid #D5E2DF !important; }}
table.jt {{ border: 1.5px solid #C5D6D2; }}
section.s1, section.s2 {{ border-color: #177083; background: #fff; }}
section {{ border-width: 2.5px !important; }}
.kk4 {{ border-top: 0; }}
.kk4 .kkr:nth-child(n+3) {{ border-top: 1.5px dashed #C5D6D2 !important; }}
.rk {{ border-top: 1.5px solid #D5E2DF !important; }} .rk:first-child {{ border-top: 0 !important; }}
.fg {{ display: inline-flex; flex-direction: column; align-items: center; gap: 2px; }}
i.tg {{ font-style: normal; font-size: 9.5px; font-weight: 900; color: #fff; background: #5E6B69; border-radius: 3px; padding: 0 5px; line-height: 1.5; white-space: nowrap; }}
i.tg.tng {{ background: #C92F42; }} i.tg.tok {{ background: #177083; }}
.kkr .fg em, .kkr > em {{ align-self: flex-end; margin-bottom: 8px; }}
.kkr span.cap2 {{ font-size: 10.5px; font-weight: 700; line-height: 1.45; color: #33403D; display: flex; flex-direction: column; }}
.kkr span.cap2 b {{ font-size: 12px; color: #C92F42; }} .kkr span.cap2 b.okb {{ color: #177083; }}
.kkr .fg .tl i {{ display: none; }}
footer {{ position: absolute; left: 28px; right: 28px; bottom: 12px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }}
footer b {{ color: #177083; font-weight: 900; }}
"""


def page(no, sub, body):
    legend = f'<div class="legend">覚える段階<br>{lv(1)}初心者 {lv(2)}中級者 {lv(3)}上級者</div>'
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700;900&display=block" rel="stylesheet">
<style>{CSS}</style></head><body>
<header><h1>鳴き（副露）のまとめ<small>{sub}</small></h1>{legend}{logo_html()}</header>
{body}
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>牌のイラストは まじゃすこ オリジナル</span></footer>
</body></html>"""


def body():
    import importlib.util
    spec = importlib.util.spec_from_file_location("machi3", os.path.join(HERE, "machi_sheet", "machi3.py"))
    sys.path.insert(0, os.path.join(HERE, "machi_sheet")); M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
    kinds = f"""<p class="lead"><b>鳴き（副露・フーロ）</b>＝ほかの人が捨てた牌に<b>「チー」「ポン」「カン」と声をかけて牌をもらい</b>、面子（3枚1組／4枚1組）をそろえること。<br>もらった牌は横向きにして、手牌の右端に表向きで並べる（晒す）。<b>だれから牌をもらったか</b>が、ゲームの進行で大事になる</p>
<div class="k5">
  <div class="kc c1"><div class="kt">{lv(1)}<b>チー</b>{hand("y:m6 m4 m5", 20)}</div><span>つながった3枚（順子）を作る<br>上家（左の人）からだけ鳴ける</span><u class="rx">リーチ ×</u></div>
  <div class="kc c1"><div class="kt">{lv(1)}<b>ポン</b>{hand("z6 y:z6 z6", 20)}</div><span>同じ牌3枚（刻子）を作る<br>だれからでも鳴ける</span><u class="rx">リーチ ×</u></div>
  <div class="kc c1"><div class="kt">{lv(1)}<b><ruby>暗槓<rt>アンカン</rt></ruby></b>{hand("d z1 z1 d", 20)}</div><span>自分で同じ牌4枚（槓子）をそろえる<br>人からもらわない（＝鳴きではない）</span><u class="ro">リーチ ○</u></div>
  <div class="kc c2"><div class="kt">{lv(2)}<b><ruby>大明槓<rt>ダイミンカン</rt></ruby></b>{hand("z2 z2 z2 y:z2", 20)}</div><span>自分で同じ牌3枚をそろえる<br>その後、人が捨てた4枚目を鳴く</span><u class="rx">リーチ ×</u></div>
  <div class="kc c1"><div class="kt">{lv(1)}<b><ruby>加槓<rt>カカン</rt></ruby></b>{hand("z7 k:z7 z7", 20)}</div><span>まずポンをする<br>その後、自分で引いた4枚目を足す</span><u class="rx">リーチ ×</u></div>
  <div class="kn"><b>鳴いたら、リーチできない</b><p><em>暗槓は鳴きではない</em>ので、リーチできる</p>
  <p>横向き＝もらった牌<br>（左＝上家・真ん中＝対面・右＝下家）</p><p>カンしたら、カンドラをめくり<br>嶺上牌をツモる</p></div>
</div>"""
    riichi = f"""<table class="ok"><colgroup><col><col><col><col><col></colgroup>
<tr><th>チー</th><th>ポン</th><th class="g">暗槓</th><th>大明槓</th><th>加槓</th></tr>
<tr><td class="x">×</td><td class="x">×</td><td class="o">○</td><td class="x">×</td><td class="x">×</td></tr>
</table>
<p class="tip">暗槓は<b>鳴きではない</b>ので、リーチできる</p>"""
    yaku = f"""<div class="grp">
<div class="c1">{lv(1)}<b>役牌のポン</b><p>ポンだけで役がつく</p></div>
<div class="c1">{lv(1)}<b>二〜八だけの鳴き</b><p>喰いタンが残る</p></div>
<div class="c2">{lv(2)}<b>一・九・字牌の鳴き</b><p>役なしになりやすい</p></div>
<div class="c2">{lv(2)}<b>大明槓</b><p>手が進まずドラが増える</p></div>
</div>"""
    # 鳴いた形と切る牌に、それぞれ札を付ける（矢印の右が切る牌だと伝わらないため。2026-11-20 ユーザーの指摘）
    def kk(naki_lab, naki, cut, ok, kind, tx):
        cls = "okb" if ok else ""
        return (f'<div class="kkr"><span class="fg"><i class="tg">{naki_lab}</i>{hand(naki, 23)}</span><em>→</em>'
                f'<span class="fg"><i class="tg {"tok" if ok else "tng"}">{"○ 切ってよい" if ok else "× 切れない"}</i>{hand(cut, 23)}</span>'
                f'<span class="cap2"><b class="{cls}">{kind}</b>{tx}</span></div>')
    kuikae = f"""<div class="kk4">
{kk("六萬をチー", "y:m6 m4 m5", "x:m6", False, "同じ牌", "鳴いた六萬と同じ牌")}
{kk("赤五筒をポン", "p5 y:p5r p5", "x:p5", False, "同じ牌", "赤でも黒でも同じ五筒")}
{kk("六萬をチー", "y:m6 m4 m5", "x:m3", False, "スジ", "三萬でも三四五萬が作れる")}
{kk("六萬をチー", "y:m6 m4 m5", "o:m9", True, "切れる", "九萬では面子が作れない")}
</div>"""
    W = 20
    base = f'{seq("123", "m")} {seq("789", "s")}'
    rk = [
        ("o", "○ できる", f'{seq("123", "m")} {seq("456", "p")} {seq("6789", "s")} z1 z1 z1', "z1", "東をカンしても、六・九索待ちのまま"),
        ("x", "× 待ちが変わる", f'{base} z1 z1 {seq("2223", "p")} p4', "p2", "二筒をカンすると、東待ちが消える"),
        ("x", "× 面子が変わる", f'{base} {seq("1112444", "p")}', "p4", "四筒をカンすると、三筒のカンチャン待ちがなくなる"),
    ]
    rkh = ""
    for k, lab, h, tsumo, tx in rk:
        ws = [c for c, _ in M.waits(h.split(), 4, 1)]
        rkh += (f'<div class="rk"><b class="{k}">{lab}</b>{hand(h + " | t:" + tsumo, W)}'
                f'<span class="rtx"><i class="wt">待ち{hand(" ".join(ws), 14)}</i><span>{tx}</span></span></div>')
    rows_o = [(1, "役牌の対子がある", "ポンで役がつく"), (1, "あと1〜2回の鳴きでテンパイ", "役もあるなら"), (1, "鳴いても満貫以上ある", "早くアガり切る"),
              (2, "終盤・他家の親を流したい", "早さを優先"), (2, "オーラスでトップを守りたい", "安くても終わらせる"), (2, "他家の一発を消したい", ""), (2, "海底（最後のツモ）をずらしたい", ""),
              (2, "同巡のフリテンを解消したい", ""), (3, "ツモ番を飛ばす・チーさせない", ""), (3, "安全牌に困る人にツモ番を回す", ""), (3, "親のテンパイのためにツモ番を回す", "")]
    rows_x = [(1, "鳴くと役が無くなる", "アガれない"), (1, "リーチの方が高い・待ちがいい", ""), (1, "鳴くと点数が下がりすぎる", "食い下がり"),
              (1, "他家のリーチから降りたい", ""), (1, "狙いを読まれたくない", "晒した牌で読まれる")]
    tr = lambda rows: "".join(f'<tr class="c{n}"><td>{lv(n)}{a}</td></tr>' for n, a, b in rows)
    naku = f"""<div class="judge">
<table class="jt"><tr><th class="o">○ 鳴く</th></tr>{tr(rows_o[:5])}</table>
<table class="jt"><tr><th class="o">○ 鳴く（駆け引き）</th></tr>{tr(rows_o[5:])}</table>
<table class="jt"><tr><th class="x">× 鳴かない</th></tr>{tr(rows_x)}</table>
</div>"""
    return f"""
<section><h2>鳴きって、なに？<small>チー・ポン・カンの3種類（カンは3つ）</small></h2><div class="in">{kinds}</div></section>
<section><h2>鳴いても、役は残る？<small>役が無いとアガれない</small></h2><div class="in">{yaku}</div></section>
<section><h2>{lv(1)}喰い替えは禁止<small>鳴いた形で同じ面子を作れる牌は切れない</small></h2><div class="in">{kuikae}</div></section>
<section><h2>{lv(2)}リーチのあとのカン<small>面子の組み方が変わらない暗槓だけ（役が変わるのはよい）</small></h2><div class="in">{rkh}</div></section>
<section><h2>鳴く？　鳴かない？　かんたん判断表<small>鳴くと早くなるが、点数が下がり役も消えやすい</small></h2><div class="in">{naku}</div></section>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        for no, html in ((0, page(0, "チー・ポン・カン／リーチ／役／喰い替え／リーチ後のカン", body())),):
            hp = os.path.join(OUT, "_p.html"); io.open(hp, "w", encoding="utf-8").write(html)
            pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=2)
            pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
            h = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - Math.max(...[...document.querySelectorAll('section')].map(s => s.getBoundingClientRect().bottom))")
            print(no, "余白", round(h)); pg.screenshot(path=os.path.join(OUT, "naki-matome.png")); pg.close(); os.remove(hp)
        b.close()


if __name__ == "__main__":
    render()
