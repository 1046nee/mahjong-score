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


def clack(vol=.9, pitch=1.0):
    """牌が卓（フェルト）や牌に当たる音。高い倍音の短い減衰＋はじめの一瞬のノイズ"""
    n = int(.12 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(7)
    s = sum(a * np.sin(2 * math.pi * f * pitch * t) * np.exp(-t / d) for f, a, d in ((2350, .55, .018), (3720, .4, .012), (5150, .25, .008), (1150, .35, .03)))
    s += rng.normal(0, 1, n) * np.exp(-t / .003) * .6
    return s * vol


def tap(vol=.35):
    """牌を持ち上げる小さな音"""
    return clack(vol, .8) * _env(int(.12 * SR), .001, .02)


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


SOUNDS = {"clack": lambda: clack(), "clack2": lambda: _two(), "tap": tap, "slide": slide, "pop": pop, "tick": tick,
          "line": lambda: pop(.22), "whoosh": whoosh, "chime": lambda: bell([1047, 1319, 1568], 1.4, .26, .07),
          "jingle": lambda: bell([784, 988, 1175, 1568], 1.6, .3, .09)}


def _two():
    a = clack(.8); b = clack(.75, 1.04); o = int(.028 * SR); s = np.zeros(len(a) + o); s[:len(a)] += a; s[o:o + len(b)] += b
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
