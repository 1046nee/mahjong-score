# -*- coding: utf-8 -*-
"""記事の中身をショート動画にする部品と台本（2026-11-06〜）。make_narrated.py の NARR に足して使う。
1本＝場面のリスト。場面＝(字幕の区切り, 場面を作る関数(出る秒, 消える秒))。
どの動画も同じ型: 冒頭（＝サムネ）は上に札と題名、下に絵。本編は上に見出し、真ん中に絵、y=1500に字幕。
絵はサイトのもの（assets/tiles の牌・assets/art・assets/thumbs・本物の記事の画面）だけを使う。
題名や字幕の決まりは docs/video-plan.md。ネタの一覧は docs/video-topics.md
"""
import functools, http.server, os, threading
import make_short as ms
v3 = ms.v3
at, esc, MJ = ms.at, ms.esc, ms.MJ
PAGES = os.path.join(ms.OUT, "pages")
os.makedirs(PAGES, exist_ok=True)

ms.CSS += """
.stage { position: absolute; left: 60px; right: 60px; }
.vcard { background: #fff; border-radius: 40px; padding: 44px 40px; box-shadow: 0 24px 60px rgba(16,40,36,.16); }
.trow { display: flex; justify-content: center; gap: 8px; }
.trow img { display: block; }
.lbl { font-size: 46px; font-weight: 900; color: #177083; text-align: center; margin: 0 0 14px; }
.big { font-size: 150px; font-weight: 900; color: #E75620; text-align: center; line-height: 1.1; font-variant-numeric: tabular-nums; }
.eqn { display: flex; justify-content: center; align-items: center; gap: 22px; font-size: 92px; font-weight: 900; color: #1F2A28; font-variant-numeric: tabular-nums; }
.eqn .o { color: #E75620; }
.vt { width: 100%; border-collapse: collapse; font-size: 48px; font-weight: 900; }
.vt td { padding: 22px 8px; border-top: 3px solid #E3E9E7; color: #1F2A28; }
.vt tr:first-child td { border-top: 0; }
.vt td.r { text-align: right; color: #1A237E; font-variant-numeric: tabular-nums; } .vt td.n { color: #C62828; } .vt td.h { color: #E75620; }
.vbar { display: grid; grid-template-columns: 110px 1fr; align-items: center; gap: 16px; margin: 30px 0; font-size: 56px; font-weight: 900; color: #1F2A28; }
.vbar i { position: relative; display: block; height: 96px; border-radius: 16px; background: #177083; transform-origin: left; }
.vbar i.b { background: #4261AA; }
.vbar .ghost { position: absolute; left: 0; top: 0; bottom: 0; border: 5px dashed #E75620; border-radius: 16px; }
.vbar b { position: absolute; left: 22px; top: 50%; transform: translateY(-50%); color: #fff; font-size: 52px; white-space: nowrap; }
.duo { display: grid; gap: 22px; }
.duo .k { font-size: 36px; font-weight: 900; color: #5F6E6B; }
.duo .v { font-size: 56px; font-weight: 900; line-height: 1.35; color: #1F2A28; }
.duo .v.o { color: #E75620; }
.ans { display: inline-block; background: #E75620; color: #fff; font-size: 84px; font-weight: 900; border-radius: 30px; padding: 22px 60px; }
.mid { text-align: center; }
.xmark { position: absolute; inset: 0; pointer-events: none; }
.tile-off { position: relative; } .tile-off::after { content: ''; position: absolute; left: -4px; right: -4px; top: 50%; height: 12px; margin-top: -6px; background: #E75620; border-radius: 6px; transform: rotate(-52deg); }
.cover .sub, .cover .dom-credit { display: none !important; }
"""

# 数を増やす・棒を伸び縮みさせる動き（make_short.py の render に足す）
ms.JS += r"""
const renderKit = window.render;
window.render = (t) => { renderKit(t);
  const e2 = x => x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
  document.querySelectorAll('[data-count]').forEach(e => { const [a, b, f, g, d] = e.dataset.count.split(',').map(Number); const p = e2(Math.min(1, Math.max(0, (t - a) / (b - a))));
    const v = f + (g - f) * p; e.textContent = (e.dataset.pre || '') + v.toLocaleString('ja-JP', { minimumFractionDigits: d, maximumFractionDigits: d }) + (e.dataset.post || ''); });
  document.querySelectorAll('[data-w]').forEach(e => { const [a, b, f, g] = e.dataset.w.split(',').map(Number); const p = e2(Math.min(1, Math.max(0, (t - a) / (b - a)))); e.style.width = (f + (g - f) * p) + '%'; });
};
"""

def tile(code, w):
    return f'<img src="{v3.furl(os.path.join(v3.TILES, code + ".svg"))}" style="width:{w}px">'

def trow(codes, w=92, off=()):
    return '<div class="trow">' + "".join(f'<span class="{"tile-off" if i in off else ""}">{tile(c, w)}</span>' for i, c in enumerate(codes)) + "</div>"

def art(rel, w, style=""):
    return f'<img src="{v3.furl(os.path.join(MJ, *rel.split("/")))}" style="display:block;width:{w}px;margin:0 auto;{style}">'

def stage(a, b, inner, top=440, anim="up", cls=""):
    return at(a, b, inner, cls="stage " + cls, style=f"top:{top}px", anim=anim)

def head(a, b, text, top=170):
    return at(a, b, f"<h1>{esc(text)}</h1>", cls="cap", style=f"top:{top}px")

def hook(badge, title, visual, g=True, top=250):
    """冒頭＝サムネ。リールの一覧で切られても残るように、題名と絵を真ん中寄りに置く"""
    def mk(a, b):
        return [at(a, b, f'<div class="badge{" g" if g else ""}">{esc(badge)}</div><h1>{esc(title)}</h1>', cls="cap hook", style=f"top:{top}px", anim="pop"),
                stage(a + .05, b, visual, top=820, anim="fade")]
    return mk

_srv = []
def page_shot(slug):
    """本物の記事の画面（スマホの幅）を撮っておく。動画の最後にスマホの中で流す"""
    path = os.path.join(PAGES, slug + ".jpg")
    if os.path.exists(path):
        return path
    from playwright.sync_api import sync_playwright
    class Q(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
        def handle(self):
            try: super().handle()
            except Exception: pass
    if not _srv:
        s = http.server.ThreadingHTTPServer(("127.0.0.1", 8812), functools.partial(Q, directory=MJ))
        s.handle_error = lambda *a: None
        threading.Thread(target=s.serve_forever, daemon=True).start()
        _srv.append(s)
    with sync_playwright() as p:
        b = p.chromium.launch()
        c = b.new_context(viewport={"width": 390, "height": 792}, device_scale_factor=2, locale="ja-JP")
        c.route(lambda u: not u.startswith("http://127.0.0.1:8812"), lambda r: r.abort())
        g = c.new_page()
        g.goto(f"http://127.0.0.1:8812/{slug}.html", wait_until="load")
        g.wait_for_timeout(500)
        g.evaluate("document.querySelectorAll('img[loading]').forEach(i => i.loading = 'eager')")
        g.wait_for_timeout(500)
        g.screenshot(path=path, type="jpeg", quality=80, clip={"x": 0, "y": 0, "width": 390, "height": 2600}, full_page=True)
        b.close()
    return path

def article_end(slug, label):
    """最後: 本物の記事をスマホの中で流す"""
    def mk(a, b):
        w = 520
        body, h, strip, inner, bz = v3.phone_frame(w, "#fff", f'<img data-scroll="{a + .5},{b - .3},0,900" src="{v3.furl(page_shot(slug))}">')
        ph = f'<div class="ph" style="left:{(1080 - w) // 2}px;top:400px;width:{w}px;height:{h}px;padding:{bz}px;border-radius:{round(w * v3.PH_R)}px">{body}</div>'
        return [head(a, b, label), at(a, b, ph, style="position:absolute;inset:0")]
    return mk

END = ["くわしくは、", "まじゃすこの記事で。"]

def vt(rows):
    """rows = [(左, 右, 右のクラス)]"""
    return '<table class="vt">' + "".join(f'<tr><td>{l}</td><td class="r {c}">{r}</td></tr>' for l, r, c in rows) + "</table>"

# ---------------- 台本 ----------------
def t_hai():
    fan = '<div class="vcard mid">' + trow(["m1", "p1", "s1", "z1", "z7"], 150) + '<p class="lbl" style="margin:26px 0 0">同じ牌が4枚ずつ</p></div>'
    def suu(a, b):
        return [head(a, b, "数牌は27種類"), *[stage(a + .3 + i * .5, b, f'<div class="vcard"><p class="lbl">{n}</p>{trow([k + str(j) for j in range(1, 10)], 92)}</div>', top=430 + i * 340)
                for i, (n, k) in enumerate((("萬子", "m"), ("筒子", "p"), ("索子", "s")))]]
    def ji(a, b):
        return [head(a, b, "字牌は7種類"), stage(a + .3, b, f'<div class="vcard"><p class="lbl">風牌 4種類</p>{trow(["z1", "z2", "z3", "z4"], 160)}</div>', top=430),
                stage(a + .9, b, f'<div class="vcard"><p class="lbl">三元牌 3種類</p>{trow(["z5", "z6", "z7"], 160)}</div>', top=880)]
    def tot(a, b):
        return [head(a, b, "全部で何枚？"), stage(a + .3, b, '<div class="vcard mid"><div class="eqn"><span>34種類</span><span>×</span><span>4枚</span></div></div>', top=470),
                stage(a + 1.0, b, f'<div class="big" data-count="{a + 1.0},{a + 2.0},0,136,0" data-post="枚">0枚</div>', top=800),
                stage(a + 1.2, b, trow(["m1", "m1", "m1", "m1"], 130), top=1090, anim="pop")]
    return [(["麻雀の牌、", "全部で何枚か知ってる？"], hook("初心者向け", "麻雀の牌、\n全部で何枚？", fan)),
            (["数字の牌は、萬子・筒子・索子。", "1から9まであるので、27種類。"], suu),
            (["文字の牌は、風が4種類、", "白・發・中が3種類で、7種類。"], ji),
            (["合わせて34種類で、", "同じ牌が4枚ずつ。", "全部で136枚です。"], tot),
            (END, article_end("blog-mahjong-suuji", "牌の図鑑は記事で"))]

def t_half():
    A = '<div class="vcard">' + '<div class="vbar"><span>A</span><i style="width:100%"><b>+400</b></i></div><div class="vbar"><span>B</span><i class="b" style="width:62%"><b>+250</b></i></div></div>'
    def bars(rows, a, d=0):
        out = ""
        for n, f, g, tx, c in rows:
            out += f'<div class="vbar"><span>{n}</span><div style="position:relative"><span class="ghost" style="width:{f}%"></span><i class="{c}" data-w="{a + .8 + d},{a + 2.0 + d},{f},{g}" style="width:{f}%"><b>{tx}</b></i></div></div>'
        return f'<div class="vcard">{out}</div>'
    def s1(a, b):
        return [head(a, b, "差も半分になる"), stage(a + .2, b, bars([("A", 100, 50, "+200", ""), ("B", 62.5, 31.25, "+125", "b")], a), top=520),
                stage(a + 2.2, b, '<div class="mid"><div class="eqn"><span>150差</span><span class="o">→</span><span class="o">75差</span></div></div>', top=1110)]
    def s2(a, b):
        return [head(a, b, "レギュラーのあとに\n半分"), stage(a + .3, b, '<div class="vcard">' + vt([("レギュラー1位 A", "+400.0", ""), ("半分で開始", "+200.0", ""), ("セミファイナル", "−80.0", "n"), ("合計", "+120.0", "h")]) + '</div>', top=540)]
    def s3(a, b):
        return [head(a, b, "もう1回、半分"), stage(a + .3, b, '<div class="vcard">' + vt([("A", "+60.0 → +130.0", "h"), ("C", "+85.0 → +105.0", ""), ("B", "+92.5 → +42.5", ""), ("E", "+7.5 → −32.5", "n")]) + '</div>', top=470),
                stage(a + 1.6, b, '<div class="mid"><span class="ans">Aが逆転優勝</span></div>', top=1130, anim="pop")]
    return [(["Mリーグのポイントは、", "シーズン中に2回も半分になる。"], hook("Mリーグ", "ポイントは\n2回半分になる", A)),
            (["半分にすると、", "チームの差も半分。", "150の差は75になります。"], s1),
            (["たとえば400で1位のAも、", "半分の200から始まって、", "ここで80落とすと120。"], s2),
            (["ファイナルでさらに半分。", "最後はAが逆転しました。", "架空のチームの例です。"], s3),
            (END, article_end("blog-mleague-points", "計算の全部は記事で"))]

def t_sanma():
    ms_ = [f"m{i}" for i in range(1, 10)]
    vis = '<div class="vcard mid">' + trow(ms_, 92, off=range(1, 8)) + '<p class="lbl" style="margin:26px 0 0">この7種類を抜く</p></div>'
    def s1(a, b):
        return [head(a, b, "萬子の二〜八を抜く"), stage(a + .3, b, '<div class="vcard mid">' + trow(ms_, 92) + "</div>", top=470),
                stage(a + 1.2, b, '<div class="vcard mid">' + trow(ms_, 92, off=range(1, 8)) + '</div>', top=760, anim="pop"),
                stage(a + 1.8, b, '<div class="eqn"><span>7種類×4枚</span><span>＝</span><span class="o">28枚</span></div>', top=1080)]
    def s2(a, b):
        return [head(a, b, "136枚が108枚に"), stage(a + .3, b, f'<div class="big" data-count="{a + .5},{a + 1.8},136,108,0" data-post="枚">136枚</div>', top=560),
                stage(a + 1.6, b, '<div class="vcard mid">' + trow(["m1", "m9"], 150) + '<p class="lbl" style="margin:20px 0 0">萬子は一と九だけ</p></div>', top=840)]
    def s3(a, b):
        return [head(a, b, "よくある設定"), stage(a + .3, b, '<div class="vcard">' + vt([("持ち点", "35,000点", ""), ("返し点", "35,000点", ""), ("ウマ", "10-0-10", ""), ("チー", "なしが主流", "h")]) + '</div>', top=470)]
    return [(["三麻って、", "どの牌を抜くか知ってる？"], hook("三麻", "三麻は、\nどの牌を抜く？", vis)),
            (["よくあるのは、", "萬子の二から八を抜く形。", "7種類の4枚で、28枚です。"], s1),
            (["136枚が108枚に減って、", "萬子は一と九だけが残ります。"], s2),
            (["持ち点は35,000点、", "ウマは10-0-10がよくある形。", "打つ前に確かめましょう。"], s3),
            (END, article_end("blog-sanma-yonma", "違いの早見表は記事で"))]

def t_tsumo():
    vis = '<div class="vcard mid">' + art("assets/art/table-yama.svg", 700) + "</div>"
    def s1(a, b):
        return [head(a, b, "136枚から引いていく"), stage(a + .3, b, '<div class="vcard">' + vt([("全部の牌", "136枚", ""), ("王牌（ツモらない）", "−14枚", "n"), ("配牌 13枚×4人", "−52枚", "n")]) + '</div>', top=470),
                stage(a + 1.6, b, f'<div class="big" data-count="{a + 1.6},{a + 2.6},136,70,0" data-post="枚">136枚</div>', top=1010)]
    def s2(a, b):
        return [head(a, b, "王牌は山の7トン分"), stage(a + .3, b, '<div class="vcard mid">' + art("assets/art/wanpai.svg", 820) + '</div>', top=520)]
    def s3(a, b):
        return [head(a, b, "1人17〜18回だけ"), stage(a + .3, b, '<div class="vcard">' + vt([("東家", "18回", ""), ("南家", "18回", ""), ("西家", "17回", ""), ("北家", "17回", "")]) + '</div>', top=470)]
    return [(["1局でツモれる牌は、", "たったの70枚。"], hook("麻雀の数字", "1局でツモれるのは\n何枚？", vis)),
            (["136枚から、", "王牌の14枚と、", "配牌の52枚を引くと70枚。"], s1),
            (["王牌は山の最後の7トン分。", "ここはツモりません。"], s2),
            (["4人で割ると、", "1人17回か18回だけ。", "鳴きがないときの数です。"], s3),
            (END, article_end("blog-mahjong-suuji", "麻雀の数字の理由は記事で"))]

def t_zure():
    vis = '<div class="vcard mid">' + art("assets/art/tenbo-color.svg", 760) + '<p class="big" style="font-size:110px;margin-top:20px">−1,000点</p></div>'
    def s1(a, b):
        return [head(a, b, "まず場を見る"), stage(a + .3, b, '<div class="vcard mid">' + art("assets/art/tenbo-color.svg", 760) + '<p class="lbl" style="margin-top:24px">場に残ったリーチ棒</p></div>', top=520)]
    def s2(a, b):
        return [head(a, b, "ズレ幅で原因がわかる"), stage(a + .3, b, '<div class="vcard">' + vt([("−1,000点", "リーチ棒", "h"), ("−300・−600点", "積み棒", ""), ("ちょうど10,000点", "万点棒", ""), ("スコア ±20.0", "オカ", "")]) + '</div>', top=470)]
    def s3(a, b):
        return [head(a, b, "合計は必ず0"), stage(a + .3, b, '<div class="vcard">' + vt([("1位", "+65.0", ""), ("2位", "−5.0", "n"), ("3位", "−5.0", "n"), ("4位", "−55.0", "n"), ("合計", "0.0", "h")]) + '</div>', top=470)]
    return [(["点数が1,000点足りない。", "犯人はだいたいこれ。"], hook("集計あるある", "1,000点足りない\n犯人は？", vis, g=False)),
            (["いちばん多いのは、", "場に残ったリーチ棒です。"], s1),
            (["300点なら積み棒、", "ちょうど10,000点なら万点棒。", "ズレ幅で原因がしぼれます。"], s2),
            (["全員のスコアを足すと、", "必ず0になります。", "ここを最初に確かめましょう。"], s3),
            (END, article_end("blog-score-mismatch", "確認の手順は記事で"))]

def t_nichijou():
    vis = '<div class="vcard mid">' + trow(["m2", "m3", "m4", "p5", "p5", "s6", "s7"], 112) + '<p class="big" style="font-size:112px;margin-top:20px">テンパる</p></div>'
    def word(w, tiles_, d1, d2):
        def mk(a, b):
            return [head(a, b, w), stage(a + .3, b, '<div class="vcard mid">' + trow(tiles_, 120) + "</div>", top=380),
                    stage(a + .8, b, f'<div class="vcard duo"><div><div class="k">麻雀では</div><div class="v">{esc(d1)}</div></div><div><div class="k">日常では</div><div class="v o">{esc(d2)}</div></div></div>', top=720)]
        return mk
    return [(["テンパるって、", "実は麻雀の言葉。"], hook("実は麻雀用語", "テンパるって、\nもとは麻雀？", vis)),
            (["麻雀ではあと1枚の状態。", "日常では余裕がないこと。"], word("テンパる", ["m2", "m3", "m4", "p5", "p5"], "あと1枚で\nあがれる状態", "せっぱつまって\n余裕がない")),
            (["安パイは、", "捨てても大丈夫な牌のこと。"], word("安パイ", ["z1", "z1", "z1"], "捨てても\nあがられない牌", "危険がなく\n扱いやすい物事や人")),
            (["オーラスは、最後の1局。", "オールラストの和製英語です。"], word("オーラス", ["z2", "m4"], "半荘の最後の1局\n（南4局）", "物事の最後")),
            (["ほかにも5語、", "記事にまとめています。"], article_end("blog-nichijougo", "8語の一覧は記事で"))]

def t_haitei():
    vis = '<div class="vcard mid">' + trow(["back", "back", "back", "m7"], 150) + '<p class="lbl" style="margin:24px 0 0">山の最後の1枚</p></div>'
    def s1(a, b):
        return [head(a, b, "答え"), stage(a + .3, b, '<div class="mid"><span class="ans">できない</span></div>', top=520, anim="pop"),
                stage(a + .9, b, '<div class="vcard mid"><p class="lbl">カンのあとに引く牌が、<br>もう山にない</p></div>', top=800)]
    def s2(a, b):
        return [head(a, b, "最後の1枚でできないこと"), stage(a + .3, b, '<div class="vcard">' + vt([("海底牌を引いた人", "カン", "h"), ("海底牌を引いた人", "リーチ", "h"), ("河底牌（最後の捨て牌）", "チー・ポン", "h")]) + '</div>', top=520),
                stage(a + 1.4, b, '<div class="mid"><p class="lbl">河底牌はロンだけ</p></div>', top=1180)]
    return [(["最後の1枚を引いた人は、", "カンできる？"], hook("知らないとチョンボ", "最後の1枚で、\nカンできる？", vis, g=False)),
            (["答えはできません。", "カンのあとに引く牌が、", "もう山にないからです。"], s1),
            (["リーチもできません。", "最後の捨て牌には、", "チーもポンもできません。"], s2),
            (END, article_end("blog-haitei", "海底の決まりは記事で"))]

# ---- 文字だけだった2本の作り直し（2026-11-06 ユーザーの指摘）----
APP_END = ["無料で、登録もいりません。", "プロフィールのリンクからどうぞ。"]

def t_aruaru():
    vis = '<div class="vcard mid">' + art("assets/photo-score-sheets.jpg", 800, "border-radius:24px;height:520px;object-fit:cover") + "</div>"
    def card(i, tx, rel):
        def mk(a, b):
            return [head(a, b, f"あるある{i}"), stage(a + .2, b, f'<div class="vcard mid">{art(rel, 620, "border-radius:24px")}<div class="tx" style="font-size:60px;font-weight:900;line-height:1.35;margin-top:26px">{esc(tx)}</div></div>', top=400, anim="right")]
        return mk
    def sol(a, b):
        return [ms.at(a, b, '<h1>それ、まじゃすこなら<br>全部自動。</h1>', cls="cap", style="top:170px", anim="pop"), ms.phone_at(a + .2, b, "howto-4.jpg", y=400)[0],
                ms.chip_at(a + .8, b, ("", "+69.1", ("medal", 1)), "l", 700), ms.chip_at(a + 1.2, b, ("通算", "自動", ""), "r", 900)]
    def q(a, b):
        return [head(a, b, "あなたの卓は、\nいくつ当てはまる？"), stage(a + .2, b, '<div class="vcard mid">' + art("assets/thumbs/blog-shukei-gakari.svg", 640, "border-radius:24px") + "</div>", top=540)]
    return [(["セット麻雀の、", "集計係あるある。"], hook("あるある", "セット麻雀の\n集計係あるある", vis, g=False)),
            (["終わったあと、", "なぜか電卓を渡される。"], card(1, "終わったあと、\n電卓を渡される", "assets/thumbs/blog-score-examples.svg")),
            (["ウマとオカの計算で、", "手が止まる。"], card(2, "ウマ・オカの計算で\n手が止まる", "assets/thumbs/blog-uma-oka.svg")),
            (["先月どっちが勝ってた？", "誰も答えられない。"], card(3, "「先月どっちが勝ってた？」\n誰も答えられない", "assets/thumbs/blog-season-ranking.svg")),
            (["スコア表の写真が、", "LINEの奥に消えていく。"], card(4, "スコア表の写真が\nLINEの奥に消える", "assets/photo-score-notebook.jpg")),
            (["それ、まじゃすこなら", "全部自動です。"], sol),
            (["あなたの卓は、", "いくつ当てはまる？"], q),
            (APP_END, lambda a, b: [ms.end_card(a)])]

def t_umaoka():
    vis = '<div class="vcard mid">' + art("assets/thumbs/blog-uma-oka.svg", 640, "border-radius:24px") + "</div>"
    def oka(a, b):
        return [head(a, b, "オカ＝\nトップへのごほうび"), stage(a + .2, b, '<div class="vcard mid">' + art("assets/art/tenbo-color.svg", 420) + "</div>", top=440),
                stage(a + .9, b, '<div class="vcard">' + vt([("25,000点持ち・30,000点返し", "", ""), ("トップ", "+15", ""), ("ほかの3人", "−5ずつ", "n")]) + "</div>", top=860)]
    def uma(a, b):
        return [head(a, b, "ウマ＝\n順位で動くポイント"), stage(a + .3, b, '<div class="vcard">' + vt([("1位", "+30", ""), ("2位", "+10", ""), ("3位", "−10", "n"), ("4位", "−30", "n")]) + "</div>", top=470)]
    def ex(a, b):
        return [head(a, b, "45,200点でトップなら"), stage(a + .2, b, '<div class="vcard">' + vt([("素点", "+20.2", ""), ("ウマ", "+30", ""), ("オカ", "+15", "")]) + "</div>", top=400),
                stage(a + 1.6, b, f'<div class="big" data-pre="+" data-count="{a + 1.6},{a + 3.0},0,65.2,1">+0.0</div>', top=1010)]
    def app(a, b):
        return [ms.at(a, b, '<h1>この計算、<br>まじゃすこなら自動。</h1>', cls="cap", style="top:170px", anim="pop"), ms.phone_at(a + .2, b, "howto-4.jpg", y=400)[0]]
    return [(["ウマとオカって、", "結局なに？"], hook("初心者の壁", "ウマ・オカって、\n結局なに？", vis)),
            (["オカは、トップへのごほうび。", "4人が5,000点ずつ出して、", "トップがまとめて受け取ります。"], oka),
            (["ウマは、順位で動くポイント。", "よくある10-30なら、", "1位はプラス30、", "4位はマイナス30。"], uma),
            (["たとえば、", "45,200点でトップなら、", "素点が20.2、", "ウマが30、オカが15。", "合わせて、プラス65.2です。"], ex),
            (["この計算、", "まじゃすこなら自動です。"], app),
            (APP_END, lambda a, b: [ms.end_card(a)])]

TOPICS = {"aruaru-shukei": t_aruaru, "kabe-umaoka": t_umaoka, "t-hai136": t_hai, "t-half": t_half, "t-sanma": t_sanma, "t-tsumo70": t_tsumo, "t-zure": t_zure, "t-nichijou": t_nichijou, "t-haitei": t_haitei}

# ---- 役シリーズ（blog-yaku-ichiran.html の役を1役1本。手の絵がある役だけ）----
import io as _io, re as _re

def _yaku_list():
    s = _io.open(os.path.join(MJ, "blog-yaku-ichiran.html"), encoding="utf-8").read()
    s = s[s.index('<h2 id="h1">'):s.index("</article>")]
    out = []
    for blk in s.split("<h3>")[1:]:
        m = _re.match(r'(.*?)</h3>\s*(<p>.*?</p>)?.*?(<div class="yaku-ex">.*?</span></span></div>)', blk, _re.S)
        if not m or "<h2" in blk[:blk.find('<div class="yaku-ex">')] if m else True:
            continue
        h, p, ex = m.group(1), m.group(2) or "", m.group(3)
        name = _re.sub(r"<rt>.*?</rt>|<[^>]+>", "", _re.search(r'<ruby class="r">(.*?)</ruby>', h).group(1))
        read = _re.search(r"<rt>(.*?)</rt>", h).group(1)
        han = _re.sub(r"<[^>]+>", "", _re.search(r'<span class="han">(.*?)</span>', h).group(1))
        desc = _re.sub(r"<rt>.*?</rt>|<[^>]+>", "", p).strip()
        codes = lambda x: _re.findall(r"/assets/tiles/([a-z0-9-]+)\.svg", x)
        hin = codes(_re.search(r'<span class="h-in">(.*?)</span>', ex, _re.S).group(1))
        win = codes(_re.search(r'<span class="h-win">(.*?)</span>', ex, _re.S).group(1))
        melds = [codes(x) for x in _re.findall(r'<span class="meld"[^>]*>(.*?)</span>', ex, _re.S)]
        out.append(dict(name=name, read=read, han=han, desc=desc, hin=hin, win=win, melds=melds))
    return out

def _chunks(text, n=17):
    """字幕の区切り: 「、」「。」で切って、n文字までにまとめる。かっこの中は字幕と声から外す"""
    text = _re.sub(r"（[^）]*）", "", text)
    parts = [x for x in _re.split(r"(?<=[、。])", text) if x.strip()]
    # 句読点のない長い文は、真ん中に近い「」・を・に・で・て」の後ろで切る（字幕が1行に入らないため）
    def cut(x):
        if len(x) <= n: return [x]
        ks = [k + 1 for k, ch in enumerate(x[:-2]) if ch in "」をにでてと" and 4 <= k + 1 <= len(x) - 4]
        if not ks: return [x]
        k = min(ks, key=lambda k: abs(k - len(x) / 2))
        return cut(x[:k]) + cut(x[k:])
    parts = [y for x in parts for y in cut(x)]
    out, cur = [], ""
    for x in parts:
        if cur and len(cur) + len(x) > n:
            out.append(cur); cur = x
        else:
            cur += x
    if cur: out.append(cur)
    return out

def _hand(y, w=60):
    """手牌の行・鳴いた組の行・あがり牌の行に分ける（横に並べると、カンが多い手で枠からはみ出した）"""
    row1 = '<div class="trow" style="gap:3px">' + "".join(tile(c, w) for c in y["hin"]) + "</div>"
    rows = row1
    if y["melds"]:
        eff = sum(len(m) + .4 * sum("yoko" in c for c in m) for m in y["melds"]) + .4 * (len(y["melds"]) - 1)
        mw = min(64, int(880 / eff))
        rows += '<div class="trow" style="margin-top:18px;gap:%dpx">' % round(mw * .4) + "".join(
            '<span style="display:inline-flex;gap:2px;align-items:flex-end">' + "".join(tile(c, round(mw * 1.4) if "yoko" in c else mw) for c in m) + "</span>" for m in y["melds"]) + "</div>"
    if y["win"]:
        rows += ('<div class="trow" style="align-items:center;margin-top:18px"><span class="lbl" style="margin:0 16px 0 0;white-space:nowrap">あがり牌</span>'
                 f'<span style="display:inline-block;padding:6px;border-radius:14px;background:#E75620">{tile(y["win"][0], 76)}</span></div>')
    return f'<div class="vcard mid">{rows}</div>'

def _yaku_video(i, y, n):
    vis = _hand(y)
    def ans(a, b):
        return [head(a, b, "答え"), stage(a + .2, b, vis, top=400, anim="fade"),
                stage(a + .6, b, f'<div class="mid"><div class="big" style="font-size:120px;color:#177083">{esc(y["name"])}</div><p class="lbl" style="font-size:52px">{esc(y["read"])}</p><span class="ans" style="font-size:60px">{esc(y["han"])}</span></div>', top=830, anim="pop")]
    def desc(a, b):
        return [head(a, b, y["name"]), stage(a + .2, b, vis, top=400, anim="fade"),
                stage(a + .5, b, f'<div class="vcard"><div class="v" style="font-size:50px;font-weight:900;line-height:1.5">{esc(_re.sub(r"（[^）]*）", "", y["desc"]))}</div></div>', top=830)]
    han_say = y["han"].replace("（", "、").replace("）", "")
    scenes = [(["この手、", "何の役かわかる？"], hook(f"役シリーズ {i}/{n}", "この手、\n何の役？", vis)),
              ([f"答えは、{y['read']}。", han_say + "。"], ans)]
    if y["desc"]:
        scenes.append((_chunks(y["desc"])[:4], desc))
    scenes.append((END, article_end("blog-yaku-ichiran", "全38役は記事で")))
    return scenes

_Y = _yaku_list()
for _i, _y in enumerate(_Y, 1):
    TOPICS[f"y-{_i:02d}"] = (lambda i=_i, y=_y: _yaku_video(i, y, len(_Y)))

# ---- 用語シリーズ（blog-mahjong-yougo.html の80語を1語1本。「この漢字、読める？」）----
# 絵の決め方（2026-11-09）: 牌・手の形の言葉＝その牌の絵／山・卓・席の言葉＝サイトの卓の図（assets/art）／点棒の言葉＝点棒の絵
_H13 = ["m1", "m2", "m3", "p4", "p5", "p6", "s7", "s8", "s9", "m5", "m5", "z1", "z1"]
_GV = {
    "数牌": ["m1", "p5", "s9"], "字牌": ["z1", "z2", "z5", "z7"], "風牌": ["z1", "z2", "z3", "z4"], "三元牌": ["z5", "z6", "z7"],
    "么九牌": ["m1", "m9", "p1", "p9", "s1", "z1", "z7"], "中張牌": ["m2", "m5", "p4", "p8", "s3", "s6"], "圏風牌": ["z1"], "門風牌": ["z2"],
    "洗牌": ["back", "back", "back", "back", "back"], "砌牌": "table-yama", "壁牌": "table-yama", "幢": "table-yama", "開門": "table-kaimon",
    "配牌": "table-haipai", "王牌": "wanpai", "嶺上牌": "wanpai", "海底牌": "table-yama", "河底牌": "table-tsumo",
    "理牌": ["m1", "m2", "m3", "p4", "p5", "p6", "s7", "s8", "s9"],
    "起家": "dice-chiicha", "荘家": "table-kaze", "散家": "table-kaze", "東家・南家・西家・北家": "table-kaze", "上家": "table-kaze", "下家": "table-kaze",
    "対面": "table-kaze", "自家・他家": "table-kaze", "連荘": "table-kaze", "輪荘": "table-kaze", "本場": "tenbo", "積み棒": "tenbo",
    "供託": "tenbo-color", "配給原点": "tenbo-color",
    "摸打": "table-tsumo", "自摸": "table-tsumo", "打牌": "table-tsumo", "和了": _H13, "栄和": _H13, "副露": ["z7", "z7", "z7-yoko"],
    "吃": ["m4-yoko", "m5", "m6"], "碰": ["p5", "p5", "p5-yoko"], "槓": ["z1", "z1", "z1", "z1"], "暗槓": ["back", "z1", "z1", "back"],
    "大明槓": ["z7", "z7", "z7", "z7-yoko"], "加槓": ["z6-yoko", "z6", "z6", "z6"], "立直": "tenbo", "聴牌": _H13[:12] + ["z2"],
    "不聴": ["m1", "m4", "m8", "p2", "p6", "p9", "s1", "s5", "z2", "z3", "z5", "z6", "z7"], "形式聴牌": _H13[:12] + ["z2"],
    "振聴": ["s4", "s5"], "倒牌": _H13, "搶槓": ["z6-yoko", "z6", "z6", "z6"],
    "流局": "table-yama", "荒牌平局": "table-yama", "不聴罰符": "tenbo-color", "九種九牌": ["m1", "m9", "p1", "p9", "s1", "s9", "z1", "z2", "z5"],
    "四風連打": ["z1", "z1", "z1", "z1"], "四家立直": "tenbo", "四開槓": "wanpai", "三家和": "table-kaze", "錯和": "tenbo", "多牌": _H13 + ["s1"],
    "少牌": _H13[:12], "包": ["z5", "z6", "z7"],
    "面子": ["m1", "m2", "m3"], "順子": ["p4", "p5", "p6"], "刻子": ["s7", "s7", "s7"], "槓子": ["z1", "z1", "z1", "z1"], "雀頭": ["m5", "m5"],
    "対子": ["z6", "z6"], "搭子": ["p3", "p4"], "両面": ["s4", "s5"], "嵌張": ["m3", "m5"], "辺張": ["p1", "p2"], "単騎": ["z1"],
    "双碰": ["m2", "m2", "s8", "s8"], "門前": _H13, "符": "tenbo", "飜": ["p5r", "p5", "p5"], "箱": "tenbo-color",
}

def _yougo_list():
    s = _io.open(os.path.join(MJ, "blog-mahjong-yougo.html"), encoding="utf-8").read()
    s = s[s.index("<article"):s.index("</article>")]
    out = []
    for a, b, c in _re.findall(r'<b class="kj">(.*?)</b><span class="ym">(.*?)</span></dt><dd>(.*?)</dd>', s):
        a = _re.sub(r"<[^>]+>", "", a); c = _re.sub(r"<rt>.*?</rt>|<[^>]+>", "", c)
        out.append(dict(kj=a, ym=_re.sub(r"<[^>]+>", "", b), desc=c, vis=_GV.get(a)))
    return out

def _gvis(v, big=False, small=False):
    if isinstance(v, str):
        wide = v == "dice-chiicha"  # 横に長い絵は幅を広く
        return '<div class="vcard mid">' + art(f"assets/art/{v}.svg", (620 if small else 860) if wide else (300 if small else 520 if big else 440)) + "</div>"
    n = len(v); w = min(110 if small else 130, int(860 / max(n, 1)))
    return '<div class="vcard mid">' + '<div class="trow" style="gap:3px;align-items:flex-end">' + "".join(tile(c, round(w * 1.4) if "yoko" in c else w) for c in v) + "</div></div>"

def _yougo_video(i, g, n):
    hk = f'<div class="mid"><div class="big" style="font-size:{170 if len(g["kj"]) <= 3 else 96}px;color:#1F2A28;margin-bottom:24px">{esc(g["kj"])}</div></div>' + _gvis(g["vis"], small=True)
    def ans(a, b):
        return [head(a, b, g["kj"]), stage(a + .2, b, f'<div class="mid"><p class="lbl" style="font-size:40px;margin:0">読み方</p><span class="ans" style="font-size:{72 if len(g["ym"]) <= 10 else 52}px">{esc(g["ym"])}</span></div>', top=380, anim="pop"),
                stage(a + .6, b, _gvis(g["vis"], True), top=620, anim="fade")]
    def mean(a, b):
        return [head(a, b, g["kj"]), stage(a + .2, b, f'<div class="vcard"><div class="v" style="font-size:52px;font-weight:900;line-height:1.5">{esc(g["desc"])}</div></div>', top=400),
                stage(a + .5, b, _gvis(g["vis"]), top=900, anim="fade")]
    say_ym = g["ym"].replace("・", "、または")
    return [(["この言葉、", "読めるかな？"], hook(f"麻雀用語 {i}/{n}", "読める？", hk, g=False, top=200)),
            ([f"答えは、{say_ym}。"], ans),
            (_chunks(g["desc"])[:4], mean),
            (["正式名称80語は、", "まじゃすこの記事で。"], article_end("blog-mahjong-yougo", "80語は記事で"))]

_G = _yougo_list()
for _i, _g in enumerate(_G, 1):
    TOPICS[f"g-{_i:02d}"] = (lambda i=_i, g=_g: _yougo_video(i, g, len(_G)))
