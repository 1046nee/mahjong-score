# -*- coding: utf-8 -*-
# 機能紹介 feature-8「機種変更しても、履歴を引き継げる」1080x1350（縦5:横4）。
# make_ig_feature7.py と同じ共通ヘルパー構成の単発生成
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

# ==== 2台のスマホ（旧→新）と、間をつなぐ矢印＋カギ ====
# feature-7のphone_frame（中央1台）ではなく、引き継ぎが一目で伝わる横並び構成にする
def draw_phone(d, x0, y0, x1, y1, screen_fill=(255, 255, 255)):
    d.rounded_rectangle([x0, y0, x1, y1], radius=44, fill=DARK)
    d.rounded_rectangle([x0 + 12, y0 + 12, x1 - 12, y1 - 12], radius=34, fill=screen_fill)
    cx = (x0 + x1) // 2
    d.rounded_rectangle([cx - 38, y0 + 24, cx + 38, y0 + 42], radius=9, fill=DARK)
    return (x0 + 12, y0 + 12, x1 - 12, y1 - 12)

def mini_history(d, sx0, sy0, sx1, title, rows, faded=False):
    cx = (sx0 + sx1) // 2
    tcol = LGRAY if faded else (26, 26, 26)
    d.text((cx, sy0 + 64), title, font=font(26, 800), fill=tcol, anchor="mm")
    y = sy0 + 96
    for name, sub in rows:
        d.rounded_rectangle([sx0 + 18, y, sx1 - 18, y + 74], radius=12,
                            fill=FAINT if not faded else (250, 250, 250),
                            outline=BORDER, width=2)
        ncol = LGRAY if faded else (26, 26, 26)
        scol = LGRAY
        d.text((sx0 + 34, y + 26), name, font=font(24, 700), fill=ncol, anchor="lm")
        d.text((sx0 + 34, y + 54), sub, font=font(18, 500), fill=scol, anchor="lm")
        y += 90

ROWS = [("金曜メンバー", "計36試合 · 四麻"),
        ("大学サークル", "計102試合 · チーム戦"),
        ("正月の親戚卓", "計12試合 · 三麻"),
        ("会社の同期会", "計58試合 · 四麻")]

def draw_key(d, cx, cy, color):
    # 右向きのカギ（絵文字は使わずPILの図形で描く: リング＋軸＋歯2本）
    d.ellipse([cx - 44, cy - 20, cx - 4, cy + 20], outline=color, width=9)
    d.line([cx + 2, cy, cx + 62, cy], fill=color, width=9)
    d.line([cx + 34, cy, cx + 34, cy + 17], fill=color, width=8)
    d.line([cx + 54, cy, cx + 54, cy + 19], fill=color, width=8)

def screen_transfer(d):
    # 左=これまでのスマホ / 右=新しいスマホ。同じ履歴が引き継がれている
    top = 615
    bottom = 1155
    draw_phone(d, 100, top, 470, bottom)
    draw_phone(d, 610, top, 980, bottom)
    mini_history(d, 112, top + 12, 458, "これまでのスマホ", ROWS)
    mini_history(d, 622, top + 12, 968, "新しいスマホ", ROWS)
    # 間のカギと矢印
    cx = 540
    draw_key(d, cx - 9, 862, GREEN)
    ay = 950
    d.line([492, ay, 574, ay], fill=ORANGE, width=10)
    d.polygon([(566, ay - 18), (596, ay), (566, ay + 18)], fill=ORANGE)
    d.text((cx, 1014), "URLを", font=font(26, 700), fill=GRAY, anchor="mm")
    d.text((cx, 1050), "開くだけ", font=font(26, 700), fill=GRAY, anchor="mm")

img, d = new_canvas()
logo_top(img)
d2 = ImageDraw.Draw(img)
y = 244
f_main = font(70, 900)
for line in ["機種変更しても、", "履歴を引き継げる"]:
    d2.text((540, y), line, font=f_main, fill=GREEN, anchor="mm")
    y += 96
d2.text((540, y + 16), "会員登録なし。引き継ぎURLを開くだけ", font=font(40, 500), fill=GRAY, anchor="mm")
screen_transfer(d2)
footer(d2)
img.save(os.path.join(OUTDIR, "feature-8.png"))
print("saved: feature-8.png")
