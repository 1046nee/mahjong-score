# -*- coding: utf-8 -*-
"""Mリーグ・プロ団体の作り直し（2026-11-10 ユーザーの指示）。チームカラーと文字で見せる（ロゴ・選手の写真は使わない＝案A）。
チームの色は Mリーグ公式サイト（m-league.jp）のチームのボタンの色（2026-11-10 に確かめた）。
歴代のMリーガーは Wikipedia「Mリーグ」と解説記事で確かめた（団体は在籍していた時の所属）。
"""
from video_topics import esc, head, stage, hook, art, vt, article_end, END
import video_topics3  # data-anim などの動きを先に足しておく
import video_topics2 as _v2

TOPICS = {}

TCOL = {"EARTH JETS": "#006934", "赤坂ドリブンズ": "#9CB832", "EX風林火山": "#1A1A1A", "KADOKAWAサクラナイツ": "#F895B5", "KONAMI麻雀格闘倶楽部": "#920101",
        "渋谷ABEMAS": "#C6AE6F", "セガサミーフェニックス": "#B74801", "TEAM RAIDEN / 雷電": "#DBB400", "BEAST X": "#002953", "U-NEXT Pirates": "#0582C8"}
SHORT = {"EARTH JETS": "EARTH JETS", "赤坂ドリブンズ": "ドリブンズ", "EX風林火山": "風林火山", "KADOKAWAサクラナイツ": "サクラナイツ", "KONAMI麻雀格闘倶楽部": "格闘倶楽部",
         "渋谷ABEMAS": "ABEMAS", "セガサミーフェニックス": "フェニックス", "TEAM RAIDEN / 雷電": "雷電", "BEAST X": "BEAST X", "U-NEXT Pirates": "Pirates"}
LIGHT = {"KADOKAWAサクラナイツ", "渋谷ABEMAS", "TEAM RAIDEN / 雷電", "赤坂ドリブンズ"}  # 地が明るいチームは字を濃く

def tchip(team, size=44, w=None):
    fg = "#1F2A28" if team in LIGHT else "#fff"
    return (f'<span style="display:inline-block;background:{TCOL[team]};color:{fg};font-size:{size}px;font-weight:900;border-radius:16px;padding:10px 24px;'
            f'{f"width:{w}px;text-align:center;box-sizing:border-box;" if w else ""}white-space:nowrap">{esc(SHORT[team])}</span>')

def badge(tx, col="#E75620"):
    return f'<span style="display:inline-block;background:{col};color:#fff;font-size:34px;font-weight:900;border-radius:999px;padding:8px 20px;white-space:nowrap">{tx}</span>'

def rows(items, a, step=.55, h=118):
    """items = [(左の字, 真ん中のHTML, 右の札)] を上から順に出す"""
    out = ""
    for i, (l, r, tag) in enumerate(items):
        out += (f'<div data-in="{a + .3 + i * step:.2f}" data-a="left" style="display:grid;grid-template-columns:190px 1fr auto;align-items:center;gap:18px;height:{h}px;border-top:3px solid #E3E9E7">'
                f'<span style="font-size:40px;font-weight:900;color:#5F6E6B">{l}</span><span>{r}</span><span>{tag}</span></div>')
    return f'<div class="tbl" style="padding:10px 34px">{out}</div>'

WIN = _v2.WIN
DWIN = dict(WIN)
MVP_T = [("2018-19", "多井隆晴", "渋谷ABEMAS"), ("2019-20", "魚谷侑未", "セガサミーフェニックス"), ("2020-21", "佐々木寿人", "KONAMI麻雀格闘倶楽部"),
         ("2021-22", "瑞原明奈", "U-NEXT Pirates"), ("2022-23", "伊達朱里紗", "KONAMI麻雀格闘倶楽部"), ("2023-24", "鈴木優", "U-NEXT Pirates"),
         ("2024-25", "醍醐大", "セガサミーフェニックス"), ("2025-26", "下石戟", "BEAST X")]
REG1 = {"2018-19": "EX風林火山", "2019-20": "セガサミーフェニックス", "2020-21": "渋谷ABEMAS", "2021-22": "U-NEXT Pirates", "2022-23": "KONAMI麻雀格闘倶楽部",
        "2023-24": "U-NEXT Pirates", "2024-25": "赤坂ドリブンズ", "2025-26": "EX風林火山"}

# ---------------- 歴代の優勝チーム ----------------
def t_mlwin():
    vis = '<div class="vcard mid" style="padding:40px">' + "".join(f'<div style="height:34px;margin:10px 0;border-radius:10px;background:{TCOL[t]}"></div>' for _, t in WIN) + '<p class="lbl" style="margin:24px 0 0">8シーズンの王者</p></div>'
    seen, items = {}, []
    for s, t in WIN:
        seen[t] = seen.get(t, 0) + 1
        items.append((s, tchip(t, 46), badge("2回目") if seen[t] == 2 else ""))
    def s1(a, b):
        return [head(a, b, "歴代の優勝チーム"), stage(a + .1, b, rows(items[:4], a, .9), top=360)]
    def s2(a, b):
        return [head(a, b, "歴代の優勝チーム"), stage(a + .1, b, rows(items, a - 2.0, .55), top=360)]
    def s3(a, b):
        return [head(a, b, "連覇はまだ一度もない"), stage(a + .1, b, rows([(s, tchip(t, 46), "") for s, t in WIN], a - 10, 0), top=360),
                stage(a + .8, b, '<div class="note">8シーズンで<b>6チーム</b>が優勝。<br>2年続けて勝ったチームはない</div>', top=1340)]
    def s4(a, b):
        it = [(s, tchip(REG1[s], 40), badge("そのまま優勝", "#177083") if REG1[s] == DWIN[s] else "") for s, _ in WIN]
        return [head(a, b, "レギュラー1位のチーム"), stage(a + .1, b, rows(it, a, .35), top=360),
                stage(a + 3.4, b, '<div class="note">1位で通過しても、優勝は<b>8回中2回</b>だけ</div>', top=1340)]
    return [(["Mリーグの歴代優勝チーム、", "全部言える？"], hook("Mリーグ", "歴代の優勝チーム\n言える？", vis)),
            (["初代王者は、赤坂ドリブンズ。", "次の年はパイレーツ、", "そのあと風林火山、", "サクラナイツと続きます。"], s1),
            (["2022-23はABEMAS。", "そこからパイレーツが2回目、", "フェニックス、", "そして風林火山が2回目の優勝。"], s2),
            (["8シーズンで、6チームが優勝。", "実は、連覇したチームは", "まだ1つもありません。"], s3),
            (["レギュラーシーズンを", "1位で通過したチームも、", "優勝できたのは8回中2回だけ。", "最後まで分からないのがMリーグです。"], s4),
            (END, article_end("blog-mleague-history", "順位の全部は記事で"))]
TOPICS["t-mlwin"] = t_mlwin

# ---------------- 歴代のMVP ----------------
def t_mlmvp():
    vis = '<div class="vcard mid"><div class="big" style="font-size:120px;color:#D4A017">MVP</div><p class="lbl" style="margin:10px 0 0">8シーズンの8人</p></div>'
    items = [(s, f'<span style="font-size:50px;font-weight:900;color:#1F2A28">{esc(n)}</span>', tchip(t, 32)) for s, n, t in MVP_T]
    def s1(a, b):
        return [head(a, b, "歴代のMVP"), stage(a + .1, b, rows(items[:4], a, .9), top=360)]
    def s2(a, b):
        return [head(a, b, "歴代のMVP"), stage(a + .1, b, rows(items, a - 2.0, .55), top=360)]
    def s3(a, b):
        it = [(s, f'<span style="font-size:48px;font-weight:900">{esc(n)}</span>', badge("優勝もした", "#177083") if DWIN[s] == t else "") for s, n, t in MVP_T]
        return [head(a, b, "MVPと優勝が重なった年"), stage(a + .1, b, rows(it, a, .3), top=360),
                stage(a + 3.0, b, '<div class="note">鈴木優はPirates、醍醐大はフェニックスで<br><b>MVPとチームの優勝を同時に</b></div>', top=1340)]
    def s4(a, b):
        rec = [("2023-24", "鈴木たろう", "112,800点"), ("2022-23", "黒沢咲", "112,700点"), ("2021-22", "伊達朱里紗", "105,500点"), ("2025-26", "内川幸太郎", "104,700点")]
        it = [(s, f'<span style="font-size:46px;font-weight:900">{esc(n)}</span>', f'<span style="font-size:46px;font-weight:900;color:#E75620">{v}</span>') for s, n, v in rec]
        return [head(a, b, "1試合の最高得点"), stage(a + .1, b, rows(it, a, .5), top=360),
                stage(a + 2.6, b, '<div class="note">25,000点から始めて<b>10万点超え</b>が4回</div>', top=900)]
    return [(["Mリーグの歴代MVP、", "誰か知ってる？"], hook("Mリーグ", "歴代のMVP\n知ってる？", vis)),
            (["最初のMVPは、ABEMASの多井隆晴。", "魚谷侑未、佐々木寿人、", "瑞原明奈と続きます。"], s1),
            (["伊達朱里紗、鈴木優、醍醐大、", "そして最新の2025-26は、", "BEAST Xの下石戟。"], s2),
            (["鈴木優と醍醐大は、", "MVPとチームの優勝を", "同じ年に手にしました。"], s3),
            (["おまけに、1試合の最高得点。", "鈴木たろうの112,800点が", "現在の記録です。"], s4),
            (END, article_end("blog-mleague-history", "記録の一覧は記事で"))]
TOPICS["t-mlmvp"] = t_mlmvp

# ---------------- 優勝回数・ファイナル進出回数 ----------------
def tbars(rs, a, total, unit="回", step=.25):
    out = ""
    for i, (t, v, note) in enumerate(rs):
        w = 100 * v / total
        out += (f'<div style="display:grid;grid-template-columns:270px 1fr 100px;align-items:center;gap:14px;height:100px">'
                f'{tchip(t, 32, 260)}<span style="display:block;height:58px;border-radius:12px;background:#E3E9E7;overflow:hidden;position:relative">'
                f'<i style="display:block;height:100%;background:{TCOL[t]};width:0%" data-w="{a + .4 + i * step:.2f},{a + 1.4 + i * step:.2f},0,{w:.1f}"></i>'
                f'<b style="position:absolute;right:14px;top:50%;transform:translateY(-50%);font-size:30px;color:#1F2A28">{esc(note)}</b></span>'
                f'<span style="font-size:46px;font-weight:900;text-align:right">{v}{unit}</span></div>')
    return f'<div class="tbl" style="padding:20px 30px">{out}</div>'

def t_mlcount():
    vis = '<div class="vcard mid"><div class="eqn"><span>優勝</span><span class="o">2回</span></div><p class="lbl" style="margin:20px 0 0">いちばん多いのは？</p></div>'
    cnt = [("U-NEXT Pirates", 2, ""), ("EX風林火山", 2, ""), ("赤坂ドリブンズ", 1, ""), ("KADOKAWAサクラナイツ", 1, ""), ("渋谷ABEMAS", 1, ""), ("セガサミーフェニックス", 1, ""),
           ("KONAMI麻雀格闘倶楽部", 0, "2位が2回"), ("TEAM RAIDEN / 雷電", 0, "3位が2回"), ("BEAST X", 0, "4位が1回"), ("EARTH JETS", 0, "2025-26から")]
    fin = [("渋谷ABEMAS", 5, "最初の5年連続"), ("EX風林火山", 5, ""), ("赤坂ドリブンズ", 4, ""), ("KADOKAWAサクラナイツ", 4, ""), ("KONAMI麻雀格闘倶楽部", 4, ""),
           ("U-NEXT Pirates", 3, ""), ("セガサミーフェニックス", 3, ""), ("TEAM RAIDEN / 雷電", 3, ""), ("BEAST X", 1, ""), ("EARTH JETS", 0, "")]
    def s1(a, b):
        return [head(a, b, "チーム別の優勝回数"), stage(a + .1, b, tbars(cnt, a, 2), top=330)]
    def s2(a, b):
        return [head(a, b, "ファイナルに出た回数"), stage(a + .1, b, tbars(fin, a, 5), top=330)]
    return [(["Mリーグで、", "いちばん優勝しているチームは？"], hook("Mリーグ", "いちばん優勝した\nチームは？", vis)),
            (["パイレーツと風林火山が、", "2回ずつで並んでいます。", "格闘倶楽部は2位が2回、", "雷電は3位が2回。", "あと一歩が続いています。"], s1),
            (["ファイナルに出た回数なら、", "ABEMASと風林火山が5回。", "ABEMASは最初の5年、", "連続でファイナルに出ました。"], s2),
            (END, article_end("blog-mleague-history", "くわしくは記事で"))]
TOPICS["t-mlcount"] = t_mlcount

# ---------------- Mリーガーの所属団体（今の40人・チームごと・歴代56人）----------------
DCOL = {"連盟": "#1F5FA8", "最高位戦": "#2E7D32", "協会": "#E07B00", "RMU": "#7B3FA0", "麻将連合": "#5F6E6B"}
DNAME = {"連盟": "日本プロ麻雀連盟", "最高位戦": "最高位戦", "協会": "日本プロ麻雀協会", "RMU": "RMU", "麻将連合": "麻将連合"}
FORMER = [("村上淳", "赤坂ドリブンズ", "最高位戦"), ("丸山奏子", "赤坂ドリブンズ", "最高位戦"), ("松ヶ瀬隆弥", "EX風林火山", "RMU"), ("二階堂瑠美", "EX風林火山", "連盟"),
          ("沢崎誠", "KADOKAWAサクラナイツ", "連盟"), ("渋川難波", "KADOKAWAサクラナイツ", "最高位戦"), ("前原雄大", "KONAMI麻雀格闘倶楽部", "連盟"), ("藤崎智", "KONAMI麻雀格闘倶楽部", "連盟"),
          ("和久津晶", "セガサミーフェニックス", "連盟"), ("近藤誠一", "セガサミーフェニックス", "最高位戦"), ("魚谷侑未", "セガサミーフェニックス", "連盟"), ("浅井堂岐", "セガサミーフェニックス", "協会"),
          ("猿川真寿", "BEAST X", "連盟"), ("菅原千瑛", "BEAST X", "連盟"), ("石橋伸洋", "U-NEXT Pirates", "最高位戦"), ("小林剛", "U-NEXT Pirates", "麻将連合")]

def dbars(rs, a, total):
    out = ""
    for i, (d, v) in enumerate(rs):
        w = 100 * v / total
        out += (f'<div style="display:grid;grid-template-columns:330px 1fr 110px;align-items:center;gap:14px;height:110px">'
                f'<span style="font-size:40px;font-weight:900;color:{DCOL[d]}">{DNAME[d]}</span>'
                f'<span style="display:block;height:64px;border-radius:12px;background:#E3E9E7;overflow:hidden"><i style="display:block;height:100%;background:{DCOL[d]};width:0%" data-w="{a + .4 + i * .25:.2f},{a + 1.5 + i * .25:.2f},0,{w:.1f}"></i></span>'
                f'<span style="font-size:48px;font-weight:900;text-align:right">{v}人</span></div>')
    return f'<div class="tbl" style="padding:20px 30px">{out}</div>'

def pchip(n, d, size=30):
    return f'<span style="display:inline-block;background:{DCOL[d]};color:#fff;font-size:{size}px;font-weight:900;border-radius:12px;padding:6px 12px;margin:3px;white-space:nowrap">{esc(n)}</span>'

LEGEND = "".join(f'<span style="display:inline-block;margin:6px 10px;font-size:32px;font-weight:900;color:{DCOL[d]}">■ {DNAME[d]}</span>' for d in DCOL)

def t_mldantai():
    vis = dbars([("連盟", 20), ("最高位戦", 14), ("協会", 5), ("RMU", 1)], -9, 20)
    def s1(a, b):
        return [head(a, b, "今の40人の所属"), stage(a + .1, b, dbars([("連盟", 20), ("最高位戦", 14), ("協会", 5), ("RMU", 1), ("麻将連合", 0)], a, 20), top=380)]
    def s2(a, b):
        out = ""
        for i, (t, ps) in enumerate(_v2.TEAMS):
            same = len({d for _, d in ps}) == 1
            out += (f'<div data-in="{a + .3 + i * .3:.2f}" data-a="left" style="display:grid;grid-template-columns:196px 1fr;align-items:center;gap:8px;min-height:94px;border-top:2px solid #E3E9E7'
                    f'{";background:#FFF3EC" if same else ""}">{tchip(t, 26, 190)}<span>{"".join(pchip(n, d, 28) for n, d in ps)}</span></div>')
        return [head(a, b, "チームごとの所属"), stage(a + .1, b, f'<div class="tbl" style="padding:10px 20px">{out}</div>', top=310),
                stage(a + .2, b, f'<div class="mid">{LEGEND}</div>', top=1300)]
    def s3(a, b):
        it = [("", tchip(t, 40), f'<span style="font-size:44px;font-weight:900;color:{DCOL[d]}">4人とも{DNAME[d]}</span>') for t, d in
              (("赤坂ドリブンズ", "最高位戦"), ("セガサミーフェニックス", "最高位戦"), ("KONAMI麻雀格闘倶楽部", "連盟"), ("TEAM RAIDEN / 雷電", "連盟"))]
        return [head(a, b, "全員が同じ団体のチーム"), stage(a + .1, b, rows(it, a, .5, 130).replace("grid-template-columns:190px", "grid-template-columns:0px"), top=420)]
    def s4(a, b):
        return [head(a, b, "歴代56人の所属"), stage(a + .1, b, dbars([("連盟", 28), ("最高位戦", 19), ("協会", 6), ("RMU", 2), ("麻将連合", 1)], a, 28), top=380),
                stage(a + 2.4, b, '<div class="note">今の40人 ＋ これまでの<b>16人</b></div>', top=1060)]
    def s5(a, b):
        out = "".join(f'<div data-in="{a + .2 + i * .12:.2f}" data-a="fade" style="display:flex;align-items:center;gap:10px;height:84px">{pchip(n, d, 32)}'
                      f'<span style="font-size:28px;font-weight:900;color:#5F6E6B;white-space:nowrap">{esc(SHORT[t])}</span></div>' for i, (n, t, d) in enumerate(FORMER))
        return [head(a, b, "これまでのMリーガー"), stage(a + .1, b, f'<div class="tbl" style="padding:20px 30px;display:grid;grid-template-columns:1fr 1fr;column-gap:20px">{out}</div>', top=310),
                stage(a + .2, b, f'<div class="mid">{LEGEND}</div>', top=1080)]
    return [(["Mリーガーは、", "どのプロ団体の選手？"], hook("Mリーグ", "Mリーガーの\n所属団体は？", vis)),
            (["2026-27シーズンの40人では、", "日本プロ麻雀連盟が20人で半分。", "最高位戦が14人、協会が5人、", "RMUが1人です。"], s1),
            (["チームごとに見ると、", "所属はこう分かれます。"], s2),
            (["ドリブンズとフェニックスは", "4人とも最高位戦。", "格闘倶楽部と雷電は", "4人とも連盟です。"], s3),
            (["これまでのMリーガーも入れた", "56人で数えると、", "連盟が28人、最高位戦が19人。", "麻将連合からも1人います。"], s4),
            (["小林剛は麻将連合、", "松ヶ瀬隆弥はRMU。", "団体は、在籍していた時の所属です。"], s5),
            (END, article_end("blog-pro-dantai-rules", "40人の一覧は記事で"))]
TOPICS["t-mldantai"] = t_mldantai

# ---------------- プロ団体のルールの違い（Mリーグを基準に）----------------
# 2026-11-10 に確かめた: Mリーグ公式（m-league.jp/about）・協会公式（npm2001.com/about/rule）・最高位戦公式（saikouisen.com/about/rules）。
# 連盟・RMU・麻将連合は公式サイトに会社の回線から入れず、解説記事と麻将連合の公式PDF（μカップ規定）で確かめた。確かめられなかった団体は表に出さない
def cmp(title, mval, rs, note=None):
    def mk(a, b):
        top = (f'<div class="tbl" style="border:6px solid #E75620;padding:24px 36px;display:flex;align-items:center;justify-content:space-between">'
               f'<span style="font-size:44px;font-weight:900;color:#E75620">Mリーグ</span><span style="font-size:54px;font-weight:900;color:#1F2A28">{mval}</span></div>')
        out = ""
        for i, (dn, v, same) in enumerate(rs):
            chip = (f'<span style="display:inline-block;font-size:38px;font-weight:900;border-radius:14px;padding:8px 20px;white-space:nowrap;'
                    f'{"background:#E4F3EC;color:#177083" if same else "background:#FDE8E0;color:#C62828"}">{v}</span>')
            out += (f'<div data-in="{a + 1.0 + i * .45:.2f}" data-a="left" style="display:flex;align-items:center;justify-content:space-between;height:104px;border-top:3px solid #E3E9E7">'
                    f'<span style="font-size:40px;font-weight:900;color:#1F2A28;white-space:nowrap">{dn}</span>{chip}</div>')
        els = [head(a, b, title), stage(a + .2, b, top, top=330, anim="pop"), stage(a + .6, b, f'<div class="tbl" style="padding:6px 36px">{out}</div>', top=520)]
        if note:
            els.append(stage(a + 1.4 + len(rs) * .45, b, f'<div class="note">{note}</div>', top=560 + len(rs) * 104 + 50))
        return els
    return mk

def t_dantairule():
    vis = art("assets/thumbs/blog-pro-dantai-rules.svg", 640, "border-radius:24px")
    def legend(a, b):
        return [head(a, b, "見方"), stage(a + .2, b, '<div class="note" style="text-align:left;line-height:2">'
                                                       '<span style="color:#E75620">■</span> いちばん上がMリーグのルール<br>'
                                                       '<span style="color:#177083">■</span> 緑はMリーグと同じ<br><span style="color:#C62828">■</span> 赤はMリーグと違う</div>', top=500)]
    other = lambda a, b: [head(a, b, "Mリーグのその他"), stage(a + .3, b, '<div class="vcard">' + vt([("途中流局", "なし", "h"), ("トビ", "なし（最後まで）", "h"),
                                                                                                ("責任払い（パオ）", "大三元・大四喜・四槓子", ""), ("流し満貫", "なし", "")]) + "</div>", top=420)]
    return [(["プロ団体によって、", "ルールはこんなに違う。", "Mリーグを基準にくらべます。"], hook("プロ団体", "団体でルールは\nどう違う？", vis)),
            (["上がMリーグのルール。", "緑は同じ、赤は違うところです。"], legend),
            (["まず、持ち点。", "Mリーグは25,000点持ちの", "30,000点返し。", "最高位戦やRMUは", "30,000点から始めます。"],
             cmp("持ち点／返し点", "25,000／30,000", [("日本プロ麻雀協会", "同じ", True), ("最高位戦", "30,000／30,000", False), ("RMU", "30,000／30,000", False),
                                                    ("麻将連合", "30,000／30,000", False), ("日本プロ麻雀連盟", "30,000（浮き沈み）", False)])),
            (["1位の順位点は、", "Mリーグと協会がプラス50。", "RMUはプラス15、", "麻将連合はプラス12と小さめです。"],
             cmp("順位点（1位）", "+50", [("日本プロ麻雀協会", "+50", True), ("最高位戦", "+30", False), ("RMU", "+15", False), ("麻将連合", "+12", False),
                                        ("日本プロ麻雀連盟", "浮き沈みで変わる", False)], "Mリーグは <b>+50／+10／−10／−30</b>")),
            (["赤ドラは、Mリーグの特徴。", "5の萬子・筒子・索子に1枚ずつ、", "合わせて3枚です。"],
             cmp("赤ドラ", "3枚", [("最高位戦", "なし", False), ("RMU", "なし", False), ("麻将連合", "なし", False), ("日本プロ麻雀連盟", "なし", False)], "ほかの団体のリーグ戦は<b>赤なし</b>が多い")),
            (["一発と裏ドラは、", "連盟の公式ルールと麻将連合だけ", "なしです。"],
             cmp("一発・裏ドラ・カンドラ", "あり", [("日本プロ麻雀協会", "あり", True), ("最高位戦", "あり", True), ("RMU", "あり", True),
                                                ("日本プロ麻雀連盟", "なし", False), ("麻将連合", "なし", False)])),
            (["喰いタンと後付けは、", "どの団体もありです。", "ここは迷わなくて大丈夫。"],
             cmp("喰いタン・後付け", "あり", [("日本プロ麻雀協会", "あり", True), ("最高位戦", "あり", True), ("RMU", "あり", True),
                                          ("日本プロ麻雀連盟", "あり", True), ("麻将連合", "あり", True)], "ここは<b>どこも同じ</b>")),
            (["ダブル役満は、", "字一色と大三元のように、", "違う役満が重なったときだけ。", "四暗刻単騎や国士の13面待ち、", "純正九蓮宝燈は、", "ふつうの役満です。"],
             cmp("ダブル役満", "役満の重なりだけ", [("日本プロ麻雀協会", "重なりは認める", True), ("最高位戦", "重なりは認める", True), ("日本プロ麻雀連盟", "重なりは認める", True),
                                               ("麻将連合", "ダブルなし", False)], "四暗刻単騎・国士13面・純正九蓮は<br><b>ダブルにしない</b>（Mリーグ）")),
            (["ダブ東などの連風牌は、", "刻子なら2翻。", "雀頭にしたときは2符です。", "4符にするルールもあるので、", "打つ前に確かめましょう。"],
             cmp("連風牌の雀頭", "2符", [("日本プロ麻雀協会", "2符", True), ("日本プロ麻雀連盟", "2符", True)], "4符にする遊び方もある。<b>打つ前に決める</b>")),
            (["2人が同時にロンしたら、", "Mリーグは頭ハネ。", "放銃した人の下家から順に、", "1人だけがあがれます。"],
             cmp("ダブロン・トリロン", "なし（頭ハネ）", [("日本プロ麻雀協会", "頭ハネ", True), ("RMU", "頭ハネ", True), ("麻将連合", "頭ハネ", True)], "プロのルールは<b>ほぼ頭ハネ</b>")),
            (["30符4翻の7,700点は、", "Mリーグでは満貫に切り上げ。", "連盟と麻将連合は", "切り上げません。"],
             cmp("切り上げ満貫", "あり", [("日本プロ麻雀協会", "あり", True), ("RMU", "あり", True), ("日本プロ麻雀連盟", "なし（7,700）", False), ("麻将連合", "なし（7,700）", False)])),
            (["ほかにも、Mリーグは", "途中流局がなく、", "持ち点がマイナスになっても", "最後まで続けます。"], other),
            (END, article_end("blog-pro-dantai-rules", "比較表は記事で"))]
TOPICS["t-dantairule"] = t_dantairule
