# -*- coding: utf-8 -*-
"""scene.py --anim が書き出したコマ（f0000.png〜）に、手順の表示をのせて mp4 にする。
  python tools/b3d/make_clip.py <コマのフォルダ> <出力.mp4> [--fps 12] [--script chi]
のせるもの（2026-11-12 ユーザーの依頼「動き・テロップ・順番を分かりやすく指し示す表示」）:
  1. 上の帯＝手順の番号の列（済み＝緑・今＝オレンジで大きく・これから＝白い輪）。いま全体のどこかが分かる
  2. 見出し＝「② 開示」＋ひとことの説明（かな書きの読みつき）
  3. 印＝その手順で動く牌を、番号つきの輪で囲む（位置は scene.py --marks の marks.json から）
  4. 手順が終わるたびに絵を止める（hold）。止めている間に説明を読める。あとで声をのせる長さにもなる
  5. 最後に、手順の一覧のカード
字は Noto Sans JP（Windows は C:/Windows/Fonts/NotoSansJP-VF.ttf）。ffmpeg は PATH のもの、無ければ imageio-ffmpeg。
"""
import glob, json, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

FONTS = ["C:/Windows/Fonts/NotoSansJP-VF.ttf", "/usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"]
GREEN, ORANGE, INK, WHITE = "#177083", "#E75620", "#1F2A28", "#FFFFFF"
W, H = 1080, 1920
NUM = "①②③④⑤⑥⑦⑧"

# 台本: 手順ごとに (名前, 読み, 説明, 最初のコマ, 最後のコマ, 止める秒, 囲む牌, 吹き出し)。コマは scene.py の anim_pose の区切り（12fps）
SCRIPTS = {
    "chi": dict(title="チーの手順", steps=[
        ("発声", "はっせい", "「チー」と声に出す。ポンが優先なので一拍おいてから", 0, 6, 2.2, [], "チー"),     # 肩ごしで顔が見えるうちに止める（カメラが動き出す前）
        ("開示", "かいじ", "鳴くのに使うターツを倒して、みんなに見せる", 7, 31, 1.6, ["m4", "m5"], ""),          # 止める所は、手がどいて真上から寄ったコマ
        ("回収", "かいしゅう", "他家（ターチャ）が切った牌を取ってくる", 32, 61, 1.4, ["m6"], ""),
        ("副露", "フーロ", "取った牌を横向きにして付け、卓の右に寄せる", 62, 84, 1.6, ["m6", "m4", "m5"], ""),
        ("打牌", "ダハイ", "手牌からいらない牌を1枚切る", 85, 105, 1.4, ["s3"], ""),
    ], tail=(106, 120, 2.4)),
}

_fc = {}
def font(size, wght=900):
    k = (size, wght)
    if k in _fc: return _fc[k]
    for f in FONTS:
        if os.path.exists(f):
            ft = ImageFont.truetype(f, size)
            try: ft.set_variation_by_axes([wght])
            except Exception: pass
            _fc[k] = ft; return ft
    raise SystemExit("Noto Sans JP が見つからない: " + " / ".join(FONTS))

def text_c(d, cx, cy, tx, ft, fill, stroke=None, sw=0):
    l, t, r, b = d.textbbox((0, 0), tx, font=ft, stroke_width=sw)
    d.text((cx - (r - l) / 2 - l, cy - (b - t) / 2 - t), tx, font=ft, fill=fill, stroke_width=sw, stroke_fill=stroke)

def rail(d, steps, cur, done_all=False):
    """上の帯。番号の丸を線でつなぐ。cur=今の手順（0始まり）"""
    n = len(steps); x0, x1, y = 130, W - 130, 150
    d.rounded_rectangle((40, 60, W - 40, 290), radius=48, fill=(12, 20, 22, 205))
    for i in range(n - 1):
        xa = x0 + (x1 - x0) * i / (n - 1); xb = x0 + (x1 - x0) * (i + 1) / (n - 1)
        d.line((xa, y, xb, y), fill=GREEN if (i < cur or done_all) else (255, 255, 255, 90), width=8)
    for i, s in enumerate(steps):
        x = x0 + (x1 - x0) * i / (n - 1)
        now = (i == cur and not done_all); done = i < cur or done_all
        r = 52 if now else 38
        if now: d.ellipse((x - r - 8, y - r - 8, x + r + 8, y + r + 8), fill=(231, 86, 32, 90))
        d.ellipse((x - r, y - r, x + r, y + r), fill=ORANGE if now else (GREEN if done else (12, 20, 22, 255)), outline=WHITE if not (now or done) else None, width=4)
        text_c(d, x, y - 2, str(i + 1), font(60 if now else 42), WHITE)
        text_c(d, x, y + 92, s[0], font(40 if now else 34, 900 if now else 700), WHITE if (now or done) else (255, 255, 255, 150))

def headline(d, i, s, k):
    """見出しと説明。k=出てからの進み（0〜1）で少し下から入る"""
    dy = int((1 - min(1, k * 4)) * 30)
    y = 330 + dy
    d.rounded_rectangle((40, y, W - 40, y + 250), radius=44, fill=(255, 255, 255, 240))
    d.ellipse((76, y + 34, 76 + 104, y + 34 + 104), fill=ORANGE)
    text_c(d, 76 + 52, y + 34 + 50, str(i + 1), font(72), WHITE)
    d.text((204, y + 22), s[0], font=font(88), fill=INK)
    l, t, r, b = d.textbbox((204, y + 22), s[0], font=font(88))
    d.text((r + 22, y + 74), s[1], font=font(38, 700), fill=GREEN)
    ft = font(40, 800); tx = s[2]
    while d.textlength(tx, font=ft) > W - 80 - 72 and ft.size > 30: ft = font(ft.size - 2, 800)
    d.text((76, y + 164), tx, font=ft, fill=INK)

def ring(d, pts, i, k):
    """動く牌を囲む輪と番号。pts=[(x,y)…]（画面の比）"""
    if not pts: return
    xs = [p[0] * W for p in pts]; ys = [p[1] * H for p in pts]
    pad = 78
    x0, y0, x1, y1 = min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad
    if x1 < 0 or x0 > W: return
    a = int(255 * min(1, k * 5))
    for wd, col in ((14, (255, 255, 255, a)), (8, (231, 86, 32, a))):
        d.rounded_rectangle((x0, y0, x1, y1), radius=40, outline=col, width=wd)
    bx, by = max(60, min(W - 60, x0)), max(700, y0)
    d.ellipse((bx - 44, by - 44, bx + 44, by + 44), fill=(231, 86, 32, a), outline=(255, 255, 255, a), width=5)
    text_c(d, bx, by - 2, str(i + 1), font(52), (255, 255, 255, a))

def bubble(d, tx, k):
    a = min(1, k * 5); s = .8 + .2 * a
    cx, cy, w, h = W / 2, 1060, 420 * s, 170 * s
    d.rounded_rectangle((cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), radius=h / 2, fill=ORANGE, outline=WHITE, width=8)
    d.polygon([(cx - 150, cy + h / 2 - 6), (cx - 90, cy + h / 2 - 6), (cx - 190, cy + h / 2 + 70)], fill=ORANGE)
    text_c(d, cx, cy - 4, "「" + tx + "」", font(int(96 * s)), WHITE)

def summary(d, sc, k):
    a = int(240 * min(1, k * 3))
    n = len(sc["steps"]); y0 = 520
    d.rounded_rectangle((90, y0, W - 90, y0 + 150 + n * 118), radius=50, fill=(255, 255, 255, a))
    text_c(d, W / 2, y0 + 78, sc["title"], font(66), (23, 112, 131, min(255, a + 15)))
    for i, s in enumerate(sc["steps"]):
        y = y0 + 150 + i * 118
        d.ellipse((150, y, 150 + 84, y + 84), fill=(231, 86, 32, min(255, a + 15)))
        text_c(d, 192, y + 40, str(i + 1), font(56), WHITE)
        d.text((264, y - 6), s[0], font=font(66), fill=INK)
        d.text((264 + d.textlength(s[0], font=font(66)) + 20, y + 22), s[1], font=font(34, 700), fill=GREEN)

def main():
    a = sys.argv[1:]
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 12
    sc = SCRIPTS[a[a.index("--script") + 1] if "--script" in a else "chi"]
    src, out = a[0], a[1]
    frames = sorted(glob.glob(os.path.join(src, "f[0-9]*.png")))
    assert frames, "コマが無い: " + src
    mp = os.path.join(src, "marks.json")
    marks = json.load(open(mp)) if os.path.exists(mp) else {}
    # 出すコマの並び: (元のコマ, 手順, その手順が出てからの秒, 止めているか)
    seq = []
    for i, s in enumerate(sc["steps"]):
        t = 0.0
        for f in range(s[3], s[4] + 1): seq.append((f, i, t, False)); t += 1 / fps
        for _ in range(int(s[5] * fps)): seq.append((s[4], i, t, True)); t += 1 / fps
    f0, f1, hold = sc["tail"]; t = 0.0
    for f in range(f0, f1 + 1): seq.append((f, -1, t, False)); t += 1 / fps
    for _ in range(int(hold * fps)): seq.append((f1, -1, t, True)); t += 1 / fps
    tmp = tempfile.mkdtemp(); cache = {}
    for n, (f, i, t, held) in enumerate(seq):
        if f not in cache:
            cache.clear(); cache[f] = Image.open(frames[min(f, len(frames) - 1)]).convert("RGBA").resize((W, H), Image.LANCZOS)
        im = cache[f].copy(); ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        if i >= 0:
            s = sc["steps"][i]
            rail(d, sc["steps"], i); headline(d, i, s, t)
            m = marks.get(str(f), {})
            ring(d, [m[k] for k in s[6] if k in m], i, t)
            if s[7] and t > .25: bubble(d, s[7], t - .25)
        else:
            rail(d, sc["steps"], len(sc["steps"]), done_all=True)
            if t > .9: summary(d, sc, t - .9)
        Image.alpha_composite(im, ov).convert("RGB").save(os.path.join(tmp, f"f{n:04d}.png"))
    ff = shutil.which("ffmpeg")
    if not ff:
        import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"),
                    "-vf", "fps=24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    shutil.rmtree(tmp); print("ok", out, len(seq), "コマ", round(len(seq) / fps, 1), "秒")

if __name__ == "__main__":
    main()
