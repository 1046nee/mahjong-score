# -*- coding: utf-8 -*-
# OGP画像ドラフト生成（2100x1103・ヒーローと同じトーン）
# メイン: 麻雀のスコア記録、まだ手書きでやってますか？ / サブ: 登録不要・無料｜URLひとつで全員のスマホに共有
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # リポジトリルート
OUT = os.path.join(BASE, "まじゃすこ素材", "ogp2-draft.png")
FONT = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"

GREEN = (23, 112, 131)      # #177083
ORANGE = (231, 86, 32)      # #E75620
LIGHT = (228, 243, 236)     # #E4F3EC
DARK = (31, 42, 40)         # #1f2a28
GRAY = (85, 99, 95)
BORDER = (226, 236, 231)    # #e2ece7
BLUE = (26, 35, 126)        # #1a237e
RED = (198, 40, 40)         # #c62828

def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

W, H = 2100, 1103
img = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(img)

# ---- 右: 淡い光の円 ----
cx, cy, r = 1735, 555, 430
d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(238, 248, 243))

# ---- キラキラ（4方向に尖った星） ----
def sparkle(x, y, R, color):
    rr = R * 0.22
    pts = []
    import math
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rad = R if i % 2 == 0 else rr
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
    d.polygon(pts, fill=color)
sparkle(2010, 150, 52, ORANGE)
sparkle(1430, 190, 34, GREEN)
sparkle(2010, 900, 34, GREEN)
d.ellipse([1925, 60, 1955, 90], fill=ORANGE)
d.ellipse([1395, 330, 1417, 352], fill=(159, 195, 189))

# ---- 右: スマホ（スコア画面） ----
px0, py0, px1, py1 = 1525, 110, 1985, 1000  # 460x890 ≒ 1:1.93
d.rounded_rectangle([px0, py0, px1, py1], radius=72, fill=DARK)
d.rounded_rectangle([px0 + 18, py0 + 18, px1 - 18, py1 - 18], radius=54, fill=(255, 255, 255))
d.rounded_rectangle([1691, 148, 1819, 178], radius=15, fill=DARK)  # ダイナミックアイランド

f_title = font(46, 800)
d.text((1755, 240), "スコア収支", font=f_title, fill=GREEN, anchor="mm")

rows = [("太郎", "+55.0", BLUE, "🥇"), ("次郎", "+8.0", BLUE, "🥈"),
        ("三郎", "-18.0", RED, "🥉"), ("四郎", "-45.0", RED, None)]
f_name = font(38, 700)
f_val = font(38, 800)
f_emoji = ImageFont.truetype(r"C:\Windows\Fonts\seguiemj.ttf", 48)
y = 300
for name, val, vc, medal in rows:
    d.rounded_rectangle([1577, y, 1933, y + 92], radius=20, fill=(255, 255, 255), outline=BORDER, width=4)
    if medal:
        d.text((1602, y + 46), medal, font=f_emoji, embedded_color=True, anchor="lm")
    d.text((1673, y + 46), name, font=f_name, fill=(26, 26, 26), anchor="lm")
    d.text((1909, y + 46), val, font=f_val, fill=vc, anchor="rm")
    y += 118

# グラフ
d.rounded_rectangle([1577, 790, 1933, 950], radius=20, fill=(246, 250, 249), outline=BORDER, width=4)
pts = [(1610, 915), (1675, 860), (1737, 885), (1800, 830), (1860, 862), (1905, 815)]
d.line(pts, fill=GREEN, width=10, joint="curve")
for p in pts:
    d.ellipse([p[0] - 9, p[1] - 9, p[0] + 9, p[1] + 9], fill=GREEN)

# ---- 左: ロゴ ----
logo = Image.open(os.path.join(BASE, "assets", "logo.png")).convert("RGBA")
lh = 150
lw = int(logo.width * lh / logo.height)
logo = logo.resize((lw, lh), Image.LANCZOS)
img.paste(logo, (92, 84), logo)

# ---- 左: メインコピー（Noto Sans JP Black＝ヒーローh1と同等） ----
f_main = font(103, 900)
d.text((104, 405), "麻雀のスコア記録、", font=f_main, fill=GREEN, anchor="lm")
d.text((104, 555), "まだ手書きでやってますか？", font=f_main, fill=GREEN, anchor="lm")

# ---- 左: サブ ----
f_sub_b = font(56, 800)
f_sub = font(56, 500)
x = 106
seg1 = "登録不要・無料"
d.text((x, 742), seg1, font=f_sub_b, fill=ORANGE, anchor="lm")
x += d.textlength(seg1, font=f_sub_b)
d.text((x, 742), "｜URLひとつで全員のスマホに共有", font=f_sub, fill=GRAY, anchor="lm")

# ---- 左下: ドメイン ----
d.text((106, 990), "majasco.jp", font=font(44, 700), fill=(154, 168, 164), anchor="lm")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT)
print("saved:", OUT, img.size)
