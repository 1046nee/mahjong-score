# -*- coding: utf-8 -*-
# IGフィード画像 v2 の追加3枚（2026-10 の新機能: 仲間ページ・マイページ・記録の確定）。1080x1350
# make_ig_v2.py と同じデザイン（緑→青のグラデーション＋見出し2行＋実画面スマホ＋浮遊カード）。
# 前提: tools/shoot_feature_screens.py で まじゃすこ素材/ig/shots/oct-*.png を作っておく。
# 実行: python tools/make_ig_v2_oct.py
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "まじゃすこ素材", "ig", "shots")
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig")
FONT = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"
W, H = 1080, 1350
BLUE_SANMA = (66, 97, 170)
ORANGE = (231, 86, 32)
LIGHT_CYAN = (219, 244, 249)
BEZEL = (20, 26, 30)


def font(size, weight):
    f = ImageFont.truetype(FONT, size)
    try:
        f.set_variation_by_axes([weight])
    except Exception:
        pass
    return f


def sparkle(d, x, y, R, color):
    rr = R * 0.22
    pts = [(x + (R if i % 2 == 0 else rr) * math.cos(math.radians(i * 45 - 90)), y + (R if i % 2 == 0 else rr) * math.sin(math.radians(i * 45 - 90))) for i in range(8)]
    d.polygon(pts, fill=color)


def diagonal_gradient(c0, c1):
    sw, sh = 108, 135
    img = Image.new("RGB", (sw, sh))
    px = img.load()
    for y in range(sh):
        for x in range(sw):
            t = (x / sw + y / sh) / 2
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
    return img.resize((W, H), Image.BICUBIC)


def add_glow(img, cx, cy, radius, color, peak_alpha):
    glow = Image.new("L", (W, H), 0)
    gd = ImageDraw.Draw(glow)
    for i in range(40, 0, -1):
        r = radius * i / 40
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=int(peak_alpha * (1 - i / 40) ** 1.5))
    img.paste(Image.new("RGB", (W, H), color), (0, 0), glow)


def rounded(im, radius):
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.size[0], im.size[1]], radius=radius, fill=255)
    im = im.convert("RGBA")
    im.putalpha(mask)
    return im


def drop_shadow(canvas, box, radius, blur=22, alpha=110, dy=14):
    x0, y0, x1, y1 = box
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(sh).rounded_rectangle([x0, y0 + dy, x1, y1 + dy], radius=radius, fill=(0, 0, 0, alpha))
    canvas.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))


def floating_card(canvas, im, width, x, y, radius=26):
    h = int(im.height * width / im.width)
    card = rounded(im.resize((width, h), Image.LANCZOS), radius)
    drop_shadow(canvas, (x, y, x + width, y + h), radius, blur=18, alpha=120, dy=10)
    canvas.alpha_composite(card, (x, y))


def phone(canvas, shot, x_center, y0, screen_w):
    screen_h = int(shot.height * screen_w / shot.width)
    bez = 16
    px0, px1 = x_center - screen_w // 2 - bez, x_center + screen_w // 2 + bez
    drop_shadow(canvas, (px0, y0, px1, min(H, y0 + screen_h + bez)), 66, blur=34, alpha=150, dy=18)
    ImageDraw.Draw(canvas).rounded_rectangle([px0, y0, px1, y0 + screen_h + 2 * bez], radius=66, fill=BEZEL)
    # スマホの画面は白地（要素のスクショは角が透けないよう白で埋める）
    bg = Image.new("RGB", (shot.width, shot.height), (255, 255, 255))
    bg.paste(shot, (0, 0))
    canvas.alpha_composite(rounded(bg.resize((screen_w, screen_h), Image.LANCZOS), 48), (px0 + bez, y0 + bez))


SLIDES = [
    # (ファイル名, 見出し1, 見出し2, 見出しの大きさ, サブ, スマホ画面, 浮遊カード[(素材, 幅, x, y)])
    ("ig-v2-8-nakama.png", "定例会の通算順位が、", "自動で出る。", 78, "仲間ページで、メンバー全員が同じ順位を見られる",
     "oct-circle-rank.png", [("oct-matchup-vs.png", 470, 30, 1105)]),
    ("ig-v2-9-mypage.png", "自分の成績が、", "ずっと残る。", 88, "Googleログインで、平均着順もスコアの推移も",
     "oct-mypage-card.png", [("oct-spark-pop-c.png", 370, 680, 940)]),
    ("ig-v2-10-kakutei.png", "終わった結果は、", "あとから変えられない。", 80, "対局の終了から12時間で、記録が確定",
     "oct-result-sheet.png", []),
]


def slide(fname, hl1, hl2, hsize, sub, shot_name, floats):
    bg = diagonal_gradient((17, 96, 116), BLUE_SANMA)
    add_glow(bg, W // 2, 830, 520, (130, 212, 226), 95)
    canvas = bg.convert("RGBA")
    d = ImageDraw.Draw(canvas)
    sparkle(d, 92, 108, 30, (255, 255, 255, 160))
    sparkle(d, 1002, 470, 40, ORANGE)
    sparkle(d, 76, 600, 24, LIGHT_CYAN)
    d.ellipse([948, 138, 972, 162], fill=ORANGE)
    d.text((W // 2, 165), hl1, font=font(hsize, 900), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 278), hl2, font=font(hsize, 900), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 383), sub, font=font(37, 600), fill=LIGHT_CYAN, anchor="mm")
    shot = Image.open(os.path.join(SHOTS, shot_name)).convert("RGB")
    phone(canvas, shot, W // 2, 470, 470)
    for src, fw, fx, fy in floats:
        floating_card(canvas, Image.open(os.path.join(SHOTS, src)).convert("RGB"), fw, fx, fy)
    d.text((56, 1292), "majasco.jp", font=font(38, 700), fill=(255, 255, 255, 230), anchor="lm")
    canvas.convert("RGB").save(os.path.join(OUTDIR, fname))
    print("saved:", fname)


for s in SLIDES:
    slide(*s)
