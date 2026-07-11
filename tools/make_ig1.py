# -*- coding: utf-8 -*-
# Instagram初投稿用 1080x1080（OGP/Xヘッダーと同じトーン）
import os, math
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # リポジトリルート
OUT = os.path.join(BASE, "まじゃすこ素材", "instagram-post1.png")
FONT = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"
EMOJI = r"C:\Windows\Fonts\seguiemj.ttf"

GREEN = (23, 112, 131)
ORANGE = (231, 86, 32)
DARK = (31, 42, 40)
GRAY = (85, 99, 95)
BORDER = (226, 236, 231)
BLUE = (26, 35, 126)
RED = (198, 40, 40)

def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

W = H = 1080
img = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(img)

# 淡い光の円（スマホの背面）
d.ellipse([540 - 340, 760 - 340, 540 + 340, 760 + 340], fill=(238, 248, 243))

# キラキラ
def sparkle(x, y, R, color):
    rr = R * 0.22
    pts = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rad = R if i % 2 == 0 else rr
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
    d.polygon(pts, fill=color)
sparkle(860, 470, 44, ORANGE)
sparkle(215, 520, 30, GREEN)
sparkle(890, 950, 30, GREEN)
d.ellipse([910, 395, 934, 419], fill=ORANGE)
d.ellipse([185, 660, 203, 678], fill=(159, 195, 189))

# ロゴ（上部中央）
logo = Image.open(os.path.join(BASE, "assets", "logo.png")).convert("RGBA")
lh = 96
lw = int(logo.width * lh / logo.height)
logo = logo.resize((lw, lh), Image.LANCZOS)
img.paste(logo, ((W - lw) // 2, 52), logo)

# メインコピー（中央揃え・Noto Sans JP Black・緑）
f_main = font(76, 900)
d.text((540, 232), "麻雀のスコア記録、", font=f_main, fill=GREEN, anchor="mm")
d.text((540, 336), "まだ手書きでやってますか？", font=f_main, fill=GREEN, anchor="mm")

# サブ（登録不要・無料はオレンジ強調）
f_sub_b = font(42, 800)
f_sub = font(42, 500)
seg1 = "登録不要・無料"
seg2 = "｜スコアは全員のスマホに共有"
total = d.textlength(seg1, font=f_sub_b) + d.textlength(seg2, font=f_sub)
x = (W - total) / 2
d.text((x, 428), seg1, font=f_sub_b, fill=ORANGE, anchor="lm")
d.text((x + d.textlength(seg1, font=f_sub_b), 428), seg2, font=f_sub, fill=GRAY, anchor="lm")

# スマホ（下端で見切れる・スコア収支画面）
px0, py0, px1 = 352, 500, 728  # 幅376
d.rounded_rectangle([px0, py0, px1, H + 160], radius=58, fill=DARK)
d.rounded_rectangle([px0 + 15, py0 + 15, px1 - 15, H + 160], radius=44, fill=(255, 255, 255))
d.rounded_rectangle([488, 532, 592, 556], radius=12, fill=DARK)  # ダイナミックアイランド

d.text((540, 610), "スコア収支", font=font(38, 800), fill=GREEN, anchor="mm")

rows = [("太郎", "+55.0", BLUE, "\U0001F947"), ("次郎", "+8.0", BLUE, "\U0001F948"),
        ("三郎", "-18.0", RED, "\U0001F949"), ("四郎", "-45.0", RED, None)]
f_name = font(31, 700)
f_val = font(31, 800)
f_emoji = ImageFont.truetype(EMOJI, 38)
y = 652
for name, val, vc, medal in rows:
    d.rounded_rectangle([394, y, 686, y + 74], radius=16, fill=(255, 255, 255), outline=BORDER, width=3)
    if medal:
        d.text((414, y + 37), medal, font=f_emoji, embedded_color=True, anchor="lm")
    d.text((472, y + 37), name, font=f_name, fill=(26, 26, 26), anchor="lm")
    d.text((664, y + 37), val, font=f_val, fill=vc, anchor="rm")
    y += 94

# グラフ（下端で見切れる）
d.rounded_rectangle([394, 1032, 686, 1180], radius=16, fill=(246, 250, 249), outline=BORDER, width=3)
pts = [(420, 1074), (472, 1050), (524, 1062), (576, 1042), (628, 1056), (664, 1038)]
d.line(pts, fill=GREEN, width=8, joint="curve")
for p2 in pts:
    d.ellipse([p2[0] - 7, p2[1] - 7, p2[0] + 7, p2[1] + 7], fill=GREEN)

# 左下: ドメイン
d.text((60, 1020), "majasco.jp", font=font(34, 700), fill=(154, 168, 164), anchor="lm")

img.save(OUT)
print("saved:", OUT, img.size)
