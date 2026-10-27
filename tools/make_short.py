# -*- coding: utf-8 -*-
"""ショート動画（縦 1080×1920・30fps）を作る（2026-10-27〜）。
make_sns_v3.py と同じ世界観（淡い緑の地・本物の画面のスマホ・数字のカード・✨）。
HTMLの1コマずつを時刻 t を進めながらブラウザで撮り、ffmpeg で mp4 にする（録画ではないので、カクつかず毎回同じ仕上がり）。

音は入れない（BGMは各アプリの中で、そのアプリが使ってよいと出している曲を後から付ける。著作権の都合）。
出力: まじゃすこ素材/video/<名前>.mp4 （コミットしない）と、見本のコマ <名前>-thumb.png
使い方: python tools/make_short.py [名前]   （省略で全部）
台本の一覧と狙いは docs/video-plan.md

要素の書き方: <div class="..." data-in="2.6" data-out="7" data-a="up"> … data-in〜data-out の間だけ出る。
  data-a: up（下から）/ pop（ふくらむ）/ fade / left / right
  スマホの画面をスクロールする: <img data-scroll="開始秒,終了秒,開始px,終了px">
"""
import io, os, sys, html, subprocess
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_sns_v3 as v3  # CSS・スマホ・カード・LPのイラストを使い回す

MJ = v3.MJ
OUT = os.path.join(MJ, "まじゃすこ素材", "video")
os.makedirs(OUT, exist_ok=True)
W, H, FPS = 1080, 1920, 30

CSS = v3.CSS + """
.cv { width: 1080px; height: 1920px; }
[data-in] { opacity: 0; }
.cap { position: absolute; left: 70px; right: 70px; text-align: center; }
.cap h1 { font-size: 84px; }
.cap p { font-size: 40px; font-weight: 700; color: #4F5C5A; margin-top: 18px; }
.hook h1 { font-size: 104px; line-height: 1.25; }
.badge { display: inline-block; background: #E75620; color: #fff; font-weight: 900; font-size: 40px; border-radius: 999px; padding: 12px 36px; margin-bottom: 30px; }
.badge.g { background: #177083; }
.card { position: absolute; left: 90px; right: 90px; background: #fff; border-radius: 40px; padding: 60px 56px; box-shadow: 0 24px 60px rgba(16,40,36,.18); }
.card .no { display: inline-grid; place-items: center; width: 92px; height: 92px; border-radius: 50%; background: #E75620; color: #fff; font-size: 52px; font-weight: 900; }
.card .tx { font-size: 66px; font-weight: 900; line-height: 1.4; margin-top: 26px; color: #1F2A28; }
.end { position: absolute; left: 0; right: 0; text-align: center; }
.end img.logo { width: 200px; height: 200px; border-radius: 46px; box-shadow: 0 20px 50px rgba(16,40,36,.2); }
.end .nm { font-size: 92px; font-weight: 900; margin-top: 30px; }
.end .dm { font-size: 56px; font-weight: 900; color: #177083; margin-top: 6px; }
.end .pt { font-size: 40px; font-weight: 700; color: #4F5C5A; margin-top: 30px; }
.end .go { display: inline-block; margin-top: 50px; background: #E75620; color: #fff; font-size: 50px; font-weight: 900; border-radius: 999px; padding: 28px 70px; }
.calc { position: absolute; }
table.ex { border-collapse: separate; border-spacing: 0 18px; margin: 0 auto; }
table.ex td { font-size: 54px; font-weight: 900; padding: 0 20px; }
table.ex td.l { color: #4F5C5A; font-size: 44px; text-align: left; }
table.ex td.p { color: #1A237E; text-align: right; } table.ex td.n { color: #C62828; text-align: right; }
.eq { font-size: 52px; font-weight: 900; color: #1F2A28; text-align: center; line-height: 1.7; }
.eq b { color: #1A237E; } .eq .o { color: #E75620; }
.race-h { position: absolute; top: 250px; font-size: 46px; font-weight: 900; text-align: center; width: 480px; }
.race-h .tm { display: block; font-size: 76px; color: #1A237E; margin-top: 6px; font-variant-numeric: tabular-nums; }
.race-h.l .tm { color: #C62828; }
.memo { position: absolute; left: 40px; top: 470px; width: 480px; height: 1080px; background: #FFFDF5; border-radius: 30px; box-shadow: 0 20px 50px rgba(16,40,36,.16);
  padding: 40px 34px; background-image: repeating-linear-gradient(#FFFDF5 0 64px, #E9E2CC 64px 66px); background-position: 0 30px; }
.memo .ln { font-size: 33px; font-weight: 700; color: #3A3A3A; height: 66px; line-height: 66px; white-space: nowrap; font-variant-numeric: tabular-nums; }
.memo .ln.r { font-weight: 900; color: #1A237E; } .memo .ln.n { color: #C62828; font-weight: 900; }
.memo .ln.nm { color: #177083; font-weight: 900; }
.done { position: absolute; z-index: 6; background: #177083; color: #fff; font-size: 44px; font-weight: 900; border-radius: 999px; padding: 18px 40px; box-shadow: 0 14px 30px rgba(16,40,36,.25); }
.done.l { background: #C62828; }
.fing, .rip { position: absolute; left: 0; top: 0; border-radius: 50%; pointer-events: none; opacity: 0; }
.fing { background: rgba(255,255,255,.6); border: 3px solid rgba(31,42,40,.45); box-shadow: 0 6px 16px rgba(16,40,36,.35); z-index: 5; }
.rip { border: 5px solid #E75620; z-index: 4; }
"""

JS = r"""
window.setLive = async (n, src, x, y, op, sc, rx, ry, rs, ro) => {
  const img = document.getElementById('lv' + n);
  if (src) { img.src = src; try { await img.decode(); } catch (e) {} }
  const f = document.getElementById('fg' + n), r = document.getElementById('rp' + n);
  if (x !== null) f.style.transform = `translate(${x}px, ${y}px) translate(-50%, -50%) scale(${sc})`;
  f.style.opacity = op;
  r.style.transform = `translate(${rx}px, ${ry}px) translate(-50%, -50%) scale(${rs})`;
  r.style.opacity = ro;
};
window.render = (t) => {
  const ease = x => 1 - Math.pow(1 - x, 3);
  const back = x => { const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
  document.querySelectorAll('[data-in]').forEach(e => {
    const a = +e.dataset.in, b = e.dataset.out ? +e.dataset.out : 1e9;
    const p = Math.min(1, Math.max(0, (t - a) / 0.4)), q = Math.min(1, Math.max(0, (b - t) / 0.3));
    const v = Math.min(p, q), k = e.dataset.a || 'up', base = e.dataset.tf || '';
    e.style.opacity = v;
    let tf = '';
    if (k === 'up') tf = `translateY(${(1 - ease(v)) * 70}px)`;
    if (k === 'pop') tf = `scale(${p < 1 ? 0.5 + 0.5 * back(p) : (0.5 + 0.5 * q) })`;
    if (k === 'left') tf = `translateX(${(1 - ease(v)) * -120}px)`;
    if (k === 'right') tf = `translateX(${(1 - ease(v)) * 120}px)`;
    e.style.transform = base + ' ' + tf;
  });
  document.querySelectorAll('[data-scroll]').forEach(e => {
    const [a, b, y0, y1] = e.dataset.scroll.split(',').map(Number);
    const p = Math.min(1, Math.max(0, (t - a) / (b - a))), s = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
    e.style.transform = `translateY(${-(y0 + (y1 - y0) * s)}px)`;
  });
  document.querySelectorAll('[data-timer]').forEach(e => {
    const [a, b] = e.dataset.timer.split(',').map(Number);
    const v = Math.max(0, Math.min(t, b) - a);
    e.textContent = v.toFixed(1) + '秒';
  });
  document.querySelectorAll('[data-shake]').forEach(e => {
    const [a, b] = e.dataset.shake.split(',').map(Number);
    e.style.rotate = (t > a && t < b) ? `${Math.sin(t * 40) * 4}deg` : '0deg';
  });
};
"""

def esc(s):
    return html.escape(s).replace("\n", "<br>")

def at(a, b, inner, cls="", style="", anim="up"):
    out = f' data-out="{b}"' if b else ""
    return f'<div class="{cls}" style="{style}" data-in="{a}"{out} data-a="{anim}">{inner}</div>'

def phone_at(a, b, img, y=560, w=520, scroll=None):
    ph, hh = v3.phone(img, (W - w) // 2, y, w)
    if scroll:
        ph = ph.replace("<img ", f'<img data-scroll="{scroll}" ', 1)
    return at(a, b, ph, style="position:absolute;inset:0"), hh

def chip_at(a, b, c, side, y):
    ch = v3.chip(c, 60, y) if side == "l" else v3.chip(c, 0, y).replace('style="left:0px;', 'style="right:60px;')
    return at(a, b, ch, style="position:absolute;inset:0", anim="pop")

# ---------------- 操作している画面（tools/record_play.py の録画） ----------------
import json, bisect
from PIL import Image
CLIPS = os.path.join(OUT, "clips")
LIVE = []  # build() のたびに作り直す

def live_at(a, b, clip, y=520, w=560, start=0.0, x=None):
    """録画 clip の start 秒からを、動画の a〜b 秒に出す。指とタップの波紋はここで30コマ/秒で描く"""
    d = os.path.join(CLIPS, clip)
    tl = json.load(io.open(os.path.join(d, "timeline.json"), encoding="utf-8"))
    n = len(LIVE)
    im = Image.open(os.path.join(d, tl["frames"][0][1])).convert("RGB")
    r, g, bb = im.getpixel((im.width // 2, 2))
    LIVE.append({"n": n, "a": a, "b": b, "start": start, "tl": tl, "dir": d, "k": 1, "ts": [f[0] for f in tl["frames"]], "cur": None})
    first = v3.furl(os.path.join(d, tl["frames"][0][1]))
    inner = w - 2 * round(w * v3.PH_BEZEL)
    k = inner / 390
    LIVE[-1]["k"] = k
    body, h, strip, inner, bz = v3.phone_frame(w, f"#{r:02X}{g:02X}{bb:02X}",
        f'<img id="lv{n}" src="{first}">'
        f'<div class="rip" id="rp{n}" style="width:{round(70*k)}px;height:{round(70*k)}px"></div>'
        f'<div class="fing" id="fg{n}" style="width:{round(50*k)}px;height:{round(50*k)}px"></div>')
    ph = (f'<div class="ph" style="left:{(W - w) // 2 if x is None else x}px;top:{y}px;width:{w}px;height:{h}px;padding:{bz}px;border-radius:{round(w * v3.PH_R)}px">'
          + body + '</div>')
    return at(a, b, ph, style="position:absolute;inset:0"), h, tl["marks"]

def live_state(L, t):
    """動画の時刻 t のときの、録画のコマ・指・波紋"""
    ct = L["start"] + (t - L["a"])
    tl = L["tl"]
    i = max(0, bisect.bisect_right(L["ts"], ct) - 1)
    fn = tl["frames"][i][1]
    ease = lambda x: x * x * (3 - 2 * x)
    x = y = None; op = 0.0
    mv = tl["moves"]
    if mv and ct >= mv[0][0] - 0.25:
        x, y = mv[0][2], mv[0][3]
        for t0, t1, x0, y0, x1, y1 in mv:
            if ct >= t1: x, y = x1, y1
            elif ct >= t0:
                e = ease((ct - t0) / (t1 - t0)); x, y = x0 + (x1 - x0) * e, y0 + (y1 - y0) * e
        # 指は動かしている間とタップの前後だけ見せる（止まっている間は離したように消す）
        spans = [(t0, t1) for t0, t1, *_ in mv] + [(tt, tt + 0.35) for tt, *_ in tl["taps"]]
        dist = min(0 if a0 <= ct <= a1 else min(abs(ct - a0), abs(ct - a1)) for a0, a1 in spans)
        op = 1.0 if dist <= 0.45 else max(0.0, 1 - (dist - 0.45) / 0.25)
    sc, rx, ry, rs, ro = 1.0, 0, 0, 0, 0
    for tt, tx, ty in tl["taps"]:
        if tt - 0.1 <= ct <= tt + 0.15: sc = 0.82
        if 0 <= ct - tt <= 0.55:
            p = (ct - tt) / 0.55; rx, ry, rs, ro = tx, ty, 0.4 + 1.3 * p, 1 - p
    k = L["k"]
    return fn, (None if x is None else round(x * k, 1)), (None if y is None else round(y * k, 1)), round(op, 3), sc, round(rx * k, 1), round(ry * k, 1), round(rs, 3), round(ro, 3)

def end_card(a, line="無料・アプリDL不要・会員登録不要"):
    logo = v3.furl(os.path.join(MJ, "assets", "favicon.png"))
    return at(a, None, f'''<img class="logo" src="{logo}"><div class="nm">まじゃすこ</div><div class="dm">majasco.jp</div>
      <div class="pt">{esc(line)}</div><div class="go">プロフィールのリンクから</div>''', cls="end", style="top:520px", anim="pop")

def sparkles():
    S = v3.SPARK
    return (S.format(st="left:900px;top:540px;width:70px", c="#E75620") + S.format(st="left:110px;top:1500px;width:52px", c="#177083")
            + S.format(st="left:150px;top:420px;width:34px", c="#9FC3BD"))

# ---------------- 台本 ----------------
def v_kinou():
    """正面から機能を見せる。導入で「まだ電卓？」と問いかける"""
    hero = v3.hero_svg().replace('<svg ', '<svg style="width:940px;height:auto;display:block;margin:0 auto" ', 1)
    els = [
        at(0, 2.8, f'<div class="badge">セット麻雀の人へ</div><h1>麻雀の集計、<br>まだ電卓で<br>やってる？</h1>', cls="cap hook", style="top:330px", anim="pop"),
        at(0.5, 2.8, hero, style="position:absolute;left:0;right:0;top:1010px", anim="fade"),
        at(2.8, 7.2, '<h1>点数を入れるだけ。</h1><p>最後の1人は自動で入る</p>', cls="cap", style="top:250px"),
    ]
    e, hh = phone_at(2.8, 7.2, "howto-3.jpg"); els.append(e)
    els.append(chip_at(4.0, 7.2, ("合計", "100,000点", "pos"), "r", 1100))
    els.append(at(7.2, 11.6, '<h1>順位とスコアが、<br>その場で出る。</h1>', cls="cap", style="top:230px"))
    e, hh = phone_at(7.2, 11.6, "howto-4.jpg", y=600); els.append(e)
    for i, (c, s) in enumerate([(("", "+69.1", ("medal", 1)), "l"), (("", "+64.0", ("medal", 2)), "r"), (("", "−53.5", ("medal", 3)), "l")]):
        els.append(chip_at(8.0 + i * 0.45, 11.6, c, s, 820 + i * 150))
    els.append(at(11.6, 15.6, '<h1>URLを送れば、<br>全員のスマホに。</h1>', cls="cap", style="top:230px"))
    e, hh = phone_at(11.6, 15.6, "howto-2.jpg", y=600); els.append(e)
    els.append(chip_at(12.6, 15.6, ("見る人は", "登録いらず", ""), "r", 900))
    els.append(at(15.6, 20.4, '<h1>通算の成績も、<br>自動でたまる。</h1>', cls="cap", style="top:230px"))
    e, hh = phone_at(15.6, 20.4, "lp-mypage.jpg", y=600, scroll="16.6,19.6,0,240"); els.append(e)
    els.append(chip_at(16.4, 20.4, ("通算スコア", "+347.0", "pos"), "r", 860))
    els.append(chip_at(17.0, 20.4, ("トップ率", "26%", ""), "l", 1060))
    els.append(end_card(20.4))
    return 24.5, els

def v_aruaru():
    """麻雀あるある（集計係）。共感 → 最後に解決"""
    items = ["終わったあと、\n電卓を渡される", "ウマ・オカの計算で\n手が止まる", "「先月どっちが\n勝ってた？」に\n誰も答えられない", "スコア表の写真が\nLINEの奥に消える"]
    els = [at(0, 2.8, '<div class="badge">あるある</div><h1>セット麻雀の<br>集計係あるある</h1>', cls="cap hook", style="top:640px", anim="pop")]
    t = 2.8
    for i, it in enumerate(items):
        els.append(at(t, t + 3.3, f'<span class="no">{i+1}</span><div class="tx">{esc(it)}</div>', cls="card", style="top:640px", anim="right"))
        t += 3.3
    els.append(at(t, t + 4.2, '<h1>それ、まじゃすこなら<br>ぜんぶ自動。</h1>', cls="cap", style="top:230px", anim="pop"))
    e, hh = phone_at(t + 0.3, t + 4.2, "howto-4.jpg", y=600); els.append(e)
    els.append(chip_at(t + 1.2, t + 4.2, ("", "+69.1", ("medal", 1)), "l", 900))
    els.append(chip_at(t + 1.6, t + 4.2, ("通算", "自動", ""), "r", 1100))
    els.append(end_card(t + 4.2))
    return t + 8.2, els

def v_umaoka():
    """初心者の壁：ウマ・オカ。例はアプリの使い方の画面と同じ数字（健太 45,200点 → +65.2）"""
    els = [at(0, 2.8, '<div class="badge g">初心者の壁</div><h1>ウマ・オカって、<br>結局なに？</h1><p>20秒でわかる</p>', cls="cap hook", style="top:620px", anim="pop")]
    els.append(at(2.8, 8.4, '<div class="badge g">オカ</div><h1>トップへの<br>ごほうび</h1>', cls="cap", style="top:300px"))
    els.append(at(3.6, 8.4, '<div class="eq">25,000点持ち・30,000点返し<br>4人とも 5,000点ずつ出して<br>トップに <b>+20</b></div>', cls="cap", style="top:820px"))
    els.append(at(8.4, 14.0, '<div class="badge g">ウマ</div><h1>順位で動く<br>ポイント</h1><p>よくある「10-30」なら</p>', cls="cap", style="top:300px"))
    els.append(at(9.2, 14.0, '<table class="ex"><tr><td class="l">1位</td><td class="p">+30</td></tr><tr><td class="l">2位</td><td class="p">+10</td></tr>'
                  '<tr><td class="l">3位</td><td class="n">−10</td></tr><tr><td class="l">4位</td><td class="n">−30</td></tr></table>', cls="cap", style="top:900px"))
    els.append(at(14.0, 20.0, '<h1>たとえば、<br>45,200点でトップなら</h1>', cls="cap", style="top:300px"))
    els.append(at(14.8, 20.0, '<div class="eq">素点 <b>+15.2</b><br>ウマ <b>+30</b><br>オカ <b>+20</b><br>＝ <span class="o">+65.2</span></div>', cls="cap", style="top:760px"))
    els.append(at(20.0, 24.2, '<h1>この計算、<br>まじゃすこなら自動。</h1>', cls="cap", style="top:230px", anim="pop"))
    e, hh = phone_at(20.3, 24.2, "howto-4.jpg", y=600); els.append(e)
    els.append(end_card(24.2))
    return 28.2, els

def caps(items, top=200):
    """[(出る秒, 消える秒, 見出し, ひとこと)] の字幕を並べる"""
    return [at(a, b, f'<h1>{esc(h)}</h1>' + (f'<p>{esc(p)}</p>' if p else ''), cls="cap", style=f"top:{top}px") for a, b, h, p in items]

def v_play_quick():
    """実際の操作：はじめる→4人→点数を入れる→最後の1人は自動→順位→共有"""
    T0 = 2.6
    els = [at(0, T0, '<div class="badge g">実際の操作</div><h1>麻雀のスコア、<br>スマホで<br>記録してみた。</h1>', cls="cap hook", style="top:620px", anim="pop")]
    e, hh, m = live_at(T0, T0 + 19.4, "play-quick", y=560, w=540)
    els.append(e)
    c = lambda k: T0 + m[k]
    els += caps([(T0, c("game"), "「はじめる」→\n人数を選ぶ", "登録もインストールもなし"),
                 (c("game"), c("auto"), "点数を入れていく", "下2桁の00は入れなくていい"),
                 (c("auto"), c("done"), "最後の1人は、\n自動。", ""),
                 (c("done"), c("share"), "順位とスコアが、\nその場で。", "ウマ・オカも計算ずみ"),
                 (c("share"), T0 + 19.4, "URLを送れば、\n全員のスマホに。", "")])
    els.append(end_card(T0 + 19.4))
    return T0 + 23.4, els

def v_play_rounds():
    """実際の操作：4試合目を入れると順位が入れかわり、成績表まで自動"""
    T0 = 2.6
    els = [at(0, T0, '<div class="badge g">実際の操作</div><h1>4試合目を<br>入れてみる。</h1><p>順位はどう変わる？</p>', cls="cap hook", style="top:640px", anim="pop")]
    e, hh, m = live_at(T0, T0 + 20.4, "play-rounds", y=560, w=540)
    els.append(e)
    c = lambda k: T0 + m[k]
    els += caps([(T0, c("input"), "3試合目まで、\n健太がトップ。", ""),
                 (c("input"), c("done"), "4試合目の点数を\n入れると…", ""),
                 (c("done"), c("scroll"), "美咲が、その場で\n逆転！", ""),
                 (c("scroll"), T0 + 20.4, "個人成績も、\n総当たりも自動。", "")])
    els.append(end_card(T0 + 20.4))
    return T0 + 24.4, els

def play_video(clip, badge, hook, steps, x=None, w=540):
    """操作の録画1本を見せる動画。steps = [(録画の目印 or 0, 見出し)]。見出しは目印の時刻から次の目印まで"""
    T0 = 2.6
    els = [at(0, T0, f'<div class="badge g">{badge}</div><h1>{esc(hook)}</h1>', cls="cap hook", style="top:660px", anim="pop")]
    tl = json.load(io.open(os.path.join(CLIPS, clip, "timeline.json"), encoding="utf-8"))
    end = tl["end"]
    e, hh, m = live_at(T0, T0 + end, clip, y=560, w=w, x=x)
    els.append(e)
    ts = [0 if k == 0 else m[k] for k, _ in steps] + [end]
    els += caps([(T0 + ts[i], T0 + ts[i + 1], h, "") for i, (_, h) in enumerate(steps)])
    els.append(end_card(T0 + end))
    return T0 + end + 4.0, els

PAGE_VIDEOS = {
 "nakama-rank": ("仲間ページ", "仲間の通算順位、\n表彰台で決まる。",
   [(0, "いつものメンバーの\n通算順位が表彰台に"), ("avg", "平均着順で\n並べかえ"), ("top", "トップ率でも"), ("las", "ラス回避でも"), ("list", "全員の順位が\nずらり")]),
 "nakama-grid": ("仲間ページ", "全員の成績を、\n1枚の表に。",
   [(0, "「成績表」を押すと"), ("grid", "試合数・着順の回数・\nトップ率まで"), ("side", "横にすべらせて\n全員ぶん")]),
 "nakama-h2h": ("仲間ページ", "あの人とあの人、\nどっちが強い？",
   [(0, "「対戦」を押すと"), ("h2h", "メンバーどうしの\n直接対決が表に"), ("side", "左の人から見た\n勝ち-負け")]),
 "nakama-member": ("仲間ページ", "名前を押すと、\nその人の成績が\n開く。",
   [(0, "表彰台の1位を押すと"), ("sheet", "平均着順・トップ率・\n推移まで"), ("h2h", "相手ごとの\n勝ち負けも"), ("vs", "2人の直接対決を\nくらべる")]),
 "nakama-games": ("仲間ページ", "あの日の結果、\nすぐ出せる？",
   [(0, "「過去の試合」を押すと"), ("list", "打った日が\nずらりと並ぶ"), ("open", "1つ押すと"), ("result", "その日の結果が\n全部わかる")]),
 "mypage-stats": ("マイページ", "自分の成績、\n数字で\n見たことある？",
   [(0, "「マイページ」を押すと"), ("top", "平均着順・トップ率・\nラス回避"), ("graph", "通算スコアの推移も\nグラフで")]),
 "mypage-graph": ("マイページ", "先月、\n勝ってた？",
   [(0, "マイページを開いて"), ("month", "通算スコアの\n推移のグラフ"), ("pick", "月を押すと"), ("pop", "その月の試合が\n並ぶ")]),
 "mypage-h2h": ("マイページ", "あの人には、\n勝ち越してる？",
   [(0, "マイページを開いて"), ("tab", "「対戦成績」を押すと"), ("h2h", "相手ごとの\n勝ち-負け"), ("pct", "勝率順にも\n並べかえ"), ("vs", "1人押すと\nくわしく")]),
 "mypage-hist": ("マイページ", "打った日の結果、\nぜんぶ残る。",
   [(0, "マイページを開いて"), ("tab", "「過去の試合」を押すと"), ("list", "順位とスコアが\n日ごとに"), ("open", "1つ押すと"), ("result", "その日の結果が\n開く")]),
 "mypage-sanma": ("マイページ", "三麻と四麻、\n成績は\n分けたい派？",
   [(0, "マイページを開いて"), ("yonma", "四麻の成績"), ("tap3", "「三麻」を押すと"), ("sanma", "三麻の成績に\n切りかわる"), ("back", "四麻にも\nすぐ戻せる")]),
}

def v_calc_vs():
    """電卓 vs まじゃすこ：左は電卓の計算メモ、右は実際の操作。上にタイマー"""
    tl = json.load(io.open(os.path.join(CLIPS, "play-quick", "timeline.json"), encoding="utf-8"))
    m = tl["marks"]
    RS = 2.8                      # よーいドン
    s0 = m["game"] - 0.2          # 録画の「点数入力」の少し前から
    fin = RS + (m["done"] + 0.3 - s0)  # まじゃすこが終わる時刻
    END = fin + 5.5
    els = [at(0, RS, '<div class="badge">どっちが速い？</div><h1>電卓 vs<br>まじゃすこ</h1><p>4人ぶんのスコアの集計</p>', cls="cap hook", style="top:640px", anim="pop")]
    els.append(at(RS, END, f'<div class="race-h l" style="left:40px">電卓<span class="tm" data-timer="{RS},999">0.0秒</span></div>', style="position:absolute;inset:0", anim="fade"))
    els.append(at(RS, END, f'<div class="race-h" style="left:560px">まじゃすこ<span class="tm" data-timer="{RS},{fin}">0.0秒</span></div>', style="position:absolute;inset:0", anim="fade"))
    lines = [("nm", "健太 45,200点"), ("", "45,200 − 30,000"), ("", "＝ +15.2"), ("", "＋ウマ30 ＋オカ20"), ("r", "＝ +65.2"),
             ("nm", "美咲 28,100点"), ("", "28,100 − 30,000"), ("", "＝ −1.9"), ("", "＋ウマ10"), ("r", "＝ +8.1"),
             ("nm", "翔 17,300点"), ("", "17,300 − 30,000"), ("", "＝ −12.7"), ("", "−ウマ10"), ("n", "＝ −22.7")]
    memo = ""
    for i, (c, tx) in enumerate(lines):
        memo += f'<div class="ln {c}" data-in="{RS + 0.3 + i * 0.95:.2f}" data-out="{END}" data-a="fade">{html.escape(tx)}</div>'
    els.append(at(RS, END, f'<div class="memo">{memo}</div>', style="position:absolute;inset:0", anim="fade"))
    e, hh, mm = live_at(RS, END, "play-quick", y=470, w=480, start=s0, x=560)
    els.append(e)
    els.append(at(fin, END, f'<div class="done" style="left:690px;top:1590px">完了！</div>', style="position:absolute;inset:0", anim="pop"))
    els.append(at(fin + 0.8, END, f'<div class="done l" style="left:120px;top:1590px">まだ3人目…</div>', style="position:absolute;inset:0", anim="pop"))
    els.append(at(fin + 2.4, END, '<h1>この差、毎回。</h1>', cls="cap", style="top:130px", anim="pop"))
    els.append(end_card(END))
    return END + 4.0, els

VIDEOS = {"kinou": v_kinou, "aruaru-shukei": v_aruaru, "kabe-umaoka": v_umaoka,
          "play-quick": v_play_quick, "play-rounds": v_play_rounds, "calc-vs": v_calc_vs}
for _k, (_b, _h, _st) in PAGE_VIDEOS.items():
    VIDEOS[_k] = (lambda k=_k, b=_b, h=_h, st=_st: play_video(k, b, h, st))

def build(name, fn):
    LIVE.clear()
    dur, els = fn()
    body = f'<div class="cv">{sparkles()}{"".join(els)}<div class="dom" style="right:60px;top:110px;font-size:34px">majasco.jp</div></div>'
    doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body>{body}<script>{JS}</script></body></html>"
    hp = os.path.join(OUT, "_" + name + ".html")
    io.open(hp, "w", encoding="utf-8").write(doc)
    mp4 = os.path.join(OUT, name + ".mp4")
    ff = subprocess.Popen([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-preset", "medium", "-movflags", "+faststart", mp4], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(v3.furl(hp)); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(400)
        n = int(dur * FPS)
        for i in range(n):
            t = i / FPS
            for L in LIVE:
                if L["a"] - 0.5 <= t <= L["b"] + 0.4:
                    fn_, x, y, op, sc, rx, ry, rs, ro = live_state(L, t)
                    src = None if fn_ == L["cur"] else v3.furl(os.path.join(L["dir"], fn_))
                    L["cur"] = fn_
                    pg.evaluate("(a) => setLive(...a)", [L["n"], src, x, y, op, sc, rx, ry, rs, ro])
            pg.evaluate(f"render({t})")
            buf = pg.screenshot(type="jpeg", quality=92)
            ff.stdin.write(buf)
            if abs(t - 1.5) < 1 / FPS / 2:
                io.open(os.path.join(OUT, name + "-thumb.jpg"), "wb").write(buf)
        b.close()
    ff.stdin.close(); ff.wait()
    os.remove(hp)
    print("ok", name, f"{dur:.1f}s", mp4)

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    for k, fn in VIDEOS.items():
        if not only or only in k:
            build(k, fn)
