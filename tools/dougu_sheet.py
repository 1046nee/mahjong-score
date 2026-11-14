# -*- coding: utf-8 -*-
"""麻雀の道具図鑑の1枚の表（2026-11-14〜・blog-mahjong-dougu の目次の下）。牌の種類・点棒・アイテムを名前と読み方つきで1枚に。
出力（assets/hai/）: mahjong-dougu-zukan.png（高画質・幅2481）／ -web.png（記事用・幅1588）／ .pdf（中身の高さの紙）。作ったら python tools/make_webp.py
実行: python tools/dougu_sheet.py
決めごと（2026-11-14 ユーザーの指定）: カテゴリーで色をそろえる（牌＝緑・点棒＝青・アイテム＝紫）／数牌・字牌・花牌・白ポッチと金青は列の幅をそろえた1つの表／
  赤牌は数牌の行の最後の列／花牌は季節牌（春夏秋冬）と草木牌（梅蘭菊竹）に分ける／白い500点棒は100点棒5本を輪ゴムで束ねたもの／
  25,000点持ちは 10,000×1・5,000×2・1,000×4・500×1・100×5／黒棒の別名は「借金棒」（CLAUDE.md の例外）／点棒とアイテムの表は行の高さをそろえる（30px）／
  説明は1行に収める。表の中の牌の絵と名前・見出しと下のマスの位置は、作り直したら目で確かめる
"""
import io, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
ROOT = os.path.dirname(HERE)
import hai_sheets as H, table_art as A
from sheet_logo import LOGO_CSS, logo_html
T = os.path.join(ROOT, "assets", "tiles"); URL = "file:///" + T.replace("\\", "/").lstrip("/")
OUT = os.path.join(ROOT, "assets", "hai"); NAME = "mahjong-dougu-zukan"
TEAL, BLUE, ORANGE, INK, GOLD, AO = "#177083", "#4261AA", "#E25A1C", "#1F2A28", "#C9A227", "#2F62C8"

def img(name, w): return f'<img src="{URL}/{name}.svg" style="width:{w}px">'
def recolor(code, col, w):
    s = open(os.path.join(T, code + ".svg")).read().replace("#E25A1C", col)
    return f'<i class="svg" style="width:{w}px">{s}</i>'
def stick(fn, v, L=118):    # 点棒（上下の厚みを入れた大きさで絵を切る＝セルの真ん中に来る）
    return f'<svg class="stk" viewBox="-1 -1 {L + 2} 19" style="width:{L}px">{fn(v, 0, 0, L=L, H=15)}</svg>'
def cap(pic, a, b): return f'<div class="cap">{pic}<b>{a}</b><span>{b}</span></div>'

def tenbako():   # 点箱（点棒入れ）。引き出しにカラーの点棒が並ぶ
    g = '<rect x="4" y="18" width="112" height="44" rx="6" fill="#2B3634"/><rect x="4" y="12" width="112" height="44" rx="6" fill="#3E4A48"/>'
    for i, c in enumerate(("#E02424", "#F5C400", "#1F6FD1", "#16A05A", "#F2F2EE")):
        g += f'<rect x="{12 + i * 20.5}" y="18" width="17" height="32" rx="3" fill="#1C2423"/>'
        for k in range(3): g += f'<rect x="{14 + i * 20.5}" y="{21 + k * 9}" width="13" height="6" rx="3" fill="{c}"/>'
    return f'<svg viewBox="0 0 120 64" style="width:84px">{g}</svg>'

# ---- 数牌 ----
SUITS = [("m", "萬子", "マンズ", ORANGE), ("p", "筒子", "ピンズ", BLUE), ("s", "索子", "ソーズ", TEAL)]
def num_cell(s, i):
    return '<td>' + cap(img(f"{s}{i}", 38), f"{H.KANSU[i - 1]}{H.NAMES[s]}", f"{H.YOMI_NUM[i - 1]}{H.YOMI_SUIT[s]}") + "</td>"
shu = "".join(f'<tr><th class="rh" style="background:{c}">{n}<small>{y}</small></th>' + "".join(num_cell(s, i) for i in range(1, 10))
              + f'<td class="aka">' + cap(img(f"{s}5r", 38), f"赤五{H.NAMES[s]}", f"アカウー{H.YOMI_SUIT[s]}") + "</td></tr>" for s, n, y, c in SUITS)
def zrow(ids): return "".join(f'<td>{cap(img(f"z{i}", 38), *H.Z[i])}</td>' for i in ids)

# ---- 点棒 ----
TB = [(10000, "10,000点棒", "イチマンテンボウ", "1"), (5000, "5,000点棒", "ゴセンテンボウ", "2"), (1000, "1,000点棒", "センテンボウ", "4"),
      (500, "500点棒", "ゴヒャクテンボウ", "1"), (100, "100点棒", "ヒャクテンボウ", "5")]

CSS = f"""svg.stk {{ display: block; margin: 0 auto; }}
.svg {{ display: inline-block; font-style: normal; vertical-align: bottom; }} .svg svg {{ width: 100%; height: auto; display: block; }}
.bar {{ display: flex; align-items: center; gap: 10px; color: #fff; background: {INK}; border-radius: 6px 6px 0 0; padding: 3px 12px; font-size: 17px; font-weight: 900; margin-top: 10px; }}
.bar small {{ font-size: 11.5px; font-weight: 700; color: #CFE0DC; }} .bar.tl {{ background: {TEAL}; border-radius: 6px; }}
.sub {{ display: flex; align-items: center; gap: 8px; margin: 7px 0 3px; font-size: 11.5px; font-weight: 800; }}
.sub em {{ font-style: normal; font-size: 14px; font-weight: 900; color: #fff; background: {TEAL}; border-radius: 4px; padding: 0 9px; line-height: 23px; }} .sub .k {{ color: {TEAL}; }}
th {{ background: {TEAL}; color: #fff; font-size: 12.5px; font-weight: 900; padding: 3px 0; border-left: 1px solid rgba(255,255,255,.35); }}
th.ak {{ background: {ORANGE}; }}
td {{ text-align: center; border: 1px solid #8FA29D; padding: 3px 1px; line-height: 1.2; vertical-align: middle; }}
th.rh {{ font-size: 14px; line-height: 1.15; border-top: 1px solid rgba(255,255,255,.35); }} th.rh small {{ display: block; font-size: 10px; font-weight: 700; opacity: .92; }}
th.rh.dk {{ background: #E9EFEE; color: {INK}; border: 1px solid #8FA29D; font-size: 12.5px; }} th.rh.dk small {{ color: {TEAL}; font-size: 9.5px; }}
td.aka {{ background: #FDEBE3; }}
.cap b {{ display: block; font-size: 11.5px; font-weight: 900; margin-top: 2px; white-space: nowrap; }} .cap span {{ display: block; font-size: 9.5px; font-weight: 800; color: #33403D; white-space: nowrap; letter-spacing: -.02em; }}
td.aka .cap span {{ color: #B23A0E; }}
td.pic {{ padding: 4px 3px; white-space: nowrap; }} .g4 {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 2px 0; }} .g2 {{ display: flex; justify-content: center; gap: 10px; }}
td.tx {{ text-align: left; font-size: 11px; font-weight: 700; padding: 4px 7px; color: #2B3634; line-height: 1.4; }}
td em {{ font-style: normal; font-size: 9.5px; font-weight: 700; color: #8A9A97; line-height: 1.25; display: block; }}
td.n {{ font-size: 17px; font-weight: 900; color: {INK}; }} td.n i {{ font-style: normal; font-size: 10px; margin-left: 1px; }}
th small.yb {{ display: block; font-size: 10px; font-weight: 700; color: #DDF0EC; line-height: 1.1; }} th small.y {{ font-size: 10px; font-weight: 700; margin-left: 4px; color: #DDF0EC; }} .ot td.tx {{ vertical-align: top; }}
td.sp {{ border: 1px solid #8FA29D; padding: 0; vertical-align: top; }} .sph {{ background: #E9EFEE; padding: 2px 0; text-align: center; border-bottom: 1px solid #8FA29D; }} .sph b {{ font-size: 12.5px; font-weight: 900; }} .sph span {{ font-size: 9.5px; font-weight: 700; color: #177083; margin-left: 4px; }}
.spb {{ display: flex; align-items: center; gap: 6px; padding: 4px 6px; }} .spt {{ display: flex; gap: 4px; flex: none; }} .spb p {{ font-size: 10.5px; font-weight: 700; line-height: 1.4; text-align: left; }}
td.chip {{ text-align: left; padding: 4px 6px; }} td.chip img {{ margin-right: 3px; }} td.chip p {{ font-size: 10.5px; font-weight: 700; margin-top: 2px; line-height: 1.35; }}
.k {{ color: #177083; }} td.tx b.k {{ display: inline; font-size: 11px; margin: 0; }}
.two {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10px; }}
.zt {{ display: grid; grid-template-columns: 4fr 3fr; gap: 10px; }} .zt p {{ font-size: 10.5px; font-weight: 700; margin-top: 3px; color: #33403D; }}
.note {{ font-size: 10.5px; font-weight: 700; margin-top: 4px; line-height: 1.5; }} .note b {{ color: #B23A0E; }}
.tip {{ margin-top: 5px; border: 1.5px dashed {TEAL}; border-radius: 6px; padding: 5px 8px; font-size: 10.5px; font-weight: 700; line-height: 1.5; background: #F4FAF9; }} .tip b {{ color: {TEAL}; }}
"""
C_HAI, C_TEN, C_ITEM = "#177083", "#4261AA", "#6A4BB0"     # 牌＝緑・点棒とチップ＝青・アイテム＝紫

# ---- 牌 ----
def hdr(col): return f'style="background:{col}"'
shu_head2 = f'<tr><th {hdr(C_HAI)}>種類</th>' + "".join(f'<th>{i}</th>' for i in range(1, 10)) + '<th class="ak">赤</th></tr>'
SEASON = [("春", "ハル"), ("夏", "ナツ"), ("秋", "アキ"), ("冬", "フユ")]; FLOWER = [("梅", "ウメ"), ("蘭", "ラン"), ("菊", "キク"), ("竹", "タケ")]
hana2 = ("".join(f'<td>{cap(img(f"f{i + 1}", 38), a, b)}</td>' for i, (a, b) in enumerate(SEASON))
         + "".join(f'<td>{cap(img(f"f{i + 5}", 38), a, b)}</td>' for i, (a, b) in enumerate(FLOWER)))
KIN = [(recolor("p5r", GOLD, 38), "金五筒", "キンウーピン"), (recolor("s5r", GOLD, 38), "金五索", "キンウーソー")]
AOP = [(recolor("m5r", AO, 38), "青五萬", "アオウーマン"), (recolor("p5r", AO, 38), "青五筒", "アオウーピン")]
kinao = "".join(f'<td class="{c}">{cap(p, a, b)}</td>' for (p, a, b), c in zip(KIN + AOP, ("kin", "kin", "ao", "ao")))
hai_html = f"""
<div class="bar" style="margin-top:0;background:{C_HAI}">牌<small>ハイ　数牌・字牌・その他の牌</small></div>
<table class="hai"><colgroup><col style="width:58px"></colgroup>
<thead>{shu_head2}</thead><tbody>{shu}</tbody>
<tbody><tr class="gh"><th {hdr(C_HAI)}>種類</th><th colspan="4">風牌（カゼハイ）</th><th colspan="3">三元牌（サンゲンパイ）</th><th colspan="3">役になるとき</th></tr>
<tr><th class="rh" style="background:#5E6B69">字牌<small>ジハイ</small></th>{zrow(range(1, 5))}{zrow(range(5, 8))}<td class="tx" colspan="3"><b class="k">風牌</b>…場風・自風の刻子で役<br><b class="k">三元牌</b>…刻子で役。3つで大三元</td></tr></tbody>
<tbody><tr class="gh"><th {hdr(C_HAI)}>種類</th><th colspan="4">季節牌（春夏秋冬）</th><th colspan="4">草木牌（梅蘭菊竹）</th><th colspan="2">使い方</th></tr>
<tr><th class="rh dk">花牌<small>ハナハイ</small></th>{hana2}<td class="tx" colspan="2">引いたら抜いて1枚引く。抜いた数だけドラ（三麻に多い）</td></tr></tbody>
<tbody><tr class="gh"><th {hdr(C_HAI)}>種類</th><th>白ポッチ</th><th colspan="2">使い方</th><th colspan="4">金牌（キンハイ）・青牌（アオハイ）</th><th colspan="3">使い方</th></tr>
<tr><th class="rh dk">印・色<small>のある牌</small></th><td>{cap(img("z5p", 38), "白ポッチ", "シロポッチ")}</td><td class="tx" colspan="2">リーチ後に引くと、どの牌にもなる決めが多い</td>{kinao}
<td class="tx" colspan="3">ドラやチップの対象。<b class="k">五の牌に多い</b>（八索などのことも）。何を何枚入れるかは場所ごと</td></tr></tbody></table>
<p class="note"><b>赤牌（アカハイ）</b>＝五の1枚を赤にした牌。持つだけでドラ1。1・9は<b class="k2">老頭牌</b>、2〜8は<b class="k2">中張牌</b>、1・9と字牌をあわせて<b class="k2">么九牌（ヤオチューハイ）</b></p>"""

# ---- 点棒とチップ ----
USE2 = {10000: "持ち点の大きなまとまり", 5000: "10,000点の半分", 1000: "いちばんよく動く。<b>リーチ棒</b>にも使う",
        500: "100点棒5本の代わり", 100: "端数の受け渡し。<b>積み棒</b>（本場の数）にも使う"}
def white3(v): return stick(A.tenbo, v, 120) if v != 500 else '<span class="b5">' + img("tb100x5", 30) + '<em>100点棒5本を<br>輪ゴムで束ねる</em></span>'
tb4_kuro = ('<tr><th class="rh dk">黒棒<small>クロボウ</small></th><td><em>白いセットには<br>ないことが多い</em></td><td>' + stick(A.tenbo_color, "tobi", 120)
            + '</td><td class="n">—</td><td class="tx">マイナスのとき借りる10,000点棒（<b>箱下</b>）。借金棒とも</td></tr>')
tb4 = "".join(f'<tr><th class="rh dk">{a}<small>{b}</small></th><td>{white3(v)}</td><td>{stick(A.tenbo_color, v, 120)}</td><td class="n">{n}<i>{"本" if n != "—" else ""}</i></td><td class="tx">{USE2[v]}</td></tr>' for v, a, b, n in TB)
CHIP = [("r", "赤"), ("b", "青"), ("g", "緑"), ("o", "オレンジ"), ("k", "黒")]
chip4 = "".join(f'<span class="ch">{img(f"chip-{c}", 26)}</span>' for c, n in CHIP)
ten_html = f"""
<div class="bar" style="background:{C_TEN}">点棒<small>テンボウ　持ち点を表す棒</small></div>
<table class="tight ten"><colgroup><col style="width:92px"><col style="width:136px"><col style="width:136px"><col style="width:62px"><col></colgroup>
<thead><tr><th>名前</th><th>白い点棒</th><th>カラーの点棒</th><th>25,000点</th><th>おもな使い方</th></tr></thead><tbody>{tb4}{tb4_kuro}</tbody></table>
<p class="note">25,000点の本数はよくある例（セットで違う）。<b>点棒の中身</b>＝全自動卓の点棒にはICチップや金属が入っていて、点箱に入れると卓が読みとる</p>"""

# ---- アイテム ----
IT2 = [("サイコロ", "", img("d3", 24) + img("d6", 24), "目の合計で山の取りはじめを決める（5・9＝自分　2・6・10＝下家　3・7・11＝対面　4・8・12＝上家）"),
       ("起家マーク", "チーチャマーク", img("chicha", 38) + img("chicha-ura", 38), "最初の親の前に置く。表が「東」、南場で裏の「南」にする"),
       ("焼き鳥マーク", "ヤキトリマーク", img("yakitori", 38) + img("yakitori-ura", 38), "最初に全員が卓に出し、アガった人は裏返せる。一度もアガれなかった人にペナルティを科す"),
       ("チップ", "", '<div class="chips">' + chip4.replace('width:26px', 'width:21px') + '</div>', "一発・裏ドラ・赤牌などで受けとる札。色や枚数の決めは場所ごと"),
       ("点箱", "テンバコ", tenbako().replace("width:84px", "width:46px"), "点棒をしまう引き出し。全自動卓は中の点棒を読んで持ち点を表示する"),
       ("牌寄せ", "ハイヨセ", img("haiyose", 36), "三麻で、空いた席の山を前に寄せて取りやすくする。卓に取り付ける自動の押出機と、手で押す板がある")]
it_rows = "".join(f'<tr><th class="rh dk">{a}' + (f'<small>{b}</small>' if b else "") + f'</th><td class="pic">{p}</td><td class="tx">{t}</td></tr>' for a, b, p, t in IT2)
item_html = f"""
<div class="bar" style="background:{C_ITEM}">アイテム<small>場を進める道具・卓まわり</small></div>
<table class="tight item"><colgroup><col style="width:92px"><col style="width:128px"><col></colgroup><tbody>{it_rows}</tbody></table>"""

EXTRA = f"""
.hai tbody + tbody tr.gh th {{ border-top: 2px solid #1F2A28; }} .hai th.rh, .ten th.rh, .item th.rh {{ border-right: 1.5px solid #5E716D; }}
.hai tr.gh th {{ background: {C_HAI}; }} 
.hai thead th:not(.ak) {{ background: {C_HAI}; }}
.ten th {{ background: {C_TEN}; }} .ten th.rh.dk {{ background: #EAF0FB; color: #1F2A28; }} .ten th.rh.dk small {{ color: {C_TEN}; }}
.item th.rh.dk {{ background: #F0ECF8; }} .item th.rh.dk small {{ color: {C_ITEM}; }}
td.kin {{ background: #FBF4DC; }} td.ao {{ background: #E9EEFB; }}
.tight td {{ padding: 1px 2px; }} .tight th.rh {{ padding: 1px 0; }} .tight td.tx {{ padding: 2px 7px; }}
.tight td em {{ display: inline-block; margin-left: 4px; vertical-align: middle; font-size: 9.5px; }} .tight td.n {{ font-size: 15px; }}
.chips {{ display: flex; justify-content: space-around; align-items: center; }} .ch {{ display: inline-flex; align-items: center; gap: 3px; }} .ch b {{ font-size: 10.5px; font-weight: 900; }}
.b5 {{ display: inline-flex; align-items: center; gap: 4px; }} .b5 em {{ margin: 0 !important; text-align: left; line-height: 1.2; }}
.ten tbody tr, .item tbody tr {{ height: 30px; }} .ten tbody td, .ten tbody th, .item tbody td, .item tbody th {{ padding-top: 0; padding-bottom: 0; }}
.item td.pic {{ padding: 0 2px; line-height: 0; }} .item td.pic svg, .item td.pic img {{ vertical-align: middle; }} .bar {{ margin-top: 8px; border-radius: 6px 6px 0 0; }} .note b.k2 {{ color: {C_HAI}; }}
"""
FOOT = '<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>対局後のスコアとチップの集計は、まじゃすこで自動に</span></footer>'
def page():
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">{H.FONT}<style>{H.CSS}{LOGO_CSS}{H.FIT_CSS}{CSS}{EXTRA}</style></head><body>'
            f'<header><h1>麻雀の道具 一覧表<small>牌の種類・点棒・アイテム（名前と読み方つき）</small></h1><div class="legend">基本の牌は<br>34種 × 4枚 ＝ <span>136枚</span></div>{logo_html()}</header>'
            f'{hai_html}{ten_html}{item_html}{FOOT}</body></html>')



def render():
    from playwright.sync_api import sync_playwright
    hp = os.path.join(OUT, "_" + NAME + ".html"); io.open(hp, "w", encoding="utf-8").write(page())
    u = "file:///" + hp.replace("\\", "/").lstrip("/")
    with sync_playwright() as p:
        b = p.chromium.launch()
        for suffix, scale in (("", 2481 / 794), ("-web", 2)):
            pg = b.new_page(viewport={"width": 794, "height": 1123}, device_scale_factor=scale)
            pg.goto(u); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
            h = pg.evaluate("Math.ceil(document.body.getBoundingClientRect().height)")
            pg.set_viewport_size({"width": 794, "height": h})
            pg.screenshot(path=os.path.join(OUT, NAME + suffix + ".png"), full_page=True); pg.close()
        pg = b.new_page(); pg.goto(u); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        hh = pg.evaluate("Math.ceil(document.body.getBoundingClientRect().height)")
        pg.pdf(path=os.path.join(OUT, NAME + ".pdf"), width="794px", height=f"{hh + 1}px", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
        b.close()
    os.remove(hp)
    from PIL import Image
    for suffix in ("", "-web"):
        f = os.path.join(OUT, NAME + suffix + ".png"); Image.open(f).save(f, optimize=True)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    render()
    for suffix in ("", "-web"):
        f = os.path.join(OUT, NAME + suffix + ".png"); print(os.path.basename(f), os.path.getsize(f) // 1024, "KB")
