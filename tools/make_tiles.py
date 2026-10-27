# -*- coding: utf-8 -*-
"""まじゃすこの牌のSVGを assets/tiles/ に書き出す（2026-10-23〜）。サイトの中ではこの絵だけを使い回す。
- <code>.svg       … 縦向き（手牌・ふつうの並び）。code は m1〜m9・p1〜p9・s1〜s9・z1〜z7（東南西北白發中）・m5r/p5r/s5r（赤五）・back（裏向き）・z5p（白ぽっち）・f1〜f8（花牌＝春夏秋冬・梅蘭菊竹）
- yakitori.svg / yakitori-ura.svg … 焼き鳥カードの表・裏（横長の札。起家札と同じ大きさ・向き）
- chicha.svg / chicha-ura.svg … 起家札の表（東）・裏（南）。オレンジの札に黒い字
- 麻雀グッズ（マイページのアイコン）: tenbo（白い1,000点棒）・tb100/tb5000/tb10000・ct100〜ct10000/cttobi（カラーの点棒）・tb100x5（100点棒5本の束）・
  dice（5の目）・d1〜d4/d6・chip-r/b/g/o/k（チップ）・haiyose（牌寄せ）
- <code>-yoko.svg  … 横向き（チー・ポン・カンで鳴いた牌）。絵だけ左に倒し、緑の背は下のまま
実行: python tools/make_tiles.py
"""
import io, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tiles

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = os.path.join(ROOT, "assets", "tiles")
os.makedirs(d, exist_ok=True)
n = 0
for code in tiles.ALL:
    for yoko in (False, True):
        if code == "back" and yoko:
            continue
        name = code + ("-yoko" if yoko else "") + ".svg"
        io.open(os.path.join(d, name), "w", encoding="utf-8", newline="\n").write(tiles.tile_svg(code, "tokumin", yoko=yoko))
        n += 1
# 焼き鳥カード（表・裏）。牌ではないが、記事で牌と並べて使う（2026-10-27）
for ura in (False, True):
    io.open(os.path.join(d, "yakitori" + ("-ura" if ura else "") + ".svg"), "w", encoding="utf-8", newline="\n").write(tiles.yakitori_svg(ura))
    io.open(os.path.join(d, "chicha" + ("-ura" if ura else "") + ".svg"), "w", encoding="utf-8", newline="\n").write(tiles.chicha_svg(ura))
    n += 1
# 麻雀グッズ（マイページのアイコンに使う。2026-10-27）。tenbo＝白い1,000点棒・dice＝5の目（最初からある名前なので変えない）
goods = {"tenbo": tiles.tenbo_svg(1000), "dice": tiles.dice_svg(5), "tb100x5": tiles.tenbo_bundle_svg(), "haiyose": tiles.haiyose_svg()}
for v in (100, 5000, 10000):
    goods[f"tb{v}"] = tiles.tenbo_svg(v)
for v in (100, 500, 1000, 5000, 10000, "tobi"):
    goods[f"ct{v}"] = tiles.tenbo_svg(v, color=True)
for i in (1, 2, 3, 4, 6):
    goods[f"d{i}"] = tiles.dice_svg(i)
for c in tiles.CHIPS:
    goods[f"chip-{c}"] = tiles.chip_svg(c)
for name, src in goods.items():
    io.open(os.path.join(d, name + ".svg"), "w", encoding="utf-8", newline="\n").write(src)
    n += 1
print(n, "枚 →", d)
