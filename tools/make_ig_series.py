# -*- coding: utf-8 -*-
# Instagram用画像一括生成: 使い方カルーセル6枚 + 機能紹介シリーズ6枚（1080x1350＝縦5:横4）。
# IGのプロフィールグリッドが縦5:横4表示のため、フィード画像はすべてこの比率で作る
import os, math
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # リポジトリルート
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig")
os.makedirs(OUTDIR, exist_ok=True)
FONT = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"
EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"

GREEN = (23, 112, 131)
BLUE_SANMA = (66, 97, 170)
ORANGE = (231, 86, 32)
DARK = (31, 42, 40)
GRAY = (85, 99, 95)
LGRAY = (154, 168, 164)
BORDER = (226, 236, 231)
BLUE = (26, 35, 126)
RED = (198, 40, 40)
FAINT = (242, 247, 246)
TEAM = {"赤": (230, 0, 18), "青": (0, 117, 194), "緑": (0, 160, 64), "橙": (243, 152, 0)}
W, H = 1080, 1350

def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f
F_EMOJI = lambda s: ImageFont.truetype(EMOJI, s)
LOGO = Image.open(os.path.join(BASE, "assets", "logo.png")).convert("RGBA")

def sparkle(d, x, y, R, color):
    rr = R * 0.22
    pts = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rad = R if i % 2 == 0 else rr
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
    d.polygon(pts, fill=color)

def new_canvas(glow_cy=920):
    img = Image.new("RGB", (W, H), (255, 255, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([540 - 390, glow_cy - 390, 540 + 390, glow_cy + 390], fill=(238, 248, 243))
    sparkle(d, 950, 590, 44, ORANGE)
    sparkle(d, 215, 580, 30, GREEN)
    sparkle(d, 940, 1200, 30, GREEN)
    d.ellipse([940, 305, 964, 329], fill=ORANGE)
    d.ellipse([185, 790, 203, 808], fill=(159, 195, 189))
    return img, d

def logo_top(img, y=52, h=96):
    lw = int(LOGO.width * h / LOGO.height)
    lg = LOGO.resize((lw, h), Image.LANCZOS)
    img.paste(lg, ((W - lw) // 2, y), lg)

def footer(d):
    d.text((60, 1290), "majasco.jp", font=font(34, 700), fill=LGRAY, anchor="lm")

def phone_frame(d, x0=352, y0=600, x1=728):
    d.rounded_rectangle([x0, y0, x1, H + 160], radius=58, fill=DARK)
    d.rounded_rectangle([x0 + 15, y0 + 15, x1 - 15, H + 160], radius=44, fill=(255, 255, 255))
    cx = (x0 + x1) // 2
    d.rounded_rectangle([cx - 52, y0 + 32, cx + 52, y0 + 56], radius=12, fill=DARK)
    return (x0 + 15, y0 + 15, x1 - 15)

# ==== スマホ画面の中身（コールバック群） ====
def screen_score(d, sx0, sy0, sx1, title="スコア収支", title_color=GREEN, team=False):
    cx = (sx0 + sx1) // 2
    d.text((cx, sy0 + 95), title, font=font(38, 800), fill=title_color, anchor="mm")
    rows = ([("赤組", "+55.0", BLUE, None, TEAM["赤"]), ("青組", "+8.0", BLUE, None, TEAM["青"]),
             ("緑組", "-18.0", RED, None, TEAM["緑"]), ("橙組", "-45.0", RED, None, TEAM["橙"])] if team else
            [("太郎", "+55.0", BLUE, "\U0001F947", None), ("次郎", "+8.0", BLUE, "\U0001F948", None),
             ("三郎", "-18.0", RED, "\U0001F949", None), ("四郎", "-45.0", RED, None, None)])
    y = sy0 + 137
    for name, val, vc, medal, dot in rows:
        d.rounded_rectangle([sx0 + 27, y, sx1 - 27, y + 74], radius=16, fill=(255, 255, 255), outline=BORDER, width=3)
        tx = sx0 + 47
        if medal:
            d.text((tx, y + 37), medal, font=F_EMOJI(38), embedded_color=True, anchor="lm")
            tx += 58
        if dot:
            d.ellipse([tx, y + 26, tx + 22, y + 48], fill=dot)
            tx += 34
        d.text((tx, y + 37), name, font=font(31, 700), fill=(26, 26, 26), anchor="lm")
        d.text((sx1 - 42, y + 37), val, font=font(31, 800), fill=vc, anchor="rm")
        y += 94
    d.rounded_rectangle([sx0 + 27, y + 6, sx1 - 27, y + 160], radius=16, fill=FAINT, outline=BORDER, width=3)
    pts = [(sx0 + 55, y + 60), (sx0 + 115, y + 34), (sx0 + 170, y + 48), (sx0 + 225, y + 26), (sx0 + 280, y + 42), (sx0 + 318, y + 22)]
    if team:
        d.line([(p[0], p[1] + 20) for p in pts], fill=TEAM["青"], width=7, joint="curve")
        d.line(pts, fill=TEAM["赤"], width=7, joint="curve")
    else:
        d.line(pts, fill=GREEN, width=8, joint="curve")
        for p in pts:
            d.ellipse([p[0] - 7, p[1] - 7, p[0] + 7, p[1] + 7], fill=GREEN)

def screen_setup(d, sx0, sy0, sx1):
    cx = (sx0 + sx1) // 2
    x = sx0 + 30
    d.text((cx, sy0 + 92), "グループ作成", font=font(36, 800), fill=GREEN, anchor="mm")
    d.text((x, sy0 + 145), "グループ名", font=font(24, 600), fill=LGRAY, anchor="lm")
    d.rounded_rectangle([x, sy0 + 162, sx1 - 30, sy0 + 222], radius=12, fill=FAINT)
    d.text((x + 18, sy0 + 192), "金曜メンバー", font=font(29, 700), fill=(26, 26, 26), anchor="lm")
    d.text((x, sy0 + 268), "メンバー名", font=font(24, 600), fill=LGRAY, anchor="lm")
    names = ["太郎 ×", "次郎 ×", "三郎 ×", "四郎 ×"]
    bx = x
    for i, nm in enumerate(names[:3]):
        w = 96
        d.rounded_rectangle([bx, sy0 + 288, bx + w, sy0 + 338], radius=25, fill=(228, 243, 236))
        d.text((bx + w / 2, sy0 + 313), nm, font=font(22, 600), fill=GREEN, anchor="mm")
        bx += w + 10
    d.rounded_rectangle([x, sy0 + 352, x + 96, sy0 + 402], radius=25, fill=(228, 243, 236))
    d.text((x + 48, sy0 + 377), names[3], font=font(22, 600), fill=GREEN, anchor="mm")
    d.text((x, sy0 + 448), "試合形式", font=font(24, 600), fill=LGRAY, anchor="lm")
    half = (sx1 - 30 - x - 12) // 2
    d.rounded_rectangle([x, sy0 + 466, x + half, sy0 + 522], radius=12, fill=GREEN)
    d.text((x + half / 2, sy0 + 494), "四麻", font=font(26, 700), fill=(255, 255, 255), anchor="mm")
    d.rounded_rectangle([x + half + 12, sy0 + 466, sx1 - 30, sy0 + 522], radius=12, fill=FAINT)
    d.text((x + half + 12 + half / 2, sy0 + 494), "三麻", font=font(26, 700), fill=LGRAY, anchor="mm")

def screen_chat(d, sx0, sy0, sx1):
    cx = (sx0 + sx1) // 2
    d.text((cx, sy0 + 92), "金曜メンバー（4）", font=font(31, 700), fill=(26, 26, 26), anchor="mm")
    d.line([sx0 + 10, sy0 + 122, sx1 - 10, sy0 + 122], fill=(238, 238, 238), width=3)
    d.rounded_rectangle([sx0 + 86, sy0 + 150, sx1 - 20, sy0 + 262], radius=22, fill=GREEN)
    d.text((sx0 + 108, sy0 + 190), "今日の対局グループ", font=font(23, 600), fill=(255, 255, 255), anchor="lm")
    d.text((sx0 + 108, sy0 + 228), "作ったよ！", font=font(23, 600), fill=(255, 255, 255), anchor="lm")
    d.rounded_rectangle([sx0 + 86, sy0 + 282, sx1 - 20, sy0 + 348], radius=22, fill=GREEN)
    d.text((sx0 + 108, sy0 + 315), "majasco.jp/#XXXX", font=font(22, 600), fill=(207, 233, 239), anchor="lm")
    d.rounded_rectangle([sx0 + 20, sy0 + 372, sx0 + 250, sy0 + 438], radius=22, fill=(240, 240, 240))
    d.text((sx0 + 44, sy0 + 405), "参加した！", font=font(23, 600), fill=(68, 68, 68), anchor="lm")
    d.rounded_rectangle([sx0 + 86, sy0 + 462, sx1 - 20, sy0 + 574], radius=22, fill=GREEN)
    d.text((sx0 + 108, sy0 + 502), "誰かが入力すれば", font=font(23, 600), fill=(255, 255, 255), anchor="lm")
    d.text((sx0 + 108, sy0 + 540), "全員に反映されるよ", font=font(23, 600), fill=(255, 255, 255), anchor="lm")

def screen_input(d, sx0, sy0, sx1, chips=False, marks=False):
    cx = (sx0 + sx1) // 2
    d.text((cx, sy0 + 92), "点数入力", font=font(36, 800), fill=(26, 26, 26), anchor="mm")
    rows = [("太郎", "350"), ("次郎", "280"), ("三郎", "220"), ("四郎", "150")]
    y = sy0 + 140
    for name, val in rows:
        d.text((sx0 + 30, y + 30), name, font=font(27, 700), fill=(85, 85, 85), anchor="lm")
        d.rounded_rectangle([sx0 + 128, y, sx1 - 30, y + 60], radius=12, fill=(255, 255, 255), outline=(221, 221, 221), width=3)
        d.text((sx1 - 92, y + 30), val, font=font(29, 600), fill=(26, 26, 26), anchor="rm")
        d.text((sx1 - 48, y + 30), "00", font=font(23, 500), fill=(170, 170, 170), anchor="rm")
        y += 84
    d.rounded_rectangle([sx0 + 27, y + 8, sx1 - 27, y + 72], radius=14, fill=(232, 245, 233))
    d.text((cx, y + 40), "入力合計: 100,000 ✓", font=font(23, 700), fill=(46, 125, 50), anchor="mm")
    d.rounded_rectangle([sx0 + 27, y + 96, sx1 - 27, y + 172], radius=38, fill=GREEN)
    d.text((cx, y + 134), "入力完了", font=font(30, 800), fill=(255, 255, 255), anchor="mm")

def screen_chips(d, sx0, sy0, sx1):
    cx = (sx0 + sx1) // 2
    d.text((cx, sy0 + 92), "点数 / チップ入力", font=font(34, 800), fill=(26, 26, 26), anchor="mm")
    rows = [("太郎", "23", "350", "", ""), ("次郎", "19", "280", "", ""),
            ("三郎", "20", "220", "\U0001F414", ""), ("四郎", "18", "150", "", "\U0001F4A9")]
    y = sy0 + 140
    for name, chip, val, yaki, chombo in rows:
        d.text((sx0 + 26, y + 30), name, font=font(25, 700), fill=(85, 85, 85), anchor="lm")
        d.rounded_rectangle([sx0 + 92, y, sx0 + 172, y + 60], radius=12, fill=(255, 255, 255), outline=(221, 221, 221), width=3)
        d.text((sx0 + 148, y + 30), chip, font=font(26, 600), fill=(26, 26, 26), anchor="rm")
        d.rounded_rectangle([sx0 + 184, y, sx0 + 296, y + 60], radius=12, fill=(255, 255, 255), outline=(221, 221, 221), width=3)
        d.text((sx0 + 272, y + 30), val, font=font(26, 600), fill=(26, 26, 26), anchor="rm")
        mk = yaki or chombo
        if mk:
            d.text((sx0 + 312, y + 30), mk, font=F_EMOJI(30), embedded_color=True, anchor="lm")
        y += 84
    d.rounded_rectangle([sx0 + 27, y + 8, sx1 - 27, y + 72], radius=14, fill=(232, 245, 233))
    d.text((cx, y + 40), "チップ合計: 80枚 ✓", font=font(23, 700), fill=(46, 125, 50), anchor="mm")

def screen_rules(d, sx0, sy0, sx1):
    cx = (sx0 + sx1) // 2
    x = sx0 + 30
    d.text((cx, sy0 + 92), "ルール設定", font=font(36, 800), fill=BLUE_SANMA, anchor="mm")
    d.text((x, sy0 + 145), "試合形式", font=font(24, 600), fill=LGRAY, anchor="lm")
    half = (sx1 - 30 - x - 12) // 2
    d.rounded_rectangle([x, sy0 + 163, x + half, sy0 + 219], radius=12, fill=FAINT)
    d.text((x + half / 2, sy0 + 191), "四麻", font=font(26, 700), fill=LGRAY, anchor="mm")
    d.rounded_rectangle([x + half + 12, sy0 + 163, sx1 - 30, sy0 + 219], radius=12, fill=BLUE_SANMA)
    d.text((x + half + 12 + half / 2, sy0 + 191), "三麻", font=font(26, 700), fill=(255, 255, 255), anchor="mm")
    items = [("持ち点", "35,000"), ("返し点", "40,000"), ("ウマ", "15-0-15"), ("スコア倍率", "×100")]
    y = sy0 + 260
    for label, val in items:
        d.text((x, y + 14), label, font=font(24, 600), fill=LGRAY, anchor="lm")
        d.rounded_rectangle([x, y + 32, sx1 - 30, y + 88], radius=12, fill=FAINT)
        d.text((x + 18, y + 60), val, font=font(27, 700), fill=(26, 26, 26), anchor="lm")
        y += 112

def two_phones(d):
    # 小さめのスマホを2台、少し重ねて表示（同じスコア画面）
    for (x0, y0, x1) in [(180, 660, 500), (580, 660, 900)]:
        d.rounded_rectangle([x0, y0, x1, H + 160], radius=50, fill=DARK)
        d.rounded_rectangle([x0 + 13, y0 + 13, x1 - 13, H + 160], radius=38, fill=(255, 255, 255))
        cx = (x0 + x1) // 2
        d.rounded_rectangle([cx - 42, y0 + 27, cx + 42, y0 + 47], radius=10, fill=DARK)
        d.text((cx, y0 + 84), "スコア収支", font=font(30, 800), fill=GREEN, anchor="mm")
        rows = [("太郎", "+55.0", BLUE, "\U0001F947"), ("次郎", "+8.0", BLUE, "\U0001F948"), ("三郎", "-18.0", RED, "\U0001F949")]
        y = y0 + 118
        for name, val, vc, medal in rows:
            d.rounded_rectangle([x0 + 26, y, x1 - 26, y + 64], radius=14, fill=(255, 255, 255), outline=BORDER, width=3)
            d.text((x0 + 42, y + 32), medal, font=F_EMOJI(30), embedded_color=True, anchor="lm")
            d.text((x0 + 92, y + 32), name, font=font(26, 700), fill=(26, 26, 26), anchor="lm")
            d.text((x1 - 40, y + 32), val, font=font(26, 800), fill=vc, anchor="rm")
            y += 80
        d.rounded_rectangle([x0 + 26, y + 4, x1 - 26, y + 130], radius=14, fill=FAINT, outline=BORDER, width=3)
        pts = [(x0 + 50, y + 90), (x0 + 105, y + 62), (x0 + 160, y + 76), (x0 + 215, y + 52), (x0 + 268, y + 66)]
        d.line(pts, fill=GREEN, width=7, joint="curve")

# ==== テンプレート ====
def slide(fname, title_lines, sub=None, sub_hl=None, screen_fn=None, step=None, title_color=GREEN, custom=None):
    img, d = new_canvas()
    logo_top(img)
    d2 = ImageDraw.Draw(img)
    y = 244
    if step:
        d2.rounded_rectangle([440, 200, 640, 260], radius=30, fill=ORANGE)
        d2.text((540, 230), step, font=font(30, 800), fill=(255, 255, 255), anchor="mm")
        y = 328
    f_main = font(70, 900)
    for line in title_lines:
        d2.text((540, y), line, font=f_main, fill=title_color, anchor="mm")
        y += 96
    if sub:
        f_b = font(40, 800)
        f_n = font(40, 500)
        if sub_hl:
            total = d2.textlength(sub_hl, font=f_b) + d2.textlength(sub, font=f_n)
            x = (W - total) / 2
            d2.text((x, y + 16), sub_hl, font=f_b, fill=ORANGE, anchor="lm")
            d2.text((x + d2.textlength(sub_hl, font=f_b), y + 16), sub, font=f_n, fill=GRAY, anchor="lm")
        else:
            d2.text((540, y + 16), sub, font=f_n, fill=GRAY, anchor="mm")
    if custom:
        custom(d2)
    elif screen_fn:
        sx0, sy0, sx1 = phone_frame(d2)
        screen_fn(d2, sx0, sy0, sx1)
    footer(d2)
    img.save(os.path.join(OUTDIR, fname))
    print("saved:", fname)

# ==== 使い方カルーセル（6枚） ====
slide("howto-1-cover.png", ["使い方は", "かんたん4ステップ"], sub="｜1分でわかる「まじゃすこ」", sub_hl="登録不要・無料", screen_fn=screen_score)
slide("howto-2-step1.png", ["グループを作る"], sub="グループ名とメンバーを入れるだけ（10秒）", screen_fn=screen_setup, step="STEP 1")
slide("howto-3-step2.png", ["URLをシェアする"], sub="LINEで送れば、全員が同じスコア表に", screen_fn=screen_chat, step="STEP 2")
slide("howto-4-step3.png", ["点数を入れるだけ"], sub="ウマ・オカ込みのスコアを自動計算", screen_fn=screen_input, step="STEP 3")
slide("howto-5-step4.png", ["結果は全員のスマホに"], sub="順位・成績・グラフまで自動で記録", screen_fn=screen_score, step="STEP 4")

def closing(d):
    y = 660
    badges = ["登録不要", "完全無料", "スコアを共有"]
    widths = [d.textlength(b, font=font(36, 700)) + 76 for b in badges]
    total = sum(widths) + 2 * 24
    x = (W - total) / 2
    for b, wdt in zip(badges, widths):
        d.rounded_rectangle([x, y, x + wdt, y + 76], radius=38, outline=GREEN, width=4, fill=(255, 255, 255))
        d.text((x + wdt / 2, y + 38), b, font=font(36, 700), fill=GREEN, anchor="mm")
        x += wdt + 24
    d.rounded_rectangle([290, 840, 790, 936], radius=48, fill=ORANGE)
    d.text((540, 888), "スコア記録をはじめる", font=font(40, 800), fill=(255, 255, 255), anchor="mm")
    d.text((540, 1020), "▲ プロフィールのリンクからすぐ使えます", font=font(32, 600), fill=GRAY, anchor="mm")
slide("howto-6-close.png", ["今日の対局から、", "スマホ1台で。"], custom=closing)

# ==== 機能紹介シリーズ（6枚） ====
slide("feature-1.png", ["点数を入れるだけで、", "自動計算"], sub="ウマ・オカ・同点処理もぜんぶおまかせ", screen_fn=screen_input)
slide("feature-2.png", ["全員のスマホが、", "同じスコア表"], sub="「いま誰がトップ？」が一目でわかる", custom=two_phones)
slide("feature-3.png", ["Mリーグみたいな、", "チーム戦"], sub="チームカラーで団体戦が盛り上がる", screen_fn=lambda d, a, b, c: screen_score(d, a, b, c, title="チーム成績", team=True))
slide("feature-4.png", ["逆転のドラマを、", "グラフで"], sub="試合ごとの推移を自動で記録", screen_fn=screen_score)
slide("feature-5.png", ["三麻もOK、", "ルールは自由自在"], sub="持ち点・ウマもいつものルールで", screen_fn=screen_rules, title_color=BLUE_SANMA)
slide("feature-6.png", ["チップも焼き鳥も、", "まとめて記録"], sub="細かいルールごと、スマホ1台で", screen_fn=screen_chips)
print("done")
