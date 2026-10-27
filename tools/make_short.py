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
"""

JS = r"""
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

VIDEOS = {"kinou": v_kinou, "aruaru-shukei": v_aruaru, "kabe-umaoka": v_umaoka}

def build(name, fn):
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
