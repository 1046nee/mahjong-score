# -*- coding: utf-8 -*-
"""牌に使う字（一〜九・萬・東南西北・發・中）の形を、フォントから図形（SVGのパス）として取り出す（2026-10-23）。
取り出した形は tools/tile_glyphs.json に入れる。tools/tiles.py はこの形で字を描くので、見る人の端末のフォントに左右されない。
フォントは Google Fonts の SIL Open Font License 1.1（図形にして絵に使ってよい）。フォントのファイルはリポジトリに入れない。
実行: python tools/tile_glyphs.py <名前>=<フォントのファイル> ...
  例: python tools/tile_glyphs.py tokumin=KaiseiTokumin-ExtraBold.ttf boku=YujiBoku-Regular.ttf
"""
import io, json, os, sys
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.boundsPen import BoundsPen

CHARS = "一二三四五六七八九萬東南西北發中春夏秋冬梅蘭菊竹焼き鳥"  # 花牌と焼き鳥カードの字を足した（2026-10-27）
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "tile_glyphs.json")


def extract(path):
    f = TTFont(path)
    gs = f.getGlyphSet()
    cmap = f.getBestCmap()
    res = {"upm": f["head"].unitsPerEm, "glyphs": {}}
    for ch in CHARS:
        g = gs[cmap[ord(ch)]]
        pen = SVGPathPen(gs)
        g.draw(pen)
        bp = BoundsPen(gs)
        g.draw(bp)
        res["glyphs"][ch] = {"d": pen.getCommands(), "bbox": [round(v, 1) for v in bp.bounds]}
    return res


if __name__ == "__main__":
    data = json.load(io.open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    for arg in sys.argv[1:]:
        name, path = arg.split("=", 1)
        data[name] = extract(path)
        data[name]["source"] = os.path.basename(path) + "（SIL Open Font License 1.1）"
        print(name, len(data[name]["glyphs"]), "字")
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(data, ensure_ascii=False))
