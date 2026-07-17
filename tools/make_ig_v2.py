# -*- coding: utf-8 -*-
# IGフィード画像 v2（1080x1350）: 実際の操作画面のスクリーンショットをスマホフレームに
# くっきり載せ、背景はブランドカラーのグラデーションで目を惹くデザイン。
# 白基調の従来シリーズ（make_ig_series.py）がプロフィールグリッドで沈むため、
# 「一目でアプリ紹介とわかる」濃色バージョンとして作成。
# 前提: tools/shoot_app_screens.py を先に実行して まじゃすこ素材/ig/shots/ を作っておく。
# 実行: python3 tools/make_ig_v2.py
import math
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "まじゃすこ素材", "ig", "shots")
OUTDIR = os.path.join(BASE, "まじゃすこ素材", "ig")
os.makedirs(OUTDIR, exist_ok=True)

# フォント: Windows（普段の作業PC）とLinux（リモート環境）の両対応
FONT = r"C:\Windows\Fonts\NotoSansJP-VF.ttf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"

W, H = 1080, 1350
GREEN = (23, 112, 131)
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
    """左上c0→右下c1の斜めグラデーション（小さく作ってから拡大）"""
    sw, sh = 108, 135
    img = Image.new("RGB", (sw, sh))
    px = img.load()
    for y in range(sh):
        for x in range(sw):
            t = (x / sw + y / sh) / 2
            px[x, y] = tuple(int(a + (b - a) * t) for a, b in zip(c0, c1))
    return img.resize((W, H), Image.BICUBIC)


def add_glow(img, cx, cy, radius, color, peak_alpha):
    """スマホの背後に置く円形の光（中心から外へフェード）"""
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
    """スクショの切り抜きを角丸＋影付きの浮遊カードとして貼る"""
    h = int(crop_im.height * width / crop_im.width)
    card = rounded(crop_im.resize((width, h), Image.LANCZOS), radius)
    drop_shadow(canvas, (x, y, x + width, y + h), radius, blur=18, alpha=120, dy=10)
    canvas.alpha_composite(card, (x, y))
    return h


def phone(canvas, shot, x_center, y0, screen_w, crop_top=0):
    """実スクショを載せたスマホ（下端は画面外へ抜ける）。crop_topでスクショ上部を切って見せ場を上に寄せる"""
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
    # ダイナミックアイランドは描かない（スクショはアプリヘッダーから始まるため、白い帯の上に浮いて見える）


def make(variant, fname):
    if variant == "vivid":  # 緑→青の斜めグラデーション（昼・ブランド色そのまま）
        bg = diagonal_gradient((17, 96, 116), BLUE_SANMA)
        glow_color, glow_alpha = (130, 212, 226), 95
    else:  # night: 濃紺ティール（夜・グロー強め）
        bg = diagonal_gradient((9, 42, 53), (24, 88, 118))
        glow_color, glow_alpha = (86, 196, 214), 120
    add_glow(bg, W // 2, 830, 520, glow_color, glow_alpha)
    canvas = bg.convert("RGBA")
    d = ImageDraw.Draw(canvas)

    # 装飾（文字の行末付近にスパークルを置かない: sns-ops落とし穴）
    sparkle(d, 92, 108, 30, (255, 255, 255, 160))
    sparkle(d, 1002, 505, 40, ORANGE)
    sparkle(d, 76, 620, 24, LIGHT_CYAN)
    sparkle(d, 1010, 1240, 26, (255, 255, 255, 150))
    d.ellipse([948, 138, 972, 162], fill=ORANGE)
    d.ellipse([130, 1180, 148, 1198], fill=(130, 212, 226))

    # 見出し
    d.text((W // 2, 165), "麻雀の集計、", font=font(88, 900), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 278), "まだ手でやってる？", font=font(88, 900), fill=(255, 255, 255), anchor="mm")
    d.text((W // 2, 383), "点数を入れるだけ。順位もグラフも自動で完成", font=font(37, 600), fill=LIGHT_CYAN, anchor="mm")

    # バッジ（半透明の白ピル）
    badges = ["登録不要", "完全無料", "インストール不要"]
    f_b = font(31, 700)
    widths = [d.textlength(b, font=f_b) + 56 for b in badges]
    bx = (W - sum(widths) - 2 * 20) / 2
    for b, bw in zip(badges, widths):
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle([bx, 438, bx + bw, 500], radius=31,
                                               fill=(255, 255, 255, 42), outline=(255, 255, 255, 220), width=3)
        canvas.alpha_composite(pill)
        d.text((bx + bw / 2, 469), b, font=f_b, fill=(255, 255, 255), anchor="mm")
        bx += bw + 20

    # スマホ（実画面スクショ）
    shot_top = Image.open(os.path.join(SHOTS, "shot-top.png")).convert("RGB")
    phone(canvas, shot_top, W // 2, 545, 460)

    # 浮遊カード: 1位の行（shot-top.pngから切り抜き）とスコア推移グラフ（shot-full.pngから）
    # 位置はスマホ内の重要情報（グループ名・プラスのスコア）を隠さないよう左下／右下寄りに置く
    row1 = shot_top.crop((95, 680, 1078, 878))
    floating_card(canvas, row1, 400, 30, 1108, radius=26)
    full = Image.open(os.path.join(SHOTS, "shot-full.png")).convert("RGB")
    graph = full.crop((38, 4230, 1132, 5155))
    floating_card(canvas, graph, 372, 666, 1000, radius=26)

    # フッター（majasco.jp表記はQA必須項目）
    d.text((56, 1292), "majasco.jp", font=font(38, 700), fill=(255, 255, 255, 230), anchor="lm")

    canvas.convert("RGB").save(os.path.join(OUTDIR, fname))
    print("saved:", fname)


make("vivid", "ig-v2-vivid.png")
make("night", "ig-v2-night.png")

# ==== v2シリーズ（機能紹介の再スタート枠。カバー=ig-v2-vivid.pngの後に3日おきで投稿） ====
# 各スライド: vividグラデーション背景＋見出し2行＋サブ＋実画面スマホ＋浮遊カード（要素スクショ）
SERIES = [
    # (ファイル名, 見出し1, 見出し2, サブ, スマホ画面, crop_top, 浮遊カード[(素材, 幅, x, y)])
    ("ig-v2-2-input.png", "点数を打つだけ、", "結果はその場で。", "ウマ・オカ込みのスコアを自動計算",
     "shot-sheet-edit.png", 0, [("el-row1.png", 420, 30, 1100)]),
    ("ig-v2-3-share.png", "URLを送るだけ、", "全員が同じスコア表。", "誰かが入力すれば、全員のスマホに反映",
     "shot-share.png", 430, [("el-row1.png", 400, 30, 1060), ("el-row2.png", 380, 666, 1160)]),
    # グラフ回はページ全体スクショから成績表後半〜グラフを切り出す（viewport版だと丈が足りず
    # スマホが下端まで届かない）
    ("ig-v2-4-graph.png", "昨夜の逆転劇が、", "グラフに残る。", "試合ごとのスコア推移を自動で記録",
     "shot-full.png", 3170, [("el-row1.png", 420, 30, 1108)]),
    ("ig-v2-5-team.png", "Mリーグ気分の、", "チーム戦モード。", "チーム合計も個人成績も自動で集計",
     "team-top.png", 0, [("el-team-chart.png", 380, 666, 1030)]),
    ("ig-v2-6-sanma.png", "三麻派も、", "いつものルールで。", "持ち点・返し点・ウマは自由に設定OK",
     "sanma-top.png", 0, [("el-sanma-row1.png", 420, 30, 1108)]),
    ("ig-v2-7-options.png", "焼き鳥もチョンボも、", "ワンタップで記録。", "チップの増減まで収支に自動反映",
     "chips-sheet.png", 0, [("el-chips-row1.png", 420, 30, 1108)]),
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
