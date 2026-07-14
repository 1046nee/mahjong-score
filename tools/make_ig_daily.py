# -*- coding: utf-8 -*-
# IG毎日投稿用の画像: 麻雀用語ミニ解説カード4枚（glossary-*）＋小ワザTips3枚（tips-*）。
# 1080x1350（縦5:横4）。共通ヘルパーは make_ig_series.py からコピー
import os, math
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig")
os.makedirs(OUTDIR, exist_ok=True)
FONT = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"
EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"

GREEN = (23, 112, 131)
ORANGE = (231, 86, 32)
DARK = (31, 42, 40)
GRAY = (85, 99, 95)
LGRAY = (154, 168, 164)
BORDER = (226, 236, 231)
BLUE = (26, 35, 126)
RED = (198, 40, 40)
FAINT = (242, 247, 246)
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

# ==== 用語ミニ解説カード ====
def glossary(fname, term, def_lines, card_header, rows, closing, bullets=False):
    """term=大見出し / def_lines=定義（中央寄せ）/ rows=例カードの中身 / closing=締めの一言"""
    img, d = new_canvas()
    logo_top(img)
    d = ImageDraw.Draw(img)
    # バッジ
    b_txt = "麻雀用語ミニ解説"
    f_b = font(30, 800)
    bw = d.textlength(b_txt, font=f_b) + 76
    d.rounded_rectangle([540 - bw / 2, 206, 540 + bw / 2, 268], radius=31, fill=ORANGE)
    d.text((540, 237), b_txt, font=f_b, fill=(255, 255, 255), anchor="mm")
    # 用語
    d.text((540, 396), term, font=font(124, 900), fill=GREEN, anchor="mm")
    # 定義
    y = 528
    for line in def_lines:
        d.text((540, y), line, font=font(38, 600), fill=GRAY, anchor="mm")
        y += 54
    # 例カード（高さは行数に合わせて可変。枠からのはみ出し防止）
    cy0 = 650
    ry = cy0 + 120
    if bullets:
        card_y1 = ry + len(rows) * 82 - 82 + 34 + 34
    else:
        card_y1 = ry + len(rows) * 80 - 16 + 34
    d.rounded_rectangle([150, cy0, 930, card_y1], radius=22, fill=(255, 255, 255), outline=BORDER, width=4)
    d.text((190, cy0 + 54), card_header, font=font(28, 800), fill=GREEN, anchor="lm")
    d.line([188, cy0 + 92, 892, cy0 + 92], fill=BORDER, width=3)
    if bullets:
        for txt in rows:
            # 絵文字はアプリ実画面のマーク再現のみ（🐔）
            x = 196
            for seg, is_emoji in txt:
                if is_emoji:
                    d.text((x, ry + 22), seg, font=F_EMOJI(34), embedded_color=True, anchor="lm")
                    x += 46
                else:
                    d.text((x, ry + 22), seg, font=font(32, 600), fill=(40, 50, 48), anchor="lm")
                    x += d.textlength(seg, font=font(32, 600))
            ry += 82
    else:
        for label, val, vc in rows:
            d.rounded_rectangle([188, ry, 892, ry + 64], radius=14, fill=FAINT)
            x = 216
            for seg, is_emoji in label:
                if is_emoji:
                    d.text((x, ry + 32), seg, font=F_EMOJI(30), embedded_color=True, anchor="lm")
                    x += 44
                else:
                    d.text((x, ry + 32), seg, font=font(29, 700), fill=(40, 50, 48), anchor="lm")
                    x += d.textlength(seg, font=font(29, 700))
            d.text((864, ry + 32), val, font=font(30, 800), fill=vc, anchor="rm")
            ry += 80
    # 締め
    d.text((540, card_y1 + 62), closing, font=font(31, 600), fill=GRAY, anchor="mm")
    footer(d)
    img.save(os.path.join(OUTDIR, fname))
    print("saved:", fname)

T = lambda s: (s, False)
E = lambda s: (s, True)

glossary(
    "glossary-1-uma.png", "ウマ",
    ["対局後、順位に応じて加減される", "スコアのボーナスのこと"],
    "例: ウマ10-30（四麻）",
    [([E("\U0001F947"), T(" 1位")], "+30", BLUE),
     ([E("\U0001F948"), T(" 2位")], "+10", BLUE),
     ([E("\U0001F949"), T(" 3位")], "−10", RED),
     ([T("　 4位")], "−30", RED)],
    "まじゃすこなら、設定するだけで自動計算")

glossary(
    "glossary-2-oka.png", "オカ",
    ["持ち点と返し点の差から生まれる、", "トップだけのボーナス"],
    "例: 25,000点持ち・30,000点返し",
    [([T("持ち点")], "25,000点", (40, 50, 48)),
     ([T("返し点")], "30,000点", (40, 50, 48)),
     ([T("→ トップに")], "+20", BLUE)],
    "まじゃすこなら、設定するだけで自動計算")

glossary(
    "glossary-3-yakitori.png", "焼き鳥",
    ["一度もアガれないまま", "対局が終わってしまうこと"],
    "卓ごとのよくある扱い",
    [[T("・罰スコアを決めておく（例: −10）")],
     [T("・マークだけ付けて成績に残す")],
     [T("・まじゃすこでは "), E("\U0001F414"), T(" マークで記録")]],
    "誰が焼き鳥か、マークひとつで残せます", bullets=True)

glossary(
    "glossary-4-chombo.png", "チョンボ",
    ["誤ロン・誤ツモなど、", "対局中の反則のこと"],
    "よくあるチョンボ",
    [[T("・誤ロン、誤ツモ")],
     [T("・ノーテンでのリーチあがり")],
     [T("・罰スコアの扱いは卓のルール次第")]],
    "まじゃすこなら、回数までしっかり記録", bullets=True)

# ==== 小ワザTips（feature系と同じスマホ入り構図） ====
def screen_input(d, sx0, sy0, sx1, auto=False, error=False):
    cx = (sx0 + sx1) // 2
    d.text((cx, sy0 + 92), "点数入力", font=font(36, 800), fill=(26, 26, 26), anchor="mm")
    rows = [("太郎", "350"), ("次郎", "280"), ("三郎", "210" if error else "220"), ("四郎", "150")]
    y = sy0 + 140
    for i, (name, val) in enumerate(rows):
        d.text((sx0 + 30, y + 30), name, font=font(27, 700), fill=(85, 85, 85), anchor="lm")
        if auto and i == 3:
            d.rounded_rectangle([sx0 + 128, y, sx1 - 30, y + 60], radius=12, fill=(228, 243, 236))
            d.text(((sx0 + 128 + sx1 - 30) / 2, y + 30), "自動で入力 ✓", font=font(23, 700), fill=GREEN, anchor="mm")
        else:
            box_outline = RED if (error and i == 2) else (221, 221, 221)
            d.rounded_rectangle([sx0 + 128, y, sx1 - 30, y + 60], radius=12, fill=(255, 255, 255), outline=box_outline, width=3)
            d.text((sx1 - 92, y + 30), val, font=font(29, 600), fill=(26, 26, 26), anchor="rm")
            d.text((sx1 - 48, y + 30), "00", font=font(23, 500), fill=(170, 170, 170), anchor="rm")
        y += 84
    if error:
        d.rounded_rectangle([sx0 + 27, y + 8, sx1 - 27, y + 72], radius=14, fill=(253, 235, 236))
        d.text((cx, y + 40), "合計 99,000 ×", font=font(23, 700), fill=RED, anchor="mm")
        d.text((cx, y + 110), "あと 1,000点 どこかにあるはず…", font=font(21, 600), fill=GRAY, anchor="mm")
    else:
        d.rounded_rectangle([sx0 + 27, y + 8, sx1 - 27, y + 72], radius=14, fill=(232, 245, 233))
        d.text((cx, y + 40), "入力合計: 100,000 ✓", font=font(23, 700), fill=(46, 125, 50), anchor="mm")
        d.rounded_rectangle([sx0 + 27, y + 96, sx1 - 27, y + 172], radius=38, fill=GREEN)
        d.text((cx, y + 134), "入力完了", font=font(30, 800), fill=(255, 255, 255), anchor="mm")

def slide(fname, title_lines, sub, screen_kw):
    img, d = new_canvas()
    logo_top(img)
    d = ImageDraw.Draw(img)
    # バッジ
    b_txt = "まじゃすこの小ワザ"
    f_b = font(30, 800)
    bw = d.textlength(b_txt, font=f_b) + 76
    d.rounded_rectangle([540 - bw / 2, 200, 540 + bw / 2, 260], radius=30, fill=ORANGE)
    d.text((540, 230), b_txt, font=f_b, fill=(255, 255, 255), anchor="mm")
    y = 328
    for line in title_lines:
        d.text((540, y), line, font=font(70, 900), fill=GREEN, anchor="mm")
        y += 96
    d.text((540, y + 16), sub, font=font(40, 500), fill=GRAY, anchor="mm")
    sx0, sy0, sx1 = phone_frame(d)
    screen_input(d, sx0, sy0, sx1, **screen_kw)
    footer(d)
    img.save(os.path.join(OUTDIR, fname))
    print("saved:", fname)

slide("tips-1-keta.png", ["点数は、", "下2桁いらない"], "「250」で25,000点として計算します", {})
slide("tips-2-auto.png", ["最後の1人は、", "自動計算"], "3人入れたら、残りはおまかせ", {"auto": True})
slide("tips-3-check.png", ["合計が合わないと、", "教えてくれる"], "入力ミスはその場で気づける", {"error": True})
print("done")
