# -*- coding: utf-8 -*-
"""作り直しの台本（2026-11-10 ユーザーの指示）。video_topics / video_topics2 の同じ名前の動画を上書きする。
- 時間は長くなってよい。数字が変わっていく様子・並びが入れかわる様子を動きで見せる
- Mリーグはチームカラーと文字で見せる（ロゴ・選手の写真は使わない。2026-11-10 ユーザーの判断で案A）
"""
import os
from video_topics import at, esc, head, stage, hook, art, vt, trow, tile, article_end, END, APP_END, ms

TOPICS = {}

ms.CSS += """
.paper { background: #FFFDF5; border-radius: 26px; box-shadow: 0 20px 50px rgba(16,40,36,.16); padding: 36px 40px;
  background-image: repeating-linear-gradient(#FFFDF5 0 68px, #E9E2CC 68px 70px); background-position: 0 24px; }
.hand { font-weight: 700; color: #2B3A67; font-size: 50px; line-height: 70px; white-space: nowrap; }
.hand s { text-decoration-thickness: 6px; text-decoration-color: #2B3A67; }
.qq { color: #C62828; font-weight: 900; }
.tbl { background: #fff; border-radius: 36px; box-shadow: 0 24px 60px rgba(16,40,36,.16); padding: 18px 40px; }
.tbl .r { position: relative; display: grid; grid-template-columns: 230px 1fr 210px; align-items: center; height: 132px; border-top: 3px solid #E3E9E7; }
.tbl .r:first-child { border-top: 0; }
.tbl .r.sum { border-top: 5px solid #1F2A28; height: 120px; }
.tbl .nm { font-size: 52px; font-weight: 900; color: #1F2A28; }
.tbl .val { position: relative; height: 100%; }
.tbl .val span { position: absolute; right: 0; top: 50%; margin-top: -42px; font-size: 72px; line-height: 84px; font-weight: 900; font-variant-numeric: tabular-nums; white-space: nowrap; }
.tbl .dl { text-align: right; }
.tbl .dl span { display: inline-block; font-size: 38px; font-weight: 900; color: #fff; background: #E75620; border-radius: 999px; padding: 8px 22px; }
.pos { color: #1A237E; } .neg { color: #C62828; } .zero { color: #177083; } .ink { color: #1F2A28; }
.step { display: inline-block; background: #177083; color: #fff; font-size: 40px; font-weight: 900; border-radius: 999px; padding: 10px 34px; margin-bottom: 18px; }
.note { background: #fff; border-radius: 30px; padding: 30px 40px; box-shadow: 0 16px 40px rgba(16,40,36,.12); font-size: 46px; font-weight: 900; line-height: 1.5; color: #1F2A28; text-align: center; }
.note b { color: #E75620; }
.bub { display: inline-block; max-width: 760px; font-size: 50px; font-weight: 900; line-height: 1.4; padding: 26px 40px; border-radius: 40px; background: #fff; box-shadow: 0 14px 34px rgba(16,40,36,.14); }
.chat { position: relative; height: 860px; overflow: hidden; background: #8CABD8; border-radius: 40px; }
.chat .in { position: absolute; left: 0; right: 0; top: 0; padding: 30px; }
.chat .m { margin: 18px 0; display: flex; } .chat .m.me { justify-content: flex-end; }
.chat .m span { font-size: 38px; font-weight: 700; background: #fff; border-radius: 30px; padding: 18px 28px; max-width: 640px; }
.chat .m.me span { background: #8DE055; }
.hb { position: absolute; left: 0; right: 0; height: 88px; }
.hb .nm { position: absolute; left: 0; width: 120px; top: 0; height: 84px; display: grid; place-items: center; font-size: 46px; font-weight: 900; color: #fff; border-radius: 18px; }
.hb .bar { position: absolute; top: 12px; height: 60px; border-radius: 12px; }
.hb .v { position: absolute; right: 0; top: 0; height: 84px; line-height: 84px; font-size: 46px; font-weight: 900; font-variant-numeric: tabular-nums; }
.axis { position: absolute; top: -10px; bottom: -10px; width: 4px; background: #1F2A28; border-radius: 2px; }
.cutline { position: absolute; left: 0; right: 0; height: 0; border-top: 6px dashed #E75620; }
.cutline b { position: absolute; left: 130px; top: -8px; background: #E4F3EC; padding: 0 12px; font-size: 38px; color: #E75620; font-weight: 900; }
"""

# 時間で値を変える動き。data-anim="出る秒,終わる秒,プロパティ,はじめ,おわり,単位;…"（時刻の順に並べる）
# data-nums="出る秒,終わる秒,はじめ,おわり,小数の桁;…"（数字。data-sign があれば＋を付ける）
ms.JS += r"""
const renderKit3 = window.render;
window.render = (t) => { renderKit3(t);
  const e2 = x => x < .5 ? 2 * x * x : 1 - Math.pow(-2 * x + 2, 2) / 2;
  const seg = (s) => s.split(';').map(x => x.split(','));
  document.querySelectorAll('[data-anim]').forEach(e => { const v = {};
    seg(e.dataset.anim).forEach(([a, b, p, f, g, u]) => { a = +a; b = +b; f = +f; g = +g;
      if (!(p in v) || t >= a) { const k = e2(Math.min(1, Math.max(0, (t - a) / Math.max(.001, b - a)))); v[p] = (f + (g - f) * k) + (u || ''); } });
    for (const p in v) e.style[p] = v[p]; });
  document.querySelectorAll('[data-nums]').forEach(e => { let n = null, d = 1;
    seg(e.dataset.nums).forEach(([a, b, f, g, dd]) => { a = +a; b = +b; f = +f; g = +g;
      if (n === null || t >= a) { const k = e2(Math.min(1, Math.max(0, (t - a) / Math.max(.001, b - a)))); n = f + (g - f) * k; d = +dd; } });
    const s = Math.abs(n).toLocaleString('ja-JP', { minimumFractionDigits: d, maximumFractionDigits: d });
    const z = Math.abs(n) < Math.pow(10, -d) / 2;
    e.textContent = (z ? '' : n < 0 ? '−' : (e.dataset.sign !== undefined ? '+' : '')) + s + (e.dataset.post || '');
    if (e.dataset.color !== undefined) { e.classList.remove('zero', 'neg', 'pos'); e.classList.add(z ? 'zero' : n < 0 ? 'neg' : 'pos'); } });
};
"""

def fmt(v, d=1, sign=True):
    s = f"{abs(v):,.{d}f}"
    if abs(v) < 10 ** -d / 2: return s
    return ("−" if v < 0 else "+" if sign else "") + s

def cls(v):
    return "zero" if abs(v) < 1e-9 else "neg" if v < 0 else "pos"

# ======================= 集計係あるある（6つ。2026-11-10 ユーザーの文面）=======================
def _paper(lines, top_pad=0):
    return f'<div class="paper" style="padding-top:{36 + top_pad}px">' + "".join(f'<div class="hand">{x}</div>' for x in lines) + "</div>"

def t_aruaru():
    vis = '<div class="vcard mid">' + art("assets/photo-score-sheets.jpg", 800, "border-radius:24px;height:520px;object-fit:cover") + "</div>"
    def card(i, tx, inner, extra=lambda a, b: []):
        def mk(a, b):
            return [head(a, b, f"あるある {i}/6"), stage(a + .2, b, inner(a, b), top=360, anim="right"),
                    stage(a + .6, b, f'<div class="note">{tx}</div>', top=1180)] + extra(a, b)
        return mk
    # 1 ウマとオカで手が止まる
    def v1(a, b):
        return _paper(["健太　45,200点", "45,200 − 30,000", "＝ ＋15.2", f'＋ウマ <span class="qq" data-shake="{a + .8},{b}">？</span>', f'＋オカ <span class="qq" data-shake="{a + 1.2},{b}">？</span>', '＝ <span class="qq">？？？</span>'])
    # 2 字が汚くて読めない
    def v2(a, b):
        L = ['<span style="display:inline-block;transform:rotate(-3deg)">健太 <s>45,800</s> 45,2<span style="display:inline-block;transform:scale(1.3,.8) rotate(12deg)">0</span>0</span>',
             '<span style="display:inline-block;transform:rotate(2deg) skewX(-14deg)">美咲 2<span style="display:inline-block;transform:rotate(-20deg)">8</span>,1<s>6</s>00</span>',
             '<span style="display:inline-block;transform:rotate(-1deg) skewX(10deg)">翔 <s>+8.1</s> <s>−2.7</s> −22.<span style="display:inline-block;transform:scaleX(.6)">7</span></span>',
             '<span style="display:inline-block;transform:rotate(4deg)">陽菜 −5<s>0</s>6.<span style="display:inline-block;filter:blur(3px)">0</span></span>',
             '<span style="display:inline-block;transform:rotate(-5deg);filter:blur(1.5px)">合計 −2?.?</span>']
        return _paper(L)
    def x2(a, b):
        return [stage(a + 1.2, b, '<div class="mid"><span class="ans" style="background:#C62828">読めない…</span></div>', top=1000, anim="pop")]
    # 3 自分のスコアを足すだけなのに時間がかかる
    def v3_(a, b):
        L = ["健太の今日のスコア", "1試合目　＋65.2", "2試合目　−40.2", "3試合目　＋57.7", "4試合目　−52.0", '合計　<span class="qq">＝ ？</span>']
        return _paper(L) + f'<div class="mid" style="margin-top:26px"><span class="ans" style="background:#1F2A28;font-variant-numeric:tabular-nums"><span data-timer="{a + .4},{b}">0.0秒</span></span></div>'
    # 4 最後の確認で数字が合わない
    def v4(a, b):
        rows = [("健太", "+30.7"), ("美咲", "+85.9"), ("翔", "−3.3"), ("陽菜", "−112.3")]
        r = "".join(f'<div class="r"><span class="nm">{n}</span><span class="val"><span class="{"neg" if v[0] == "−" else "pos"}">{v}</span></span><span></span></div>' for n, v in rows)
        r += f'<div class="r sum"><span class="nm">合計</span><span class="val"><span class="neg" data-shake="{a + 1.2},{a + 2.4}">+1.0</span></span><span class="dl"><span style="background:#C62828">ズレ</span></span></div>'
        return f'<div class="tbl">{r}</div>'
    # 5 先月どっちが勝ってた？
    def v5(a, b):
        return (f'<div style="height:760px;position:relative">'
                f'<div style="position:absolute;left:0;top:40px" data-in="{a + .4}" data-a="left"><div class="bub">健太「先月は<br>俺が勝ってた」</div></div>'
                f'<div style="position:absolute;right:0;top:300px" data-in="{a + 1.2}" data-a="right"><div class="bub" style="background:#FFE9E0">美咲「いや、<br>私でしょ？」</div></div>'
                f'<div style="position:absolute;left:0;right:0;top:560px;text-align:center" data-in="{a + 2.0}" data-a="pop"><span class="ans" style="background:#5F6E6B">記録がない…</span></div></div>')
    # 6 スコア表の写真が、LINEの奥に消えていく
    def v6(a, b):
        msgs = [("", "今日おつかれ！"), ("me", '<img src="%s" style="width:420px;border-radius:18px;display:block">' % ms.v3.furl(os.path.join(ms.MJ, "assets", "photo-score-sheets.jpg"))),
                ("me", "スコア表の写真です"), ("", "ありがとう〜"), ("", "次いつにする？"), ("me", "来週の土曜は？"), ("", "OK!"), ("", "店どこにする？"),
                ("me", "いつものところで"), ("", "了解"), ("", "そういえば先月の結果って？"), ("me", "写真…どこだっけ"), ("", "？？？")]
        inner = "".join(f'<div class="m {k}"><span>{t}</span></div>' for k, t in msgs)
        return f'<div class="chat"><div class="in" data-scroll="{a + .8},{b - .4},0,820">{inner}</div></div>'
    def sol(a, b):
        return [ms.at(a, b, '<h1>それ、まじゃすこなら<br>全部自動。</h1>', cls="cap", style="top:170px", anim="pop"), ms.phone_at(a + .2, b, "howto-4.jpg", y=400)[0],
                ms.chip_at(a + .8, b, ("", "+69.1", ("medal", 1)), "l", 700), ms.chip_at(a + 1.2, b, ("通算", "自動", ""), "r", 900)]
    def q(a, b):
        return [head(a, b, "あなたの卓は、\nいくつ当てはまる？"), stage(a + .2, b, '<div class="vcard mid">' + art("assets/thumbs/blog-shukei-gakari.svg", 640, "border-radius:24px") + "</div>", top=540)]
    return [(["セット麻雀の、", "集計係あるある。"], hook("あるある", "セット麻雀の\n集計係あるある", vis, g=False)),
            (["ウマとオカの計算で、", "手が止まる。"], card(1, "ウマとオカの計算で、<br><b>手が止まる</b>", v1)),
            (["スコア表に書かれた数字や取り消し線が、", "汚すぎて読めない。"], card(2, "数字や取り消し線が<br><b>汚すぎて読めない</b>", v2, x2)),
            (["自分のスコアを足し算するだけなのに、", "時間がかかる。"], card(3, "自分のスコアを足すだけなのに<br><b>時間がかかる</b>", v3_)),
            (["最後のスコア確認で、", "なぜか数字が合わない。"], card(4, "最後の確認で、<br>なぜか<b>数字が合わない</b>", v4)),
            (["先月どっちが勝ってた？", "と聞かれても、", "誰も答えられない。"], card(5, "「先月どっちが勝ってた？」<br><b>誰も答えられない</b>", v5)),
            (["スコア表の写真が、", "LINEの奥に消えていく。"], card(6, "スコア表の写真が、<br><b>LINEの奥に消えていく</b>", v6)),
            (["それ、まじゃすこなら", "全部自動です。"], sol),
            (["あなたの卓は、", "いくつ当てはまる？"], q),
            (APP_END, lambda a, b: [ms.end_card(a)])]
TOPICS["aruaru-shukei"] = t_aruaru

# ======================= ウマ・オカ（点数→返し点を引く→1,000点を1に→オカ→ウマ）=======================
NM = ["健太", "美咲", "翔", "陽菜"]
P0 = [45200, 28100, 17300, 9400]
P1 = [p - 30000 for p in P0]
P2 = [p / 1000 for p in P1]
P3 = [P2[0] + 20] + P2[1:]
UMA = [30, 10, -10, -30]
P4 = [round(x + u, 1) for x, u in zip(P3, UMA)]

def _tbl(a, ch, old, new, dold, dnew, deltas=None, sum_old=None, sum_new=None, hl=()):
    """4人の表。ch 秒に old → new へ数字が入れかわる。deltas は右の札（ch の少し前に出る）"""
    rows = ""
    for i in range(4):
        o = f'<span class="{cls(old[i]) if dold is not None else "ink"}" data-in="{a + .1}" data-out="{ch}" data-a="fade">{fmt(old[i], dold) if dold is not None else f"{old[i]:,}"}</span>'
        n = "" if new is None else f'<span class="{cls(new[i])}" data-in="{ch}" data-a="pop"' + (' style="text-shadow:0 0 0 #000"' if i in hl else "") + f'>{fmt(new[i], dnew)}</span>'
        dl = f'<span data-in="{ch - .7}" data-a="pop">{deltas[i]}</span>' if deltas and deltas[i] else ""
        rows += f'<div class="r"><span class="nm">{NM[i]}</span><span class="val">{o}{n}</span><span class="dl">{dl}</span></div>'
    if sum_old is not None:
        so = f'<span class="{cls(sum_old[0])}" data-in="{a + .1}" data-out="{ch if sum_new else 999}" data-a="fade">{sum_old[1]}</span>'
        sn = f'<span class="{cls(sum_new[0])}" data-in="{ch}" data-a="pop">{sum_new[1]}</span>' if sum_new else ""
        rows += f'<div class="r sum"><span class="nm">合計</span><span class="val">{so}{sn}</span><span></span></div>'
    return f'<div class="tbl">{rows}</div>'

def t_umaoka():
    hk = ('<div class="vcard mid"><div class="eqn"><span>45,200点</span><span class="o">→</span><span class="o">+65.2</span></div>'
          '<p class="lbl" style="margin:24px 0 0">どうしてこうなる？</p></div>')
    def rule(a, b):
        return [head(a, b, "よくあるルール"), stage(a + .3, b, '<div class="vcard">' + vt([("持ち点", "25,000点", ""), ("返し点", "30,000点", ""), ("ウマ", "10-30", "h")]) + "</div>", top=440)]
    def s0(a, b):
        return [head(a, b, "半荘が終わった"), stage(a + .2, b, _tbl(a, 999, P0, None, None, None, sum_old=(1, "100,000")), top=400)]
    def s1(a, b):
        ch = a + 2.2
        return [head(a, b, "① 返し点を引く"), stage(a + .2, b, _tbl(a, ch, P0, P1, None, 0, ["−30,000"] * 4), top=400),
                stage(a + .4, b, '<div class="note">45,200 − 30,000 ＝ <b>＋15,200</b></div>', top=1130)]
    def s2(a, b):
        ch = a + 2.0
        return [head(a, b, "② 1,000点を1にする"), stage(a + .2, b, _tbl(a, ch, P1, P2, 0, 1, ["÷1,000"] * 4), top=400),
                stage(a + .4, b, '<div class="note">＋15,200点 → <b>＋15.2</b>　これが「素点」</div>', top=1130)]
    def s3(a, b):
        ch = a + 2.6
        return [head(a, b, "全員を足すと…"), stage(a + .2, b, _tbl(a, ch, P2, P2, 1, 1, sum_old=(-20, "−20.0")), top=400),
                stage(a + 1.4, b, '<div class="note">25,000点で始めて30,000点で引いたので<br>4人とも<b>5,000点ずつ足りない</b></div>', top=1150)]
    def s4(a, b):
        ch = a + 2.4
        return [head(a, b, "③ オカ ＝ トップへ＋20"), stage(a + .2, b, _tbl(a, ch, P2, P3, 1, 1, ["＋20", "", "", ""], (-20, "−20.0"), (0, "0.0"), hl=(0,)), top=400),
                stage(a + .4, b, '<div class="note">足りない<b>5.0 × 4人 ＝ 20</b>を<br>トップがまとめて受け取る</div>', top=1150)]
    def s5(a, b):
        ch = a + 3.4
        return [head(a, b, "④ ウマ ＝ 順位で動く"), stage(a + .2, b, _tbl(a, ch, P3, P4, 1, 1, ["＋30", "＋10", "−10", "−30"], (0, "0.0"), (0, "0.0")), top=400),
                stage(a + .4, b, '<div class="note">10-30なら　1位<b>＋30</b>　2位<b>＋10</b><br>3位<b>−10</b>　4位<b>−30</b></div>', top=1150)]
    def s6(a, b):
        return [head(a, b, "完成！"), stage(a + .2, b, _tbl(a, 999, P4, None, 1, 1, sum_old=(0, "0.0")), top=400),
                stage(a + .8, b, '<div class="note">点数 → 返し点を引く → 1,000点を1に<br>→ <b>オカ</b> → <b>ウマ</b></div>', top=1150)]
    def app(a, b):
        return [ms.at(a, b, '<h1>この4段階、<br>まじゃすこなら自動。</h1>', cls="cap", style="top:170px", anim="pop"), ms.phone_at(a + .2, b, "howto-4.jpg", y=400)[0]]
    return [(["45,200点のトップが、", "なぜプラス65.2になるのか。", "順番に見ていきます。"], hook("初心者の壁", "ウマ・オカって、\n結局なに？", hk)),
            (["ルールは、よくある", "25,000点持ちの30,000点返し。", "ウマは10-30です。"], rule),
            (["半荘が終わって、", "4人の点数はこうなりました。", "合計は100,000点です。"], s0),
            (["まず、全員の点数から、", "返し点の30,000点を引きます。", "健太は、プラス15,200点。"], s1),
            (["次に、1,000点を1にして、", "数字を小さくします。", "これが素点です。"], s2),
            (["ここで全員を足すと、", "マイナス20。", "25,000点で始めたのに、", "30,000点で引いたからです。"], s3),
            (["この20が、オカ。", "トップの健太が、", "まとめて受け取ります。", "健太は35.2に。", "合計は0に戻りました。"], s4),
            (["最後に、ウマ。", "1位にプラス30、2位にプラス10、", "3位にマイナス10、", "4位にマイナス30。"], s5),
            (["健太はプラス65.2、", "陽菜はマイナス50.6。", "全員を足すと、必ず0になります。"], s6),
            (["この4段階、", "まじゃすこなら、", "点数を入れるだけです。"], app),
            (APP_END, lambda a, b: [ms.end_card(a)])]
TOPICS["kabe-umaoka"] = t_umaoka

# ======================= Mリーグのポイントは2回半分になる =======================
# 架空の10チーム。数字は blog-mleague-points.html の例（A〜F）に、レギュラーで敗退する4チームを足した（合計0）
TC = {"A": "#E75620", "B": "#4261AA", "C": "#2E9E5B", "D": "#8E5BB5", "E": "#D4A017", "F": "#C92F42", "G": "#7A8B87", "H": "#7A8B87", "I": "#7A8B87", "J": "#7A8B87"}
REG = {"A": 400, "B": 250, "C": 100, "D": 40, "E": -60, "F": -120, "G": -130, "H": -150, "I": -160, "J": -170}
SEMI = {"A": -80, "B": 60, "C": 120, "D": -15, "E": 45, "F": -130}
FIN = {"A": 70, "C": 20, "B": -50, "E": -40}

ROW = 104
def _chart(a, teams, phases, out=(), cut=None, zero=380, scale=1.0, top_out=()):
    """phases = [(秒, {チーム: 値})]。値が変わると棒が伸び縮みし、順位が入れかわると行が上下に動く"""
    S = lambda v: v * scale
    els = ""
    for tname in teams:
        anim_w, anim_l, anim_y, nums = [], [], [], []
        prev = None
        for k, (tt, vals) in enumerate(phases):
            v = vals[tname]
            order = sorted(vals, key=lambda x: -vals[x])
            y = order.index(tname) * ROW
            w = abs(S(v)); l = zero + (S(v) if v < 0 else 0)
            if prev is None:
                anim_w.append(f"0,0,width,{w},{w},px"); anim_l.append(f"0,0,left,{l},{l},px"); anim_y.append(f"0,0,top,{y},{y},px"); nums.append(f"0,0,{v},{v},1")
            else:
                pw, pl, py, pv = prev
                anim_w.append(f"{tt},{tt + 1.2},width,{pw},{w},px"); anim_l.append(f"{tt},{tt + 1.2},left,{pl},{l},px")
                anim_y.append(f"{tt + 1.0},{tt + 2.0},top,{py},{y},px"); nums.append(f"{tt},{tt + 1.2},{pv},{v},1")
            prev = (w, l, y, v)
        col = TC[tname]
        dim = ""
        for when, names in out:
            if tname in names:
                dim = f' data-anim="{when},{when + .6},opacity,1,.25,"'
        els += (f'<div class="hb" data-anim="{";".join(anim_y)}"><div style="position:absolute;inset:0"{dim}>'
                f'<span class="nm" style="background:{col}">{tname}</span>'
                f'<span class="bar" style="background:{col}" data-anim="{";".join(anim_w + anim_l)}"></span>'
                f'<span class="v" data-nums="{";".join(nums)}" data-sign data-color></span></div></div>')
    h = len(teams) * ROW
    line = ""
    if cut:
        n, when, label = cut
        line = f'<div class="cutline" style="top:{n * ROW - 4}px" data-in="{when}" data-a="fade"><b>{label}</b></div>'
    return f'<div style="position:relative;height:{h}px"><div class="axis" style="left:{zero - 2}px"></div>{els}{line}</div>'

def t_half():
    T10 = list("ABCDEFGHIJ")
    reg = {k: v for k, v in REG.items()}
    half1 = {k: REG[k] / 2 for k in "ABCDEF"}
    semi = {k: half1[k] + SEMI[k] for k in "ABCDEF"}
    half2 = {k: semi[k] / 2 for k in "ABCE"}
    fin = {k: half2[k] + FIN[k] for k in "ABCE"}
    hk = '<div class="vcard mid"><div class="eqn"><span>+400</span><span class="o">→</span><span>+200</span><span class="o">→</span><span>？</span></div><p class="lbl" style="margin:24px 0 0">1位でも2回半分に</p></div>'
    def sc0(a, b):
        return [head(a, b, "レギュラーが終わった"), stage(a + .2, b, _chart(a, T10, [(0, reg)], out=[(a + 2.4, "GHIJ")], cut=(6, a + 2.0, "ここまで進出"), scale=1.0), top=360)]
    def sc1(a, b):
        return [head(a, b, "セミファイナルは半分"), stage(a + .2, b, _chart(a, list("ABCDEF"), [(0, {k: REG[k] for k in "ABCDEF"}), (a + 1.2, half1)], scale=1.5), top=420),
                stage(a + 2.6, b, '<div class="note">A：+400 → <b>+200</b>　F：−120 → <b>−60</b><br>差も半分になる</div>', top=1150)]
    def sc2(a, b):
        return [head(a, b, "セミファイナルの結果"), stage(a + .2, b, _chart(a, list("ABCDEF"), [(0, half1), (a + 1.0, semi)], out=[(a + 3.6, "DF")], cut=(4, a + 3.2, "ファイナルへ"), scale=1.6), top=420),
                stage(a + 4.0, b, '<div class="note">Aは−80で3位に落ち、<br>Eが<b>5位から4位へ</b>すべりこみ</div>', top=1150)]
    def sc3(a, b):
        return [head(a, b, "ファイナル：また半分"), stage(a + .2, b, _chart(a, list("ABCE"), [(0, {k: semi[k] for k in "ABCE"}), (a + 1.2, half2)], scale=1.6), top=480),
                stage(a + 2.6, b, '<div class="note">B：+185 → <b>+92.5</b>　A：+120 → <b>+60</b><br>1位と3位の差は65 → <b>32.5</b></div>', top=1020)]
    def sc4(a, b):
        return [head(a, b, "ファイナルの成績を足す"), stage(a + .2, b, _chart(a, list("ABCE"), [(0, half2), (a + 1.0, fin)], scale=1.6), top=480),
                stage(a + 3.4, b, '<div class="mid"><span class="ans">Aが逆転優勝！</span></div>', top=1000, anim="pop")]
    def sc5(a, b):
        return [head(a, b, "2回の半分で起きること"), stage(a + .3, b, '<div class="vcard">' + vt([("レギュラーの大差", "2回で4分の1に", "h"), ("下位のチーム", "まだ逆転できる", ""), ("最後まで", "目が離せない", "")]) + "</div>", top=440),
                stage(a + 1.4, b, '<div class="note">チーム名と数字は<b>架空の例</b>です</div>', top=1000)]
    return [(["Mリーグのポイントは、", "シーズン中に2回も半分になる。", "流れを見てみましょう。"], hook("Mリーグ", "ポイントは\n2回半分になる", hk)),
            (["10チームがレギュラーシーズンを戦い、", "上位6チームだけが", "セミファイナルへ進みます。"], sc0),
            (["セミファイナルは、", "レギュラーのポイントを", "半分にして始まります。", "400の差は200に。"], sc1),
            (["セミファイナルの成績を足すと、", "順位が入れかわります。", "上位4チームがファイナルへ。"], sc2),
            (["ファイナルでも、", "ポイントをもう1回半分に。", "差はさらに小さくなります。"], sc3),
            (["ファイナルの成績を足すと、", "3位だったAが、", "逆転で優勝しました。"], sc4),
            (["レギュラーの大差は、", "2回の半分で4分の1。", "だから最後まで目が離せません。", "チームは架空の例です。"], sc5),
            (END, article_end("blog-mleague-points", "計算の全部は記事で"))]
TOPICS["t-half"] = t_half

# ======================= 麻雀AI：NAGAをすすめる =======================
def t_ai():
    vis = art("assets/thumbs/blog-naga-guide.svg", 640, "border-radius:24px")
    def s1(a, b):
        return [head(a, b, "おすすめはNAGA"), stage(a + .2, b, '<div class="mid"><span class="ans">NAGA</span></div>', top=380, anim="pop"),
                stage(a + .6, b, '<div class="vcard">' + vt([("危ない牌・テンパイ率", "数字で見える", "h"), ("7つのタイプ", "答えを見比べる", ""), ("局面を変えて", "もしもを試せる", "")]) + "</div>", top=600)]
    def s2(a, b):
        flow = ('<div class="vcard mid" style="padding:40px 30px">'
                '<div class="ans" style="background:#177083;font-size:56px">雀魂の牌譜</div><div class="big" style="font-size:90px;line-height:1.2">↓</div>'
                '<div class="ans" style="background:#4261AA;font-size:46px;padding:22px 34px">Chromeの拡張機能<br><span style="font-size:36px">雀魂牌譜検討サポーター</span></div>'
                '<div class="big" style="font-size:90px;line-height:1.2">↓</div><div class="ans" style="font-size:56px">NAGAで解析</div></div>')
        return [head(a, b, "雀魂でも使える"), stage(a + .2, b, flow, top=360)]
    def s3(a, b):
        return [head(a, b, "天鳳ならもっと簡単"), stage(a + .3, b, '<div class="vcard">' + vt([("天鳳", "牌譜のURLを貼るだけ", "h"), ("雀魂", "拡張機能で変換", ""), ("対面の麻雀", "局面を作って解析", "")]) + "</div>", top=440)]
    def s4(a, b):
        return [head(a, b, "料金のめやす"), stage(a + .3, b, '<div class="vcard">' + vt([("NAGA", "月550円から", ""), ("天鳳の東南戦", "1回 50NP", ""), ("雀魂", "1局 10NPから", "h")]) + "</div>", top=440),
                stage(a + 1.2, b, '<div class="note">雀魂は<b>悩んだ局だけ</b>選ぶのがコツ</div>', top=1000)]
    return [(["麻雀AI、", "結局どれを使えばいい？"], hook("麻雀AI", "麻雀AI、\nどれを使う？", vis)),
            (["おすすめは、NAGA。", "危ない牌やテンパイの確率まで", "数字で見えて、", "7つのタイプの答えを見比べられます。"], s1),
            (["雀魂で打っている人も大丈夫。", "Chromeの拡張機能を入れれば、", "雀魂の牌譜をNAGAで解析できます。"], s2),
            (["天鳳なら、", "牌譜のURLを貼るだけです。"], s3),
            (["料金は月550円から。", "雀魂は1局ごとなので、", "悩んだ局だけ選ぶのがコツです。"], s4),
            (["やり方は、", "画面つきで記事にまとめました。", "読めばすぐ使えます。"], article_end("blog-naga-guide", "手順は記事で"))]
TOPICS["t-ai"] = t_ai
