# -*- coding: utf-8 -*-
"""3Dの所作の動画の音楽（入りのサウンドロゴ・締めのジングル・BGM・小さな切りかえ音）を自分で作る（2026-11-24 ユーザーの依頼
「ショート動画としてフックになり耳に残る感じに。冒頭と締めのサウンドや音楽も決めたい」）。素材のライセンスが要らないよう、すべて数式で鳴らす。

耳に残らせる工夫: 「ま・じゃ・す・こ」の4音のモチーフ（MOTIF）を、入り・BGMの中・締めで同じ形でくり返す（サウンドロゴ）。
入りは上がって止まる（問いかけ＝続きが気になる）、締めは主音に落ちて終わる（答え＝まじゃすこ で）。
候補は3つ（PACKS）: wa＝和モダン（拍子木と琴）／stage＝対局の緊張感（会場のような低い鼓動と金管）／pop＝ポップ（マリンバと手拍子）。

試し聞き: python3.13 tools/b3d/music.py <出力フォルダ>  → 各パックの intro.wav・outro.wav・bgm.wav・step.wav・card.wav
動画に試しにのせる: python3.13 tools/b3d/music.py <出力フォルダ> --demo <声と効果音の入った mp4>  → demo-<パック>.mp4
"""
import math, os, subprocess, sys, wave
import numpy as np

SR = 44100
rng = np.random.default_rng(1)


def t_(sec): return np.arange(int(sec * SR)) / SR
def env(n, a=.005, d=.3, s=0.0, r=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * (s + (1 - s) * np.exp(-t / d))
    if r: e *= np.clip((n / SR - t) / r, 0, 1)
    return e
def hz(note):      # "C4" "F#3" → 周波数
    names = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
    k = names[note[0]] + (1 if "#" in note else -1 if "b" in note[1:2] else 0); o = int(note[-1])
    return 440 * 2 ** ((k + 12 * (o + 1) - 69) / 12)
def lp(x, cut):      # 1次のローパス
    a = math.exp(-2 * math.pi * cut / SR); y = np.empty_like(x); p = 0.0
    for i, v in enumerate(x): p = (1 - a) * v + a * p; y[i] = p
    return y
def hpf(x, cut): return x - lp(x, cut)
def norm(x, v=1.0): return x / (np.abs(x).max() + 1e-9) * v
def put(buf, x, at):
    o = int(at * SR)
    if o >= len(buf): return
    n = min(len(x), len(buf) - o); buf[o:o + n] += x[:n]


# ---------- 楽器 ----------
def koto(f, dur=1.2, v=.6):
    """琴（はじく弦。カルプラス・ストロングで、はじいた音が細くなって消える）"""
    n = int(dur * SR); p = max(2, int(SR / f)); buf = rng.uniform(-1, 1, p); out = np.empty(n)
    for i in range(n):
        out[i] = buf[i % p]; buf[i % p] = .5 * (buf[i % p] + buf[(i + 1) % p]) * .996
    out += .3 * np.sin(2 * math.pi * f * 2 * t_(dur)) * env(n, .001, .08)      # 爪の当たる硬い音
    return norm(out, v) * env(n, .001, dur * .6)
def marimba(f, dur=.9, v=.6):
    t = t_(dur); n = len(t)
    s = np.sin(2 * math.pi * f * t) * env(n, .001, .35) + .5 * np.sin(2 * math.pi * f * 4 * t) * env(n, .001, .05) + .2 * np.sin(2 * math.pi * f * 10 * t) * env(n, .0005, .01)
    return s * v
def bell(f, dur=1.6, v=.4):
    t = t_(dur); n = len(t)
    return (np.sin(2 * math.pi * f * t) + .5 * np.sin(2 * math.pi * f * 2.76 * t) * env(n, .001, .25) + .3 * np.sin(2 * math.pi * f * 5.4 * t) * env(n, .001, .08)) * env(n, .002, .7) * v
def brass(f, dur=.5, v=.5):
    """金管っぽい音（のこぎり波を重ねて少しずらし、こもらせる）"""
    t = t_(dur); n = len(t); s = np.zeros(n)
    for d in (-.006, 0, .006):
        ph = (f * (1 + d) * t) % 1; s += 2 * ph - 1
    return lp(s, 1800 + 1500 * 1) * env(n, .03, 10, .9, .08) * v / 3
def pad(fs, dur, v=.15, cut=900):
    t = t_(dur); n = len(t); s = np.zeros(n)
    for f in fs:
        for d in (-.004, .004):
            s += 2 * ((f * (1 + d) * t) % 1) - 1
    return lp(s, cut) * env(n, .4, 100, 1, .6) * v / len(fs)
def bass(f, dur=.4, v=.5):
    t = t_(dur); n = len(t)
    return np.tanh(2 * np.sin(2 * math.pi * f * t)) * env(n, .003, dur * .7) * v
def kick(v=.9):
    t = t_(.35); n = len(t); f = 45 + 110 * np.exp(-t / .03)
    return np.sin(2 * math.pi * np.cumsum(f) / SR) * env(n, .001, .14) * v
def taiko(v=1.0):
    t = t_(.9); n = len(t); f = 62 + 40 * np.exp(-t / .04)
    s = np.sin(2 * math.pi * np.cumsum(f) / SR) * env(n, .001, .35) + .3 * hpf(rng.normal(0, 1, n), 200) * env(n, .001, .03)
    return s * v
def snare(v=.4):
    n = int(.2 * SR); return (hpf(rng.normal(0, 1, n), 1500) * .8 + .4 * np.sin(2 * math.pi * 190 * t_(.2))) * env(n, .001, .06) * v
def clap(v=.4):
    n = int(.25 * SR); x = hpf(rng.normal(0, 1, n), 1000); e = np.zeros(n)
    for k in (0, .011, .022): e += env(n, .0005, .012) * (np.arange(n) >= k * SR)
    return x * (e + env(n, .03, .08) * .5) * v
def hat(v=.12, open_=False):
    n = int((.25 if open_ else .05) * SR); return hpf(rng.normal(0, 1, n), 7000) * env(n, .0005, .08 if open_ else .015) * v
def hyoshigi(v=.9):
    """拍子木（木を打つ「カンッ」。高い木の共鳴を2つ）"""
    t = t_(.4); n = len(t)
    s = (np.sin(2 * math.pi * 1650 * t) + .6 * np.sin(2 * math.pi * 2460 * t) + .3 * np.sin(2 * math.pi * 3900 * t)) * env(n, .0005, .06)
    s += hpf(rng.normal(0, 1, n), 2000) * env(n, .0003, .004) * .8
    return s * v
def kaka(n=2, v=.9):
    """拍子木を「カカッ」とテンポよく（2026-11-24 ユーザーの指定）。短く硬い木の音を、少しずつ高くして約70ミリ秒おきに"""
    gap = .07; b = np.zeros(int((gap * n + .3) * SR))
    for i in range(n):
        t = t_(.18); m = len(t); f = 1900 * (1 + .06 * i)
        s = (np.sin(2 * math.pi * f * t) + .55 * np.sin(2 * math.pi * f * 1.52 * t) + .25 * np.sin(2 * math.pi * f * 2.4 * t)) * env(m, .0003, .025)
        s += hpf(rng.normal(0, 1, m), 2500) * env(m, .0002, .003) * .9
        put(b, s * v * (1 if i == n - 1 else .8), i * gap)
    return b


# 和モダンの入りの琴のバリエーション（2026-11-24 ユーザーの指定「いろんなバリエーション・音数を増やした版も」）。(音, 長さの拍) を並べる。1拍＝0.16秒
WA_INTROS = {
    "A 4音 上がって止まる（今の形）": [("D4", 1), ("G4", 1), ("A4", 1), ("C5", 3)],
    "B 4音 跳んで戻る": [("G4", 1), ("D5", 1), ("C5", 1), ("A4", 3)],
    "C 4音 タタタ・ターン（最後をのばす）": [("D4", .6), ("G4", .6), ("A4", .6), ("D5", 3)],
    "D 5音 上がりきる": [("D4", 1), ("G4", 1), ("A4", 1), ("C5", 1), ("D5", 3)],
    "E 6音 駆け上がる": [("D4", .5), ("E4", .5), ("G4", .5), ("A4", .5), ("C5", .5), ("D5", 3)],
    "F 7音 流して決める": [("D5", .35), ("C5", .35), ("A4", .35), ("G4", .35), ("E4", .35), ("G4", 1), ("D5", 3)],
    "G 8音 2回に分けて": [("D4", .5), ("G4", .5), ("A4", 1), ("A4", .5), ("C5", .5), ("D5", .5), ("G5", .5), ("D5", 3)],
    "H 6音 装飾音つき（ツ・タ・タ・ターン）": [("C5", .25), ("D5", .75), ("A4", 1), ("G4", 1), ("A4", .25), ("D5", 3)],
}
WA_INTRO = "D 5音 上がりきる"      # 入りは D に決定（2026-11-24 ユーザーの判断）
# 締めの候補（入りの D と同じ5音の形で、主音の G に落ち着かせる）
WA_OUTROS = {
    "1 同じ5音で上がり、主音のGへ": [("D4", 1), ("G4", 1), ("A4", 1), ("C5", 1), ("D5", 1), ("G5", 4)],
    "2 上がった5音を、下りて主音へ（答え）": [("D5", 1), ("C5", 1), ("A4", 1), ("G4", 4)],
    "3 入りと同じ5音＋低いGで落とす": [("D4", 1), ("G4", 1), ("A4", 1), ("C5", 1), ("D5", 2), ("G4", 4)],
}
def wa_outro(notes):
    beat = .17; b = np.zeros(int((sum(d for _, d in notes) * beat + 2.4) * SR)); t = .02
    for i, (n, d) in enumerate(notes):
        last = i == len(notes) - 1; put(b, koto(hz(n), 2.2 if last else 1.0, .58 if last else .48), t)
        if last: put(b, koto(hz(n) / 2, 2.2, .3), t); put(b, taiko(.9), t); put(b, pad([hz("G3"), hz("D4"), hz("B4")], 2.2, .1, 1500), t)
        t += d * beat
    return b


def wa_intro(notes, hits=0):
    beat = .16; head = (.2 + .07 * hits) if hits else .02      # hits=0 で拍子木なし（2026-11-24 ユーザーの指定「最初の拍子木はいらない」）
    b = np.zeros(int((head + sum(d for _, d in notes) * beat + 1.6) * SR))
    if hits: put(b, kaka(hits), 0)
    t = head
    for i, (n, d) in enumerate(notes):
        put(b, koto(hz(n), 1.6 if i == len(notes) - 1 else 1.0, .55 if i == len(notes) - 1 else .48), t); t += d * beat
    put(b, taiko(.8), t - 3 * beat)      # 最後の音に太鼓を重ねる
    return b


def riser(dur=1.2, v=.3):
    t = t_(dur); n = len(t); x = rng.normal(0, 1, n); y = np.zeros(n)
    for i, (a, b) in enumerate(zip(np.linspace(300, 6000, 8)[:-1], np.linspace(300, 6000, 8)[1:])):
        seg = slice(i * n // 7, (i + 1) * n // 7); y[seg] = hpf(lp(x[seg], b), a)
    return y * (t / dur) ** 2 * v
def whoosh(dur=.35, v=.25):
    t = t_(dur); n = len(t); x = hpf(lp(rng.normal(0, 1, n), 4000), 400)
    return x * np.sin(math.pi * t / dur) ** 2 * v


# ---------- 4音のモチーフ「ま・じゃ・す・こ」 ----------
# 入り＝5・1・3・2度（上がって2度で止まる＝続きが気になる）／締め＝5・1・3・1度（主音に落ちて終わる）
def motif(key, end_home):
    deg = {"C": ["G3", "C4", "E4", "D4", "C4"], "D": ["A3", "D4", "F#4", "E4", "D4"], "A": ["E4", "A4", "C5", "B4", "A4"]}[key]
    return deg[:3] + [deg[4] if end_home else deg[3]]


def pack_wa(kind):
    """和モダン: 拍子木2回 → 琴の4音（陰の音階っぽく、3度を短く）。BGMはゆっくりのビートに琴"""
    if kind == "intro": return wa_intro(WA_INTROS[WA_INTRO])
    if kind == "outro": return wa_outro(WA_OUTROS[os.environ.get("WA_OUTRO", "1 同じ5音で上がり、主音のGへ")])
    if kind == "bgm":
        bpm = 86; beat = 60 / bpm; bars = 8; b = np.zeros(int(bars * 4 * beat * SR))
        prog = [("G2", ["G3", "D4", "A4"]), ("Eb2", ["Eb3", "Bb3", "G4"]), ("C2", ["C3", "G3", "D4"]), ("D2", ["D3", "A3", "F#4"])]
        for bar in range(bars):
            root, ch = prog[bar % 4]; t0 = bar * 4 * beat
            put(b, pad([hz(c) for c in ch], 4 * beat, .07, 1100), t0)
            for k in range(4):
                put(b, kick(.55) if k in (0, 2) else snare(.18), t0 + k * beat)
                put(b, hat(.05), t0 + k * beat + beat / 2)
            put(b, bass(hz(root), beat * 1.5, .3), t0); put(b, bass(hz(root), beat, .22), t0 + 2.5 * beat)
            if bar % 2 == 1:      # 2小節に1回、琴でモチーフの頭3音（耳に残す）
                for i, n in enumerate(["D4", "G4", "A4"]): put(b, koto(hz(n), 1.0, .22), t0 + 2 * beat + i * beat / 2)
        return b
    if kind == "step": b = np.zeros(int(.6 * SR)); put(b, koto(hz("A4"), .6, .35), 0); put(b, hyoshigi(.25), 0); return b
    if kind == "card": return whoosh(.3, .18)


def pack_stage(kind):
    """対局の緊張感: 低い鼓動とライザーから、金管の4音がドンと鳴る。BGMは脈打つベースとハット"""
    if kind == "intro":
        b = np.zeros(int(2.6 * SR)); put(b, riser(.8, .25), 0)
        for i, n in enumerate(["A3", "D4", "F4", "E4"]): put(b, brass(hz(n), .32 if i < 3 else .9, .5), .8 + i * .17); put(b, brass(hz(n) / 2, .32 if i < 3 else .9, .3), .8 + i * .17)
        put(b, kick(1.0), .8); put(b, taiko(.7), .8); put(b, bell(hz("A5"), 1.6, .15), 1.31); return b
    if kind == "outro":
        b = np.zeros(int(3.2 * SR))
        for i, n in enumerate(["A3", "D4", "F4", "D4"]): put(b, brass(hz(n), .3 if i < 3 else 1.4, .5), i * .18); put(b, brass(hz(n) / 2, .3 if i < 3 else 1.4, .3), i * .18)
        put(b, kick(1.0), .54); put(b, taiko(.8), .54); put(b, pad([hz("D3"), hz("A3"), hz("F4")], 2.4, .12, 1400), .54); put(b, bell(hz("D6"), 2.0, .12), .54); return b
    if kind == "bgm":
        bpm = 112; beat = 60 / bpm; bars = 12; b = np.zeros(int(bars * 4 * beat * SR))
        prog = [("D2", ["D3", "F3", "A3"]), ("Bb1", ["Bb2", "D3", "F3"]), ("C2", ["C3", "E3", "G3"]), ("A1", ["A2", "C#3", "E3"])]
        for bar in range(bars):
            root, ch = prog[bar % 4]; t0 = bar * 4 * beat
            put(b, pad([hz(c) for c in ch], 4 * beat, .06, 800), t0)
            for k in range(8):
                put(b, bass(hz(root), beat / 2 * .9, .25 if k % 2 == 0 else .16), t0 + k * beat / 2)
                put(b, hat(.04 if k % 2 else .06), t0 + k * beat / 2)
            for k in (0, 2): put(b, kick(.6), t0 + k * beat)
            put(b, snare(.12), t0 + 3 * beat)
            if bar % 4 == 3:
                for i, n in enumerate(["A4", "D5", "F5"]): put(b, bell(hz(n), .8, .07), t0 + 2 * beat + i * beat / 2)
        return b
    if kind == "step": b = np.zeros(int(.6 * SR)); put(b, kick(.35), 0); put(b, bell(hz("D6"), .5, .12), 0); return b
    if kind == "card": return whoosh(.3, .2)


def pack_pop(kind):
    """ポップ: 手拍子2回 → マリンバの4音。BGMははずむマリンバとキック"""
    if kind == "intro":
        b = np.zeros(int(2.2 * SR)); put(b, clap(.5), 0); put(b, clap(.5), .22)
        for i, n in enumerate(["G4", "C5", "E5", "D5"]): put(b, marimba(hz(n), .9, .55), .5 + i * .15)
        put(b, kick(.8), .5); put(b, bell(hz("D6"), 1.2, .1), .95); return b
    if kind == "outro":
        b = np.zeros(int(2.6 * SR))
        for i, n in enumerate(["G4", "C5", "E5", "C5"]): put(b, marimba(hz(n), 1.2, .55), i * .17)
        put(b, kick(.8), .51); put(b, clap(.4), .51); put(b, bell(hz("C6"), 1.6, .12), .51); put(b, bell(hz("G6"), 1.6, .07), .51); return b
    if kind == "bgm":
        bpm = 108; beat = 60 / bpm; bars = 12; b = np.zeros(int(bars * 4 * beat * SR))
        prog = [("C3", ["C4", "E4", "G4"]), ("A2", ["A3", "C4", "E4"]), ("F2", ["F3", "A3", "C4"]), ("G2", ["G3", "B3", "D4"])]
        for bar in range(bars):
            root, ch = prog[bar % 4]; t0 = bar * 4 * beat
            for k in range(4):
                put(b, kick(.5), t0 + k * beat) if k in (0, 2) else put(b, clap(.16), t0 + k * beat)
                put(b, hat(.04), t0 + k * beat + beat / 2)
            put(b, bass(hz(root), beat * .9, .25), t0); put(b, bass(hz(root), beat * .9, .2), t0 + 1.5 * beat); put(b, bass(hz(root), beat * .9, .2), t0 + 2 * beat)
            for k, c in enumerate([ch[0], ch[2], ch[1], ch[2]]): put(b, marimba(hz(c), .5, .12), t0 + k * beat + beat / 2)
            if bar % 4 == 3:
                for i, n in enumerate(["G4", "C5", "E5"]): put(b, marimba(hz(n), .6, .18), t0 + 2 * beat + i * beat / 2)
        return b
    if kind == "step": return marimba(hz("C6"), .4, .25)
    if kind == "card": return whoosh(.28, .16)


PACKS = {"wa": pack_wa, "stage": pack_stage, "pop": pack_pop}
NAMES = {"wa": "和モダン", "stage": "対局の緊張感", "pop": "ポップ"}


def save(path, x):
    x = np.clip(x, -1, 1); y = (x * 32000).astype(np.int16)
    with wave.open(path, "wb") as w: w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(y.tobytes())


def load_audio(mp4):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-ac", "1", "-ar", str(SR), "-f", "s16le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.int16).astype(np.float64) / 32768


def demo(out_dir, mp4, key):
    """声と効果音の入った動画に、入り・締め・BGM をのせる。BGMは声の大きさに合わせて下げる（声が聞こえるように）"""
    voice = load_audio(mp4); n = len(voice); dur = n / SR; P = PACKS[key]
    mix = voice * .95
    bgm = P("bgm"); bgm = np.tile(bgm, int(n / len(bgm)) + 1)[:n]
    win = int(.25 * SR); lev = np.sqrt(np.convolve(voice ** 2, np.ones(win) / win, "same")); lev = lev / (lev.max() + 1e-9)
    duck = 1 - .65 * np.clip(lev * 4, 0, 1); duck = np.convolve(duck, np.ones(win) / win, "same")
    fade = np.ones(n); a, z = int(2.0 * SR), int(4.5 * SR); fade[:a] = 0; fade[a:a + int(1.5 * SR)] = np.linspace(0, 1, int(1.5 * SR))      # 入りの音が鳴り終わってからBGM
    fade[n - z:] = np.linspace(1, 0, z)
    mix += norm(bgm, .16) * duck * fade
    put(mix, norm(P("intro"), .75), .05)
    put(mix, norm(P("outro"), .75), dur - 4.6)
    mix = norm(mix, .95)
    wav = os.path.join(out_dir, f"_demo-{key}.wav"); save(wav, mix)
    out = os.path.join(out_dir, f"demo-{key}.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", mp4, "-i", wav, "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", out], check=True)
    os.remove(wav); print(out)


if __name__ == "__main__":
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    for k, P in PACKS.items():
        for kind in ("intro", "outro", "bgm", "step", "card"):
            save(os.path.join(out, f"{k}-{kind}.wav"), norm(P(kind), .8 if kind != "bgm" else .6))
        print(k, NAMES[k])
    if "--wa" in sys.argv:      # 和モダンの入りの聞き比べ（A〜H を1.2秒あけて続けて。カカッ×2。最後に カカカッ×3 の版）
        seq = [wa_intro(v) for v in WA_INTROS.values()]
        gap = np.zeros(int(1.2 * SR)); save(os.path.join(out, "wa-intros.wav"), norm(np.concatenate([np.concatenate([x, gap]) for x in seq]), .85))
        for k, v in WA_INTROS.items(): save(os.path.join(out, f"wa-intro-{k[0]}.wav"), norm(wa_intro(v), .85))
    if "--wa-outro" in sys.argv:      # 締めの聞き比べ（入りD → 1.2秒 → 締め1、…）
        gap = np.zeros(int(1.2 * SR)); seq = []
        for v in WA_OUTROS.values(): seq += [wa_intro(WA_INTROS[WA_INTRO]), gap, wa_outro(v), gap, gap]
        save(os.path.join(out, "wa-outros.wav"), norm(np.concatenate(seq), .85))
    if "--demo" in sys.argv:
        for k in PACKS: demo(out, sys.argv[sys.argv.index("--demo") + 1], k)
