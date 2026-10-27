# -*- coding: utf-8 -*-
"""SNS・サイト画像 v3（2026-10-27〜）。
LPの最初の画面と同じ世界観（淡い緑の地・本物の画面のスマホ・飛び出す数字のカード・✨）を、
PILではなくHTMLをブラウザ（Playwright）で描いて撮る。文字の折り返し・影・角丸がサイトと同じ品質になる。

出力（まじゃすこ素材/v3/。コミットしない）:
  feat-XX-*.png        IGフィード 1080×1350（機能を1つずつ紹介するシリーズ）
  feat-XX-*-story.png  ストーリーズ 1080×1920（同じ中身）
  howto-0..4.png       使い方カルーセル 1080×1350（表紙＋4ステップ）
  intro.png            はじめましての1枚 1080×1350
  ogp4.png             OGP 2100×1103（サイトでも使う → assets/ogp4.png にコピー）
  x-header-v3.png      Xヘッダー 1500×500
使い方: python tools/make_sns_v3.py [名前の一部]   （省略で全部）
"""
import io, os, re, sys, html
from PIL import Image
from playwright.sync_api import sync_playwright

MJ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(MJ, "まじゃすこ素材", "v3")
SCR = os.path.join(MJ, "assets", "screens")
os.makedirs(OUT, exist_ok=True)
FONT = "file:///C:/Windows/Fonts/NotoSansJP-VF.ttf"
if not os.path.exists(r"C:\Windows\Fonts\NotoSansJP-VF.ttf"):
    FONT = "file:///usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"

def furl(p):
    return "file:///" + p.replace("\\", "/")

def topcolor(name):
    im = Image.open(os.path.join(SCR, name)).convert("RGB")
    r, g, b = im.getpixel((im.width // 2, 2))
    return f"#{r:02X}{g:02X}{b:02X}"

# LPの最初の画面のイラスト（SVG）をそのまま使う
def hero_svg():
    s = io.open(os.path.join(MJ, "index.html"), encoding="utf-8").read()
    m = re.search(r'<div class="hero-illust" aria-hidden="true">\s*(<svg viewBox="0 0 380 220".*?</svg>)', s, re.S)
    assert m, "LPのイラストが見つからない"
    return m.group(1)

SPARK = '<svg class="spk" style="{st}" viewBox="0 0 20 20"><path d="M10 0 Q11.8 8.2 20 10 Q11.8 11.8 10 20 Q8.2 11.8 0 10 Q8.2 8.2 10 0Z" fill="{c}"/></svg>'
MEDAL = {1: ("#D4A017", "#3B2C00"), 2: ("#9AA5AD", "#1F2A28"), 3: ("#C97B3F", "#2E1A0A")}

CSS = """
@font-face { font-family: NJP; src: url('%s'); font-weight: 100 900; }
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: NJP, sans-serif; color: #1F2A28; }
.cv { position: relative; overflow: hidden; background: #E6F1EC; }
.glow { position: absolute; border-radius: 50%%; background: #D8EEE3; }
.spk { position: absolute; }
.tag { display: inline-flex; align-items: center; gap: 14px; }
.tag b { background: #177083; color: #fff; font-weight: 800; border-radius: 999px; padding: 8px 24px; font-size: 30px; }
.tag b.mp { background: #177083; } .tag b.cp { background: #4261AA; } .tag b.gm { background: #E75620; }
.tag span { font-size: 26px; font-weight: 700; color: #5B6866; }
h1 { font-weight: 900; color: #177083; letter-spacing: .01em; line-height: 1.28; }
.sub { font-weight: 600; color: #4F5C5A; line-height: 1.6; }
.dom { position: absolute; font-weight: 800; color: #7C8B88; letter-spacing: .04em; }
.ph { position: absolute; background: #1F2A28; border-radius: 58px; padding: 13px 13px 22px; box-shadow: 0 30px 60px rgba(16,40,36,.25); }
.ph .bar { height: 40px; border-radius: 46px 46px 0 0; display: flex; justify-content: center; align-items: center; }
.ph .bar i { width: 30%%; height: 22px; border-radius: 14px; background: #1F2A28; }
.ph .scr { overflow: hidden; border-radius: 0 0 44px 44px; background: #fff; }
.ph .scr img { display: block; width: 100%%; }
.chip { position: absolute; z-index: 3; display: flex; align-items: center; gap: 14px; background: #fff; border-radius: 26px; padding: 18px 28px;
  box-shadow: 0 14px 34px rgba(16,40,36,.18); white-space: nowrap; }
.chip .l { font-size: 28px; font-weight: 800; color: #4F5C5A; }
.chip .n { font-size: 46px; font-weight: 900; color: #1F2A28; line-height: 1; }
.chip .n.pos { color: #1A237E; } .chip .n.neg { color: #C62828; }
.chip .md { width: 46px; height: 46px; border-radius: 50%%; display: grid; place-items: center; font-size: 26px; font-weight: 900; }
.chip svg { display: block; }
""" % FONT

def phone(img, x, y, w, rot=0):
    """本物の画面（720×1558）をそのまま入れたスマホ。短い画面は下をアプリの地の色で埋めてiPhoneの縦横比にする"""
    im = Image.open(os.path.join(SCR, img))
    inner = w - 26
    scr_h = round(inner * 1558 / 720)  # いつもiPhoneの縦横比
    bg = "#F4F7F6" if im.height / im.width < 2 else "#fff"
    return (f'<div class="ph" style="left:{x}px;top:{y}px;width:{w}px;transform:rotate({rot}deg)">'
            f'<div class="bar" style="background:{topcolor(img)}"><i></i></div>'
            f'<div class="scr" style="height:{scr_h}px;background:{bg}"><img src="{furl(os.path.join(SCR, img))}"></div></div>'), 13 + 40 + scr_h + 22

def chip(c, x, y):
    """c = (ラベル, 数字, 種類)。種類: pos/neg/'' か、('medal', 順位) か ('line',)"""
    lab, num, kind = c
    inner = ""
    if isinstance(kind, tuple) and kind[0] == "medal":
        bgc, fg = MEDAL[kind[1]]
        inner += f'<span class="md" style="background:{bgc};color:{fg}">{kind[1]}</span>'
        kind = "pos" if num.startswith("+") else ("neg" if num.startswith("−") else "")
    if lab:
        inner += f'<span class="l">{html.escape(lab)}</span>'
    if kind == "line":
        inner += ('<svg width="120" height="48" viewBox="0 0 64 24"><polyline points="2,20 13,15 23,17 35,9 46,11 59,4" fill="none" stroke="#177083" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>'
                  '<circle cx="59" cy="4" r="3.6" fill="#E75620"/></svg>')
    elif num:
        inner += f'<span class="n {kind}">{html.escape(num)}</span>'
    return f'<div class="chip" style="left:{x}px;top:{y}px">{inner}</div>'

# ---- 機能を1つずつ紹介するシリーズ ----
# (番号, ファイル名, 区分, 見出し, ひとこと, 画面, 数字のカード[(左/右, 縦位置0〜1, カード)])
FEATS = [
 (1, "mypage-stats", "mp", "自分の成績が、\n1枚にまとまる。", "平均着順・トップ率・ラス回避まで自動で", "lp-mypage.jpg",
  [("l", .22, ("平均着順", "2.49", "")), ("r", .30, ("通算スコア", "+347.0", "pos")), ("l", .52, ("トップ率", "26%", ""))]),
 (2, "mypage-graph", "mp", "グラフの月を押すと、\nその月の試合が並ぶ。", "通算スコアの上がり下がりが一目で", "lp-mypage.jpg",
  [("r", .48, ("推移", "", "line")), ("l", .70, ("2026年10月", "+225.0", "pos")), ("r", .80, ("", "+123.8", ("medal", 1)))]),
 (3, "mypage-games", "mp", "打った日の結果が、\nずらりと残る。", "押せばその日の順位とスコアが開く", "lp-games.jpg",
  [("l", .24, ("10/10（土）", "+101.2", ("medal", 1))), ("r", .44, ("10/3（土）", "+123.8", ("medal", 1))), ("l", .66, ("9/22（火）", "+51.4", ("medal", 2)))]),
 (4, "mypage-h2h", "mp", "あの人には、\n勝ち越してる？", "同じ試合で上だった回数を、相手ごとに", "lp-myh2h.jpg",
  [("r", .22, ("合計", "728勝 721敗", "")), ("l", .52, ("vs 樹", "27勝 23敗", "pos")), ("r", .70, ("vs 拓海", "勝率 61%", "pos"))]),
 (5, "circle-rank", "cp", "仲間の通算順位が、\n表彰台で決まる。", "ゲームを集めるだけで自動で並ぶ", "lp-rank.jpg",
  [("r", .20, ("", "+1443.7", ("medal", 1))), ("l", .30, ("", "+1240.0", ("medal", 2))), ("r", .42, ("", "+1183.9", ("medal", 3)))]),
 (6, "circle-grid", "cp", "全員の成績を、\n1枚の表に。", "試合数・着順の回数・トップ率・ラス回避", "lp-grid.jpg",
  [("l", .40, ("トップ率", "30%", "")), ("r", .58, ("ラス回避", "80%", ""))]),
 (7, "circle-h2h", "cp", "総当たりで、\n相性が数字に出る。", "メンバーどうしの直接対決の勝ち負け", "lp-h2h.jpg",
  [("r", .26, ("大輝 vs 悠斗", "68-51", "pos")), ("l", .48, ("悠斗 vs 葵", "49-48", "pos")), ]),
 (8, "circle-member", "cp", "メンバーごとの\n成績と推移も。", "名前を押すと、その人の成績が開く", "lp-member.jpg",
  [("l", .24, ("通算", "4位", "")), ("r", .40, ("通算スコア", "+1159.2", "pos")), ("l", .68, ("推移", "", "line"))]),
 (9, "game-auto", "gm", "スコアは、\n入力するだけで自動計算。", "ウマ・オカ・順位までその場で", "howto-4.jpg",
  [("l", .22, ("", "+69.1", ("medal", 1))), ("r", .34, ("", "+64.0", ("medal", 2))), ("l", .46, ("", "−53.5", ("medal", 3)))]),
 (10, "game-share", "gm", "URLを送るだけで、\n全員のスマホに。", "見るだけの人は登録もアプリも不要", "howto-2.jpg",
  [("r", .70, ("LINEで送る", "", "")), ("l", .56, ("この試合のURL", "", ""))]),
]
KIND = {"mp": ("マイページ", "mp"), "cp": ("仲間ページ", "cp"), "gm": ("試合の記録", "gm")}

def feat_html(f, H):
    n, slug, k, title, sub, img, chips = f
    W = 1080
    story = H == 1920
    top = 250 if story else 92
    pw = 470 if story else 380
    py = 600 if story else 440
    px = (W - pw) // 2
    ph, phh = phone(img, px, py, pw)
    glow_r = 470 if story else 420
    cs = ""
    for side, fy, c in chips:
        y = py + int(phh * fy)
        if side == "l":
            cs += chip(c, 40, y)
        else:
            cs += chip(c, 0, y).replace('style="left:0px;', f'style="right:40px;')
    label, cls = KIND[k]
    t = html.escape(title).replace("\n", "<br>")
    return f"""<div class="cv" style="width:{W}px;height:{H}px">
  <div class="glow" style="left:{W//2-glow_r}px;top:{py+phh//2-glow_r}px;width:{glow_r*2}px;height:{glow_r*2}px"></div>
  {SPARK.format(st=f"left:{px+pw+40}px;top:{py-10}px;width:56px", c="#E75620")}
  {SPARK.format(st=f"left:{px-110}px;top:{py+phh-120}px;width:40px", c="#177083")}
  {SPARK.format(st=f"left:{px-70}px;top:{py+40}px;width:26px", c="#9FC3BD")}
  <div style="position:absolute;left:72px;right:72px;top:{top}px">
    <div class="tag"><b class="{cls}">{label}</b><span>まじゃすこの機能 {n}</span></div>
    <h1 style="font-size:{78 if story else 70}px;margin-top:26px">{t}</h1>
    <p class="sub" style="font-size:{34 if story else 32}px;margin-top:16px">{html.escape(sub)}</p>
  </div>
  {ph}{cs}
  <div class="dom" style="right:56px;top:{top+8}px;font-size:28px">majasco.jp</div>
</div>"""

HOWTO = [
 (1, "人数を選ぶだけで、\nすぐ始められる。", "会員登録もインストールも不要", "howto-1.jpg"),
 (2, "URLを送れば、\n全員のスマホで見られる。", "LINEで送るボタンもある", "howto-2.jpg"),
 (3, "点数を入れると、\n最後の1人は自動。", "下2桁の00は入力しなくていい", "howto-3.jpg"),
 (4, "順位とスコアが、\nその場で出る。", "画像にしてLINEに貼ることもできる", "howto-4.jpg"),
]

def howto_html(h):
    n, title, sub, img = h
    W, H = 1080, 1350
    pw, py = 380, 440
    px = (W - pw) // 2
    ph, phh = phone(img, px, py, pw)
    t = html.escape(title).replace("\n", "<br>")
    return f"""<div class="cv" style="width:{W}px;height:{H}px">
  <div class="glow" style="left:120px;top:{py+phh//2-420}px;width:840px;height:840px"></div>
  {SPARK.format(st=f"left:{px+pw+40}px;top:{py-10}px;width:56px", c="#E75620")}
  {SPARK.format(st=f"left:{px-110}px;top:{py+phh-120}px;width:40px", c="#177083")}
  <div style="position:absolute;left:72px;right:72px;top:92px">
    <div class="tag"><b class="gm" style="background:#177083">STEP {n}</b><span>1分でわかる使い方</span></div>
    <h1 style="font-size:70px;margin-top:26px">{t}</h1>
    <p class="sub" style="font-size:32px;margin-top:16px">{html.escape(sub)}</p>
  </div>
  {ph}
  <div class="dom" style="right:56px;top:100px;font-size:28px">majasco.jp</div>
</div>"""

def cover_html(kind):
    """howto-0（使い方の表紙）と intro（はじめまして）。LPのイラストを大きく"""
    W, H = 1080, 1350
    svg = hero_svg().replace('<svg ', '<svg style="width:1000px;height:auto;display:block" ', 1)
    if kind == "howto":
        tag, title, sub = "1分でわかる使い方", "麻雀のスコア記録、\n4ステップで。", "ブラウザだけで、会員登録もいらない"
    else:
        tag, title, sub = "はじめまして", "麻雀のスコア記録、\nまだ電卓と紙とペン？", "まじゃすこは、無料のスコア記録サービスです"
    t = html.escape(title).replace("\n", "<br>")
    return f"""<div class="cv" style="width:{W}px;height:{H}px">
  <div style="position:absolute;left:72px;right:72px;top:110px">
    <div class="tag"><b>{tag}</b></div>
    <h1 style="font-size:80px;margin-top:30px">{t}</h1>
    <p class="sub" style="font-size:34px;margin-top:20px">{sub}</p>
  </div>
  <div style="position:absolute;left:40px;top:560px">{svg}</div>
  <div style="position:absolute;left:72px;bottom:70px;display:flex;align-items:center;gap:22px">
    <img src="{furl(os.path.join(MJ, 'assets', 'favicon.png'))}" style="width:76px;height:76px;border-radius:18px">
    <div><div style="font-size:38px;font-weight:900">まじゃすこ</div><div style="font-size:28px;font-weight:800;color:#7C8B88">majasco.jp</div></div>
  </div>
  <div style="position:absolute;right:72px;bottom:82px;background:#E75620;color:#fff;font-weight:900;font-size:34px;border-radius:999px;padding:20px 44px">{'スワイプ ›' if kind=='howto' else '無料ではじめる'}</div>
</div>"""

def ogp_html():
    W, H = 2100, 1103
    svg = hero_svg().replace('<svg ', '<svg style="width:960px;height:auto;display:block" ', 1)
    return f"""<div class="cv" style="width:{W}px;height:{H}px">
  <div style="position:absolute;left:130px;top:250px;width:900px">
    <div style="display:flex;align-items:center;gap:26px">
      <img src="{furl(os.path.join(MJ, 'assets', 'favicon.png'))}" style="width:96px;height:96px;border-radius:22px">
      <div style="font-size:54px;font-weight:900">まじゃすこ</div>
    </div>
    <h1 style="font-size:90px;margin-top:44px;line-height:1.3;white-space:nowrap">麻雀のスコア記録、<br>まだ電卓と紙とペンで<br>やってますか？</h1>
    <p class="sub" style="font-size:42px;margin-top:30px">無料・アプリDL不要・会員登録不要</p>
  </div>
  <div style="position:absolute;left:1090px;top:250px">{svg}</div>
  <div class="dom" style="right:110px;bottom:70px;font-size:40px">majasco.jp</div>
</div>"""

def xheader_html():
    W, H = 1500, 500
    svg = hero_svg().replace('<svg ', '<svg style="width:620px;height:auto;display:block" ', 1)
    # アイコンは入れない（2026-10-27 一度入れたが、ユーザーの判断で外した。プロフィール画像がすでにアイコン）
    return f"""<div class="cv" style="width:{W}px;height:{H}px">
  <div style="position:absolute;left:400px;top:130px;width:560px;white-space:nowrap">
    <h1 style="font-size:50px;line-height:1.3">麻雀のスコア記録を、<br>スマホでかんたんに。</h1>
    <p class="sub" style="font-size:23px;margin-top:14px">無料・アプリDL不要・会員登録不要</p><p class="sub" style="font-size:23px;font-weight:800;color:#7C8B88">majasco.jp</p>
  </div>
  <div style="position:absolute;left:860px;top:70px">{svg}</div>
</div>"""

def jobs():
    for f in FEATS:
        yield f"feat-{f[0]:02d}-{f[1]}", 1080, 1350, feat_html(f, 1350)
        yield f"feat-{f[0]:02d}-{f[1]}-story", 1080, 1920, feat_html(f, 1920)
    yield "howto-0", 1080, 1350, cover_html("howto")
    for h in HOWTO:
        yield f"howto-{h[0]}", 1080, 1350, howto_html(h)
    yield "intro", 1080, 1350, cover_html("intro")
    yield "ogp4", 2100, 1103, ogp_html()
    yield "x-header-v3", 1500, 500, xheader_html()

def main():
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(device_scale_factor=1)
        for name, w, h, body in jobs():
            if only and only not in name:
                continue
            doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}</body></html>"
            hp = os.path.join(OUT, "_" + name + ".html")
            io.open(hp, "w", encoding="utf-8").write(doc)
            pg.set_viewport_size({"width": w, "height": h})
            pg.goto(furl(hp)); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(300)
            # はみ出しの確認: カードが画面の外に出ていないか
            bad = pg.evaluate(f"""[...document.querySelectorAll('.chip,h1,.sub,.ph')].filter(e => {{ const r = e.getBoundingClientRect(); return r.left < 0 || r.right > {w} || r.bottom > {h}; }}).map(e => e.textContent.trim().slice(0, 20))""")
            if bad:
                print("  はみ出し:", name, bad)
            pg.screenshot(path=os.path.join(OUT, name + ".png"))
            os.remove(hp)
            print("ok", name)
        b.close()

if __name__ == "__main__":
    main()
