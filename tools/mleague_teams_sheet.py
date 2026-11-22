# -*- coding: utf-8 -*-
"""Mリーグ 2026-27 の全10チームと選手の1枚（SNSの投稿用。2026-11-22 ユーザーの依頼）。
チームごとにロゴ・紹介（オーナー企業・参入・優勝回数）・4人の選手。選手の所属団体は、文字と色でひと目で分かるように札にする。
団体の色は記事 blog-mleague-2026 の「選手の所属団体」と同じ（連盟＝緑・最高位戦＝青・協会＝オレンジ・RMU＝紫）。
チームと選手・団体は tools/video_topics2.py の TEAMS（Mリーグ公式サイト・2026年10月に確認）。参入と優勝は blog-mleague-history と同じ。
ロゴはユーザーから受け取った画像（2026-11-22 ユーザーの判断で使う）。元の画像は非公開の素材リポジトリ まじゃすこ素材/x/mleague-teams/src/ だけに置く。
ロゴが無いチームは、チーム名の頭文字の丸で代わりにする（受け取ったら src/ に置けば出る）。
出力: まじゃすこ素材/x/mleague-teams/mleague-teams.png（1588×3120。過去の所属選手を足して縦に伸ばした）
実行: python3.13 tools/mleague_teams_sheet.py
"""
import base64, io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheet_logo import LOGO_CSS, logo_html  # noqa: E402
from video_topics2 import TEAMS  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "まじゃすこ素材", "x", "mleague-teams"); SRC = os.path.join(OUT, "src")
DANTAI = {"連盟": ("#177083", "日本プロ麻雀連盟"), "最高位戦": ("#4261AA", "最高位戦日本プロ麻雀協会"), "協会": ("#E25A1C", "日本プロ麻雀協会"), "RMU": ("#6B46C1", ""), "麻将連合": ("#B7791F", "")}
# チーム名 → (ロゴのファイル, オーナー企業, 参入シーズン, 優勝したシーズン)
INFO = {
    "EARTH JETS": ("earthjets", "アース製薬", "2025-26", []),
    "赤坂ドリブンズ": ("drivens", "博報堂", "2018-19", ["2018-19"]),
    "EX風林火山": ("furinkazan", "テレビ朝日", "2018-19", ["2020-21", "2025-26"]),
    "KADOKAWAサクラナイツ": ("sakura", "KADOKAWA", "2019-20", ["2021-22"]),
    "KONAMI麻雀格闘倶楽部": ("konami", "コナミグループ", "2018-19", []),
    "渋谷ABEMAS": ("abemas", "サイバーエージェント", "2018-19", ["2022-23"]),
    "セガサミーフェニックス": ("phoenix", "セガサミーグループ", "2018-19", ["2024-25"]),
    "TEAM RAIDEN / 雷電": ("raiden", "電通", "2018-19", []),
    "BEAST X": ("beastx", "ジャパネット", "2023-24", []),
    "U-NEXT Pirates": ("pirates", "U-NEXT", "2018-19", ["2019-20", "2023-24"]),
}


# 過去の所属選手（2026-11-22 ユーザーの指定）: チーム名 → [(名前, 団体, 始めの年, 終わりの年, 移った先の今のチーム or "")]
# 年は「始めのシーズンの始まりの年〜最後のシーズンの終わりの年」（2018-19〜2020-21 → 2018〜2021）。
# 出典: Wikipedia「Mリーグ」の「2026年以前にMリーグ所属歴のある選手」と各チームの記事（レギュラーシーズンの選手・得点の表。2026-11-22 に確認）
PAST = {
    "赤坂ドリブンズ": [("村上淳", "最高位戦", 2018, 2023, ""), ("丸山奏子", "最高位戦", 2019, 2023, "")],
    "EX風林火山": [("滝沢和典", "連盟", 2018, 2021, "KONAMI"), ("松ヶ瀬隆弥", "RMU", 2021, 2025, ""), ("二階堂瑠美", "連盟", 2021, 2025, "")],
    "KADOKAWAサクラナイツ": [("沢崎誠", "連盟", 2019, 2022, ""), ("内川幸太郎", "連盟", 2019, 2025, "風林火山"), ("渋川難波", "最高位戦", 2022, 2026, "")],
    "KONAMI麻雀格闘倶楽部": [("前原雄大", "連盟", 2018, 2021, ""), ("藤崎智", "連盟", 2019, 2021, "")],
    "セガサミーフェニックス": [("魚谷侑未", "連盟", 2018, 2024, ""), ("近藤誠一", "最高位戦", 2018, 2023, ""), ("和久津晶", "連盟", 2019, 2021, ""), ("東城りお", "連盟", 2021, 2024, "BEAST X"), ("浅井堂岐", "協会", 2024, 2026, "")],
    "BEAST X": [("猿川真寿", "連盟", 2023, 2025, ""), ("菅原千瑛", "連盟", 2023, 2025, "")],
    "U-NEXT Pirates": [("小林剛", "麻将連合", 2018, 2026, ""), ("石橋伸洋", "最高位戦", 2018, 2022, ""), ("朝倉康心", "最高位戦", 2018, 2022, "復帰")],
}
# チームカラー（ロゴの色から。2026-11-22 ユーザーの指定でカードを色分け）: (主の色, 2つ目の色)
TCOL = {"EARTH JETS": ("#1E7A3C", "#D7262E"), "赤坂ドリブンズ": ("#B5123B", "#C9D920"), "EX風林火山": ("#D7262E", "#1F1F1F"),
        "KADOKAWAサクラナイツ": ("#E58FAA", "#1F1F1F"), "KONAMI麻雀格闘倶楽部": ("#E50012", "#FFFFFF"), "渋谷ABEMAS": ("#B49A5E", "#1F1F1F"),
        "セガサミーフェニックス": ("#E8541E", "#F2A81D"), "TEAM RAIDEN / 雷電": ("#F5C400", "#1F1F1F"), "BEAST X": ("#13294B", "#C5A54E"),
        "U-NEXT Pirates": ("#1E8FD0", "#1F1F1F")}
# カードの地のグラデーションの色（無ければ主の色）。EARTH JETS・ドリブンズ・BEAST X は緑っぽく（2026-11-22 ユーザーの指定）
TGRAD = {"EARTH JETS": "#2FA05A", "赤坂ドリブンズ": "#7FB82E", "BEAST X": "#2E8B57"}
# 女性の選手（今と過去。ほかは男性）。名前の前に ♀・♂ を付ける（2026-11-22 ユーザーの指定）
FEMALE = {"逢川恵夢", "浅見真紀", "二階堂亜樹", "岡田紗佳", "高宮まり", "伊達朱里紗", "日向藍子", "茅森早香", "佐野ひなこ", "黒沢咲", "中田花奈", "東城りお", "瑞原明奈",
          "丸山奏子", "二階堂瑠美", "魚谷侑未", "和久津晶", "菅原千瑛"}
def sx(n): return '<u class="sx f">♀</u>' if n in FEMALE else '<u class="sx m">♂</u>'
# 生年月日（Wikipedia の各選手の記事。2026-11-22 に確認）。年齢は AGE_AT の日の年齢。黒沢咲は非公開なので出さない（2026-11-22 ユーザーの指定）
BIRTH = {"石井一馬": "1986-02-21", "三浦智博": "1987-04-26", "逢川恵夢": "1987-08-28", "HIRO柴田": "1976-02-16", "園田賢": "1980-11-25", "鈴木たろう": "1973-10-04",
         "浅見真紀": "1985-08-30", "渡辺太": "1988-07-25", "二階堂亜樹": "1981-11-15", "勝又健志": "1981-03-15", "永井孝典": "1986-08-10", "内川幸太郎": "1981-05-06",
         "岡田紗佳": "1994-02-19", "堀慎吾": "1984-03-23", "阿久津翔太": "1996-04-23", "尻無濱航": "1992-01-26", "佐々木寿人": "1977-01-12", "高宮まり": "1988-11-08",
         "伊達朱里紗": "1991-05-10", "滝沢和典": "1979-12-06", "多井隆晴": "1972-03-17", "白鳥翔": "1986-08-27", "松本吉弘": "1992-05-03", "日向藍子": "1988-09-24",
         "茅森早香": "1982-05-04", "醍醐大": "1976-04-21", "竹内元太": "1986-03-12", "佐野ひなこ": "1994-10-13", "萩原聖人": "1971-08-21", "瀬戸熊直樹": "1970-08-27",
         "本田朋広": "1983-10-03", "鈴木大介": "1974-07-11", "中田花奈": "1994-08-06", "下石戟": "1987-03-20", "東城りお": "1990-09-18", "瑞原明奈": "1986-11-19",
         "鈴木優": "1981-09-13", "仲林圭": "1985-09-17", "朝倉康心": "1986-03-04"}
AGE_AT = os.environ.get("AGE_AT", "2026-11-22")
def age(n):
    if n not in BIRTH: return ""
    y, m, d = map(int, BIRTH[n].split("-")); ty, tm, td = map(int, AGE_AT.split("-"))
    return f'<em class="ag">{ty - y - ((tm, td) < (m, d))}</em>'
# 団体の代表と最高タイトル・今の保持者（2026-11-22 ユーザーの指定。Wikipedia の各団体の記事と、各団体の公式サイトのタイトルの歴代表で確認）
HEAD = {"連盟": ("会長", "森山茂和"), "最高位戦": ("代表", "新津潔"), "協会": ("代表理事", "鍛冶田良一"), "RMU": ("代表", "多井隆晴"), "麻将連合": ("代表", "忍田幸夫")}
TITLE = {"連盟": ("鳳凰位", "白鳥翔", "第42期"), "最高位戦": ("最高位", "牧野伸彦", "第50期"), "協会": ("雀王", "西村雄一郎", "第24期"), "RMU": ("令昭位", "小川光", "第17期"), "麻将連合": ("将王", "石原真人", "第23期")}
# 最高タイトルを取ったことがある選手（今と過去のMリーガー）→ (タイトル, 回数)。歴代の保持者の表から
WON = {"前原雄大": ("鳳凰位", 4), "瀬戸熊直樹": ("鳳凰位", 3), "藤崎智": ("鳳凰位", 2), "勝又健志": ("鳳凰位", 1), "佐々木寿人": ("鳳凰位", 3), "HIRO柴田": ("鳳凰位", 1),
       "白鳥翔": ("鳳凰位", 2), "村上淳": ("最高位", 3), "石橋伸洋": ("最高位", 1), "近藤誠一": ("最高位", 4), "醍醐大": ("最高位", 1), "鈴木優": ("最高位", 1),
       "竹内元太": ("最高位", 2), "石井一馬": ("最高位", 1), "鈴木たろう": ("雀王", 4), "堀慎吾": ("雀王", 1), "渋川難波": ("雀王", 1), "浅井堂岐": ("雀王", 1),
       "仲林圭": ("雀王", 2), "多井隆晴": ("令昭位", 1), "小林剛": ("将王", 4)}
NOW = {v[1] for v in TITLE.values()}
TROPHY = '<svg viewBox="0 0 24 24"><path d="M7 3h10v5.5a5 5 0 0 1-10 0z" fill="#D4A017"/><path d="M7 4.5H4.3a2.7 2.7 0 0 0 2.9 4.3M17 4.5h2.7a2.7 2.7 0 0 1-2.9 4.3" stroke="#D4A017" stroke-width="1.8" fill="none"/><rect x="10.8" y="13" width="2.4" height="4" fill="#D4A017"/><rect x="7.6" y="17" width="8.8" height="3.2" rx="1" fill="#B8860B"/></svg>'
def trophy(n):
    if n not in WON: return ""
    t, k = WON[n]
    return f'<u class="tr{" now" * (n in NOW)}">{TROPHY}{"現" if n in NOW else ""}{t}×{k}</u>'
NOPAST = {"渋谷ABEMAS": "2018年から入れ替わりなし", "TEAM RAIDEN / 雷電": "2018年から入れ替わりなし", "EARTH JETS": "2025年の参入から同じ4人"}


def past_html(team):
    if team in NOPAST: return f'<div class="past"><b>過去</b><span class="none">{NOPAST[team]}</span></div>'
    xs = "".join(f'<span class="pp" style="--c:{DANTAI[d][0]}">{sx(n)}{n}<i>{d}</i>{trophy(n)}<small>{y0}〜{str(y1)[2:]}{"・" + to + ("へ" if to != "復帰" else "") if to else ""}</small></span>' for n, d, y0, y1, to in PAST[team])
    return f'<div class="past"><b>過去</b><div class="pps">{xs}</div></div>'


def logo(key, name):
    for ext in ("png", "jpg", "webp"):
        p = os.path.join(SRC, f"{key}.{ext}")
        if os.path.exists(p):
            from PIL import Image
            im = Image.open(p).convert("RGBA")
            px = im.load(); w, h = im.size      # 白い地は透かして、余白を切る
            for y in range(h):
                for x in range(w):
                    r, g, b, a = px[x, y]
                    if a and min(r, g, b) > 246: px[x, y] = (255, 255, 255, 0)
            bb = im.getbbox(); im = im.crop(bb) if bb else im
            buf = io.BytesIO(); im.save(buf, "PNG")
            return f'<img src="data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}">'
    ini = "".join(w[0] for w in name.replace("/", " ").split()[:2]).upper()
    return f'<span class="ph">{ini}</span>'


def card(team, players):
    key, owner, since, wins = INFO[team]
    win = f'<span class="win">優勝 {len(wins)}回</span>' if wins else ""
    players = sorted(players, key=lambda p: BIRTH.get(p[0], "9999"))      # 年齢の高い順（年齢が非公開の黒沢咲は最後。2026-11-22 ユーザーの指定）
    pls = "".join(f'<span class="pl" style="--c:{DANTAI[d][0]}"><b><span>{sx(n)}{n}</span><span class="sub">{age(n)}{trophy(n)}</span></b><i>{d}</i></span>' for n, d in players)
    c1, c2 = TCOL[team]
    return (f'<div class="tm" style="--t1:{c1};--t2:{c2};--tg:{TGRAD.get(team, c1)}"><div class="lg">{logo(key, team)}</div><div class="bd"><h2>{team}</h2>'
            f'<p class="in">{owner}<em>・</em>{since[:4]}年から{win}</p><div class="pls">{pls}</div>{past_html(team)}</div></div>')


# カードのチームカラーの出し方（2026-11-22 ユーザーの指定「2色以上あるなら交互に・表現を変えてみて」）。STYLE=stripe|band|split で試せる
STYLE = os.environ.get("STYLE", "stripe")      # stripe に決定（2026-11-22 ユーザーの判断・案A）
TM_CSS = {
    # 枠を2色の斜めのしま（交互）に
    "stripe": ".tm { border: 6px solid transparent; background: linear-gradient(135deg, color-mix(in srgb, var(--tg) 16%, #fff) 0%, #fff 55%) padding-box, repeating-linear-gradient(135deg, var(--t1) 0 14px, var(--t2) 14px 28px) border-box; padding: 14px 7px 11px !important; } .tm .lg { width: 68px !important; } .tm .lg img { max-width: 68px !important; }",
    # 上に2色が交互に並ぶ帯（市松の1列）＋主の色の枠
    "band": ".tm { border: 3px solid var(--t1); background: linear-gradient(180deg, color-mix(in srgb, var(--t1) 12%, #fff) 0%, #fff 60%); padding-top: 24px !important; } .tm::before { content: ''; position: absolute; left: 0; right: 0; top: 0; height: 10px; background: repeating-linear-gradient(90deg, var(--t1) 0 26px, var(--t2) 26px 52px); }",
    # ロゴの側を2色の斜めの帯で塗り分け（ロゴは白い丸に）＋主の色の枠
    "split": ".tm { border: 3px solid var(--t1); background: linear-gradient(90deg, transparent 0 96px, #fff 96px), linear-gradient(160deg, var(--t1) 0 50%, var(--t2) 50% 100%); padding-left: 6px !important; } .tm .lg { width: 84px; height: 84px; border-radius: 50%; background: #fff; box-shadow: 0 0 0 3px #fff; } .tm .lg img { max-width: 64px !important; max-height: 64px !important; }",
}


def html():
    cnt = {k: sum(1 for _, ps in TEAMS for _, d in ps if d == k) for k in DANTAI}
    # 所属団体のカード: 5つの団体を同じ幅の升に並べ、1行に収める（札＋人数／正式名。2026-11-22 ユーザーの指定）
    full = {"連盟": "日本プロ麻雀連盟", "最高位戦": "最高位戦日本プロ麻雀協会", "協会": "日本プロ麻雀協会", "RMU": "RMU", "麻将連合": "麻将連合"}
    leg = "".join(f'<span class="dl" style="--c:{c}"><span class="t"><i>{k}</i><b>{f"{cnt[k]}人" if cnt[k] else "過去のみ"}</b></span><small>{full[k]}</small><em class="hd">{HEAD[k][0]} {HEAD[k][1]}</em><em class="ti">{TROPHY}{TITLE[k][0]}<br>{TITLE[k][1]}<span>（{TITLE[k][2]}）</span></em></span>' for k, (c, _) in DANTAI.items())
    cards = "".join(card(t, ps) for t, ps in sorted(TEAMS, key=lambda x: INFO[x[0]][2]))      # 参入の古いチームから（同じ年は公式サイトの並び。2026-11-22 ユーザーの指定）
    return f"""<!doctype html><html lang="ja"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@500;700;900&display=block" rel="stylesheet">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: 794px; height: 1560px; }}
body {{ font-family: 'Noto Sans JP', sans-serif; color: #1F2A28; background: #EEF6F3; padding: 14px 22px 18px; position: relative; font-feature-settings: "palt"; }}
header {{ display: flex; align-items: center; justify-content: space-between; background: #177083; color: #fff; border-radius: 8px; padding: 9px 16px; }}
header .ml {{ flex: none; background: #fff; border-radius: 8px; width: 74px; height: 62px; display: flex; align-items: center; justify-content: center; margin-right: 14px; }} header .ml img {{ max-height: 54px; max-width: 64px; display: block; }}
header h1 {{ flex: 1; font-size: 27px; font-weight: 900; line-height: 1.15; }} header h1 small {{ display: block; font-size: 12.5px; font-weight: 700; color: #DDF0EC; margin-top: 4px; }}
{LOGO_CSS}
.legend {{ display: grid; grid-template-columns: auto repeat(5, minmax(0, 1fr)); gap: 6px; align-items: center; background: #fff; border: 2px solid #177083; border-radius: 8px; padding: 7px 10px; margin: 8px 0; font-size: 11px; font-weight: 800; }}
.legend > b small {{ display: block; font-size: 9px; color: #5E6B69; font-weight: 700; margin-top: 3px; line-height: 1.3; }}
.legend > b {{ font-size: 12.5px; font-weight: 900; color: #177083; margin-right: 2px; line-height: 1.25; }}
.dl {{ display: flex; flex-direction: column; align-items: center; gap: 2px; border-left: 1.5px solid #DCE7E4; padding-left: 6px; }} .dl .t {{ display: flex; align-items: center; gap: 5px; }} .dl small {{ font-size: 9px; font-weight: 700; color: #5E6B69; white-space: nowrap; letter-spacing: -.03em; }} .dl i {{ font-style: normal; color: #fff; background: var(--c); border-radius: 4px; padding: 1px 7px; font-weight: 900; }} .dl b {{ color: var(--c); font-weight: 900; }}
.grid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 10px; }}
.tm {{ display: flex; gap: 8px; min-width: 0; align-items: center; position: relative; overflow: hidden; border-radius: 10px; padding: 18px 10px 14px; }}
{TM_CSS[STYLE]}
.lg {{ flex: none; width: 84px; height: 96px; display: flex; align-items: center; justify-content: center; }}
.lg img {{ max-width: 84px; max-height: 96px; display: block; }}
.ph {{ width: 78px; height: 78px; border-radius: 50%; background: #E3ECEA; color: #5E6B69; font-size: 20px; font-weight: 900; display: flex; align-items: center; justify-content: center; }}
.bd {{ flex: 1; min-width: 0; }}
h2 {{ color: color-mix(in srgb, var(--t1) 55%, #1F2A28); font-size: 17.5px; font-weight: 900; line-height: 1.2; white-space: nowrap; }}
.in {{ font-size: 11px; font-weight: 700; color: #5E6B69; margin: 3px 0 8px; white-space: nowrap; display: flex; align-items: center; }} .in em {{ font-style: normal; margin: 0 2px; }}
.win {{ margin-left: 6px; font-size: 10px; font-weight: 900; color: #8A6A00; background: #FFF1C2; border: 1.5px solid #D4A017; border-radius: 9px; padding: 0 6px; }}
.pls {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 6px 5px; }}
.pl {{ display: flex; align-items: center; justify-content: space-between; gap: 4px; border: 2px solid var(--c); border-radius: 6px; overflow: hidden; background: #fff; }}
.pl b {{ font-size: 13px; font-weight: 900; padding: 4px 0 4px 4px; letter-spacing: -.02em; white-space: nowrap; }}
.pl i {{ font-style: normal; font-size: 9.5px; font-weight: 900; color: #fff; background: var(--c); padding: 4px 3px; white-space: nowrap; letter-spacing: -.06em; align-self: stretch; display: flex; align-items: center; }}
.past {{ display: flex; align-items: flex-start; gap: 5px; margin-top: 7px; padding-top: 6px; border-top: 1.5px dashed #D5E0DD; }}
.past > b {{ flex: none; font-size: 10px; font-weight: 900; color: #fff; background: #8A9A97; border-radius: 4px; padding: 1px 6px; margin-top: 1px; }}
.past .none {{ font-size: 10.5px; font-weight: 700; color: #6B7A77; }}
.pps {{ display: flex; flex-wrap: wrap; gap: 3px 9px; }}
.pp {{ display: inline-flex; align-items: center; gap: 3px; font-size: 11px; font-weight: 900; color: #33403D; white-space: nowrap; }}
.pp i {{ font-style: normal; font-size: 9px; font-weight: 900; color: #fff; background: var(--c); border-radius: 3px; padding: 0 4px; line-height: 1.45; }}      /* 過去の選手も団体を文字と色で */ .pp small {{ font-size: 9.5px; font-weight: 700; color: #6B7A77; margin-left: 2px; }}
.pl b {{ display: flex; flex-direction: column; line-height: 1.2; }} em.ag {{ font-style: normal; font-size: 10px; font-weight: 800; color: #6B7A77; margin-left: 12px; line-height: 1.1; }}      /* 年齢は名前の下に小さく（横に並べると札に入らない） */ em.ag::after {{ content: "歳"; font-size: 8.5px; }}
.sub {{ display: flex; align-items: center; gap: 2px; }} .sub em.ag {{ margin-left: 9px; }}
u.tr {{ text-decoration: none; display: inline-flex; align-items: center; gap: 0; font-size: 8.5px; letter-spacing: -.08em; font-weight: 900; color: #8A6A00; white-space: nowrap; }} u.tr svg {{ width: 10px; height: 10px; }}
u.tr sup {{ font-size: 8px; margin-left: 1px; vertical-align: 3px; line-height: 0; }}

.pp u.tr {{ margin-left: 2px; }}
.dl em.hd {{ font-style: normal; font-size: 9.5px; font-weight: 800; color: #33403D; white-space: nowrap; margin-top: 2px; }}
.dl em.ti {{ font-style: normal; font-size: 9.5px; font-weight: 900; color: #8A6A00; text-align: center; line-height: 1.3; background: #FFF8E1; border-radius: 6px; padding: 2px 6px; margin-top: 2px; white-space: nowrap; }} .dl em.ti svg {{ width: 11px; height: 11px; vertical-align: -1px; margin-right: 1px; }} .dl em.ti span {{ font-weight: 700; color: #8A7A55; font-size: 8.5px; }}
u.sx {{ text-decoration: none; font-weight: 900; margin-right: 1px; font-size: .9em; }} u.sx.f {{ color: #D9487D; }} u.sx.m {{ color: #2F8FD8; }}
.note {{ font-size: 10.5px; font-weight: 700; color: #4F5C5A; line-height: 1.55; margin-top: 8px; }}
footer {{ position: absolute; left: 22px; right: 22px; bottom: 7px; display: flex; justify-content: space-between; font-size: 10px; color: #8A9A97; }} footer b {{ color: #177083; font-weight: 900; }}
</style></head><body>
<header><span class="ml">{logo("mleague", "M")}</span><h1>Mリーグ 2026-27 全10チーム40人<small>チームと選手、選手の所属するプロ団体、過去の所属選手</small></h1>{logo_html()}</header>
<div class="legend"><b>選手の<br>所属団体<small>代表・<br>最高タイトルと<br>今の保持者</small></b>{leg}</div>
<div class="grid">{cards}</div>
<p class="note">チームと選手・所属団体は Mリーグ公式サイト（2026年10月時点）、過去の選手は Wikipedia「Mリーグ」と各チームの記事（2026年11月に確認）による。名前の前の♀は女性・♂は男性。トロフィーは所属団体の最高タイトル（鳳凰位・最高位・雀王・令昭位・将王）を取ったことがある選手（×は回数・「現」は今の保持者。取った当時の団体のタイトル）。代表とタイトルは各団体の公式サイトとWikipedia（2026年11月に確認）。名前の右は年齢（2026年11月22日時点・Wikipedia の生年月日による。黒沢咲は非公開）。過去の選手の色は所属団体（Mリーグにいたとき）、年はシーズンの始めの年〜終わりの年。チームの並びは参入の古い順（同じ年は公式サイトの並び）、選手は年齢の高い順。団体の色は見分けやすくするためにまじゃすこで付けたもの。</p>
<footer><span>麻雀スコア記録アプリ <b>まじゃすこ</b>　majasco.jp</span><span>全チームの紹介は「Mリーグ2026-27 完全ガイド」</span></footer>
</body></html>"""


def render():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    hp = os.path.join(OUT, "_p.html"); io.open(hp, "w", encoding="utf-8").write(html())
    with sync_playwright() as p:
        b = p.chromium.launch(); pg = b.new_page(viewport={"width": 794, "height": 1560}, device_scale_factor=2)
        pg.goto("file:///" + hp.replace("\\", "/").lstrip("/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(1200)
        gap = pg.evaluate("document.querySelector('footer').getBoundingClientRect().top - document.querySelector('.note').getBoundingClientRect().bottom")
        over = pg.evaluate("[...document.querySelectorAll('.tm h2, .in, .pl, .pl b')].filter(e => e.scrollWidth > e.clientWidth + 1 || e.getBoundingClientRect().right > e.closest('.tm').getBoundingClientRect().right - 2).map(e => e.textContent)")
        over += pg.evaluate("[...document.querySelectorAll('.tm, .legend')].filter(e => e.getBoundingClientRect().right > document.body.clientWidth - 21 || e.scrollWidth > e.clientWidth + 1).map(e => '右へ:' + e.textContent.slice(0, 8))")
        print("余白", round(gap), "はみ出し", over); pg.screenshot(path=os.path.join(OUT, "mleague-teams.png")); b.close()
    os.remove(hp)
    assert gap > 0 and not over


if __name__ == "__main__":
    render()
