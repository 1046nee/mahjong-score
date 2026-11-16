# -*- coding: utf-8 -*-
"""待ちの形の一覧（1枚）と、解説（1面子1雀頭・2面子1雀頭①②）の4枚の表を作る（2026-11-16〜）。
出力: assets/hai/machi-katachi-ichiran.png ／ machi-katachi-4mai.png ／ machi-katachi-7mai-1.png ／ machi-katachi-7mai-2.png（幅1588）。
作ったら python tools/make_webp.py（記事の中は WebP）。記事は blog-machi-katachi。
決めごと（2026-11-16 ユーザーの指定）は docs/image-tools.md「Xに出す1枚の表」と、machi_sheet/ の各スクリプトのコメントに。
  待ちと枚数は手で書かず計算（machi_sheet/machi3.py の waits）。形の一覧・段階（初心者・脱初心者・中級者）・名前は machi3.py の SECS・LV1〜LV3
実行: python tools/machi_sheet.py ／ Instagram用（1080×1350・8枚。まじゃすこ素材/ig/machi/）: python tools/machi_sheet.py --ig
"""
import os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "assets", "hai")
JOBS = [("machi4.py", "A", "machi-katachi-ichiran"), ("detail.py", "1", "machi-katachi-4mai"),
        ("detail.py", "2a", "machi-katachi-7mai-1"), ("detail.py", "2b", "machi-katachi-7mai-2")]
IG_DIR = os.path.join(ROOT, "まじゃすこ素材", "ig", "machi")   # 画像の元は公開リポジトリに入れない
IG_W, IG_H, MINT = 1080, 1350, (238, 246, 243)


def ig_page(im, path):
    """1枚の表を 1080×1350（縦5:横4）のまん中に、はみ出さない大きさで置く（地はミント）"""
    from PIL import Image
    k = min(IG_W / im.width, IG_H / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    pg = Image.new("RGB", (IG_W, IG_H), MINT); pg.paste(im, ((IG_W - im.width) // 2, (IG_H - im.height) // 2))
    pg.save(path); print("ig", os.path.relpath(path, ROOT))


def ichiran_split(src):
    """一覧は縦に長いので、1面子1雀頭と2面子1雀頭の間の二重線で2枚に分ける。
    1枚目＝見出し〜1面子1雀頭＋下の凡例、2枚目＝見出し＋表の頭＋2面子1雀頭〜凡例"""
    from PIL import Image
    import numpy as np
    im = Image.open(src).convert("RGB"); a = np.asarray(im).astype(int)
    dark = [y for y in range(im.height) if (a[y, 200:1500].sum(1) < 200).mean() > .9]
    runs = []
    for y in dark:
        if runs and y - runs[-1][1] <= 1: runs[-1][1] = y
        else: runs.append([y, y])
    top = runs[0][0]                     # 表の上の線（ここまでが見出し）
    head = runs[2][1] + 1                # 表の頭の下の二重線
    mid = [r for r in runs if r[0] > im.height * .3][0][0]   # 1面子1雀頭と2面子1雀頭の間の二重線（の上の線）
    foot = runs[-1][1] + 1               # 表の下の線（ここから下が凡例）
    def stack(parts):
        out = Image.new("RGB", (im.width, sum(b - t for t, b in parts)), MINT); y = 0
        for t, b in parts: out.paste(im.crop((0, t, im.width, b)), (0, y)); y += b - t
        return out
    return [stack([(0, mid + 4), (foot, im.height)]), stack([(0, head), (mid, im.height)])]


def ig():
    import tempfile
    from PIL import Image
    os.makedirs(IG_DIR, exist_ok=True)
    n = 0
    for im in ichiran_split(os.path.join(OUT, "machi-katachi-ichiran.png")):
        n += 1; ig_page(im, os.path.join(IG_DIR, f"{n}.png"))
    with tempfile.TemporaryDirectory() as td:
        for arg in ("ig1a", "ig1b", "2a", "ig2b", "ig2c", "ig2d"):
            o = os.path.join(td, arg)
            subprocess.run([sys.executable, os.path.join(HERE, "machi_sheet", "detail.py"), o, arg], check=True)
            n += 1; ig_page(Image.open(o + ".png").convert("RGB"), os.path.join(IG_DIR, f"{n}.png"))


if __name__ == "__main__":
    if "--ig" in sys.argv: ig(); sys.exit()
    for script, arg, name in JOBS:
        subprocess.run([sys.executable, os.path.join(HERE, "machi_sheet", script), os.path.join(OUT, name), arg], check=True)
