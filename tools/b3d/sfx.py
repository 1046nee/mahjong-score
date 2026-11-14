# -*- coding: utf-8 -*-
"""3Dの所作の動画の効果音（2026-11-14〜・ユーザーの依頼「人が気持ちいいと感じる所に音をハメる」）。
音は自分で作る（素材のライセンスを気にしなくてよい）。make_clip.py --sfx で、声と一緒に入れる。
音をハメる所:
  - 牌が卓に当たる瞬間（晒す・置く・切る）＝短く硬い「カチッ」。2枚同時は少しずらして2回
  - 牌を持ち上げる＝小さな「コッ」／卓の上をすべらせる＝「シャッ」から「カチッ」
  - 吹き出し（ポン・カン…）が出る＝「ポンッ」とはじける音
  - 前置きで、鳴くのに使う手牌（發發）が動いた瞬間と、他家がその牌を切った瞬間＝「ポンッ」
  - 手順の番号・箇条書き・まとめ・タイトル・締めでは鳴らさない（2026-11-14 ユーザーの指定）
  - 吹き出しは「〇〇と声に出します。」を言い終わってから出し、そのとき「ポンッ」と鳴らす（make_clip.py の BUB_AT）
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


def clack(vol=.9, pitch=1.0, seed=7, ring=.22, body=.12):
    """牌が当たる音（2026-11-14 ユーザーが送った2本目の実際の音に合わせて作り直した）。
    実際の音は、力の大半が3,000〜12,000Hzの高い所にある、2〜5ミリ秒で消える鋭い「パチッ」。そのあと3,200Hzあたりが小さく50ミリ秒ほど響く。
    低い「コッ」はほとんど無い（1本目に合わせた版は低い音が多すぎて、こもって聞こえた）"""
    n = int(.08 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    click = _band(rng.normal(0, 1, n), 3000 * pitch, 11500) * np.exp(-t / .0012)
    s = click / (np.abs(click).max() + 1e-9)
    if body:
        b = _band(rng.normal(0, 1, n), 150, 700) * np.exp(-t / .004); s += body * b / (np.abs(b).max() + 1e-9)
    if ring:      # 牌のかたい胴が少しだけ響く
        s += ring * (np.sin(2 * math.pi * 3220 * pitch * t) + .5 * np.sin(2 * math.pi * 7400 * pitch * t)) * np.exp(-t / .014)
    s[:int(.0004 * SR)] *= np.linspace(0, 1, int(.0004 * SR))
    return s / np.abs(s).max() * vol


def slap(vol=1.0):
    """強く打ちつける「タンッ」（タイトル・結論の1行）。鋭い音に、低い胴の音を足す"""
    return clack(vol, .95, seed=21, ring=.3, body=.45)


def jara(vol=.8):
    """牌をかき混ぜる「ジャラッ」（締め）。短い牌の音を、ばらばらの間で8回"""
    rng = np.random.default_rng(13); out = np.zeros(int(.6 * SR)); o = 0
    for i in range(8):
        c = clack(vol * (1 - i * .07), 0.9 + rng.random() * .25, seed=40 + i, ring=.15)
        out[o:o + len(c)] += c[:len(out) - o]; o += int((.035 + rng.random() * .04) * SR)
    return out / np.abs(out).max() * vol


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


SOUNDS = {"clack": lambda: clack(), "clackt": lambda: clack(ring=.35), "slap": slap, "jara": jara, "clack2": lambda: _two(), "tap": tap, "slide": slide, "pop": pop, "tick": tick,
          "line": lambda: pop(.22), "whoosh": whoosh, "chime": lambda: bell([1047, 1319, 1568], 1.4, .26, .07),
          "jingle": lambda: bell([784, 988, 1175, 1568], 1.6, .3, .09)}


def _two():
    a = clack(.8); b = clack(.7, 1.05, seed=9); o = int(.028 * SR); s = np.zeros(len(a) + o); s[:len(a)] += a; s[o:o + len(b)] += b
    return s


# 牌の音の時刻（scene.py の「もとの時刻 t」と、その時の音）。scene.py の動きを変えたら、ここもそろえる
TILE_EVENTS = {
    "pon": [(2.0, "clack2"), (2.9, "tap"), (3.8, "clackt"), (5.0, "slide"), (6.5, "clack")],
}
# 前置き（scene.py の pre_pose の時刻）: 手牌の2枚が持ち上がる＝1.6秒・切った牌が河に出る＝3.1秒
PRE_EVENTS = {"pon": [(1.6, "pop"), (3.1, "pop")], "chi": [(1.6, "pop"), (3.1, "pop")]}
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


# ---- 牌の音の候補（2026-11-14 ユーザーの依頼「何個か候補を出して、その中から選ぶ」）----
def _modes(freqs, amps, decays_ms, n_ms=90, click=.6, click_band=(3000, 11500), seed=31):
    """かたい牌の「固有の響き」をいくつか重ねる（モード合成）＋はじめの一瞬のノイズ"""
    n = int(n_ms / 1000 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    s = sum(a * np.sin(2 * math.pi * f * t + rng.random() * 6.28) * np.exp(-t / (d / 1000)) for f, a, d in zip(freqs, amps, decays_ms))
    c = _band(rng.normal(0, 1, n), *click_band) * np.exp(-t / .0012)
    s = s / (np.abs(s).max() + 1e-9) + click * c / (np.abs(c).max() + 1e-9)
    s[:int(.0004 * SR)] *= np.linspace(0, 1, int(.0004 * SR))
    return s / np.abs(s).max()


def _felt(ms=6, lo=150, hi=1500, seed=41):
    n = int(.06 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    b = _band(rng.normal(0, 1, n), lo, hi) * np.exp(-t / (ms / 1000)); return b / np.abs(b).max()


def _mix(*parts):
    n = max(len(p) for _, p in parts); s = np.zeros(n)
    for o, p in parts: s[o:o + len(p)] += p[:n - o]
    return s / np.abs(s).max()


CAND_TT = {   # 牌と牌が当たる音（晒す・置く・寄せる）
    "A": ("今の音（短いパチッ）", lambda: clack(1.0)),
    "B": ("固い響き（中くらいの高さ）", lambda: _modes([3220, 4870, 6610, 8420], [1, .6, .45, .3], [12, 8, 6, 4])),
    "C": ("高く短いカチッ", lambda: _modes([5300, 7400, 9100], [1, .7, .5], [5, 4, 3], click=.8)),
    "D": ("カチン（よく響く）", lambda: _modes([3220, 6440, 9600], [1, .45, .2], [30, 14, 6], click=.5)),
    "E": ("2回当たるカチャ", lambda: _mix((0, _modes([3220, 4870, 6610, 8420], [1, .6, .45, .3], [12, 8, 6, 4])), (int(.012 * SR), .6 * _modes([3400, 5100, 7000], [1, .6, .4], [10, 6, 4], seed=33)))),
}
CAND_DA = {   # 打牌（マットの上に置く・河に切る）
    "1": ("やわらかいトン（マットの音）", lambda: _mix((0, _felt(6)), (0, .35 * _modes([4200, 6800], [1, .5], [3, 2], n_ms=40, click=.3)))),
    "2": ("パチッ＋トン（半々）", lambda: _mix((0, clack(1.0, ring=.1, body=0)), (0, .7 * _felt(5, 250, 1000)))),
    "3": ("強いパシッ", lambda: _modes([], [], [], click=1.0, click_band=(500, 10000))),
    "4": ("牌が響いてマットで止まる", lambda: _mix((0, _modes([2900, 4600, 7100], [1, .6, .4], [4, 3, 2], n_ms=50)), (0, .6 * _felt(5)))),
    "5": ("角が当たってから倒れる", lambda: _mix((0, .45 * clack(1.0, 1.1, seed=51, ring=.1, body=0)), (int(.018 * SR), _mix((0, clack(1.0, ring=.1, body=0)), (0, .7 * _felt(5, 250, 1000)))))),
}


def _fit(noise_band, noise_ms, rings, tail=None, seed=61, n_ms=80):
    """送ってもらった実際の音を測った値で作る牌どうしの音（2026-11-14）。
    実際の音: 2,800〜5,000Hzに集まった、2ミリ秒ほどで消える音のかたまり＋3,250Hzあたりが8ミリ秒ほど響く（7,300Hzも少し）。
    音そのものは使わず、測った「高さ・強さ・消える速さ」だけを使って作る"""
    n = int(n_ms / 1000 * SR); t = np.arange(n) / SR; rng = np.random.default_rng(seed)
    nz = _band(rng.normal(0, 1, n), *noise_band) * np.exp(-t / (noise_ms / 1000)); s = nz / np.abs(nz).max()
    for f, a, d in rings: s += a * np.sin(2 * math.pi * f * t + rng.random() * 6.28) * np.exp(-t / (d / 1000))
    if tail: f, a, d = tail; s += a * np.sin(2 * math.pi * f * t) * np.exp(-t / (d / 1000))
    s[:int(.0003 * SR)] *= np.linspace(0, 1, int(.0003 * SR))
    return s / np.abs(s).max()


CAND_TT2 = {
    "F": ("実際の音に合わせた音（基本）", lambda: _fit((2600, 5200), 2.0, [(3250, .5, 8), (7300, .22, 4), (3870, .3, 2)])),
    "G": ("F＋かすかな余韻", lambda: _fit((2600, 5200), 2.0, [(3234, .35, 8), (3275, .35, 8), (7300, .2, 4)], tail=(3250, .1, 25))),
    "H": ("少し低め（2本目の別の音）", lambda: _fit((2500, 5000), 2.2, [(2840, .3, 4), (2985, .3, 4), (3375, .45, 3), (7350, .3, 4)], seed=63)),
}
SOUNDS["clack"] = lambda: CAND_DA["3"][1]()      # 打牌の音は候補3（強いパシッ）に決定（2026-11-14 ユーザーの判断）
SOUNDS["tap"] = lambda: .4 * CAND_DA["3"][1]()
SOUNDS["clack2"] = lambda: _mix((0, CAND_TT2["H"][1]()), (int(.028 * SR), .85 * _fit((2500, 5000), 2.2, [(2840, .3, 4), (2985, .3, 4), (3375, .45, 3), (7350, .3, 4)], seed=65)))
SOUNDS["clackt"] = lambda: CAND_TT2["H"][1]()      # 牌どうしの音は候補H に決定（2026-11-14 ユーザーの判断。録音が届いたら差しかえる）
