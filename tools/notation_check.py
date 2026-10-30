# -*- coding: utf-8 -*-
"""表記の決まり（docs/blog-spec.md「表記の決まり」）どおりかを全記事で確かめる・直す（2026-10-30〜）。
決まり2「読みを（）や・で重ねて書かない」の、機械で確かに判断できる形だけを扱う:
  a) ルビのあとに同じ読み: <ruby>刻子<rt>コーツ</rt></ruby>（コーツ） / ・コーツ / ＝コーツ  → 読みを消す
  b) 読みの（）の中にルビの漢字: コーツ（<ruby>刻子<rt>コーツ</rt></ruby>）            → ルビの漢字だけに
  c) ルビのない 漢字（読み）・読み（漢字）で、読みが add_ruby の読みと同じ                → 漢字だけにして、ルビは add_ruby に任せる
読みが違うもの（別の読み＝決まり3）は残す。
実行: python tools/notation_check.py          （数えるだけ）
      python tools/notation_check.py --fix    （直して、直した記事に add_ruby をかける）
"""
import io, os, re, sys, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from add_ruby import READ, SKIP_FILES  # 読み方そのものを見せるページ（用語集など）は対象外

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = "--fix" in sys.argv
K = "|".join(sorted(map(re.escape, READ), key=len, reverse=True))
RUBY = r"<ruby>(%s)<rt>([^<]+)</rt></ruby>" % K

def norm(x):
    return x.replace("・", "").replace(" ", "")

def fix_text(s):
    n = 0
    # a) ルビ＋（同じ読み）/・同じ読み/＝同じ読み
    def a(m):
        nonlocal n
        kan, rt, tail = m.group(1), m.group(2), m.group(3)
        if norm(tail) == norm(rt):
            n += 1; return f"<ruby>{kan}<rt>{rt}</rt></ruby>"
        return m.group(0)
    s = re.sub(RUBY + r"(?:（([ァ-ヶー・]+)）)", lambda m: a(type("M", (), {"group": lambda self, i: (m.group(0), m.group(1), m.group(2), m.group(3))[i]})()), s)
    s = re.sub(RUBY + r"(?:[・＝]([ァ-ヶー]+))(?=[）、。＝\s<]|$)", lambda m: a(type("M", (), {"group": lambda self, i: (m.group(0), m.group(1), m.group(2), m.group(3))[i]})()), s)
    # b) 読み（ルビの漢字）
    def b(m):
        nonlocal n
        yomi, kan, rt = m.group(1), m.group(2), m.group(3)
        if norm(yomi) == norm(rt):
            n += 1; return f"<ruby>{kan}<rt>{rt}</rt></ruby>"
        return m.group(0)
    s = re.sub(r"([ァ-ヶー]+)（" + RUBY + r"）", b, s)
    # c) ルビのない 漢字（読み）・読み（漢字）
    def c1(m):
        nonlocal n
        kan, yomi = m.group(1), m.group(2)
        if norm(READ[kan]) == norm(yomi):
            n += 1; return kan
        return m.group(0)
    s = re.sub(r"(?<![>ァ-ヶー一-龥])(%s)（([ァ-ヶー・]+)）" % K, c1, s)
    def c2(m):
        nonlocal n
        yomi, kan = m.group(1), m.group(2)
        if norm(READ[kan]) == norm(yomi):
            n += 1; return kan
        return m.group(0)
    s = re.sub(r"(?<![ァ-ヶー])([ァ-ヶー]+)（(%s)）" % K, c2, s)
    return s, n

def main():
    files = sorted(glob.glob(os.path.join(ROOT, "blog-*.html")))
    total, changed = 0, []
    for f in files:
        if os.path.basename(f) in SKIP_FILES:
            continue
        t = io.open(f, encoding="utf-8").read()
        a = t.find('<article class="blog-post">'); b = t.find("</article>", a)
        if a < 0:
            continue
        body, n = fix_text(t[a:b])
        if n:
            total += n
            print(f"{os.path.basename(f)}: {n}")
            if FIX:
                io.open(f, "w", encoding="utf-8", newline="").write(t[:a] + body + t[b:]); changed.append(f)
    print("合計", total, "か所" + ("（直した）" if FIX else ""))
    if FIX and changed:
        subprocess.run([sys.executable, os.path.join(ROOT, "tools", "add_ruby.py")] + [os.path.basename(c) for c in changed], cwd=ROOT)
    return 0 if FIX or not total else 1

if __name__ == "__main__":
    sys.exit(main())
