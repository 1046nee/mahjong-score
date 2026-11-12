# -*- coding: utf-8 -*-
"""3Dの選手の見本（前・横・後ろ）を1枚にまとめる。
  python tools/b3d/make_sheet.py <名簿.json> <出力フォルダ> p01 p02 ...   （id を書かなければ全員）
  bpy の入った Python を環境変数 B3D_PY に（無ければ scratchpad の bvenv を探す）。
1人あたり約12秒（360×480・16サンプルを3方向）。見本は名簿と同じく非公開（素材リポジトリ）に置く。
"""
import glob, json, os, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = ["C:/Windows/Fonts/NotoSansJP-VF.ttf", "/usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf"]


def font(size, w=800):
    for f in FONTS:
        if os.path.exists(f):
            ft = ImageFont.truetype(f, size)
            try: ft.set_variation_by_axes([w])
            except Exception: pass
            return ft
    return ImageFont.load_default()


def main():
    roster_p, out = sys.argv[1], sys.argv[2]
    R = json.load(open(roster_p, encoding="utf-8"))
    ids = sys.argv[3:] or list(R["people"])
    py = os.environ.get("B3D_PY") or (glob.glob("/tmp/claude-*/**/bvenv/bin/python", recursive=True) or ["python"])[0]
    tmp = os.path.join(out, "_views"); os.makedirs(tmp, exist_ok=True)
    for pid in ids:
        subprocess.run([py, os.path.join(HERE, "scene.py"), "--roster", roster_p, "--sheet", pid, "--out", tmp, "--size", "360x480", "--samples", "16"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pp = R["people"][pid]; tm = R["teams"][pp["team"]]
        sheet = Image.new("RGB", (360 * 3 + 40, 480 + 120), "#FFFFFF"); d = ImageDraw.Draw(sheet)
        for k, v in enumerate(("front", "side", "back")):
            sheet.paste(Image.open(os.path.join(tmp, f"{pid}_{v}.png")).convert("RGB"), (10 + k * 370, 110))
            d.text((10 + k * 370 + 8, 116), {"front": "前", "side": "横", "back": "後ろ"}[v], font=font(24), fill="#1F2A28")
        g = {"f": "女性", "m": "男性"}.get(pp.get("gender"), "性別未設定")
        d.text((14, 14), f"{pid}  {pp['name']}", font=font(38, 900), fill="#1F2A28")
        d.text((14, 64), f"{tm['name']}・{g}" + ("" if pp.get("photo") else "・写真まだ（仮の見た目）"), font=font(22, 700), fill="#5F6E6B")
        sheet.save(os.path.join(out, f"{pid}.png")); print("ok", pid, pp["name"])


if __name__ == "__main__":
    main()
