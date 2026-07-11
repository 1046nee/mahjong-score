# -*- coding: utf-8 -*-
# X（Twitter）ヘッダー画像 1500x500。OGPと同じトーン。
# 左下（プロフィールアイコンが重なる領域）と上下60px（端末トリミング）を避けて配置
import os, math
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # リポジトリルート
OUT = os.path.join(BASE, "まじゃすこ素材", "x-header-draft.png")
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

W, H = 1500, 500
img = Image.new("RGB", (W, H), (255, 255, 255))
d = ImageDraw.Draw(img)

# ---- 右: 淡い光の円 ----
d.ellipse([1190 - 300, 250 - 300, 1190 + 300, 250 + 300], fill=(238, 248, 243))

# ---- キラキラ ----
def sparkle(x, y, R, color):
    rr = R * 0.22
    pts = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rad = R if i % 2 == 0 else rr
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
    d.polygon(pts, fill=color)
sparkle(1428, 112, 38, ORANGE)
sparkle(965, 120, 24, GREEN)
sparkle(1438, 398, 24, GREEN)
d.ellipse([1372, 72, 1392, 92], fill=ORANGE)
d.ellipse([940, 300, 956, 316], fill=(159, 195, 189))

# ---- 右: スマホ（下は画面外へ続く） ----
px0, py0, px1 = 1030, 72, 1360  # 幅330。高さは画面外まで
d.rounded_rectangle([px0, py0, px1, H + 120], radius=52, fill=DARK)
d.rounded_rectangle([px0 + 14, py0 + 14, px1 - 14, H + 120], radius=40, fill=(255, 255, 255))
d.rounded_rectangle([1148, 100, 1242, 122], radius=11, fill=DARK)  # ダイナミックアイランド

d.text((1195, 168), "スコア収支", font=font(34, 800), fill=GREEN, anchor="mm")

rows = [("太郎", "+55.0", BLUE, "\U0001F947"), ("次郎", "+8.0", BLUE, "\U0001F948"),
        ("三郎", "-18.0", RED, "\U0001F949"), ("四郎", "-45.0", RED, None)]
f_name = font(28, 700)
f_val = font(28, 800)
f_emoji = ImageFont.truetype(EMOJI, 34)
y = 208
for name, val, vc, medal in rows:
    d.rounded_rectangle([1068, y, 1322, y + 66], radius=14, fill=(255, 255, 255), outline=BORDER, width=3)
    if medal:
        d.text((1086, y + 33), medal, font=f_emoji, embedded_color=True, anchor="lm")
    d.text((1138, y + 33), name, font=f_name, fill=(26, 26, 26), anchor="lm")
    d.text((1304, y + 33), val, font=f_val, fill=vc, anchor="rm")
    y += 84

# ---- 左: メインコピー（上下トリミング安全域 y90〜410 内） ----
f_main = font(66, 900)
d.text((100, 158), "麻雀のスコア記録、", font=f_main, fill=GREEN, anchor="lm")
d.text((100, 252), "まだ手書きでやってますか？", font=f_main, fill=GREEN, anchor="lm")

# ---- 左: サブ（アイコンが重なる左下を避けて y345 まで） ----
f_sub_b = font(35, 800)
f_sub = font(35, 500)
x = 102
seg1 = "登録不要・無料"
d.text((x, 345), seg1, font=f_sub_b, fill=ORANGE, anchor="lm")
x += d.textlength(seg1, font=f_sub_b)
d.text((x, 345), "｜URLひとつで全員のスマホに共有", font=f_sub, fill=GRAY, anchor="lm")

# ---- 左上: ドメイン ----
d.text((102, 84), "majasco.jp", font=font(28, 700), fill=(154, 168, 164), anchor="lm")

img.save(OUT)
print("saved:", OUT, img.size)
