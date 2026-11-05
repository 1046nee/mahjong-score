# -*- coding: utf-8 -*-
# record_howto_demo.py が録った1本の.webmを、howto-marks.jsonの境目で4つのmp4に切り出す。
# 出力: assets/screens/howto-1.mp4 ... howto-4.mp4（音無し・2倍解像度）
import glob
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from record_app_demo import ffmpeg_exe  # noqa: E402

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VIDEO_DIR = os.path.join(BASE, "まじゃすこ素材", "ig", "video")
SITE = os.path.join(BASE, "assets", "screens")
VIEW_W, VIEW_H = 390, 792


def main():
    webms = sorted(glob.glob(os.path.join(VIDEO_DIR, "*.webm")), key=os.path.getmtime)
    assert webms, "howto-demo の .webm が無い（先に record_howto_demo.py を実行）"
    raw_webm = webms[-1]
    marks = json.load(open(os.path.join(VIDEO_DIR, "howto-marks.json"), encoding="utf-8"))
    ff = ffmpeg_exe()

    raw_mp4 = os.path.join(VIDEO_DIR, "howto-raw.mp4")
    subprocess.run([ff, "-y", "-i", raw_webm,
                    "-vf", f"scale={VIEW_W * 2}:{VIEW_H * 2}:flags=lanczos",
                    "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", raw_mp4],
                   check=True, capture_output=True)

    segs = [(marks["start"], marks["step1_end"]), (marks["step1_end"], marks["step2_end"]), (marks["step3_start"], marks["step3_end"]), (marks["step3_end"], marks["step4_end"])]
    PAD = 0.15
    for i in range(4):
        a2, b2 = segs[i]
        if i != 2: a2 = max(segs[0][0], a2 - PAD)  # 3の最初は閉じる途中を映さない
        if i != 1: b2 = min(segs[3][1], b2 + PAD)  # 2の最後も同じ
        out = os.path.join(SITE, f"howto-{i + 1}.mp4")
        subprocess.run([ff, "-y", "-ss", f"{a2:.2f}", "-to", f"{b2:.2f}", "-i", raw_mp4,
                        "-an", "-c:v", "libx264", "-crf", "22", "-pix_fmt", "yuv420p",
                        "-movflags", "+faststart", out],
                       check=True, capture_output=True)
        size = os.path.getsize(out) // 1024
        print(f"howto-{i + 1}.mp4  {b2 - a2:.2f}s  {size}KB")
        # 動画を読めない端末で出す静止画（ステップの最後のコマ）。1枚目はLPの最初のコマも撮る
        subprocess.run([ff, "-y", "-sseof", "-0.2", "-i", out, "-frames:v", "1", "-q:v", "4", os.path.join(SITE, f"howto-step-{i + 1}.jpg")], check=True, capture_output=True)
        if i == 0:
            subprocess.run([ff, "-y", "-i", out, "-frames:v", "1", "-q:v", "4", os.path.join(SITE, "howto-poster.jpg")], check=True, capture_output=True)


if __name__ == "__main__":
    main()
    import join_howto_demo
    join_howto_demo.main()  # 4本を1本につなぐ（LPが再生するのは howto-all.mp4）
