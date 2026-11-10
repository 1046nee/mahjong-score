# -*- coding: utf-8 -*-
"""ナレーションと字幕の入ったショート動画を作る（2026-11-04〜）。縦 1080×1920・30fps。
見た目は make_short.py の動画と同じ。声の長さから画面の切り替えの時刻を決めるので、声と画面と字幕がずれない。

声: edge-tts（ja-JP-KeitaNeural・男性）。台本の文字を Microsoft のサービスへ送って音声にする（要: pip install edge-tts）
BGM: 自作（numpy）。外の曲は使わない
出力: まじゃすこ素材/video/<名前>.mp4 （コミットしない）
使い方: python tools/make_narrated.py [名前]  → まじゃすこ素材/video/voice-<名前>.mp4（名前なしで全部）
  VOICEVOX の声: 先にエンジン（run.exe）を動かして python tools/make_narrated.py [名前] --vv <話者ID> <クレジットの名前> [接尾辞]
  例: python tools/make_narrated.py --vv 3 ずんだもん zundamon → voice-<名前>-zundamon.mp4
場面で組む動画（NARR）は声の長さで場面の時刻が決まる。録画の動画（TIMED）は録画の目印の時刻に声を重ねる
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

# 字幕は動画のカードと同じ白い丸の帯＋濃い文字。語尾の「、」「。」は出さない（2026-11-05 ユーザーの判断。白文字に黒縁は動画の雰囲気に合わない）
ms.CSS += """
.sub { position: absolute; left: 60px; right: 60px; top: 1500px; z-index: 30; text-align: center; opacity: 0; }
.sub span { display: inline-block; background: rgba(255,255,255,.96); color: #1F2A28; font-size: 50px; font-weight: 900; line-height: 1.3; white-space: nowrap; border-radius: 999px; padding: 16px 44px; box-shadow: 0 12px 30px rgba(16,40,36,.14); }
"""
ms.JS += r"""
const renderBase = window.render;
window.render = (t) => { renderBase(t); document.querySelectorAll('[data-sub]').forEach(e => { const [a, b] = e.dataset.sub.split(',').map(Number); e.style.opacity = t >= a && t < b ? 1 : 0; }); };
"""

# 声に渡す前の読みかえ（字幕はそのまま）。VOICEVOX の読み違いはここか下の VV_WORDS・VV_ACCENT に足す
SAY = {"URL": "ユーアールエル", "10-30": "ワンスリー", "10-0-10": "じゅう、ゼロ、じゅう", "素点": "ソテン", "四麻": "よんま", "三麻": "さんま",
       "萬子": "マンズ", "筒子": "ピンズ", "索子": "ソーズ", "白・發・中": "ハク、ハツ、チュン", "王牌": "ワンパイ", "安パイ": "アンパイ", "積み棒": "ツミボー",
       "平均着順": "ヘイキンチャクジュン", "勝ってた": "かってた",
       # 牌・用語（2026-11-09 用語・役・Mリーグの台本で読み違いを洗い出した）
       "白發中": "ハク、ハツ、チュン", "二・三・四・六・八索と發": "リャン、サン、スー、ロー、パーソーと、ハツ", "一二・八九": "イーリャン、パーチュー",
       "四五": "スーウー", "一・九": "イー、チュー", "萬・筒・索": "マン、ピン、ソー", "南家・西家・北家": "ナンチャ、シャーチャ、ペーチャ", "起家": "チーチャ",
       "嶺上牌": "リンシャンパイ", "断么九": "タンヤオ", "牌山": "ハイヤマ", "流局": "リューキョク", "大明槓": "ダイミンカン", "小明槓": "ショーミンカン",
       "加槓": "カカン", "槓子": "カンツ", "槓": "カン", "面子": "メンツ", "刻子": "コーツ", "順子": "シュンツ", "雀頭": "ジャントー", "明刻": "ミンコー",
       "四暗刻": "スーアンコー", "暗刻": "アンコー", "翻": "ハン", "幢": "トン", "雀魂": "ジャンソウル", "天鳳": "テンホー", "MAKA": "マカ", "NAGA": "ナガ",
       "麻将連合": "マージャンレンゴウ", "上家": "カミチャ", "下家": "シモチャ", "対面": "トイメン", "副露": "フーロ", "東家": "トンチャ",
       # 2026-11-09 完成した動画の読みを全部取り出して見つけた読み違い
       "東南西北": "トン、ナン、シャー、ペー", "東・南・西・北": "トン、ナン、シャー、ペー", "風牌": "フォンパイ", "場風": "バカゼ", "自風": "ジカゼ",
       "東場なら東": "トンバならトン", "東家なら東": "トンチャならトン", "東場": "トンバ", "南場": "ナンバ", "打牌": "ダハイ", "〜": "から",
       "HIRO柴田": "ヒロシバタ",
       "一盃口": "イーペーコー", "純全帯么九": "ジュンチャンタイヤオチュー", "么九牌": "ヤオチューハイ", "形聴": "ケイテン", "四六": "スーロー",
       "対子": "トイツ", "東南戦": "トンナンセン", "50NP": "ごじゅうエヌピー", "2025-26": "にせんにじゅうご、にじゅうろく", "2026-27": "にせんにじゅうろく、にじゅうなな",
       "123・456・789": "イチニーサン、スーウーロー、チーパーチュー", "「1112345678999」": "イチイチイチ、ニー、サン、スー、ウー、ロー、チー、パー、キュウキュウキュウ",
       # 選手の名前
       "下石戟": "シモイシゲキ", "逢川恵夢": "アイカワメム", "茅森早香": "カヤモリサヤカ", "岡田紗佳": "オカダサヤカ", "萩原聖人": "ハギワラマサト",
       "醍醐大": "ダイゴマサル", "尻無濱航": "シリナシハマワタル", "伊達朱里紗": "ダテアリサ", "朝倉康心": "アサクラコウシン", "中田花奈": "ナカダカナ"}

# 2026-11-10 作り直しの台本（用語・役・待ち・ルール・Mリーグ）で見つけた読み違い
SAY.update({
    "跳満": "ハネマン", "三倍満": "サンバイマン", "暗槓": "アンカン", "明槓": "ミンカン", "東風戦": "トンプウセン", "洗牌": "シーパイ", "砌牌": "チーパイ",
    "壁牌": "ピーパイ", "摸打": "モーター", "和了": "ホーラ", "栄和": "ロンホー", "倒牌": "トーハイ", "海底摸月": "ハイテイモーユエ", "河底撈魚": "ホーテイラオユイ",
    "海底牌": "ハイテイハイ", "河底牌": "ホーテイハイ", "海底": "ハイテイ", "搶槓": "チャンカン", "輪荘": "ロンチャン", "荘家": "チャンチャ", "散家": "サンチャ",
    "自家": "ジチャ", "他家": "ターチャ", "包": "パオ", "大四喜": "ダイスーシー", "小四喜": "ショウスーシー", "荒牌平局": "ホワンパイピンチュー",
    "四風連打": "スーフーレンダ", "四家立直": "スーチャリーチ", "四開槓": "スーカイカン", "三家和": "サンチャホー", "錯和": "サクホー", "多牌": "ターハイ",
    "十三不塔": "シーサンプートー", "搭子": "ターツ", "人和": "レンホー", "二盃口": "リャンペーコー", "三面張": "サンメンチャン", "嵌張": "カンチャン",
    "辺張": "ペンチャン", "一気通貫": "イッキツーカン", "花牌": "ホアパイ", "七対子": "チートイツ", "雀王": "ジャンオウ", "混一色": "ホンイーソー",
    "清一色": "チンイーソー", "混老頭": "ホンロートー", "清老頭": "チンロートー", "混と清": "ホンとチン", "混は": "ホンは", "清は": "チンは",
    "中張牌": "チュンチャンパイ", "場風牌": "チャンフォンパイ", "自風牌": "メンフォンパイ", "空テン": "カラテン", "北抜き": "ペーヌキ",
    "南家": "ナンチャ", "西家": "シャーチャ", "北家": "ペーチャ", "西入": "シャーニュウ", "西場": "シャーバ", "ダブ東": "ダブトン", "ダブ南": "ダブナン",
    "一・五・七・九索": "イー、ウー、チー、チューソー", "一二、八九": "イーリャン、パーチュー", "四・五は三": "スー、ウーは、サン",
    "ABEMAS": "アベマズ", "ABEMA": "アベマ", "BEAST X": "ビーストエックス", "2022-23": "にせんにじゅうに、にじゅうさん", "5-10": "ゴットー",
    "月・火・木・金": "げつ、か、もく、きん", "1シーズン": "ワンシーズン", "小林剛": "コバヤシゴウ", "松ヶ瀬隆弥": "マツガセタカヤ", "百万石": "ヒャクマンゴク",
    "単位は台": "単位はタイ",
})
import re as _re
_TILE_N = dict(zip("一二三四五六七八九", ["イー", "リャン", "サン", "スー", "ウー", "ロー", "チー", "パー", "チュー"]))
_TILE_S = {"萬": "ワン", "筒": "ピン", "索": "ソー"}
_DIG = dict(zip("123456789", ["イチ", "ニー", "サン", "ヨン", "ゴー", "ロク", "ナナ", "ハチ", "キュー"]))
_HONOR = {"東": "トン", "南": "ナン", "西": "シャー", "北": "ペー", "白": "ハク", "發": "ハツ", "中": "チュン"}

def say(text):
    for k in sorted(SAY, key=len, reverse=True): text = text.replace(k, SAY[k])  # 長い語から（「槓」より「大明槓」が先）
    # 数牌: 四萬→スーワン・三索→サンソー
    text = _re.sub(r"([一二三四五六七八九])([萬筒索])", lambda m: _TILE_N[m[1]] + _TILE_S[m[2]], text)
    # 局: 東2局→トン2局・南4局→ナン4局
    text = _re.sub(r"([東南])(?=[0-9１-９]局)", lambda m: _HONOR[m[1]], text)
    # 字牌1文字（白・發・中・東南西北）: 区切りに挟まれたときだけ（「中国」「途中」「アプリの中の」「白鳥」は変えない）
    text = _re.sub(r"(?:(?<=^)|(?<=[、。「・とはがやをにらた]))([東南西北白發中])(?=[、。」・とをでだはのがやなまもしに]|$)", lambda m: _HONOR[m[1]], text)
    # 牌の数字の並び: 222を→ニーニーニー・123のような→イチニーサン（点数・枚数などの単位がつく数と、プラス／マイナス／第のあとは変えない）
    text = _re.sub(r"(?<![0-9,.\-ス第])([1-9]{2,})(?=[をのがと＋・、。なやは]|$)",
                   lambda m: "".join(_DIG[c] for c in m[1]), text)
    return text

async def tts(text, path):
    c = edge_tts.Communicate(say(text), VOICE, rate=RATE, boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary": words.append((ch["offset"] / 1e7, ch["text"]))
    return words

VV = None  # (話者ID, クレジットの名前)
DRAFT = False  # True: 声なし。字幕の長さは文字数から見積もる（声は個人PCで --vv を付けて作り直す）
VV_URL = "http://127.0.0.1:50021"

def vv_post(path, body=None, ctype="application/json"):
    r = urllib.request.Request(VV_URL + path, data=body if body is not None else b"", headers={"Content-Type": ctype}, method="POST")
    return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(r, timeout=120).read()

# 読みとアクセントの直し（2026-11-05 ユーザーの指摘）。エンジンの辞書はそのPCにしか残らないので、毎回ここから入れる
VV_WORDS = [("まじゃすこ", "マジャスコ", 0), ("その場", "ソノバ", 0), ("ユーアールエル", "ユーアールエル", 5), ("ヘイキンチャクジュン", "ヘイキンチャクジュン", 5)]
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
            (END_LINE, s5)]

END_LINE = ["無料で、登録もいりません。", "プロフィールのリンクからどうぞ。"]

def v_aruaru():
    """集計係あるある（B）。最後に問いかけてコメントを呼ぶ"""
    def hook(a, b):
        return [ms.at(a, b, '<div class="badge">あるある</div><h1>セット麻雀の<br>集計係あるある</h1>', cls="cap hook", style="top:640px", anim="pop")]
    def card(i, tx):
        return lambda a, b: [ms.at(a, b, f'<span class="no">{i}</span><div class="tx">{ms.esc(tx)}</div>', cls="card", style="top:640px", anim="right")]
    def sol(a, b):
        return [ms.at(a, b, '<h1>それ、まじゃすこなら<br>全部自動。</h1>', cls="cap", style="top:170px", anim="pop"), ms.phone_at(a + .2, b, "howto-4.jpg", y=400)[0],
                ms.chip_at(a + .8, b, ("", "+69.1", ("medal", 1)), "l", 700), ms.chip_at(a + 1.2, b, ("通算", "自動", ""), "r", 900)]
    def q(a, b):
        return [ms.at(a, b, '<h1>あなたの卓は、<br>いくつ当てはまる？</h1>', cls="cap", style="top:640px", anim="pop")]
    return [(["セット麻雀の、", "集計係あるある。"], hook),
            (["終わったあと、", "なぜか電卓を渡される。"], card(1, "終わったあと、\n電卓を渡される")),
            (["ウマとオカの計算で、", "手が止まる。"], card(2, "ウマ・オカの計算で\n手が止まる")),
            (["先月どっちが勝ってた？", "誰も答えられない。"], card(3, "「先月どっちが\n勝ってた？」に\n誰も答えられない")),
            (["スコア表の写真が、", "LINEの奥に消えていく。"], card(4, "スコア表の写真が\nLINEの奥に消える")),
            (["それ、まじゃすこなら", "全部自動です。"], sol),
            (["あなたの卓は、", "いくつ当てはまる？"], q),
            (END_LINE, lambda a, b: [ms.end_card(a)])]

def v_umaoka():
    """初心者の壁：ウマ・オカ（D）。例はアプリの使い方の画面と同じ数字（健太 45,200点 → +65.2）"""
    def hook(a, b):
        return [ms.at(a, b, '<div class="badge g">初心者の壁</div><h1>ウマ・オカって、<br>結局なに？</h1>', cls="cap hook", style="top:620px", anim="pop")]
    def oka(a, b):
        return [ms.at(a, b, '<div class="badge g">オカ</div><h1>トップへの<br>ごほうび</h1>', cls="cap", style="top:300px"),
                ms.at(a + .8, b, '<div class="eq">25,000点持ち・30,000点返し<br>4人とも 5,000点ずつ出して<br>トップがまとめて受け取る<br>トップ <b>+15</b>／ほか <span style="color:#C62828">−5</span></div>', cls="cap", style="top:800px")]
    def uma(a, b):
        return [ms.at(a, b, '<div class="badge g">ウマ</div><h1>順位で動く<br>ポイント</h1><p>よくある「10-30」なら</p>', cls="cap", style="top:260px"),
                ms.at(a + .8, b, '<table class="ex"><tr><td class="l">1位</td><td class="p">+30</td></tr><tr><td class="l">2位</td><td class="p">+10</td></tr>'
                      '<tr><td class="l">3位</td><td class="n">−10</td></tr><tr><td class="l">4位</td><td class="n">−30</td></tr></table>', cls="cap", style="top:820px")]
    def ex(a, b):
        return [ms.at(a, b, '<h1>たとえば、<br>45,200点でトップなら</h1>', cls="cap", style="top:300px"),
                ms.at(a + .8, b, '<div class="eq">素点 <b>+20.2</b><small style="font-size:.6em;color:#5B6866">（45,200−25,000）</small><br>ウマ <b>+30</b><br>オカ <b>+15</b><br>＝ <span class="o">+65.2</span></div>', cls="cap", style="top:740px")]
    def app(a, b):
        return [ms.at(a, b, '<h1>この計算、<br>まじゃすこなら自動。</h1>', cls="cap", style="top:170px", anim="pop"), ms.phone_at(a + .2, b, "howto-4.jpg", y=400)[0]]
    return [(["ウマとオカって、", "結局なに？"], hook),
            (["オカは、トップへのごほうび。", "4人が5,000点ずつ出して、", "トップがまとめて受け取ります。"], oka),
            (["ウマは、順位で動くポイント。", "よくある10-30なら、", "1位はプラス30、", "4位はマイナス30。"], uma),
            (["たとえば、", "45,200点でトップなら、", "素点が20.2、", "ウマが30、オカが15。", "合わせて、プラス65.2です。"], ex),
            (["この計算、", "まじゃすこなら自動です。"], app),
            (END_LINE, lambda a, b: [ms.end_card(a)])]

NARR = {"kinou": v_kinou, "aruaru-shukei": v_aruaru, "kabe-umaoka": v_umaoka}
import video_topics  # 記事をもとにした動画（台本は tools/video_topics.py）
NARR.update(video_topics.TOPICS)
import video_topics2  # NAGA・Mリーグ・プロ団体・麻雀AI（tools/video_topics2.py）
NARR.update(video_topics2.TOPICS)
import video_topics3  # 作り直し（2026-11-10〜）。同じ名前の動画を上書きする
NARR.update(video_topics3.TOPICS)
import video_topics_ml  # Mリーグ・プロ団体の作り直し（チームカラー）
NARR.update(video_topics_ml.TOPICS)
import video_topics_yaku  # 役シリーズの作り直し（詳しい版・2つ並べる版）
NARR.update(video_topics_yaku.TOPICS)
for _k in video_topics_yaku.DROP: NARR.pop(_k, None)
import video_topics_yougo  # 用語シリーズをカテゴリごとの12本に（gy-01〜12）
NARR.update(video_topics_yougo.TOPICS)
for _k in video_topics_yougo.DROP: NARR.pop(_k, None)
import video_topics_rules  # 打つ前に決めるルール（一般・玄人・ローカル役・三麻）
NARR.update(video_topics_rules.TOPICS)
import video_topics_quiz  # この手の待ちは？（14問）
NARR.update(video_topics_quiz.TOPICS)
import video_topics_basic  # 初心者向け b-01〜11・点数とスコア s-01〜13
NARR.update(video_topics_basic.TOPICS)
import video_topics_more  # 分かれ目の続き・Mリーグとプロ・AI・雑学・集まりの運営
NARR.update(video_topics_more.TOPICS)

# ---- 録画の動画（画面の時刻は録画で決まる）：make_short.py の動画に、目印の時刻から声と字幕を重ねる ----
# (make_short の動画名, フックの声, [(いつ, 声)]) 。いつ = 録画の目印の名前 / 0（録画の始まり）/ 関数 c -> 秒
# c = {"T0": 録画が始まる秒, "m": 録画の目印, "end": 最後のロゴの秒}
TIMED = {
 "play-quick": (["麻雀のスコア、", "スマホで記録してみました。"],
   [(0, ["はじめるを押して、", "人数を選ぶだけ。"]), ("game", ["あとは、点数を入れていきます。", "下の2桁は、入れなくて大丈夫。"]),
    ("auto", ["最後の1人は、自動です。"]), ("done", ["順位とスコアも、すぐ出ます。"]), ("share", ["URLを送れば、", "全員のスマホに。"])]),
 "play-rounds": (["4試合目で、", "逆転なるか？"],
   [(lambda c: c["T0"] + .2, ["3試合目が終わって、", "トップは健太、プラス82.7。"]),
    (lambda c: c["T0"] + 3.4, ["2位の美咲は、プラス13.9。", "差は68.8です。"]),
    (lambda c: c["T0"] + 6.6, ["4試合目、", "美咲は逆転できるのか？"]),
    (lambda c: c["T0"] + ms.PRE_ROUNDS, ["4試合目の点数を入れていきます。"]),
    (lambda c: c["T0"] + ms.PRE_ROUNDS + c["m"]["input"], ["健太は8,000点のラス。", "美咲は52,000点の大トップ！"]),
    (lambda c: c["T0"] + ms.PRE_ROUNDS + c["m"]["done"], ["美咲がプラス85.9で、逆転の1位！", "健太は2位に落ちました。"]),
    (lambda c: c["T0"] + ms.PRE_ROUNDS + c["m"]["scroll"], ["1試合ごとのスコアも、", "個人の成績も、全部自動です。"])]),
 "play-team": (["チーム戦も、", "まじゃすこで記録できます。"],
   [(0, ["はじめるから、", "先にメンバーを決めます。"]), ("members", ["8人の名前を入れて、"]), ("team", ["チーム戦を押すと、"]),
    ("teams", ["4つのチームに、", "自動で分かれます。"]), ("start", ["開始したら、", "URLを送ります。"]),
    ("input", ["その試合の4人を選んで、", "点数を入れるだけ。"]), ("done", ["チームの順位も、", "その場で出ます。"]),
    ("later", ["何試合打っても、", "チームの合計は自動です。"])]),
 "play-mawashi": (["5人以上で打つ日、", "集計どうしてますか？"],
   [(0, ["はじめるから、", "先にメンバーを決めます。"]), ("members", ["6人の名前を入れて、"]), ("start", ["四麻で開始。"]),
    ("r1", ["試合ごとに、", "入る4人を選んで、", "点数を入れます。"]), ("r2", ["次の試合は、", "抜け番を入れかえて。"]),
    ("done", ["試合数が違っても、"]), ("stats", ["通算と個人の成績は、", "自動で出ます。"])]),
 "calc-vs": (["電卓とまじゃすこ、", "どっちが速い？"],
   [(lambda c: c["T0"] + .2, ["よーい、スタート！"]), (lambda c: c["T0"] + 1.9, ["電卓は1人ずつ、", "ウマとオカを足していく。"]),
    (lambda c: c["T0"] + 5.4, ["まじゃすこは、", "点数を入れるだけ。"]),
    (lambda c: c["end"] - 5.5, ["まじゃすこは、もう完了。", "電卓は、まだ3人目…"]), (lambda c: c["end"] - 2.6, ["この差が、毎回です。"])]),
}
# 仲間ページ・マイページの録画（社用PCで撮る）は、make_short.py の字幕をそのまま声にする
for _k, (_b, _h, _st) in ms.PAGE_VIDEOS.items():
    if _k not in TIMED:
        TIMED[_k] = (_h.split("\n"), [(k, h.split("\n")) for k, h in _st])

def synth(ph, tmp, i):
    """声を作って (波形, 区切りごとの始まりの秒, 長さ) を返す"""
    if DRAFT:
        lens = [max(4, len(p)) / 6.6 + .12 for p in ph]
        d = sum(lens); acc = 0; st = []
        for x_ in lens: st.append(acc); acc += x_
        return np.zeros(int(d * SR)), st, d
    mp3 = os.path.join(tmp, f"{i}.mp3")
    if VV: ratio = vv_tts(ph, mp3)
    else: words = asyncio.run(tts("".join(ph), mp3))
    x = load(mp3, tmp)
    nz = np.nonzero(np.abs(x) > .004)[0]
    head = nz[0] / SR
    x = x[nz[0]:nz[-1] + 1]
    d = len(x) / SR
    return x, ([r * d for r in ratio] if VV else [max(0, t - head) for t in phrase_times(ph, words, d)]), d

def build(name, fn):
    """場面ごとに声を作り、声の長さで場面の時刻を決める"""
    scenes = fn()
    with tempfile.TemporaryDirectory() as tmp:
        clips = [synth(ph, tmp, i) for i, (ph, _) in enumerate(scenes)]
    t, els, items = 0.0, [], []
    for (ph, mk), (x, marks, d) in zip(scenes, clips):
        a, b = t, t + LEAD + d + GAP
        last = (ph, mk) == scenes[-1]
        if last: b += 1.2
        els += mk(round(a, 2), round(b, 2))
        items.append((a + LEAD, ph, x, marks, d))
        t = b
    render(name, t, els, items)

def build_timed(name, vname, hook, cues):
    """録画の動画に声を重ねる。声が前の声とぶつかるときは後ろへずらす（ずれが大きいと警告）"""
    tl = os.path.join(ms.CLIPS, vname if vname != "calc-vs" else "play-quick", "timeline.json")
    if not os.path.exists(tl):
        print("skip", name, "（録画がない: python tools/record_play.py", vname, "）"); return
    marks = json.load(io.open(tl, encoding="utf-8"))["marks"]
    with tempfile.TemporaryDirectory() as tmp:
        hk = synth(hook, tmp, "h")
        cs = [synth(ph, tmp, i) for i, (_, ph) in enumerate(cues)]
        en = synth(END_LINE, tmp, "e")
    H = max(2.6, round(LEAD + hk[2] + GAP, 2))
    def remake():
        ms.NARR = True; ms.HOOK = H
        try:
            ms.LIVE.clear()
            return ms.VIDEOS[vname]()
        finally:
            ms.NARR = False; ms.HOOK = 2.6
    dur, els = remake()
    c = {"T0": H, "m": marks, "end": dur - 4.0}
    items = [(LEAD, hook, *hk)]
    nxt = LEAD + hk[2] + .15
    for (when, ph), (x, mk, d) in zip(cues, cs):
        want = (c["T0"] if when == 0 else c["T0"] + marks[when] if isinstance(when, str) else when(c)) + .15
        s = max(want, nxt)
        if s - want > .6: print(f"  ！声が {s - want:.1f}秒 おくれる: {''.join(ph)}")
        items.append((s, ph, x, mk, d)); nxt = s + d + .15
    s = max(c["end"] + LEAD, nxt)
    items.append((s, END_LINE, *en))
    render(name, max(dur, s + en[2] + 1.4), None, items, lambda: remake()[1])

def render(name, dur, els, items, remake=None):
    """items = [(声の始まりの秒, 字幕の区切り, 波形, 区切りの始まり, 長さ)]"""
    sub, place = [], []
    for s, ph, x, marks, d in items:
        place.append((s, x))
        for k, p in enumerate(ph):
            s0 = s + marks[k]
            s1 = s + marks[k + 1] if k + 1 < len(ph) else s + d + .12
            sub.append(f'<div class="sub" data-sub="{s0:.2f},{s1:.2f}"><span>{ms.esc(p.rstrip("、。"))}</span></div>')
            print(f"  {s0:5.2f}-{s1:5.2f} {p}")
    tmpname = "_narr-" + name
    credit = [f'<div class="dom" style="left:0;right:0;top:1700px;text-align:center;font-size:32px">VOICEVOX:{ms.esc(VV[1])}</div>'] if VV else []
    ms.build(tmpname, lambda: (dur, (remake() if remake else els) + sub + credit))  # 録画の動画は build() が LIVE を消すので作り直す
    # 音
    v = np.zeros(int(dur * SR))
    for a, x in place: mh.put(v, x, a, 1.0)
    v = v / max(np.abs(v).max(), 1e-9)
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
    tail = ""
    if "--vv" in a:
        k = a.index("--vv"); VV = (int(a[k + 1]), a[k + 2]); vv_dict()
        if len(a) > k + 3: tail = "-" + a[k + 3]
        a = a[:k]
    if "--draft" in a:
        a.remove("--draft"); DRAFT = True; tail = "-draft"
    only = a[0] if a else ""
    for k, fn in NARR.items():
        if not only or only == k:
            build(f"voice-{k}{tail}", fn)
    for k, (hook, cues) in TIMED.items():
        if not only or only == k:
            build_timed(f"voice-{k}{tail}", k, hook, cues)
