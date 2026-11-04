# -*- coding: utf-8 -*-
"""テンポの速い、音ありのショート動画を作る（2026-11-04〜）。縦 1080×1920・30fps。
1拍0.4秒（150BPM）に合わせて、1.6秒ごとに画面を切り替える。文字は叩きつけて、画面をゆらす。

音はすべてここで作るので、外の曲の権利は関係ない:
  BGM・効果音＝numpy で合成／ナレーション＝Windows の音声合成（Microsoft Haruka）
出力: まじゃすこ素材/video/<名前>.mp4 （コミットしない）
使い方: python tools/make_hype.py [名前]   （省略で全部）
台本は HYPE に足す。1コマ＝cut(長さの拍, 地の色, 中身, 声, 効果音)
"""
import io, os, sys, subprocess, tempfile, wave
import numpy as np
import imageio_ffmpeg
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_short as ms
v3 = ms.v3

W, H, FPS, SR = 1080, 1920, 30, 44100
BEAT = 0.4
GREEN, ORANGE, DARK, CREAM = "#177083", "#E75620", "#1F2A28", "#FFF7E8"
ACC = "#FFE24A"

CSS = ms.CSS + """
html, body { margin: 0; background: #000; overflow: hidden; }
.cv { position: relative; overflow: hidden; }
.cut { position: absolute; inset: 0; display: none; overflow: hidden; }
.t { position: absolute; left: 60px; right: 60px; text-align: center; font-weight: 900; line-height: 1.16; letter-spacing: -2px; color: #fff; }
.t.s { font-size: 74px; } .t.m { font-size: 118px; } .t.l { font-size: 172px; } .t.x { font-size: 300px; }
.t.k { color: #1F2A28; } .t b { color: #FFE24A; font-weight: 900; } .t.k b { color: #E75620; }
.st { position: absolute; background: #fff; color: #1A237E; font-size: 92px; font-weight: 900; border-radius: 28px; padding: 16px 38px; box-shadow: 0 16px 0 rgba(0,0,0,.22); font-variant-numeric: tabular-nums; }
.st.y { background: #FFE24A; color: #1F2A28; }
.fl { position: absolute; inset: 0; background: #fff; opacity: 0; z-index: 50; pointer-events: none; }
.hy-pg { position: absolute; left: 0; top: 0; height: 14px; background: #FFE24A; z-index: 40; }
.en { position: absolute; left: 0; right: 0; top: 400px; text-align: center; color: #fff; }
.en img { width: 240px; height: 240px; border-radius: 54px; box-shadow: 0 14px 0 rgba(0,0,0,.2); }
.en .nm { font-size: 128px; font-weight: 900; margin-top: 34px; } .en .dm { font-size: 70px; font-weight: 900; color: #FFE24A; margin-top: 8px; }
.en .pt { font-size: 46px; font-weight: 800; margin-top: 34px; } .en .go { display: inline-block; margin-top: 46px; background: #E75620; color: #fff; font-size: 56px; font-weight: 900; border-radius: 999px; padding: 28px 64px; }
"""

JS = r"""
window.render = (t, cuts, beat) => {
  let c = cuts.findIndex(x => t >= x[0] && t < x[1]); if (c < 0) c = cuts.length - 1;
  const t0 = cuts[c][0], u = t - t0;
  document.querySelectorAll('.cut').forEach((e, i) => { e.style.display = i === c ? 'block' : 'none'; });
  const cut = document.querySelectorAll('.cut')[c];
  const out = x => 1 - Math.pow(1 - x, 3);
  let shake = 0;
  cut.querySelectorAll('[data-d]').forEach(e => {
    const d = +e.dataset.d, k = e.dataset.k, r = e.dataset.r || 0, p = (u - d);
    if (p < 0) { e.style.opacity = 0; return; }
    e.style.opacity = 1;
    if (k === 'slam') { const q = Math.min(1, p / 0.13); e.style.transform = `rotate(${r}deg) scale(${2.5 - 1.5 * out(q)})`; if (p < 0.24) shake = Math.max(shake, 1 - p / 0.24); }
    if (k === 'rise') { const q = Math.min(1, p / 0.2), o = 1 + 2.7 * Math.pow(q - 1, 3) + 1.7 * Math.pow(q - 1, 2); e.style.transform = `translateY(${(1 - o) * 900}px) scale(${1 + p * 0.035})`; }
    if (k === 'side') { const q = Math.min(1, p / 0.14); e.style.transform = `rotate(${r}deg) translateX(${(1 - out(q)) * 900 * (e.dataset.s || 1)}px)`; }
  });
  cut.querySelectorAll('[data-scroll]').forEach(e => {
    const [a, b, y0, y1] = e.dataset.scroll.split(',').map(Number);
    const p = Math.min(1, Math.max(0, (u - a) / (b - a))), s = p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
    e.style.transform = `translateY(${-(y0 + (y1 - y0) * s)}px)`;
  });
  const b = (t % beat) / beat, pulse = 1 + 0.012 * Math.pow(1 - b, 3);
  const cv = document.querySelector('.cv');
  const sx = Math.sin(t * 93) * 22 * shake, sy = Math.cos(t * 71) * 22 * shake;
  cv.style.transform = `translate(${sx}px, ${sy}px) scale(${pulse})`;
  document.querySelector('.fl').style.opacity = Math.max(0, 0.75 - u / 0.09);
  document.querySelector('.hy-pg').style.width = (t / cuts[cuts.length - 1][1] * 100) + '%';
};
"""

def T(cls, html, top, d=0.0, k="slam", r=0):
    return f'<div class="t {cls}" style="top:{top}px" data-d="{d}" data-k="{k}" data-r="{r}">{html}</div>'

def S(txt, x, y, d, r=-5, y_=False, s=1):
    return f'<div class="st{" y" if y_ else ""}" style="left:{x}px;top:{y}px" data-d="{d}" data-k="side" data-r="{r}" data-s="{s}">{txt}</div>'

def PH(img, y=700, w=600, d=0.08, scroll=None):
    ph, _ = v3.phone(img, (W - w) // 2, y, w)
    if scroll:
        ph = ph.replace("<img ", f'<img data-scroll="{scroll}" ', 1)
    return f'<div style="position:absolute;inset:0" data-d="{d}" data-k="rise">{ph}</div>'

def END():
    logo = v3.furl(os.path.join(ms.MJ, "assets", "favicon.png"))
    return f'''<div class="en" data-d="0" data-k="slam"><img src="{logo}"><div class="nm">まじゃすこ</div><div class="dm">majasco.jp</div>
      <div class="pt">無料・アプリDL不要・会員登録不要</div><div class="go">プロフィールのリンクから</div></div>'''

def cut(beats, bg, html, voice=None, sfx=()):
    return dict(beats=beats, bg=bg, html=html, voice=voice, sfx=sfx)

def h_kinou():
    return [
        cut(4, DARK, T("s", "麻雀の集計", 500) + T("l", "<b>まだ<br>電卓？</b>", 640, 0.2, r=-3), "麻雀の集計、まだ電卓？", [("hit", .2)]),
        cut(4, GREEN, T("m", "点数を<br><b>入れるだけ！</b>", 230) + PH("howto-3.jpg"), "点数を、入れるだけ！", [("hit", 0)]),
        cut(4, ORANGE, T("m", "ウマもオカも", 300) + T("l", "<b>全自動！</b>", 500, .2, r=-3)
            + S("+69.1", 120, 880, .5) + S("+64.0", 560, 1040, .7, 4, s=-1) + S("−53.5", 120, 1210, .9, -3), "ウマもオカも、全自動！", [("hit", .2), ("coin", .5), ("coin", .7), ("coin", .9)]),
        cut(4, GREEN, T("m", "順位も<br><b>その場で！</b>", 230) + PH("howto-4.jpg"), "順位も、その場で！", [("hit", 0)]),
        cut(4, DARK, T("m", "URLを送れば<br><b>全員に！</b>", 230) + PH("howto-2.jpg"), "URLを送れば、全員に！", [("hit", 0)]),
        cut(4, GREEN, T("m", "成績も<br><b>勝手にたまる！</b>", 230) + PH("lp-mypage.jpg", scroll="0.3,1.5,0,240"), "成績も、勝手にたまる！", [("hit", 0)]),
        cut(4, ORANGE, T("m", "仲間の順位も<br><b>一発！</b>", 230) + PH("lp-rank.jpg"), "仲間の順位も、一発！", [("hit", 0)]),
        cut(2, DARK, T("l", "これ<b>全部</b>", 720), "これ全部", [("rise", -1.2)]),
        cut(2, ORANGE, T("x", "<b>無料</b>", 660, r=-4), "無料！", [("boom", 0)]),
        cut(7, GREEN, END(), "まじゃすこ。プロフィールのリンクから！", [("ding", 0)]),
    ]

HYPE = {"hype-kinou": h_kinou}

# ---------------- 音 ----------------
def tone(f, d, kind="sq", a=1.0):
    t = np.arange(int(d * SR)) / SR
    ph = (f * t) % 1
    w = np.where(ph < .5, 1., -1.) if kind == "sq" else 2 * np.abs(2 * ph - 1) - 1 if kind == "tri" else np.sin(2 * np.pi * f * t)
    return w * a * np.exp(-t / max(d * .55, .01)) * np.minimum(1, t / .002)

def put(buf, x, t, g=1.0):
    i = int(t * SR)
    if i < 0: x = x[-i:]; i = 0
    n = min(len(x), len(buf) - i)
    if n > 0: buf[i:i + n] += x[:n] * g

def noise(d, seed=1):
    return np.random.default_rng(seed).uniform(-1, 1, int(d * SR))

def lowpass(x, a):
    y = np.empty_like(x); s = 0.0
    for i in range(len(x)):
        s += a[i] * (x[i] - s) if hasattr(a, "__len__") else a * (x[i] - s); y[i] = s
    return y

def kick():
    t = np.arange(int(.22 * SR)) / SR
    return np.sin(2 * np.pi * (48 * t + 22 * (1 - np.exp(-t * 34)))) * np.exp(-t * 15)

def snare():
    t = np.arange(int(.16 * SR)) / SR
    return (noise(.16, 2) * .8 + np.sin(2 * np.pi * 200 * t) * .4) * np.exp(-t * 26)

def hat():
    x = noise(.05, 3); return (x - lowpass(x, .3)) * np.exp(-np.arange(len(x)) / SR * 90)

NOTE = lambda n: 440 * 2 ** ((n - 69) / 12)
CH = [(60, 64, 67), (55, 59, 62), (57, 60, 64), (53, 57, 60)]  # C G Am F

def bgm(dur, drop):
    """drop: 音を止める時刻（a, b）。b から元に戻る"""
    b = np.zeros(int((dur + 1) * SR))
    k, sn, hh = kick(), snare(), hat()
    s16 = BEAT / 4
    n = int(dur / BEAT) + 1
    for i in range(n):
        t = i * BEAT
        if drop[0] <= t < drop[1]: continue
        put(b, k, t, .9)
        put(b, hh, t + BEAT / 2, .35)
        if i % 2 == 1: put(b, sn, t, .5)
        c = CH[(i // 4) % 4]
        put(b, tone(NOTE(c[0] - 24), BEAT * .48, "tri"), t, .55)
        put(b, tone(NOTE(c[0] - 24), BEAT * .3, "tri"), t + BEAT / 2, .45)
        for j in range(4):
            f = NOTE(c[(i * 4 + j) % 3] + (12 if (i + j) % 4 else 24))
            put(b, tone(f, s16 * 1.1, "sq"), t + j * s16, .1)
    return b

def sfx(name):
    if name == "whoosh":
        d = .22; x = noise(d, 5); t = np.arange(len(x)) / SR
        return lowpass(x, np.clip(.04 + .5 * np.sin(np.pi * t / d), 0, 1)) * np.sin(np.pi * t / d) * 1.2
    if name == "hit":
        t = np.arange(int(.32 * SR)) / SR
        return np.sin(2 * np.pi * (40 * t + 30 * (1 - np.exp(-t * 40)))) * np.exp(-t * 12) + lowpass(noise(.32, 6), .25) * np.exp(-t * 28) * .9
    if name == "boom":
        t = np.arange(int(.9 * SR)) / SR
        return np.sin(2 * np.pi * (34 * t + 40 * (1 - np.exp(-t * 30)))) * np.exp(-t * 5) * 1.2 + lowpass(noise(.9, 7), .3) * np.exp(-t * 9)
    if name == "coin":
        return np.concatenate([tone(1319, .07, "sq", .55), tone(1760, .24, "sq", .55)])
    if name == "ding":
        return sum(tone(NOTE(n), 1.3, "sin", .5) for n in (72, 76, 79, 84))
    if name == "rise":
        d = 1.2; t = np.arange(int(d * SR)) / SR
        return np.sin(2 * np.pi * (200 * t + 500 * t * t)) * (t / d) ** 2 * .4 + lowpass(noise(d, 8), .4) * (t / d) ** 2 * .5
    raise KeyError(name)

def speak(text, path, rate):
    say = text.replace("URL", "ユーアールエル").replace("'", "")
    ps = ("Add-Type -AssemblyName System.Speech; $s=New-Object System.Speech.Synthesis.SpeechSynthesizer; $s.SelectVoice('Microsoft Haruka Desktop');"
          f"$s.Rate={rate}; $s.SetOutputToWaveFile('{path}'); $s.Speak('{say}'); $s.Dispose()")
    subprocess.run(["powershell", "-NoProfile", "-Command", "[Console]::InputEncoding=[Text.Encoding]::UTF8;" + ps], check=True, capture_output=True, encoding="utf-8")
    with wave.open(path) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        x = np.frombuffer(w.readframes(n), dtype=np.int16).astype(float) / 32768
    if ch == 2: x = x.reshape(-1, 2).mean(1)
    nz = np.nonzero(np.abs(x) > .01)[0]   # 前後の無音を切る
    return x[nz[0]:nz[-1] + 1], sr

def voice(text, fit, tmp, i):
    """声を少し高く速くして元気に。長さ fit に入らなければ速める"""
    short = len(text) < 6  # 「無料！」のような決めの一言は、速くせず言い切る
    x, sr = speak(text, os.path.join(tmp, f"v{i}.wav"), -2 if short else 4)
    speed = max(1.0 if short else 1.12, len(x) / sr / fit)
    assert speed < 1.75, (text, len(x) / sr)
    n = int(len(x) / sr * SR / speed)
    y = np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)
    return y / max(1e-6, np.abs(y).max()), speed

def mix(cuts, times, dur, wav):
    drop = next(((times[i][0], times[i][1]) for i, c in enumerate(cuts) if "これ全部" == c["voice"]), (1e9, 1e9))
    m = bgm(dur, drop) * .34
    s = np.zeros_like(m); v = np.zeros_like(m)
    with tempfile.TemporaryDirectory() as tmp:
        for i, (c, (a, b)) in enumerate(zip(cuts, times)):
            if i: put(s, sfx("whoosh"), a - .1, .45)
            for nm, d in c["sfx"]:
                put(s, sfx(nm), a + d, .6)
            if c["voice"]:
                y, sp = voice(c["voice"], (b - a) - .12, tmp, i)
                put(v, y, a + .03, 1.0)
                print(f"  {a:5.1f}s 声 {len(y) / SR:.2f}s 速さ×{sp:.2f} {c['voice']}")
    env = np.convolve((np.abs(v) > .02).astype(float), np.ones(2000) / 2000, "same")  # 声の間はBGMを下げる
    x = m * (1 - .45 * env) + s + v * .95
    x = x[:int(dur * SR)]
    fade = int(.5 * SR); x[-fade:] *= np.linspace(1, 0, fade)
    x = np.tanh(x * 1.1); x = x / np.abs(x).max() * .92
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
    return x

def build(name, fn):
    cuts = fn()
    times, t = [], 0.0
    for c in cuts:
        times.append((round(t, 3), round(t + c["beats"] * BEAT, 3))); t += c["beats"] * BEAT
    dur = t
    body = "".join(f'<div class="cut" style="background:{c["bg"]}">{c["html"]}</div>' for c in cuts)
    doc = f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS}</style></head><body><div class='cv'>{body}<div class='fl'></div><div class='hy-pg'></div></div><script>{JS}</script></body></html>"
    hp = os.path.join(ms.OUT, "_" + name + ".html")
    io.open(hp, "w", encoding="utf-8").write(doc)
    silent, wav, mp4 = os.path.join(ms.OUT, "_" + name + ".mp4"), os.path.join(ms.OUT, "_" + name + ".wav"), os.path.join(ms.OUT, name + ".mp4")
    mix(cuts, times, dur, wav)
    exe = imageio_ffmpeg.get_ffmpeg_exe()
    ff = subprocess.Popen([exe, "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-preset", "medium", silent], stdin=subprocess.PIPE)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.goto(v3.furl(hp)); pg.wait_for_load_state("networkidle"); pg.wait_for_timeout(500)
        for i in range(int(dur * FPS)):
            tt = i / FPS
            pg.evaluate("([t, c, b]) => render(t, c, b)", [tt, times, BEAT])
            buf = pg.screenshot(type="jpeg", quality=92)
            ff.stdin.write(buf)
            if abs(tt - 1.0) < 1 / FPS / 2:
                io.open(os.path.join(ms.OUT, name + "-thumb.jpg"), "wb").write(buf)
        b.close()
    ff.stdin.close(); ff.wait()
    subprocess.run([exe, "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    os.remove(hp); os.remove(silent); os.remove(wav)
    print("ok", name, f"{dur:.1f}s", mp4)

if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    for k, fn in HYPE.items():
        if not only or only in k:
            build(k, fn)
