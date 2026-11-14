# -*- coding: utf-8 -*-
"""表記のそろえ（2026-11-14 ユーザーの指定）。何度実行しても同じ結果。
  1. 麻雀の「あがり」はカタカナ: 名詞は「アガリ」（ツモアガリ・ロンアガリ・アガリ牌）、動詞は「アガる・アガれる・アガらず・アガった」（送りがなはひらがな）。
     「あがります」のような丁寧な形は「アガります」。漢字の「上がり」（盛り上がり・勝ち上がり）は麻雀の語ではないのでそのまま
  2. 点棒は算用数字: 10,000点棒・5,000点棒・1,000点棒・500点棒・100点棒（千点棒・万点棒・五千点棒…は使わない）
  3. 暗刻の読みは「アンコ」（四暗刻・三暗刻の役の名前は今までどおり）
  python tools/agari_notation.py          … 記事・ブログの部品・1枚の表のスクリプト・3D動画の字幕を書きかえる
  python tools/agari_notation.py --check  … 残っている所を数えて、あれば 1 で終わる
"""
import glob, io, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILES = (glob.glob(os.path.join(ROOT, "blog-*.html")) + glob.glob(os.path.join(ROOT, "news", "*.html")) +
         [os.path.join(ROOT, "assets", f) for f in ("blog-site.js", "fu-calc.js")] +
         [os.path.join(ROOT, "tools", f) for f in ("hai_sheets.py", "score_sheet.py", "yaku_rate_sheet.py", "rule_sheet.py", "dougu_sheet.py", "sanma_score_sheet.py", "tiles.py")] +
         [os.path.join(ROOT, "tools", "b3d", f) for f in ("make_clip.py", "narration.py")])
TENBOU = [("五百点棒", "500点棒"), ("五千点棒", "5,000点棒"), ("一万点棒", "10,000点棒"), ("万点棒", "10,000点棒"), ("千点棒", "1,000点棒"), ("百点棒", "100点棒")]


def fix(s, path):
    s = re.sub(r"あがり(?=[まませ])", "アガり", s)            # あがります・あがりません
    s = re.sub(r"あがり", "アガリ", s)
    s = re.sub(r"あが(?=[らるれろっ])", "アガ", s)
    for a, b in TENBOU:
        s = re.sub(r"(?<![0-9,])" + a, b, s)
    s = s.replace("<ruby>暗刻<rt>アンコー</rt></ruby>", "<ruby>暗刻<rt>アンコ</rt></ruby>").replace("{暗刻|アンコー}", "{暗刻|アンコ}")
    if path.endswith("narration.py"):
        s = s.replace('"暗刻": "アンコー"', '"暗刻": "アンコ"').replace('"千点棒": "センテンボウ"', '"1,000点棒": "センテンボウ"')
    if path.endswith("add_ruby.py"):
        s = s.replace('"暗刻": "アンコー"', '"暗刻": "アンコ"')
    return s


def main():
    check = "--check" in sys.argv; left = 0
    for p in FILES + [os.path.join(ROOT, "tools", "add_ruby.py")]:
        if not os.path.exists(p): continue
        s = io.open(p, encoding="utf-8").read(); t = fix(s, p)
        if t != s:
            left += 1
            print(("要: " if check else "直した: ") + os.path.relpath(p, ROOT))
            if not check: io.open(p, "w", encoding="utf-8", newline="").write(t)
    if check: sys.exit(1 if left else 0)


if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    main()
