# -*- coding: utf-8 -*-
"""3Dの所作の動画の効果音（2026-11-14〜・ユーザーの依頼「人が気持ちいいと感じる所に音をハメる」）。
音は自分で作る（素材のライセンスを気にしなくてよい）。make_clip.py --sfx で、声と一緒に入れる。
音をハメる所:
  - 牌が卓に当たる瞬間（晒す・置く・切る）＝短く硬い「カチッ」。2枚同時は少しずらして2回
  - 牌を持ち上げる＝小さな「コッ」／卓の上をすべらせる＝「シャッ」から「カチッ」
  - 吹き出し（ポン・カン…）が出る＝「ポンッ」とはじける音
  - 手順の番号が進む＝小さな「ピッ」／前置きのカードの行が出る＝やわらかい「ポッ」
  - タイトル＝風切り音／まとめのカード＝きれいな和音／締め＝短いジングル
牌の当たる時刻は scene.py の動き（もとの時刻 t）から決める。止める間（FREEZE・PAUSE）をはさんだ実際の時刻 → コマ番号は frame_of() で変える
"""
import math, random
import numpy as np

SR = 24000


def _env(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(1, t / max(a, 1e-4)) * np.exp(-t / d)


def _band(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


def clack(vol=.9, pitch=1.0, seed=7, ring=0.0):
    """牌が当たる音（2026-11-14 実際の牌の音に合わせて作り直した）。
    実際の音は、ピークから1〜10ミリ秒で消える、とても短い「パチッ」。中心は2〜5kHz、下に200〜600Hzの「コッ」という胴の音、
    牌どうしが当たるときだけ3kHzあたりが少し響く。前の版は高い音が長く鳴り続けて、電子音のように聞こえた"""
    n = int(.06 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    click = _band(rng.normal(0, 1, n), 1500 * pitch, 7500) * np.exp(-t / .0016)
    body = _band(rng.normal(0, 1, n), 120, 700) * np.exp(-t / .006)
    s = click / (np.abs(click).max() + 1e-9) + .3 * body / (np.abs(body).max() + 1e-9)
    if ring:      # 牌どうしが当たる音（少しだけ響く）
        s += ring * (np.sin(2 * math.pi * 3200 * pitch * t) + .6 * np.sin(2 * math.pi * 4350 * pitch * t)) * np.exp(-t / .006)
    s[:int(.0004 * SR)] *= np.linspace(0, 1, int(.0004 * SR))
    return s / np.abs(s).max() * vol


def tap(vol=.35):
    """牌を持ち上げる小さな音"""
    return clack(vol, .85, seed=11)


def slide(dur=.45, vol=.25):
    """卓の上をすべらせる音（帯域を絞ったノイズ）。最後に置く音を足す"""
    n = int(dur * SR); rng = np.random.default_rng(3); x = rng.normal(0, 1, n)
    x = np.convolve(x, np.ones(6) / 6, "same") - np.convolve(x, np.ones(60) / 60, "same")
    t = np.arange(n) / n; s = x * np.sin(math.pi * t) ** 1.5 * vol
    c = clack(.7); s[-len(c):] += c[:len(s)] if len(c) <= len(s) else 0
    return s


def pop(vol=.5):
    """吹き出しが出る音（下から上へ音の高さが上がる短い音）"""
    n = int(.11 * SR); t = np.arange(n) / SR
    f = 380 + 900 * (t / t[-1]) ** .6; ph = 2 * math.pi * np.cumsum(f) / SR
    return np.sin(ph) * _env(n, .004, .035) * vol


def tick(vol=.18, f=1900):
    n = int(.05 * SR); t = np.arange(n) / SR
    return np.sin(2 * math.pi * f * t) * _env(n, .002, .012) * vol


def whoosh(dur=.55, vol=.22):
    n = int(dur * SR); rng = np.random.default_rng(5); x = rng.normal(0, 1, n)
    k = np.convolve(x, np.ones(14) / 14, "same"); t = np.arange(n) / n
    return k * (np.sin(math.pi * t) ** 2) * vol


def bell(freqs, dur=1.2, vol=.22, gap=.0):
    out = np.zeros(int((dur + gap * len(freqs)) * SR))
    for i, f in enumerate(freqs):
        n = int(dur * SR); t = np.arange(n) / SR
        s = (np.sin(2 * math.pi * f * t) + .35 * np.sin(2 * math.pi * f * 2.01 * t) + .15 * np.sin(2 * math.pi * f * 3.0 * t)) * _env(n, .003, .35)
        o = int(i * gap * SR); out[o:o + n] += s
    return out * vol / max(1, len(freqs) ** .5)


SOUNDS = {"clack": lambda: clack(), "clackt": lambda: clack(ring=.35), "clack2": lambda: _two(), "tap": tap, "slide": slide, "pop": pop, "tick": tick,
          "line": lambda: pop(.22), "whoosh": whoosh, "chime": lambda: bell([1047, 1319, 1568], 1.4, .26, .07),
          "jingle": lambda: bell([784, 988, 1175, 1568], 1.6, .3, .09)}


def _two():
    a = clack(.8, ring=.25); b = clack(.7, 1.05, seed=9, ring=.25); o = int(.028 * SR); s = np.zeros(len(a) + o); s[:len(a)] += a; s[o:o + len(b)] += b
    return s


# 牌の音の時刻（scene.py の「もとの時刻 t」と、その時の音）。scene.py の動きを変えたら、ここもそろえる
TILE_EVENTS = {
    "pon": [(2.0, "clack2"), (2.9, "tap"), (3.8, "clack"), (5.0, "slide"), (6.5, "clack")],
}
FREEZE = {"pon": (2.0, 3.8, 5.0), "chi": (2.0, 3.8, 5.0)}
PAUSE = .7


def frame_of(scene, t, fps=12):
    """もとの時刻 t → 書き出したコマの番号（止める間の分だけ後ろへずれる）"""
    tr = t + PAUSE * sum(1 for f in FREEZE.get(scene, ()) if f < t)
    return int(round(tr * fps))


def render(events, total_sec, sr=SR):
    """events: [(秒, 音の名前)] → 1本の音（-1〜1）"""
    buf = np.zeros(int((total_sec + 2) * sr))
    for sec, name in events:
        s = SOUNDS[name](); o = int(sec * sr)
        if name == "slide": o -= len(s) - int(.04 * sr)     # すべらせる音は、最後の「カチッ」がその時刻に来るように前から
        o = max(0, o); buf[o:o + len(s)] += s[:len(buf) - o]
    return buf
