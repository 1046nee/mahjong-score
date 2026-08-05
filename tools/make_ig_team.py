# -*- coding: utf-8 -*-
# IGフィード画像「チーム戦Week」7枚（1080x1350）: make_ig_v2.py のデザイン言語を継承
# （vividグラデーション＋実画面スマホ＋浮遊カード）。お盆前後のチーム戦訴求週間用。
# 実行: python tools/make_ig_team.py（出力: まじゃすこ素材/ig/team-wk-*.png）
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "まじゃすこ素材", "ig", "shots")
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig")
os.makedirs(OUTDIR, exist_ok=True)

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
    pts = []
    for i in range(8):
        ang = math.radians(i * 45 - 90)
        rad = R if i % 2 == 0 else rr
        pts.append((x + rad * math.cos(ang), y + rad * math.sin(ang)))
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
    steps = 40
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(peak_alpha * (1 - i / steps) ** 1.5)
        gd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=a)
    layer = Image.new("RGB", (W, H), color)
    img.paste(layer, (0, 0), glow)


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


def floating_card(canvas, crop_im, width, x, y, radius=22):
    h = int(crop_im.height * width / crop_im.width)
    card = rounded(crop_im.resize((width, h), Image.LANCZOS), radius)
    drop_shadow(canvas, (x, y, x + width, y + h), radius, blur=18, alpha=120, dy=10)
    canvas.alpha_composite(card, (x, y))
    return h


def phone(canvas, shot, x_center, y0, screen_w, crop_top=0):
    if crop_top:
        shot = shot.crop((0, crop_top, shot.width, shot.height))
    screen_h = int(shot.height * screen_w / shot.width)
    bez = 16
    px0 = x_center - screen_w // 2 - bez
    px1 = x_center + screen_w // 2 + bez
    drop_shadow(canvas, (px0, y0, px1, min(H, y0 + screen_h + bez)), 66, blur=34, alpha=150, dy=18)
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle([px0, y0, px1, y0 + screen_h + 2 * bez], radius=66, fill=BEZEL)
    scr = rounded(shot.resize((screen_w, screen_h), Image.LANCZOS), 48)
    canvas.alpha_composite(scr, (px0 + bez, y0 + bez))


# (ファイル名, 見出し1, 見出し2, サブ, スマホ画面, crop_top, 浮遊カード[(素材, 幅, x, y)])
SERIES = [
    ("team-wk-1-cover.png", "お盆は、みんなで", "チーム戦。", "Mリーグ気分の対抗戦。集計は全部おまかせ",
     "team-top.png", 0, [("el-team-chart.png", 380, 666, 1030)]),
    ("team-wk-2-total.png", "チームの合計で、", "勝負が決まる。", "個人スコアを自動で合算、チーム順位もその場で",
     "team-top.png", 330, [("el-team.png", 360, 690, 1050)]),
    ("team-wk-3-color.png", "誰がどのチーム？", "色でわかる。", "成績表もグラフもチームカラーで色分け",
     "team-top.png", 205, [("el-team-chart.png", 372, 666, 1050)]),
    ("team-wk-4-40players.png", "最大40人、", "回し打ちOK。", "試合ごとに打つメンバーを選ぶだけ。抜け番も自動集計",
     "shot-top.png", 0, [("el-row1.png", 420, 30, 1100)]),
    ("team-wk-5-graph.png", "追い上げが、", "グラフでバレる。", "チームスコア推移を試合ごとに自動記録",
     "team-top.png", 420, [("el-team-chart.png", 372, 30, 960)]),
    ("team-wk-6-ufo.png", "役満を出したら、", "カップ焼きそば。", "うちのチーム戦の名物ルール。景品はアイデア次第",
     "team-top.png", 0, [("el-team.png", 380, 666, 1060)]),
    ("team-wk-7-article.png", "10人集まる日の、", "教科書できました。", "チーム対抗戦・トーナメントの開き方をブログで公開中",
     "shot-top.png", 0, [("el-graph.png", 372, 666, 1000)]),
]


def series_slide(fname, hl1, hl2, sub, shot_name, crop_top, floats):
    bg = diagonal_gradient((17, 96, 116), BLUE_SANMA)
    add_glow(bg, W // 2, 830, 520, (130, 212, 226), 95)
    canvas = bg.convert("RGBA")
    d = ImageDraw.Draw(canvas)

    sparkle(d, 92, 108, 30, (255, 255, 255, 160))
    sparkle(d, 1002, 470, 40, ORANGE)
    sparkle(d, 76, 600, 24, LIGHT_CYAN)
    sparkle(d, 1010, 1240, 26, (255, 255, 255, 150))
    d.ellipse([948, 138, 972, 162], fill=ORANGE)
    d.ellipse([130, 1000, 148, 1018], fill=(130, 212, 226))

    d.text((W // 2, 165), hl1, font=font(88, 900), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 278), hl2, font=font(88, 900), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 383), sub, font=font(37, 600), fill=LIGHT_CYAN, anchor="mm")

    shot = Image.open(os.path.join(SHOTS, shot_name)).convert("RGB")
    phone(canvas, shot, W // 2, 470, 460, crop_top=crop_top)

    for src, fw, fx, fy in floats:
        fim = Image.open(os.path.join(SHOTS, src)).convert("RGB")
        floating_card(canvas, fim, fw, fx, fy, radius=26)

    d.text((56, 1292), "majasco.jp", font=font(38, 700), fill=(255, 255, 255, 230), anchor="lm")
    canvas.convert("RGB").save(os.path.join(OUTDIR, fname))
    print("saved:", fname)


for slide_def in SERIES:
    series_slide(*slide_def)
print("done")
