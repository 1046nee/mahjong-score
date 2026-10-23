# -*- coding: utf-8 -*-
"""麻雀の道具・卓の図（tools/table_art.py）を assets/art/ に1枚ずつのSVGで書き出す（2026-10-23〜）。
牌の絵は assets/tiles/ のSVGの中身をそのまま埋め込む（<img> で表示したときも牌が出るように。外のファイルを読みに行かない）。
実行: python tools/make_art.py
"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import table_art as ta

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TILES = os.path.join(ROOT, "assets", "tiles")
OUT = os.path.join(ROOT, "assets", "art")


def inline_tiles(svg):
    """<image href="/assets/tiles/xx.svg" x y width height/> を、牌のSVGの中身（入れ子の svg）に置きかえる"""
    def rep(m):
        name, x, y, w, h, extra = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5), (m.group(6) or "")
        t = io.open(os.path.join(TILES, name), encoding="utf-8").read()
        vb = re.search(r'viewBox="([^"]+)"', t).group(1)
        inner = t[t.index(">") + 1:t.rindex("</svg>")]
        return f'<svg x="{x}" y="{y}" width="{w}" height="{h}" viewBox="{vb}"{extra}>{inner}</svg>'
    return re.sub(r'<image href="/assets/tiles/([\w-]+\.svg)" x="([\d.-]+)" y="([\d.-]+)" width="([\d.]+)" height="([\d.]+)"((?: [\w-]+="[^"]*")*)/>', rep, svg)


ITEMS = {
    "table-yama.svg": lambda: ta.table_scene("yama"),
    "table-kaimon.svg": lambda: ta.table_scene("kaimon"),
    "table-haipai.svg": lambda: ta.table_scene("haipai"),
    "table-tsumo.svg": lambda: ta.table_scene("tsumo"),
    "table-kaze.svg": lambda: ta.table_scene("kaze"),
    "wanpai.svg": lambda: ta.dead_wall_zoom(),
    "tenbo.svg": ta.tenbo_set,
    "tenbo-color.svg": ta.tenbo_color_set,
    "dice-chiicha.svg": ta.small_parts,
    "jidou-taku.svg": ta.jidou_taku,
}

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, f in ITEMS.items():
        s = inline_tiles(f())
        assert "/assets/tiles/" not in s, name
        io.open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n").write(s)
        print(name, len(s) // 1024, "KB")
