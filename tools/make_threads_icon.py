# Threads/IG @munii_dev プロフィールアイコン 3案（1080x1080・円形クロップ前提）
# 円形セーフゾーン: 中心から半径~470px以内に要素を収める
import os
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, 'まじゃすこ素材', 'threads')
os.makedirs(OUT, exist_ok=True)

GREEN = (23, 112, 131)
ORANGE = (231, 86, 32)
DARK = (31, 42, 40)
PALE = (228, 243, 236)
WHITE = (255, 255, 255)

def jp(size, weight=900):
    f = ImageFont.truetype(r'C:\Windows\Fonts\NotoSansJP-VF.ttf', size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f

def sparkle(d, cx, cy, R, color):
    # 4方向に尖ったキラキラ（waist ≈ R*0.22）
    w = R * 0.22
    pts = [(cx, cy - R), (cx + w, cy - w), (cx + R, cy), (cx + w, cy + w),
           (cx, cy + R), (cx - w, cy + w), (cx - R, cy), (cx - w, cy - w)]
    d.polygon(pts, fill=color)

def text_wh(d, s, f):
    b = d.textbbox((0, 0), s, font=f)
    return b[2] - b[0], b[3] - b[1], b

# ---- A: ターミナル風（ダーク背景・緑の「>」＋白「む」＋オレンジのカーソル） ----
img = Image.new('RGB', (1080, 1080), DARK)
d = ImageDraw.Draw(img)
f_mu = jp(500)
f_gt = jp(300)
w_gt, h_gt, _ = text_wh(d, '>', f_gt)
w_mu, h_mu, bb = text_wh(d, 'む', f_mu)
cur_w, cur_h = 60, 340
gap = 40
total = w_gt + gap + w_mu + gap + cur_w
x = (1080 - total) / 2
cy = 540
d.text((x - 10, cy - h_gt / 2 - 40), '>', font=f_gt, fill=GREEN)
d.text((x + w_gt + gap - bb[0], cy - h_mu / 2 - bb[1]), 'む', font=f_mu, fill=WHITE)
d.rectangle([x + w_gt + gap + w_mu + gap, cy - cur_h / 2 + 60,
             x + w_gt + gap + w_mu + gap + cur_w, cy + cur_h / 2 + 60], fill=ORANGE)
sparkle(d, 790, 260, 54, GREEN)
img.save(os.path.join(OUT, 'icon-a-terminal.png'))

# ---- B: ブランド緑背景＋白「む」＋オレンジ✨ ----
img = Image.new('RGB', (1080, 1080), GREEN)
d = ImageDraw.Draw(img)
f_mu = jp(600)
w_mu, h_mu, bb = text_wh(d, 'む', f_mu)
d.text(((1080 - w_mu) / 2 - bb[0], 540 - h_mu / 2 - bb[1]), 'む', font=f_mu, fill=WHITE)
sparkle(d, 795, 300, 62, ORANGE)
sparkle(d, 300, 800, 38, (159, 195, 189))
img.save(os.path.join(OUT, 'icon-b-green.png'))

# ---- C: 淡緑背景＋緑「む」＋オレンジ✨（やわらかトーン） ----
img = Image.new('RGB', (1080, 1080), PALE)
d = ImageDraw.Draw(img)
f_mu = jp(600)
w_mu, h_mu, bb = text_wh(d, 'む', f_mu)
d.text(((1080 - w_mu) / 2 - bb[0], 540 - h_mu / 2 - bb[1]), 'む', font=f_mu, fill=GREEN)
sparkle(d, 795, 300, 62, ORANGE)
sparkle(d, 300, 800, 38, (159, 195, 189))
img.save(os.path.join(OUT, 'icon-c-pale.png'))

print('done:', OUT)
