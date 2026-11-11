# -*- coding: utf-8 -*-
"""scene.py --anim が書き出したコマ（f0000.png〜）に、手順の字をのせて mp4 にする。
  python tools/b3d/make_clip.py <コマのフォルダ> <出力.mp4> [--fps 12]
字は Noto Sans JP（Windows は C:/Windows/Fonts/NotoSansJP-VF.ttf）。ffmpeg は PATH のもの、無ければ imageio-ffmpeg。
"""
import glob, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

FONTS = ["C:/Windows/Fonts/NotoSansJP-VF.ttf", "/usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"]
# チーの5つの手順（秒）。scene.py の anim_pose の区切りと合わせる
CAPS = [(0.2, 1.5, "① 声を出す", "「チー」"), (1.5, 2.1, "② 手の牌を晒す", ""), (2.1, 3.8, "③ 相手の牌を取る", ""),
        (3.8, 5.0, "④ 右の隅に並べる", ""), (5.0, 6.7, "⑤ 1枚切る", ""), (6.9, 8.0, "鳴きが完了", "")]

def font(size):
    for f in FONTS:
        if os.path.exists(f):
            ft = ImageFont.truetype(f, size)
            try: ft.set_variation_by_axes([900])
            except Exception: pass
            return ft
    raise SystemExit("Noto Sans JP が見つからない: " + " / ".join(FONTS))

def pill(d, cx, cy, text, ft, fg, bg, pad):
    l, t, r, b = d.textbbox((0, 0), text, font=ft)
    w, h = r - l, b - t
    d.rounded_rectangle((cx - w / 2 - pad * 1.6, cy - h / 2 - pad, cx + w / 2 + pad * 1.6, cy + h / 2 + pad), radius=h / 2 + pad, fill=bg)
    d.text((cx - w / 2 - l, cy - h / 2 - t), text, font=ft, fill=fg)

def main():
    a = sys.argv[1:]
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 12
    src, out = a[0], a[1]
    frames = sorted(glob.glob(os.path.join(src, "f[0-9]*.png")))
    assert frames, "コマが無い: " + src
    tmp = tempfile.mkdtemp()
    for i, fp in enumerate(frames):
        im = Image.open(fp).convert("RGB"); W, H = im.size; d = ImageDraw.Draw(im); t = i / fps
        for a0, b0, cap, say in CAPS:
            if a0 <= t < b0:
                pill(d, W / 2, H * .085, cap, font(round(W * .074)), "#FFFFFF", "#177083", W * .022)
                if say: pill(d, W / 2, H * .62, say, font(round(W * .1)), "#FFFFFF", "#E75620", W * .03)
        im.save(os.path.join(tmp, f"f{i:04d}.png"))
    ff = shutil.which("ffmpeg")
    if not ff:
        import imageio_ffmpeg; ff = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([ff, "-loglevel", "error", "-y", "-framerate", str(fps), "-i", os.path.join(tmp, "f%04d.png"),
                    "-vf", "scale=1080:-2:flags=lanczos,fps=24", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", out], check=True)
    shutil.rmtree(tmp); print("ok", out, len(frames), "コマ")

if __name__ == "__main__":
    main()
