# -*- coding: utf-8 -*-
"""3D動画（麻雀の所作）の字幕と牌姿を、Notion に貼れる Markdown で書き出す（2026-11-17 ユーザーの依頼）。
字幕＝画面に出る1枚ずつの文（make_clip.py の sub_units と subtitle と同じ区切り・字の大きさ・読み）。字幕が出るのは手順とまとめだけで、入り・確認・締めは声とカードだけ。
牌姿＝scene.py の HANDS・RIVERS など（自分の手牌・自分の河・鳴く/アガる牌）。scene.py の「席ごとの牌」の部分だけを取り出して動かす（bpy は使わない。Blender が無い会社PCでも動く）。
動画の中で切る牌は scene.py のコメントから（CUT。牌姿を変えたらここも直す）。
実行: python tools/b3d/subs_dump.py > 出力.md
"""
import sys, os, io, math
R = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, R); sys.path.insert(0, os.path.dirname(R))
sys.argv = [sys.argv[0]]
import make_clip as MC, narration as N
from PIL import Image, ImageDraw

D = ImageDraw.Draw(Image.new("RGBA", (8, 8)))


def rows(tx):
    """make_clip.subtitle と同じ折り方: まず字を小さくして1行に、入らなければ「、」「。」で2〜3行に"""
    ft = MC.font(46, 800); maxw = MC.W - 2 * 90; rs = [tx]
    while D.textlength(tx, font=ft) > maxw and ft.size > MC.SUB_MIN: ft = MC.font(ft.size - 2, 800)
    if D.textlength(tx, font=ft) > maxw:
        cuts = [k + 1 for k, ch in enumerate(tx[:-1]) if ch in "、。"] or [len(tx) // 2]
        c = min(cuts, key=lambda k: abs(k - len(tx) / 2)); rs = [tx[:c], tx[c:]]
        if max(D.textlength(r_, font=ft) for r_ in rs) > maxw:
            best = None
            for c1 in cuts:
                for c2 in cuts:
                    if c2 <= c1: continue
                    r3 = [tx[:c1], tx[c1:c2], tx[c2:]]; w_ = max(D.textlength(r_, font=ft) for r_ in r3)
                    if best is None or w_ < best[0]: best = (w_, r3)
            if best: rs = best[1]
        while max(D.textlength(r_, font=ft) for r_ in rs) > maxw and ft.size > 34: ft = MC.font(ft.size - 2, 800)
    return rs, ft.size


def rub(t): return "".join(p + (f"（{r}）" if r else "") for p, r, _ in MC.ruby_parts(t))


NM = dict(zip("1234567", "東南西北白發中")); K = "〇一二三四五六七八九"
def jp(c):
    if c == "back": return "（裏）"
    if c[0] == "z": return NM[c[1]]
    return ("赤" if c.endswith("r") else "") + K[int(c[1])] + {"m": "萬", "p": "筒", "s": "索"}[c[0]]


SRC = io.open(os.path.join(R, "scene.py"), encoding="utf-8").read()
SEG = SRC[SRC.index("HANDS = ["):SRC.index("CALL_K = ")]
CUT = {"chi": "三索", "pon": "八萬", "kan": "六索（嶺上牌のあと）", "daiminkan": "發（嶺上牌をそのまま）", "kakan": "北（嶺上牌をそのまま）", "riichi": "西（横向き）",
       "tsumo": "なし（ツモアガリ）", "ron": "なし（ロンアガリ）", "dahai": "白 → 次の番で西をツモ切り", "furiten": "なし（ツモアガリ）", "ryukyoku": "なし（流局）"}
CALL = {"chi": "鳴く牌", "pon": "鳴く牌", "daiminkan": "鳴く牌", "ron": "ロンする牌", "furiten": "切られてもロンできない牌"}      # 他家の捨て牌を使う動画だけ
TITLE = {"kan": "カンの方法（暗槓）", "daiminkan": "カンの方法（大明槓）", "kakan": "カンの方法（加槓）"}
SEAT = {0: "自家", 1: "下家", 2: "対面", 3: "上家"}
SEGN = {"intro": "入り", "pre": "確認", "tail": "まとめ", "outro": "締め"}


def scene(name):
    g = {"arg": lambda n, dflt: name if n == "--scene" else dflt, "sys": type("S", (), {"argv": []}), "TAKEN": .5, "DORA": "m8", "TL": .03, "math": math}
    exec(SEG, g)
    return g


def main():
    md = ["自動で書き出したもの（`python tools/b3d/subs_dump.py`）。台本や牌姿を変えたら書き出し直す。",
          "字幕は1行＝画面に1枚ずつ出る文（声に合わせて切りかわる）。「／」は同じ1枚の中の改行。（ ）は字幕に付く読み。字の大きさは画面の幅1080pxでの大きさ（ふだん46・長い文は38まで小さくする）。",
          "字幕が出るのは手順とまとめだけ。入り・確認・締めは声とカード（字幕なし）。", ""]
    for name in N.NARR:
        g = scene(name)
        title = TITLE.get(name) or N.NARR[name]["intro"].split("を、")[0].split("。")[0]
        md += [f"## {title}（{name}）", "", "| | |", "|---|---|", f"| 自分の手牌（左から） | {'・'.join(jp(c) for c in g['HANDS'][0])} |"]
        if g["MELD0"]: md.append(f"| 晒してある牌 | {'・'.join(jp(c) for c in g['MELD0'])} |")
        md.append(f"| 自分の河（左から） | {'・'.join(jp(c) for c in g['RIVERS'][0])} |")
        cs = g["CALL_SEAT"]
        if name in CALL: md.append(f"| {CALL[name]} | {SEAT[cs]}が切った {jp(g['RIVERS'][cs][-1])} |")
        if g["NEXT_CODE"] != "back": md.append(f"| ツモる牌 | {jp(g['NEXT_CODE'])}" + (f"、次に {jp(g['NEXT2_CODE'])}" if g["NEXT2_CODE"] != "back" else "") + " |")
        if name in ("kan", "daiminkan", "kakan"): md.append(f"| 嶺上牌 | {jp(g['RINSHAN'])} |")
        for k_, h_ in g["OPEN_HANDS"].items(): md.append(f"| {SEAT[k_]}の手牌（倒す） | {'・'.join(jp(c) for c in h_)} |")
        md += [f"| 動画の中で切る牌 | {CUT.get(name, '')} |", "| ドラ表示牌 | 八萬 |", "", "| 場面 | 字幕（1行＝1枚） | 字の大きさ |", "|---|---|---|"]
        for sg, tx in N.lines(name):
            lab = SEGN.get(sg, sg.replace("step", "手順"))
            if sg.startswith("step") or sg == "tail":
                for j, u in enumerate(MC.sub_units(tx)):
                    rs, sz = rows(u); md.append(f"| {lab if j == 0 else ''} | {'／'.join(rub(r) for r in rs)} | {sz} |")
            else: md.append(f"| {lab} | （声だけ）{tx} | |")
        md.append("")
    sys.stdout.reconfigure(encoding="utf-8"); print("\n".join(md))


if __name__ == "__main__":
    main()
