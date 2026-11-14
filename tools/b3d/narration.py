# -*- coding: utf-8 -*-
"""3Dの対局動画（麻雀の所作）の声の台本と、読みの確かめ。
  python tools/b3d/narration.py --check            … 台本に出てくる麻雀の語の読みを表にして、VOICEVOX が実際に読むカナを全部の文について出す（声を作る前に必ず見る）
  声を入れるのは make_clip.py（--voice）。声は VOICEVOX の 青山龍星（ノーマル・話者ID 13）＝2026-11-13 ユーザーの判断
読みの決まり（2026-11-13 ユーザーの指定「麻雀の語句は、読み仮名が合っているか確かめたうえで台本を作る」）:
  1. 麻雀の語の読みは TERMS に書く。出どころは サイトの用語の辞書（tools/add_ruby.py の READ＝記事のルビ）と、ショート動画の読みの辞書（tools/make_narrated.py の SAY）。
     2つの辞書で読みが食い違う語・どちらにも無い語は、--check が「要確認」として出す。TERMS に無い麻雀の語が台本にあっても「要確認」
  2. 声に渡す文は、TERMS の語をカナに置きかえてから渡す（VOICEVOX は漢字の麻雀の語をよく読み違える: 流局→ナガレキョク・平和→ヘイワ・対面→タイメン）
  3. 置きかえたあとに VOICEVOX が読むカナを出して、TERMS の読みがそのまま入っているかを機械で確かめる（アクセントの区切りで別の音にならないか）
"""
import io, json, os, re, sys, urllib.parse, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
SPEAKER = (13, "青山龍星")      # 2026-11-13 ユーザーの判断（候補A。一度Fの玄野武宏にしてから変更）
VV_URL = "http://127.0.0.1:50021"

# 台本に出てくる麻雀の語 → 読み。ここに無い語は --check で止まる
TERMS = {
 "手牌": "テハイ", "上家": "カミチャ", "下家": "シモチャ", "対面": "トイメン", "他家": "ターチャ", "順子": "シュンツ", "対子": "トイツ", "搭子": "ターツ",
 "暗刻": "アンコー", "刻子": "コーツ", "槓子": "カンツ", "副露": "フーロ", "打牌": "ダハイ", "暗槓": "アンカン", "大明槓": "ダイミンカン", "加槓": "カカン", "槍槓": "チャンカン",
 "嶺上牌": "リンシャンパイ", "王牌": "ワンパイ", "門前": "メンゼン", "流局": "リューキョク", "連荘": "レンチャン", "平和": "ピンフ", "断么九": "タンヤオ",
 "三色同順": "サンショクドウジュン", "供託": "キョウタク", "千点棒": "センテンボウ", "点棒": "テンボウ", "捨て牌": "ステハイ", "発声": "ハッセイ", "開示": "カイジ",
 "役満": "ヤクマン", "両面": "リャンメン", "単騎": "タンキ", "山": "ヤマ", "河": "カワ", "親": "オヤ", "一拍": "イッパク", "1枚": "イチマイ", "4枚目": "ヨンマイメ",
 "3枚": "サンマイ", "2枚": "ニマイ", "4枚": "ヨンマイ", "1本": "イッポン", "千点": "センテン", "1500点": "センゴヒャクテン", "7700": "ナナセンナナヒャク",
 "400・700": "ヨンヒャク、ナナヒャク", "鳴く": "ナク", "鳴き": "ナキ", "鳴いた": "ナイタ", "鳴いて": "ナイテ", "横向き": "ヨコムキ", "表向き": "オモテムキ",
 "ドラ表示牌": "ドラヒョウジハイ", "あがり牌": "アガリハイ", "白": "ハク", "發": "ハツ", "中": "チュン", "東": "トン", "西": "シャー", "北": "ペー", "役": "ヤク", "牌": "ハイ", "卓": "タク", "倒し": "タオシ", "伏せ": "フセ",
}
_N = dict(zip("一二三四五六七八九", ["イー", "リャン", "サン", "スー", "ウー", "ロー", "チー", "パー", "キュー"]))      # 九はキュー（サイトの牌の一覧表と同じ。ショート動画の辞書はチュー）
_S = {"萬": "ワン", "筒": "ピン", "索": "ソー"}

# 動画ごとの台本。intro＝題名のあいだ／pre＝①の前の確認／steps＝手順ごと／tail＝まとめ／outro＝締め（どの動画も同じ）
OUTRO = "麻雀のスコア記録は、まじゃすこで。"
NARR = {
 "chi": dict(intro="チーの方法を、5つの手順で覚えましょう。",
    pre="手牌に、搭子があります。上家がつながる牌を切ったら、チーできます。チーできるのは、上家の捨て牌だけです。",
    steps=["まず、チー、と声に出します。ポンが優先なので、一拍おいてから言いましょう。", "鳴くのに使う搭子を倒して、みんなに見せます。", "上家が切った牌を、取ってきます。",
           "取った牌を横向きにして左に付け、卓の右に寄せます。", "最後に、手牌からいらない牌を1枚切ります。"],
    tail="発声、開示、回収、副露、打牌。この順番です。"),
 "pon": dict(intro="ポンの方法を、5つの手順で覚えましょう。",
    pre="手牌に、対子があります。他家が同じ牌を切ったら、ポンできます。だれの捨て牌でも、ポンできます。",
    steps=["まず、ポン、と声に出します。ポンは、チーより優先されます。", "鳴くのに使う対子を倒して、みんなに見せます。", "対面が切った牌を、取ってきます。",
           "取った牌は横向きに。対面から鳴いたときは、まんなかに置きます。", "最後に、手牌からいらない牌を1枚切ります。"],
    tail="発声、開示、回収、副露、打牌。この順番です。"),
 "kan": dict(intro="カンの方法。暗槓の手順です。",
    pre="手牌に、暗刻があります。自分で4枚目を引いたら、暗槓できます。",
    steps=["まず、カン、と声に出します。", "まず、同じ牌4枚を表向きに倒して、みんなに見せます。そのあと、外側の2枚を裏返します。", "4枚を、卓の右に寄せます。", "ドラ表示牌のとなりを、1枚めくります。カンドラです。",
           "王牌の端から、嶺上牌を1枚取ります。", "最後に、手牌からいらない牌を1枚切ります。"],
    tail="カンをしたら、カンドラをめくり、嶺上牌を取る。ここまでがワンセットです。"),
 "daiminkan": dict(intro="カンの方法。大明槓の手順です。",
    pre="手牌に、暗刻があります。他家が4枚目を切ったら、大明槓できます。だれの捨て牌でも、できます。",
    steps=["まず、カン、と声に出します。", "手牌の同じ牌3枚を倒して、みんなに見せます。", "下家が切った牌を、取ってきます。", "取った牌は横向きに。下家から鳴いたときは、右に置きます。",
           "ドラ表示牌のとなりを、1枚めくります。", "王牌の端から、嶺上牌を1枚取ります。", "最後に、手牌からいらない牌を1枚切ります。"],
    tail="大明槓は鳴きなので、門前ではなくなります。"),
 "kakan": dict(intro="カンの方法。加槓の手順です。",
    pre="ポンした刻子があります。自分で4枚目を引いたら、ポンした3枚に足して、加槓できます。",
    steps=["まず、カン、と声に出します。", "ポンした牌の、横向きの1枚の上に、横向きで重ねます。", "ドラ表示牌のとなりを、1枚めくります。", "王牌の端から、嶺上牌を1枚取ります。",
           "最後に、手牌からいらない牌を1枚切ります。"],
    tail="加えた牌でロンされることがあります。槍槓という役です。"),
 "riichi": dict(intro="リーチの方法を、4つの手順で覚えましょう。",
    pre="鳴いていない手で、あと1枚であがれる形なら、千点棒を出して、リーチできます。",
    steps=["まず、リーチ、と声に出します。", "いらない牌を、横向きにして切ります。", "千点棒を1本、卓の中央に出します。供託といいます。", "あとは、手牌を変えられません。あがり牌を待ちます。"],
    tail="発声、横向きの打牌、千点棒。この順番です。"),
 "tsumo": dict(intro="ツモあがりの方法を、4つの手順で覚えましょう。",
    pre="あと1枚であがれる形で、自分であがり牌を引いたら、ツモあがりです。役が1つ以上いります。",
    steps=["山から引いたあがり牌を、手牌の横に置きます。手牌には入れません。", "ツモ、と声に出します。", "手牌を倒して、みんなに見せます。", "役と点数を言います。ツモ、平和。400・700。"],
    tail="あがり牌を手牌に入れないのが、大事なところです。"),
 "ron": dict(intro="ロンあがりの方法を、4つの手順で覚えましょう。",
    pre="あと1枚であがれる形で、他家があがり牌を切ったら、ロンあがりです。だれの捨て牌でも、ロンできます。",
    steps=["まず、ロン、と声に出します。", "手牌を倒して、みんなに見せます。", "あがり牌は、相手の河に置いたままにします。取ってきません。", "役と点数を言います。断么九、平和、三色同順。7700。"],
    tail="ロンした牌は、動かさない。これがきまりです。"),
 "ryukyoku": dict(intro="流局のしかたを、4つの手順で覚えましょう。",
    pre="だれもあがらないまま、山の牌がなくなると、流局です。",
    steps=["だれもあがらずに山がなくなると、流局です。", "あと1枚であがれる人は、テンパイ、と言って、手牌を倒します。", "親から順番に。テンパイでない人は、ノーテン、と言って、手牌を伏せます。",
           "ノーテンの人が、テンパイの人へ点棒を払います。ここでは、1500点ずつです。"],
    tail="親がテンパイなら、連荘。親をもう一度やります。"),
}


def say(text):
    """声に渡す文。麻雀の語をカナに（長い語から）。数牌は 四萬→スーワン"""
    text = re.sub(r"([一二三四五六七八九])([萬筒索])", lambda m: _N[m[1]] + _S[m[2]], text)
    for k in sorted(TERMS, key=len, reverse=True):
        if len(k) == 1:      # 1文字の語（白・發・中・東・役・牌・卓・山・河・親）は、前後が漢字でないときだけ（途中・役満・手牌 を壊さない）
            text = re.sub(r"(?<![一-龥々])" + re.escape(k) + r"(?![一-龥々])", TERMS[k], text)
        else:
            text = text.replace(k, TERMS[k])
    return text


def vv(path, body=None):
    r = urllib.request.Request(VV_URL + path, data=body if body is not None else b"", headers={"Content-Type": "application/json"}, method="POST")
    return urllib.request.build_opener(urllib.request.ProxyHandler({})).open(r, timeout=180).read()


def query(text):
    q = json.loads(vv("/audio_query?" + urllib.parse.urlencode({"text": say(text), "speaker": SPEAKER[0]})))
    q["speedScale"] = 1.08; q["intonationScale"] = 1.15; q["prePhonemeLength"] = .05; q["postPhonemeLength"] = .1
    return q


def kana(q):
    return "".join(m["text"] for a in q["accent_phrases"] for m in a["moras"])


def synth(text, path):
    open(path, "wb").write(vv(f"/synthesis?speaker={SPEAKER[0]}", json.dumps(query(text)).encode("utf-8")))


def lines(name):
    n = NARR[name]
    return [("intro", n["intro"]), ("pre", n["pre"])] + [(f"step{i + 1}", s) for i, s in enumerate(n["steps"])] + [("tail", n["tail"]), ("outro", OUTRO)]


def _norm(k):
    """VOICEVOX のカナ（長音をアイウエオで書く）と比べられる形に: 長音・小さい字のゆれを落とす"""
    k = k.replace("ー", "").replace("、", "")
    for a, b in (("ウ", ""), ("オ", ""), ("イ", ""), ("エ", ""), ("ア", "")): pass
    return k


def check():
    import add_ruby, make_narrated
    R, Sy = add_ruby.READ, make_narrated.SAY
    used = [k for k in sorted(TERMS, key=len, reverse=True) if any(k in t for nm in NARR for _, t in lines(nm))]
    print("== 台本に出てくる語の読み（出どころ） ==")
    bad = 0
    for k in used:
        src = []
        if k in R: src.append("記事の辞書=" + R[k])
        if k in Sy: src.append("動画の辞書=" + Sy[k])
        norm = lambda x: x.replace("ー", "ウ").replace("ュウ", "ュウ")
        flag = ""
        if src and not any(norm(v.split("=")[1]) == norm(TERMS[k]) or v.split("=")[1] == TERMS[k] for v in src): flag = "  ★要確認（辞書と違う）"; bad += 1
        print(f"  {k}\t{TERMS[k]}\t{' / '.join(src) or '（ふつうの言葉・牌の名前）'}{flag}")
    # TERMS に無い麻雀の語（辞書にあるのに台本でカナにしていない語）
    for nm in NARR:
        for seg, t in lines(nm):
            rest = say(t)
            for k in list(R) + list(Sy):
                if len(k) >= 2 and k in rest and re.search(r"[一-龥]", k): print(f"  ★要確認: {nm} {seg} に「{k}」が漢字のまま残っている"); bad += 1
    print("== VOICEVOX が読むカナ ==")
    for nm in NARR:
        for seg, t in lines(nm):
            k = kana(query(t)); print(f"{nm}\t{seg}\t{t}\t{k}")
            sp = say(t)
            for w in re.findall(r"[ァ-ヴー]{3,}", sp):      # カナにした語が、そのままの音で読まれているか（長音は VOICEVOX の書き方に直して比べる）
                vv_w = kana(json.loads(vv("/audio_query?" + urllib.parse.urlencode({"text": w, "speaker": SPEAKER[0]}))))
                nz = lambda x: re.sub(r"[ウオー]", "", x)      # 長音の書き方のゆれ（ボウ／ボオ）は同じ音
                if nz(vv_w) not in nz(k): print(f"  ★要確認: 「{w}」が文の中で別の音になっている（単独では {vv_w}）"); bad += 1
    print("要確認:", bad)
    return bad


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    if "--check" in sys.argv: sys.exit(1 if check() else 0)
