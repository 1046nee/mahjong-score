# -*- coding: utf-8 -*-
"""記事をもとにした動画の続き（2026-11-09〜）: NAGAの使い方・Mリーグの歴代・Mリーガーの所属・プロ団体・麻雀AIの比較。
数字と名前は各記事の表から写した（記事の時点の情報。シーズンが変わったら記事と一緒に直す）。
チームのロゴ・選手の写真・NAGAの公式の絵は使わない（文字・サイトの絵・自作の図だけ）。
"""
from video_topics import at, esc, head, stage, hook, art, vt, trow, article_end, END, ms

TOPICS = {}

def card(rows):
    return '<div class="vcard">' + vt([tuple(r) + ("",) * (3 - len(r)) for r in rows]) + "</div>"  # (左, 右) だけの行も受ける

def bars(rows, a, total, unit="人"):
    """rows = [(名前, 数)]。数に合わせて棒が伸びる"""
    out = ""
    for i, (n, v) in enumerate(rows):
        w = 100 * v / total
        out += (f'<div style="display:grid;grid-template-columns:330px 1fr 90px;align-items:center;gap:14px;margin:22px 0;font-size:40px;font-weight:900;color:#1F2A28">'
                f'<span>{esc(n)}</span><span style="display:block;height:64px;border-radius:12px;background:#E3E9E7;overflow:hidden">'
                f'<i style="display:block;height:100%;background:{"#E75620" if i == 0 else "#177083"};width:0%" data-w="{a + .5 + i * .2},{a + 1.5 + i * .2},0,{w:.1f}"></i></span>'
                f'<span style="text-align:right">{v}{unit}</span></div>')
    return f'<div class="vcard vbar-like" style="padding:30px 36px"><div class="vbar" style="display:none"></div>{out}</div>'

# ---------------- NAGAの使い方 ----------------
def t_naga():
    vis = art("assets/thumbs/blog-ai-haifu.svg", 640, "border-radius:24px")
    def s1(a, b):
        return [head(a, b, "打った場所で変わる"), stage(a + .3, b, card([("天鳳", "URLを貼る", ""), ("雀魂", "拡張機能で変換", "h"), ("対面の麻雀", "局面を作る", "")]), top=440)]
    def s2(a, b):
        return [head(a, b, "使うのはポイント"), stage(a + .3, b, card([("天鳳の東南戦", "50NP", ""), ("天鳳の東風戦", "30NP", ""), ("カスタム牌譜", "1局10NPから", "h")]), top=440)]
    def s3(a, b):
        return [head(a, b, "MAKAとくらべると"), stage(a + .3, b, card([("料金", "MAKAは無料", ""), ("NAGA", "月550円から", "h"), ("三麻", "MAKAだけ", "")]), top=440)]
    return [(["麻雀AIのNAGA、", "使い方わかる？"], hook("麻雀AI", "NAGAの使い方、\n3ステップ", vis)),
            (["天鳳なら、牌譜のURLを貼るだけ。", "雀魂は、拡張機能で変換します。"], s1),
            (["解析にはポイントを使います。", "天鳳の東南戦で50NPです。"], s2),
            (["雀魂のMAKAは無料。", "NAGAは月550円から。", "三麻はMAKAだけです。"], s3),
            (END, article_end("blog-naga-guide", "画面つきの手順は記事で"))]
TOPICS["t-naga"] = t_naga

# ---------------- Mリーグの歴代 ----------------
WIN = [("2018-19", "赤坂ドリブンズ"), ("2019-20", "U-NEXT Pirates"), ("2020-21", "EX風林火山"), ("2021-22", "KADOKAWAサクラナイツ"),
       ("2022-23", "渋谷ABEMAS"), ("2023-24", "U-NEXT Pirates"), ("2024-25", "セガサミーフェニックス"), ("2025-26", "EX風林火山")]
MVP = [("2018-19", "多井隆晴"), ("2019-20", "魚谷侑未"), ("2020-21", "佐々木寿人"), ("2021-22", "瑞原明奈"),
       ("2022-23", "伊達朱里紗"), ("2023-24", "鈴木優"), ("2024-25", "醍醐大"), ("2025-26", "下石戟")]

def t_mlwin():
    vis = art("assets/thumbs/blog-mleague-history.svg", 640, "border-radius:24px")
    def part(rows, t):
        return lambda a, b: [head(a, b, t), stage(a + .3, b, card(rows), top=420)]
    return [(["Mリーグの歴代優勝チーム、", "全部言える？"], hook("Mリーグ", "歴代の優勝チーム\n言える？", vis)),
            (["2018年の最初の優勝は、", "赤坂ドリブンズ。"], part(WIN[:4], "前半の4シーズン")),
            (["後半は、", "パイレーツと風林火山が", "2回目の優勝。"], part(WIN[4:], "後半の4シーズン")),
            (END, article_end("blog-mleague-history", "各シーズンの順位は記事で"))]
TOPICS["t-mlwin"] = t_mlwin

def t_mlmvp():
    vis = art("assets/thumbs/blog-mleague-2026.svg", 640, "border-radius:24px")
    def part(rows, t):
        return lambda a, b: [head(a, b, t), stage(a + .3, b, card(rows), top=420)]
    return [(["Mリーグの歴代MVP、", "誰か知ってる？"], hook("Mリーグ", "歴代のMVP\n知ってる？", vis)),
            (["最初のMVPは、多井隆晴。"], part(MVP[:4], "前半の4シーズン")),
            (["最新の2025-26は、", "下石戟が選ばれました。"], part(MVP[4:], "後半の4シーズン")),
            (END, article_end("blog-mleague-history", "記録の一覧は記事で"))]
TOPICS["t-mlmvp"] = t_mlmvp

def t_mlcount():
    vis = art("assets/thumbs/blog-mleague-history.svg", 640, "border-radius:24px")
    rows = [("U-NEXT Pirates", 2), ("EX風林火山", 2), ("赤坂ドリブンズ", 1), ("サクラナイツ", 1), ("渋谷ABEMAS", 1), ("フェニックス", 1)]
    def s1(a, b):
        return [head(a, b, "チーム別の優勝回数"), stage(a + .2, b, bars(rows, a, 2, "回"), top=400)]
    def s2(a, b):
        return [head(a, b, "まだ優勝がないチーム"), stage(a + .3, b, card([("麻雀格闘倶楽部", "2位が2回", ""), ("TEAM RAIDEN / 雷電", "3位が2回", ""), ("BEAST X", "2025-26に4位", ""), ("EARTH JETS", "2025-26から", "")]), top=420)]
    return [(["Mリーグで、", "いちばん優勝しているチームは？"], hook("Mリーグ", "いちばん優勝した\nチームは？", vis)),
            (["パイレーツと風林火山が、", "2回ずつで並んでいます。"], s1),
            (["4チームは、", "まだ優勝がありません。"], s2),
            (END, article_end("blog-mleague-history", "くわしくは記事で"))]
TOPICS["t-mlcount"] = t_mlcount

# ---------------- Mリーガーの所属（団体）----------------
TEAMS = [("EARTH JETS", [("石井一馬", "最高位戦"), ("三浦智博", "連盟"), ("逢川恵夢", "協会"), ("HIRO柴田", "連盟")]),
         ("赤坂ドリブンズ", [("園田賢", "最高位戦"), ("鈴木たろう", "最高位戦"), ("浅見真紀", "最高位戦"), ("渡辺太", "最高位戦")]),
         ("EX風林火山", [("二階堂亜樹", "連盟"), ("勝又健志", "連盟"), ("永井孝典", "最高位戦"), ("内川幸太郎", "連盟")]),
         ("KADOKAWAサクラナイツ", [("岡田紗佳", "連盟"), ("堀慎吾", "連盟"), ("阿久津翔太", "連盟"), ("尻無濱航", "協会")]),
         ("KONAMI麻雀格闘倶楽部", [("佐々木寿人", "連盟"), ("高宮まり", "連盟"), ("伊達朱里紗", "連盟"), ("滝沢和典", "連盟")]),
         ("渋谷ABEMAS", [("多井隆晴", "RMU"), ("白鳥翔", "連盟"), ("松本吉弘", "協会"), ("日向藍子", "最高位戦")]),
         ("セガサミーフェニックス", [("茅森早香", "最高位戦"), ("醍醐大", "最高位戦"), ("竹内元太", "最高位戦"), ("佐野ひなこ", "最高位戦")]),
         ("TEAM RAIDEN / 雷電", [("萩原聖人", "連盟"), ("瀬戸熊直樹", "連盟"), ("黒沢咲", "連盟"), ("本田朋広", "連盟")]),
         ("BEAST X", [("鈴木大介", "連盟"), ("中田花奈", "連盟"), ("下石戟", "協会"), ("東城りお", "連盟")]),
         ("U-NEXT Pirates", [("瑞原明奈", "最高位戦"), ("鈴木優", "最高位戦"), ("仲林圭", "協会"), ("朝倉康心", "最高位戦")])]

def t_mldantai():
    vis = art("assets/thumbs/blog-pro-dantai-rules.svg", 640, "border-radius:24px")
    rows = [("日本プロ麻雀連盟", 20), ("最高位戦", 14), ("日本プロ麻雀協会", 5), ("RMU", 1), ("麻将連合", 0)]
    def s1(a, b):
        return [head(a, b, "40人の所属団体"), stage(a + .2, b, bars(rows, a, 20), top=400)]
    return [(["Mリーガー40人は、", "どのプロ団体の選手？"], hook("Mリーグ", "Mリーガー40人の\n所属団体は？", vis)),
            (["いちばん多いのは連盟で20人。", "最高位戦が14人です。", "2026-27シーズンの数です。"], s1),
            (END, article_end("blog-pro-dantai-rules", "40人の一覧は記事で"))]
TOPICS["t-mldantai"] = t_mldantai

def _team_video(i, team, players):
    vis = f'<div class="mid"><p class="lbl" style="font-size:{60 if len(team) <= 12 else 46}px;color:#1F2A28;margin-bottom:24px">{esc(team)}</p></div>' + art("assets/thumbs/blog-mleague-2026.svg", 520, "border-radius:24px")
    def s1(a, b):
        return [at(a, b, f'<h1 style="font-size:{84 if len(team) <= 10 else 60}px;word-break:keep-all">{esc(team)}</h1>', cls="cap", style="top:170px"), stage(a + .3, b, card([(n, d, "h" if d != "連盟" else "") for n, d in players]), top=420),
                stage(a + .5, b, '<div class="mid"><p class="lbl" style="font-size:36px">右は所属するプロ団体</p></div>', top=1180)]
    n = [p for p, _ in players]
    return [(["このチームの4人、", "言える？"], hook(f"Mリーグ 2026-27 {i}/10", "このチームの\n4人は？", vis)),
            (["答えは、", f"{n[0]}、{n[1]}、", f"{n[2]}、{n[3]}。"], s1),
            (["全10チーム40人は、", "まじゃすこの記事で。"], article_end("blog-mleague-2026", "全10チームは記事で"))]

# 「このチームの4人、言える？」（ml-01〜10）は2026-11-10 ユーザーの判断でやめた

# ---------------- プロ団体 ----------------
def t_dantai():
    vis = art("assets/thumbs/blog-dantai-rekishi.svg", 640, "border-radius:24px")
    def s1(a, b):
        return [head(a, b, "できた順に"), stage(a + .3, b, card([("1976 最高位戦", "最高位", ""), ("1981 日本プロ麻雀連盟", "鳳凰位", ""), ("1997 麻将連合", "将王", ""), ("2001 日本プロ麻雀協会", "雀王", ""), ("2007 RMU", "令昭位", "")]), top=420),
                stage(a + .6, b, '<div class="mid"><p class="lbl" style="font-size:36px">右はいちばん上のタイトル</p></div>', top=1260)]
    return [(["麻雀のプロ団体、", "いくつあるか知ってる？"], hook("プロ団体", "麻雀のプロ団体は\nいくつある？", vis)),
            (["主な団体は5つ。", "いちばん古いのは最高位戦で、", "1976年です。"], s1),
            (END, article_end("blog-dantai-rekishi", "団体の歴史は記事で"))]
TOPICS["t-dantai"] = t_dantai

def t_dantairule():
    vis = art("assets/thumbs/blog-pro-dantai-rules.svg", 640, "border-radius:24px")
    def s1(a, b):
        return [head(a, b, "一発と裏ドラ"), stage(a + .3, b, card([("Mリーグ", "あり", ""), ("最高位戦・協会・RMU", "あり", ""), ("日本プロ麻雀連盟（公式）", "なし", "n"), ("麻将連合", "なし", "n")]), top=420)]
    def s2(a, b):
        return [head(a, b, "順位点（1位）"), stage(a + .3, b, card([("Mリーグ・協会", "+50", ""), ("最高位戦", "+30", ""), ("RMU", "+15", ""), ("麻将連合", "+12", ""), ("連盟", "浮き沈みで変わる", "h")]), top=420)]
    return [(["プロ団体によって、", "ルールはこんなに違う。"], hook("プロ団体", "団体でルールは\nどう違う？", vis)),
            (["連盟の公式ルールと麻将連合は、", "一発も裏ドラもなし。"], s1),
            (["1位の順位点も、", "団体でこれだけ違います。"], s2),
            (END, article_end("blog-pro-dantai-rules", "比較表は記事で"))]
TOPICS["t-dantairule"] = t_dantairule

# ---------------- 麻雀AIの比較 ----------------
def t_ai():
    vis = art("assets/thumbs/blog-mahjong-ai.svg", 640, "border-radius:24px")
    def s1(a, b):
        return [head(a, b, "使えるAIは3つ"), stage(a + .3, b, card([("NAGA", "有料", ""), ("Mortal", "無料", ""), ("MAKA", "雀魂の中で", ""), ("Suphx", "使えない", "n"), ("LuckyJ", "使えない", "n")]), top=420)]
    def s2(a, b):
        return [head(a, b, "遊ぶ場所で選ぶ"), stage(a + .3, b, card([("雀魂", "MAKA → Mortal", ""), ("天鳳", "Mortal → NAGA", ""), ("対面の麻雀", "牌譜が残らない", "h")]), top=420)]
    return [(["麻雀AI、", "結局どれを使えばいい？"], hook("麻雀AI", "麻雀AI、\nどれを使う？", vis)),
            (["有名な5つのうち、", "自分の牌譜を見てもらえるのは3つ。"], s1),
            (["雀魂ならMAKAから、", "天鳳ならMortalから。"], s2),
            (END, article_end("blog-mahjong-ai", "AIの違いは記事で"))]
TOPICS["t-ai"] = t_ai
