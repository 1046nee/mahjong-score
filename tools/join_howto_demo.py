# -*- coding: utf-8 -*-
# 使い方の4本（howto-1〜4.mp4）を1本（howto-all.mp4）につなぎ、ステップの切れ目の秒を index.html の data-marks に書く。
# 1本にする理由: iPhoneは動画を替えるたびに自動再生を止められることがある。ステップの間に0.4秒の止めを入れる
# split_howto_demo.py の最後に呼ばれる。単体でも実行できる: python tools/join_howto_demo.py
import io
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from record_app_demo import ffmpeg_exe  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(BASE, "assets", "screens")
HOLD = 0.4


def duration(ff, path):
    r = subprocess.run([ff, "-hide_banner", "-i", path], capture_output=True, text=True, encoding="utf-8", errors="ignore").stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r).groups()
    return int(h) * 3600 + int(m) * 60 + float(s)


def main():
    ff = ffmpeg_exe()
    src = [os.path.join(SITE, f"howto-{i}.mp4") for i in range(1, 5)]
    marks, t = [0.0], 0.0
    for i, p in enumerate(src):
        t += duration(ff, p) + (HOLD if i < 3 else 0)
        marks.append(round(t, 2))
    chains = "".join(f"[{i}:v]{f'tpad=stop_mode=clone:stop_duration={HOLD},' if i < 3 else ''}setpts=PTS-STARTPTS[v{i}];" for i in range(4))
    out = os.path.join(SITE, "howto-all.mp4")
    args = [ff, "-y", "-loglevel", "error"]
    for p in src:
        args += ["-i", p]
    args += ["-filter_complex", chains + "".join(f"[v{i}]" for i in range(4)) + "concat=n=4:v=1:a=0[o]", "-map", "[o]", "-an",
             "-c:v", "libx264", "-profile:v", "main", "-crf", "23", "-pix_fmt", "yuv420p", "-g", "25", "-movflags", "+faststart", out]
    subprocess.run(args, check=True)
    idx = os.path.join(BASE, "index.html")
    s = io.open(idx, encoding="utf-8", newline="").read()
    s, n = re.subn(r'data-marks="[\d.,]*"', 'data-marks="' + ",".join(str(m) for m in marks) + '"', s)
    if n == 1:
        io.open(idx, "w", encoding="utf-8", newline="").write(s)
    print("howto-all.mp4", os.path.getsize(out) // 1024, "KB", marks, "index", n)


if __name__ == "__main__":
    main()
