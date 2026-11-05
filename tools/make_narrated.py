# -*- coding: utf-8 -*-
"""ナレーションと字幕の入ったショート動画を作る（2026-11-04〜）。縦 1080×1920・30fps。
見た目は make_short.py の動画と同じ。声の長さから画面の切り替えの時刻を決めるので、声と画面と字幕がずれない。

声: edge-tts（ja-JP-KeitaNeural・男性）。台本の文字を Microsoft のサービスへ送って音声にする（要: pip install edge-tts）
BGM: 自作（numpy）。外の曲は使わない
出力: まじゃすこ素材/video/<名前>.mp4 （コミットしない）
使い方: python tools/make_narrated.py [名前]
  VOICEVOX の声: 先にエンジン（run.exe）を動かして python tools/make_narrated.py [名前] --vv <話者ID> <クレジットの名前> [出力名]
台本は NARR に足す。1場面＝(字幕の区切りのリスト, 場面を作る関数)。場面を作る関数は (出る秒, 消える秒) を受けて要素を返す
"""
import asyncio, io, json, os, subprocess, sys, tempfile, urllib.parse, urllib.request, wave
import numpy as np
import truststore
truststore.inject_into_ssl()  # 会社のネットワークでは Windows の証明書で検証する（検証は無効にしない）
import edge_tts
import imageio_ffmpeg

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_short as ms
import make_hype as mh
v3 = ms.v3

SR = 44100
VOICE, RATE = "ja-JP-KeitaNeural", "+12%"
GAP = 0.22    # 場面の間の息つぎ
LEAD = 0.25   # 場面が切り替わってから声が始まるまで

ms.CSS += """
.sub { position: absolute; left: 60px; right: 140px; top: 1500px; z-index: 30; text-align: center; opacity: 0; }
.sub span { display: inline-block; color: #fff; font-size: 54px; font-weight: 900; line-height: 1.3; white-space: nowrap; -webkit-text-stroke: 12px #1F2A28; paint-order: stroke fill; }
"""
ms.JS += r"""
const renderBase = window.render;
window.render = (t) => { renderBase(t); document.querySelectorAll('[data-sub]').forEach(e => { const [a, b] = e.dataset.sub.split(',').map(Number); e.style.opacity = t >= a && t < b ? 1 : 0; }); };
"""

def say(text):
    return text.replace("URL", "ユーアールエル")

async def tts(text, path):
    c = edge_tts.Communicate(say(text), VOICE, rate=RATE, boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": words.append((ch["offset"] / 1e7, ch["text"]))
    return words

VV = None  # (話者ID, クレジットの名前)
VV_URL = "http://127.0.0.1:50021"

def vv_post(path, body=None, ctype="application/json"):
    r = urllib.request.Request(VV_URL + path, data=body if body is not None else b"", headers={"Content-Type": ctype}, method="POST")
    return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(r, timeout=120).read()

# 読みとアクセントの直し（2026-11-05 ユーザーの指摘）。エンジンの辞書はそのPCにしか残らないので、毎回ここから入れる
VV_WORDS = [("まじゃすこ", "マジャスコ", 0), ("その場", "ソノバ", 0), ("ユーアールエル", "ユーアールエル", 5)]
# 辞書で直らない語は、アクセント句の読みの頭で見つけて下がる位置を直す（0 = 平板）
VV_ACCENT = {"マアジャン": 1, "シュウケエ": 0, "ムリョオ": 1}

def vv_dict():
    have = {(w["surface"], w["pronunciation"]) for w in json.loads(urllib.request.build_opener(urllib.request.ProxyHandler({})).open(VV_URL + "/user_dict", timeout=30).read()).values()}
    for sf, pr, ac in VV_WORDS:
        if (sf, pr) not in have and (sf.translate({i: i + 0xFEE0 for i in range(0x21, 0x7F)}), pr) not in have:
            vv_post("/user_dict_word?" + urllib.parse.urlencode({"surface": sf, "pronunciation": pr, "accent_type": ac, "word_type": "PROPER_NOUN", "priority": 10}))

def vv_query(text):
    q = json.loads(vv_post("/audio_query?" + urllib.parse.urlencode({"text": say(text), "speaker": VV[0]})))
    hit = False
    for a in q["accent_phrases"]:
        kana = "".join(m["text"] for m in a["moras"])
        for k, ac in VV_ACCENT.items():
            if kana.startswith(k):
                a["accent"] = ac or len(a["moras"]); hit = True
    if hit:
        q["accent_phrases"] = json.loads(vv_post(f"/mora_pitch?speaker={VV[0]}", json.dumps(q["accent_phrases"]).encode("utf-8")))
    return q

def vv_len(q):
    return sum(m["vowel_length"] + (m.get("consonant_length") or 0) for a in q["accent_phrases"] for m in a["moras"] + ([a["pause_mora"]] if a.get("pause_mora") else []))

def vv_tts(phrases, path):
    """声は1文まとめて作る。字幕の区切りは、区切りごとの長さの割合から出す"""
    q = vv_query("".join(phrases))
    q["speedScale"] = 1.18; q["prePhonemeLength"] = 0.03; q["postPhonemeLength"] = 0.05; q["intonationScale"] = 1.35; q["pitchScale"] = 0.03  # 元気に（2026-11-05 ユーザーの判断）
    open(path, "wb").write(vv_post(f"/synthesis?speaker={VV[0]}", json.dumps(q).encode("utf-8")))
    ls = [vv_len(vv_query(p)) for p in phrases]
    return [sum(ls[:i]) / sum(ls) for i in range(len(ls))]

def load(mp3, tmp):
    w = os.path.join(tmp, "x.wav")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), w], check=True)
    with wave.open(w) as f:
        return np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).astype(float) / 32768

def phrase_times(phrases, words, total):
    """字幕の区切りごとの始まりの秒。声の単語の時刻に合わせる（見つからなければ文字数の割合）"""
    text = say("".join(phrases))
    pos, marks = 0, []
    for t, w in words:
        i = text.find(w, pos)
        if i >= 0:
            marks.append((i, t)); pos = i + len(w)
    out, at = [], 0
    for p in phrases:
        hit = [t for i, t in marks if i >= at]
        out.append(hit[0] if hit else total * at / max(1, len(text)))
        at += len(say(p))
    out[0] = 0.0
    return out

def soft_bgm(dur):
    """声のじゃまをしない、やわらかい伴奏（120BPM）"""
    b = np.zeros(int((dur + 2) * SR)); beat = 0.5
    k = mh.kick()
    for i in range(int(dur / beat) + 1):
        t = i * beat; c = mh.CH[(i // 4) % 4]
        if i % 2 == 0: mh.put(b, k, t, .28)
        mh.put(b, mh.hat(), t + beat / 2, .1)
        mh.put(b, mh.tone(mh.NOTE(c[0] - 24), beat * .9, "tri"), t, .34)
        for j, n in enumerate(c):
            mh.put(b, mh.tone(mh.NOTE(n + 12), beat * 1.2, "sin"), t + j * beat / 3, .1)
    return b[:int(dur * SR)]

def v_kinou():
    hero = v3.hero_svg().replace('<svg ', '<svg style="width:940px;height:auto;display:block;margin:0 auto" ', 1)
    def s0(a, b):
        return [ms.at(a, b, '<div class="badge">セット麻雀の人へ</div><h1>麻雀の集計、<br>まだ電卓で<br>やってる？</h1>', cls="cap hook", style="top:330px", anim="pop"),
                ms.at(a + .3, b, hero, style="position:absolute;left:0;right:0;top:880px", anim="fade")]
    def s1(a, b):
        return [ms.at(a, b, '<h1>点数を入れるだけ。</h1>', cls="cap", style="top:230px"), ms.phone_at(a, b, "howto-3.jpg", y=400)[0],
                ms.chip_at(a + 1.0, b, ("合計", "100,000点", "pos"), "r", 900)]
    def s2(a, b):
        e = [ms.at(a, b, '<h1>順位とスコアが、<br>その場で出る。</h1>', cls="cap", style="top:170px"), ms.phone_at(a, b, "howto-4.jpg", y=400)[0]]
        for i, (c, s) in enumerate([(("", "+69.1", ("medal", 1)), "l"), (("", "+64.0", ("medal", 2)), "r"), (("", "−53.5", ("medal", 3)), "l")]):
            e.append(ms.chip_at(a + .4 + i * .3, b, c, s, 620 + i * 150))
        return e
    def s3(a, b):
        return [ms.at(a, b, '<h1>URLを送れば、<br>全員のスマホに。</h1>', cls="cap", style="top:170px"), ms.phone_at(a, b, "howto-2.jpg", y=400)[0],
                ms.chip_at(a + .7, b, ("見る人は", "登録いらず", ""), "r", 700)]
    def s4(a, b):
        return [ms.at(a, b, '<h1>通算の成績も、<br>自動でたまる。</h1>', cls="cap", style="top:170px"),
                ms.phone_at(a, b, "lp-mypage.jpg", y=400, scroll=f"{a + .6},{b - .3},0,120")[0],
                ms.chip_at(a + .5, b, ("通算スコア", "+347.0", "pos"), "r", 660), ms.chip_at(a + .9, b, ("トップ率", "26%", ""), "l", 860)]
    def s5(a, b):
        return [ms.end_card(a)]
    return [(["麻雀の集計、", "まだ電卓でやってますか？"], s0),
            (["まじゃすこなら、", "点数を入れるだけ。", "最後の1人は、自動で入ります。"], s1),
            (["順位とスコアも、その場で出ます。"], s2),
            (["URLを送れば、", "全員のスマホで見られます。"], s3),
            (["通算の成績も、", "自動でたまっていきます。"], s4),
            (["無料で、登録もいりません。", "プロフィールのリンクからどうぞ。"], s5)]

NARR = {"voice-kinou": v_kinou}

def build(name, fn):
    scenes = fn()
    with tempfile.TemporaryDirectory() as tmp:
        clips = []
        for i, (ph, _) in enumerate(scenes):
            mp3 = os.path.join(tmp, f"{i}.mp3")
            if VV: ratio = vv_tts(ph, mp3)
            else: words = asyncio.run(tts("".join(ph), mp3))
            x = load(mp3, tmp)
            nz = np.nonzero(np.abs(x) > .004)[0]
            head = nz[0] / SR
            x = x[nz[0]:nz[-1] + 1]
            d = len(x) / SR
            clips.append((x, [r * d for r in ratio] if VV else [max(0, t - head) for t in phrase_times(ph, words, d)], d))
    t, els, sub, place = 0.0, [], [], []
    for (ph, mk), (x, marks, d) in zip(scenes, clips):
        a, b = t, t + LEAD + d + GAP
        last = (ph, mk) == scenes[-1]
        if last: b += 1.2
        els += mk(round(a, 2), round(b, 2))
        place.append((a + LEAD, x))
        for k, p in enumerate(ph):
            s0 = a + LEAD + marks[k]
            s1 = a + LEAD + marks[k + 1] if k + 1 < len(ph) else a + LEAD + d + .12
            sub.append(f'<div class="sub" data-sub="{s0:.2f},{s1:.2f}"><span>{ms.esc(p)}</span></div>')
            print(f"  {s0:5.2f}-{s1:5.2f} {p}")
        t = b
    dur = t
    tmpname = "_narr-" + name
    credit = [f'<div class="dom" style="left:0;right:0;top:1560px;text-align:center;font-size:32px">VOICEVOX:{ms.esc(VV[1])}</div>'] if VV else []
    ms.build(tmpname, lambda: (dur, els + sub + credit))
    # 音
    v = np.zeros(int(dur * SR))
    for a, x in place: mh.put(v, x, a, 1.0)
    v = v / np.abs(v).max()
    env = np.convolve((np.abs(v) > .02).astype(float), np.ones(4000) / 4000, "same")
    m = soft_bgm(dur); m = m / np.abs(m).max() * .3 * (1 - .5 * np.clip(env * 2, 0, 1))
    x = v * .95 + m
    f = int(.8 * SR); x[-f:] *= np.linspace(1, 0, f)
    x = x / np.abs(x).max() * .9
    wav = os.path.join(ms.OUT, tmpname + ".wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype(np.int16).tobytes())
    silent, mp4 = os.path.join(ms.OUT, tmpname + ".mp4"), os.path.join(ms.OUT, name + ".mp4")
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-i", silent, "-i", wav, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4], check=True)
    os.replace(os.path.join(ms.OUT, tmpname + "-thumb.jpg"), os.path.join(ms.OUT, name + "-thumb.jpg"))
    os.remove(silent); os.remove(wav)
    print("ok", name, f"{dur:.1f}s", mp4)

if __name__ == "__main__":
    a = sys.argv[1:]
    out = None
    if "--vv" in a:
        k = a.index("--vv"); VV = (int(a[k + 1]), a[k + 2]); vv_dict()
        if len(a) > k + 3: out = a[k + 3]
        a = a[:k]
    only = a[0] if a else ""
    for k, fn in NARR.items():
        if not only or only in k:
            build(out or k, fn)
