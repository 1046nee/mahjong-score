# -*- coding: utf-8 -*-
# 機能紹介 feature-7「CSVで書き出せる」1080x1350（縦5:横4）。
# make_ig_series.py の共通ヘルパーをコピーして単発生成（seriesを再生成しないため独立ファイル）
import os, math
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # リポジトリルート
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

# ==== スマホ画面: 対局履歴カード + CSV保存 ====
def screen_csv(d, sx0, sy0, sx1):
    cx = (sx0 + sx1) // 2
    d.text((cx, sy0 + 92), "過去の試合", font=font(36, 800), fill=(26, 26, 26), anchor="mm")
    # 履歴カード（第3試合・順位順）
    card_y0 = sy0 + 130
    card_y1 = card_y0 + 300
    d.rounded_rectangle([sx0 + 27, card_y0, sx1 - 27, card_y1], radius=16,
                        fill=(255, 255, 255), outline=BORDER, width=3)
    d.text((sx0 + 47, card_y0 + 36), "第3試合", font=font(26, 800), fill=(26, 26, 26), anchor="lm")
    d.text((sx1 - 47, card_y0 + 36), "20:45", font=font(22, 500), fill=LGRAY, anchor="rm")
    d.line([sx0 + 45, card_y0 + 64, sx1 - 45, card_y0 + 64], fill=BORDER, width=2)
    rows = [("太郎", "+55.0", BLUE, "\U0001F947"), ("次郎", "+8.0", BLUE, "\U0001F948"),
            ("三郎", "-18.0", RED, "\U0001F949"), ("四郎", "-45.0", RED, None)]
    y = card_y0 + 82
    for name, val, vc, medal in rows:
        tx = sx0 + 47
        if medal:
            d.text((tx, y + 26), medal, font=F_EMOJI(30), embedded_color=True, anchor="lm")
        d.text((tx + 48, y + 26), name, font=font(26, 700), fill=(26, 26, 26), anchor="lm")
        d.text((sx1 - 47, y + 26), val, font=font(26, 800), fill=vc, anchor="rm")
        y += 54
    # CSV保存ボタン
    btn_y0 = card_y1 + 40
    d.rounded_rectangle([sx0 + 62, btn_y0, sx1 - 62, btn_y0 + 74], radius=37, fill=GREEN)
    d.text((cx, btn_y0 + 37), "CSVで保存 ↓", font=font(28, 800), fill=(255, 255, 255), anchor="mm")
    # ダウンロードされたファイルのチップ
    chip_y0 = btn_y0 + 106
    d.rounded_rectangle([sx0 + 27, chip_y0, sx1 - 27, chip_y0 + 60], radius=14,
                        fill=FAINT, outline=BORDER, width=3)
    # アイコン+ファイル名をまとめて中央寄せ（枠からのはみ出し防止のため名前は短縮形）
    fname_txt = "金曜メンバー.csv"
    f_chip = font(22, 700)
    tw = d.textlength(fname_txt, font=f_chip)
    start_x = cx - (34 + tw) / 2
    d.text((start_x, chip_y0 + 30), "\U0001F4C4", font=F_EMOJI(26), embedded_color=True, anchor="lm")
    d.text((start_x + 40, chip_y0 + 30), fname_txt, font=f_chip, fill=GRAY, anchor="lm")
    d.text((cx, chip_y0 + 96), "Excelでそのまま開ける", font=font(22, 600), fill=LGRAY, anchor="mm")

def slide(fname, title_lines, sub=None, screen_fn=None, title_color=GREEN):
    img, d = new_canvas()
    logo_top(img)
    d2 = ImageDraw.Draw(img)
    y = 244
    f_main = font(70, 900)
    for line in title_lines:
        d2.text((540, y), line, font=f_main, fill=title_color, anchor="mm")
        y += 96
    if sub:
        d2.text((540, y + 16), sub, font=font(40, 500), fill=GRAY, anchor="mm")
    if screen_fn:
        sx0, sy0, sx1 = phone_frame(d2)
        screen_fn(d2, sx0, sy0, sx1)
    footer(d2)
    img.save(os.path.join(OUTDIR, fname))
    print("saved:", fname)

slide("feature-7.png", ["対局履歴は、", "CSVで書き出せる"],
      sub="Excelで自分だけの集計表も作れる", screen_fn=screen_csv)
print("done")
