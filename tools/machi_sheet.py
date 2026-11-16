# -*- coding: utf-8 -*-
"""待ちの形の一覧（1枚）と、解説（1面子1雀頭・2面子1雀頭①②）の4枚の表を作る（2026-11-16〜）。
出力: assets/hai/machi-katachi-ichiran.png ／ machi-katachi-4mai.png ／ machi-katachi-7mai-1.png ／ machi-katachi-7mai-2.png（幅1588）。
作ったら python tools/make_webp.py（記事の中は WebP）。記事は blog-machi-katachi。
決めごと（2026-11-16 ユーザーの指定）は docs/image-tools.md「Xに出す1枚の表」と、machi_sheet/ の各スクリプトのコメントに。
  待ちと枚数は手で書かず計算（machi_sheet/machi3.py の waits）。形の一覧・段階（初心者・脱初心者・中級者）・名前は machi3.py の SECS・LV1〜LV3
実行: python tools/machi_sheet.py
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "hai")
JOBS = [("machi4.py", "A", "machi-katachi-ichiran"), ("detail.py", "1", "machi-katachi-4mai"),
        ("detail.py", "2a", "machi-katachi-7mai-1"), ("detail.py", "2b", "machi-katachi-7mai-2")]
if __name__ == "__main__":
    for script, arg, name in JOBS:
        subprocess.run([sys.executable, os.path.join(HERE, "machi_sheet", script), os.path.join(OUT, name), arg], check=True)
