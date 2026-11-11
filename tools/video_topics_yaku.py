# -*- coding: utf-8 -*-
"""役シリーズの作り直し（2026-11-10 ユーザーの指示）。
- リーチ・ピンフは条件を1つずつ、ダメな例もつけて完璧にわかるように
- 役牌は全部のパターン（三元牌・場風・自風・連風牌・役にならない風）を、門前と鳴いた具体例で
- 似ている役は2つ並べて違いを見せる（三色と一通・チャンタと純チャン・三暗刻と四暗刻）
同じ名前で y-01・y-03・y-05・y-07・y-09・y-11 を上書きし、2つ並べた相手（y-08・y-17・y-21）は DROP で外す
"""
from video_topics import esc, head, stage, hook, tile, art, article_end, END
import video_topics3  # noqa: 動き（data-anim）を先に足しておく
import make_short as ms

TOPICS = {}
DROP = ["y-08", "y-17", "y-21"]

ms.CSS += """
.hand { display: flex; justify-content: center; align-items: flex-end; gap: 14px; flex-wrap: nowrap; }
.hand .g { display: inline-flex; gap: 2px; padding-bottom: 12px; border-bottom: 10px solid transparent; border-radius: 4px; }
.hand .g img { display: block; }
.hand .win { padding: 6px; border-radius: 12px; background: #E75620; }
.yk { font-size: 40px; font-weight: 900; color: #1F2A28; line-height: 1.5; }
.ok, .ng { display: inline-block; font-size: 40px; font-weight: 900; color: #fff; border-radius: 999px; padding: 6px 26px; }
.ok { background: #177083; } .ng { background: #C62828; }
.seat { position: relative; width: 640px; height: 640px; margin: 0 auto; background: #2E7D5B; border-radius: 40px; box-shadow: inset 0 0 0 14px #24664A; }
.seat .p { position: absolute; width: 170px; height: 110px; display: grid; place-items: center; font-size: 60px; font-weight: 900; color: #1F2A28; background: #fff; border-radius: 22px; }
.seat .c { position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%); text-align: center; color: #fff; font-size: 40px; font-weight: 900; }
"""

COL = {"o": "#E75620", "g": "#177083", "b": "#4261AA", "y": "#D4A017", "r": "#C62828", "k": "#B4C0BD"}

def hand(groups, w=62, win=None, label=None):
    """groups = [(色の記号 or '', [牌…])]。色をつけた組は下に線。win はあがり牌（右に橙の枠）"""
    out = ""
    for c, ts in groups:
        bc = COL.get(c, "transparent")
        out += f'<span class="g" style="border-bottom-color:{bc}">' + "".join(tile(t, round(w * 1.4) if "yoko" in t else w) for t in ts) + "</span>"
    if win:
        out += f'<span class="win">{tile(win, w)}</span>'
    lb = f'<p class="lbl" style="margin:18px 0 0;font-size:40px">{label}</p>' if label else ""
    return f'<div class="vcard mid" style="padding:30px 20px"><div class="hand">{out}</div>{lb}</div>'

def card(html, top, a, b, d=.3, anim="up"):
    return stage(a + d, b, html, top=top, anim=anim)

def note(tx):
    return f'<div class="note">{tx}</div>'

def tag(ok, tx):
    return f'<span class="{"ok" if ok else "ng"}">{tx}</span>'

def scene(title, *parts):
    """parts = [(出る秒のずれ, 上の位置, HTML)]"""
    def mk(a, b):
        return [head(a, b, title)] + [stage(a + d, b, h, top=t) for d, t, h in parts]
    return mk

YAKU_END = (END, article_end("blog-yaku-ichiran", "全38役は記事で"))

# ======================= リーチ（y-01）=======================
R13 = [("", ["m1", "m2", "m3"]), ("", ["m5", "m6"]), ("", ["p7", "p8", "p9"]), ("", ["s9", "s9", "s9"]), ("", ["z4", "z4"])]
def t_riichi():
    vis = hand(R13, 58, label="役がない…でも")
    return [(["リーチって、", "何がうれしいの？", "条件から、ぜんぶ説明します。"], hook("役シリーズ", "リーチを\n完璧に理解する", vis)),
            (["リーチは1翻の役。", "条件は3つ。", "鳴いていないこと、", "テンパイしていること、", "1,000点を出せること。"],
             scene("リーチの条件", (.3, 360, '<div class="vcard">' + "".join(f'<div class="yk" style="margin:14px 0">{tag(True, str(i + 1))}　{t}</div>' for i, t in enumerate(
                 ["鳴いていない（門前）", "あと1枚であがれる（テンパイ）", "1,000点棒を出せる", "山に4枚以上残っている"])) + "</div>"))),
            (["この手は、役がありません。", "このままだと、", "四萬や七萬が捨てられても、", "ロンではあがれないんです。"],  # 自分で引けば門前ツモの1翻であがれる（2026-11-11 ユーザー指摘）
             scene("役がない手", (.2, 360, hand(R13, 58)), (1.0, 700, note("待ちは <b>四萬・七萬</b><br>役がないので<b>ロンはできない</b><br><small>（自分で引けばメンゼンツモであがれる）</small>")))),
            (["そこでリーチ。", "宣言して、1,000点を場に出します。", "これだけで1翻がつくので、", "ロンでもあがれる手に変わります。"],
             scene("リーチをかける", (.2, 360, hand(R13, 58)), (.8, 640, '<div class="mid"><span class="ans">リーチ！</span></div>'),
                   (1.4, 860, '<div class="vcard mid">' + art("assets/art/tenbo.svg", 420) + '<div class="yk">1,000点を場に出す → <b style="color:#E75620">1翻</b></div></div>'))),
            (["リーチのあとは、", "手を変えられません。", "引いた牌があがり牌でなければ、", "そのまま捨てます。"],
             scene("リーチのあと", (.3, 360, '<div class="vcard">' + "".join(f'<div class="yk" style="margin:14px 0">{tag(ok, k)}　{t}</div>' for ok, k, t in [
                 (False, "×", "手の牌を入れかえる"), (True, "○", "引いた牌をそのまま捨てる"), (True, "○", "あがり牌ならツモ・ロン"), (True, "○", "待ちが変わらない暗槓")]) + "</div>"))),
            (["そのかわり、ごほうびが2つ。", "1巡以内にあがると一発で1翻。", "あがったあとに裏ドラをめくれます。"],
             scene("リーチのごほうび", (.3, 360, '<div class="vcard">' + vt3([("一発", "1巡以内にあがると＋1翻"), ("裏ドラ", "ドラの下の牌をめくる"), ("門前ツモ", "自分で引けば＋1翻")]) + "</div>"),
                   (1.4, 900, note("リーチ＋一発＋ツモ＋裏ドラ1枚で<br><b>4翻</b>まで伸びることも")))),
            (["気をつけたいのは、", "もう手を変えられないこと。", "相手のリーチが来ても、", "危ない牌を止められません。"],
             scene("リーチの弱点", (.3, 380, note("手を変えられないので<br>相手がリーチしても<b>危ない牌を止められない</b>")),
                   (1.0, 640, '<div class="vcard mid"><div class="yk">迷ったら</div><div class="big" style="font-size:80px;color:#177083">良い待ち・早い巡目</div><div class="yk">ならリーチ</div></div>'))),
            YAKU_END]
TOPICS["y-01"] = t_riichi

def vt3(rows):
    return '<table class="vt">' + "".join(f'<tr><td style="color:#E75620">{esc(l)}</td><td class="r">{esc(r)}</td></tr>' for l, r in rows) + "</table>"

# ======================= ピンフ（y-03）=======================
PIN = [("g", ["m2", "m3", "m4"]), ("g", ["p5", "p6", "p7"]), ("g", ["s3", "s4", "s5"]), ("o", ["m6", "m7"]), ("b", ["p9", "p9"])]
def t_pinfu():
    vis = hand(PIN, 60, label="これがピンフ")
    ng1 = [("g", ["m2", "m3", "m4"]), ("g", ["p5", "p6", "p7"]), ("r", ["s7", "s7", "s7"]), ("o", ["m6", "m7"]), ("b", ["p9", "p9"])]
    ng2 = [("g", ["m2", "m3", "m4"]), ("g", ["p5", "p6", "p7"]), ("g", ["s3", "s4", "s5"]), ("o", ["m6", "m7"]), ("r", ["z5", "z5"])]
    ng3 = [("g", ["m2", "m3", "m4"]), ("g", ["p5", "p6", "p7"]), ("g", ["s3", "s4", "s5"]), ("r", ["m6", "m8"]), ("b", ["p9", "p9"])]
    return [(["ピンフって、", "結局どんな手？", "4つの条件で説明します。"], hook("役シリーズ", "ピンフを\n完璧に理解する", vis)),
            (["ピンフは1翻。", "条件は4つです。"],
             scene("ピンフの4つの条件", (.3, 360, '<div class="vcard">' + "".join(f'<div class="yk" style="margin:14px 0">{tag(True, str(i + 1))}　{t}</div>' for i, t in enumerate(
                 ["鳴いていない（門前）", "面子が4つとも順子", "雀頭が役牌ではない", "待ちが両面"])) + "</div>"))),
            (["この手を見てみましょう。", "緑の3つは、", "123のような順番の組、順子。", "青が雀頭で、", "オレンジの2枚が待ちです。"],
             scene("ピンフの形", (.2, 360, hand(PIN, 60)), (1.0, 640, note('<span style="color:#177083">■</span> 順子　<span style="color:#4261AA">■</span> 雀頭　<span style="color:#E75620">■</span> 待ち<br>五萬か八萬で<b>あがれる両面待ち</b>')))),
            (["ダメな例、その1。", "同じ牌3つの刻子が入ると、", "ピンフになりません。"],
             scene("ダメな例① 刻子がある", (.2, 360, hand(ng1, 60)), (.8, 660, f'<div class="mid">{tag(False, "ピンフにならない")}</div>'))),
            (["その2。", "雀頭が白・發・中や、", "自分の風、場の風だとダメ。"],
             scene("ダメな例② 雀頭が役牌", (.2, 360, hand(ng2, 60)), (.8, 660, f'<div class="mid">{tag(False, "ピンフにならない")}</div>'))),
            (["その3。", "六萬と八萬で七萬を待つ、", "カンチャン待ちはダメ。", "待ちは両面だけです。"],
             scene("ダメな例③ 両面じゃない", (.2, 360, hand(ng3, 60)), (.8, 660, f'<div class="mid">{tag(False, "ピンフにならない")}</div>'),
                   (1.4, 820, note("カンチャン・ペンチャン・単騎・シャンポンは<b>ダメ</b>")))),
            (["ピンフは、", "リーチやタンヤオと重なりやすい役。", "ツモったときは、", "ツモの1翻もつきます。"],
             scene("ピンフのいいところ", (.3, 380, '<div class="vcard">' + vt3([("リーチ", "門前なので重なる"), ("タンヤオ", "二〜八だけなら重なる"), ("ツモ", "ツモでも符は20符")]) + "</div>"),
                   (1.4, 820, note("リーチ・ピンフ・タンヤオで<b>3翻</b>はよくある形")))),
            YAKU_END]
TOPICS["y-03"] = t_pinfu

# ======================= 役牌（y-05）=======================
SEATS = {"東": (235, 500), "南": (450, 265), "西": (235, 30), "北": (20, 265)}
def seat_fig(field="東", me=None, hl=()):
    out = ""
    for w, (x, y) in SEATS.items():
        st = "background:#E75620;color:#fff" if w == me else ("background:#FFE9E0" if w in hl else "")
        out += f'<div class="p" style="left:{x}px;top:{y}px;{st}">{w}家</div>'
    return f'<div class="seat">{out}<div class="c">{field}場<br><span style="font-size:30px">（場の風＝{field}）</span></div></div>'

def t_yakuhai():
    vis = '<div class="vcard mid">' + "".join(tile(t, 120) for t in ["z5", "z6", "z7", "z1", "z2"]) + '<p class="lbl" style="margin:20px 0 0">どれが役になる？</p></div>'
    sangen_m = [("", ["m2", "m3", "m4"]), ("", ["p6", "p7", "p8"]), ("", ["s4", "s5"]), ("o", ["z7", "z7", "z7"]), ("", ["m9", "m9"])]
    sangen_n = [("", ["m2", "m3", "m4"]), ("", ["p6", "p7", "p8"]), ("", ["s4", "s5"]), ("", ["m9", "m9"]), ("o", ["z6", "z6-yoko", "z6"])]
    return [(["役牌って、", "どの牌のことか全部言える？", "全部のパターンを説明します。"], hook("役シリーズ", "役牌を\n完璧に理解する", vis)),
            (["役牌は、", "同じ牌を3枚そろえると1翻。", "なる牌は3種類あります。", "三元牌、場の風、自分の風です。"],
             scene("役牌は3種類", (.3, 360, '<div class="vcard">' + vt3([("三元牌", "白・發・中はいつでも"), ("場風", "東場なら東・南場なら南"), ("自風", "自分の席の風")]) + "</div>"),
                   (1.4, 820, note("刻子（3枚）にすると<b>1つにつき1翻</b>")))),
            (["まず三元牌。", "白、發、中は、", "いつ、誰がそろえても1翻です。"],
             scene("三元牌はいつでも", (.3, 380, '<div class="mid">' + "".join(tile(t, 170) for t in ["z5", "z6", "z7"]) + "</div>"),
                   (1.0, 700, note("白・發・中のどれかを<b>3枚</b>で1翻")))),
            (["門前ならこう。", "中を3枚持ったまま、", "残りをそろえてあがれば、", "中で1翻です。"],
             scene("門前の例（中）", (.2, 360, hand(sangen_m, 60, win="s6", label="三索か六索であがり")), (1.0, 700, note("鳴かなくても<b>中で1翻</b>")))),
            (["役牌は、鳴いてもOK。", "發をポンして、", "早くあがるのが定番です。", "鳴いた牌は横に倒します。"],
             scene("鳴いた例（發をポン）", (.2, 360, hand(sangen_n, 60, label="横に倒した牌＝ポンした牌")), (1.0, 700, note("鳴いても<b>1翻</b>。早くあがりたい時に強い")))),
            (["次に場風。", "東場は東、南場は南が、", "全員にとって役牌です。"],
             scene("場風（ばかぜ）", (.3, 340, seat_fig("東", hl=("東", "南", "西", "北"))), (1.2, 1020, note("東場なら<b>東</b>が全員の役牌")))),
            (["そして自風。", "自分の席の風が役牌です。", "南家なら南、", "西家なら西、北家なら北。"],
             scene("自風（じかぜ）", (.3, 340, seat_fig("東", me="南")), (1.2, 1020, note("南家の人は<b>南</b>が役牌。<br>東場なら<b>東</b>も役牌")))),
            (["東場の東家は、", "東が場風と自風の両方。", "これがダブ東で、2翻です。", "南場の南家なら、ダブ南です。"],
             scene("ダブ東・ダブ南は2翻", (.3, 340, seat_fig("東", me="東")), (1.2, 1020, note("場風＋自風が重なると<b>2翻</b>")))),
            (["反対に、東場の南家にとって、", "西と北は役になりません。", "3枚そろえても0翻です。"],
             scene("役にならない風", (.3, 340, seat_fig("東", me="南", hl=())), (1.0, 1020, '<div class="mid">' + tile("z3", 110) + tile("z3", 110) + tile("z3", 110) + f' {tag(False, "0翻")}</div>'))),
            (["役牌は2つ重なることも。", "白と中を3枚ずつなら2翻。", "数えもれに気をつけましょう。"],
             scene("重なると翻が増える", (.3, 380, '<div class="vcard mid">' + "".join(tile(t, 84) for t in ["z5", "z5", "z5"]) + "　" + "".join(tile(t, 84) for t in ["z7", "z7", "z7"]) + '<div class="yk" style="margin-top:16px">白＋中で <b style="color:#E75620">2翻</b></div></div>'))),
            YAKU_END]
TOPICS["y-05"] = t_yakuhai

# ======================= 似ている役をくらべる =======================
def duo(nameA, hanA, handA, descA, nameB, hanB, handB, descB):
    def mk(a, b):
        A = f'<div class="mid"><span class="ans" style="background:#177083;font-size:54px">{nameA}　{hanA}</span></div>' + handA + f'<div class="yk mid" style="margin-top:8px">{descA}</div>'
        B = f'<div class="mid"><span class="ans" style="font-size:54px">{nameB}　{hanB}</span></div>' + handB + f'<div class="yk mid" style="margin-top:8px">{descB}</div>'
        return [stage(a + .2, b, A, top=180), stage(a + 1.2, b, B, top=760)]
    return mk

SAN = [("o", ["m1", "m2", "m3"]), ("o", ["p1", "p2", "p3"]), ("o", ["s1", "s2", "s3"]), ("", ["p6", "p7", "p8"]), ("", ["s9", "s9"])]
ITT = [("b", ["m1", "m2", "m3"]), ("b", ["m4", "m5", "m6"]), ("b", ["m7", "m8", "m9"]), ("", ["p2", "p3", "p4"]), ("", ["s5", "s5"])]
def t_san_itt():
    vis = '<div class="vcard mid"><div class="eqn"><span>三色</span><span class="o">vs</span><span>一通</span></div><p class="lbl" style="margin:20px 0 0">違い、説明できる？</p></div>'
    return [(["三色と一通、", "違いを説明できる？"], hook("似ている役", "三色と一通\nどう違う？", vis)),
            (["三色同順は、", "萬子・筒子・索子で、", "同じ数字の順子を3つ。", "この手なら、123が3色です。"],
             scene("三色同順（さんしょく）", (.2, 360, hand(SAN, 60)), (1.0, 640, note("<b>同じ数字</b>を<b>3つの色</b>で<br>萬子123・筒子123・索子123")))),
            (["一気通貫は、", "同じ色で、", "123、456、789。", "1から9までが1本につながります。"],
             scene("一気通貫（いっつう）", (.2, 360, hand(ITT, 60)), (1.0, 640, note("<b>同じ色</b>で<b>1〜9</b>がつながる<br>萬子123・456・789")))),
            (["並べるとこう。", "三色は横に3色、", "一通は縦に1色。", "どちらも2翻で、", "鳴くと1翻に下がります。"],
             duo("三色", "2翻", hand(SAN, 56), "同じ数字 × 3色", "一通", "2翻", hand(ITT, 56), "1色で 1〜9")),
            (["覚え方は、", "三色は同じ数字、", "一通は同じ色。", "どちらも鳴くと1翻です。"],
             scene("覚え方", (.3, 380, '<div class="vcard">' + vt3([("三色", "同じ数字・3つの色"), ("一通", "同じ色・1〜9"), ("鳴いたら", "どちらも1翻")]) + "</div>"))),
            YAKU_END]
TOPICS["y-07"] = t_san_itt

CHA = [("o", ["m1", "m2", "m3"]), ("o", ["p7", "p8", "p9"]), ("o", ["s1", "s2", "s3"]), ("r", ["z5", "z5", "z5"]), ("o", ["m9", "m9"])]
JUN = [("o", ["m1", "m2", "m3"]), ("o", ["p7", "p8", "p9"]), ("o", ["s1", "s2", "s3"]), ("o", ["s7", "s8", "s9"]), ("o", ["m9", "m9"])]
def t_chanta():
    vis = '<div class="vcard mid"><div class="eqn"><span>チャンタ</span><span class="o">vs</span><span>純チャン</span></div><p class="lbl" style="margin:20px 0 0">1つだけ違う</p></div>'
    return [(["チャンタと純チャン、", "違いは1つだけ。"], hook("似ている役", "チャンタと\n純チャン", vis)),
            (["チャンタは、", "すべての組と雀頭に、", "一か九か字牌が入る形。", "この手は、白の刻子もOKです。"],
             scene("チャンタ", (.2, 360, hand(CHA, 60)), (1.0, 640, note("どの組にも<b>一・九・字牌</b>が入る<br>2翻（鳴くと1翻）")))),
            (["純チャンは、", "字牌を使わずに、", "すべての組に一か九が入る形。"],
             scene("純チャン", (.2, 360, hand(JUN, 60)), (1.0, 640, note("<b>字牌なし</b>で、どの組にも一・九<br>3翻（鳴くと2翻）")))),
            (["並べるとこう。", "違いは、字牌が入るかどうか。", "字牌がないだけで、", "1翻アップします。"],
             duo("チャンタ", "2翻", hand(CHA, 56), "字牌が<b style='color:#C62828'>入る</b>", "純チャン", "3翻", hand(JUN, 56), "字牌が<b>入らない</b>")),
            (["二〜八だけで作るタンヤオの、", "ちょうど反対の役です。", "鳴くと1翻下がります。"],
             scene("覚え方", (.3, 380, '<div class="vcard">' + vt3([("チャンタ", "一・九・字牌（2翻）"), ("純チャン", "一・九だけ（3翻）"), ("反対の役", "タンヤオ（二〜八）")]) + "</div>"))),
            YAKU_END]
TOPICS["y-09"] = t_chanta

SA = [("o", ["m2", "m2", "m2"]), ("o", ["p5", "p5", "p5"]), ("o", ["s8", "s8", "s8"]), ("", ["z1", "z1"]), ("", ["m6", "m6"])]
def t_anko():
    vis = '<div class="vcard mid"><div class="eqn"><span>三暗刻</span><span class="o">vs</span><span>四暗刻</span></div><p class="lbl" style="margin:20px 0 0">あがり方で変わる</p></div>'
    return [(["同じ手なのに、", "あがり方で2翻にも、", "役満にもなる。"], hook("似ている役", "三暗刻と四暗刻\nの分かれ目", vis)),
            (["暗刻は、", "鳴かずにそろえた、", "同じ牌3枚の組のこと。", "3つあれば三暗刻で2翻です。"],
             scene("三暗刻は2翻", (.2, 360, hand(SA[:3] + [("", ["m4", "m5", "m6"]), ("", ["z1", "z1"])], 58)), (1.0, 640, note("鳴かずにそろえた刻子が<b>3つ</b>で2翻")))),
            (["4つそろえば四暗刻で役満。", "この手は、東と六萬の", "どちらかを待つシャンポン待ちです。"],
             scene("シャンポン待ち", (.2, 360, hand(SA, 58)), (1.0, 640, note("待ちは <b>東</b> か <b>六萬</b>")))),
            (["自分で引いてツモなら、", "4つとも暗刻になって、", "四暗刻、役満です。"],
             scene("ツモなら", (.2, 360, hand(SA, 58, win="m6")), (.9, 680, '<div class="mid"><span class="ans">四暗刻　役満</span></div>'))),
            (["でもロンだと、", "人の牌で作った組は", "暗刻にならないので、", "三暗刻とトイトイ。", "2翻と2翻です。"],
             scene("ロンなら", (.2, 360, hand(SA, 58, win="m6")), (.9, 680, '<div class="mid"><span class="ans" style="background:#177083">三暗刻＋トイトイ</span></div>'),
                   (1.6, 900, note("ロンでそろった組は<b>明刻</b>あつかい")))),
            (["ただし、単騎待ちなら、", "ロンでも四暗刻。", "雀頭であがるからです。"],
             scene("単騎待ちなら", (.2, 360, hand([("o", ["m2", "m2", "m2"]), ("o", ["p5", "p5", "p5"]), ("o", ["s8", "s8", "s8"]), ("o", ["z1", "z1", "z1"]), ("", ["z7"])], 58, win="z7")),
                   (.9, 680, note("暗刻が4つそろって、<b>中の1枚待ち</b><br>雀頭であがるので<b>ロンでも役満</b>")))),
            YAKU_END]
TOPICS["y-11"] = t_anko
