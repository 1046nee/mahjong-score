# -*- coding: utf-8 -*-
"""3Dの所作の動画を、全部まとめて本番の設定で書き出す（2026-11-25〜。Windows・Mac・Linux で動く）。
1本ずつ: 入り → 前置き → 本題 → 締め の絵（scene.py）→ 声・効果音・音楽をのせて mp4（make_clip.py --voice --sfx --music）。
止まっても、同じ命令でもう一度動かせば続きから（できた絵は飛ばす・できた動画は飛ばす）。

使い方（リポジトリのいちばん上のフォルダで）:
  1. VOICEVOX のエンジンを動かしておく（アプリでも、エンジンだけでもよい。127.0.0.1:50021）
  2. python tools/b3d/render_all.py                 … 全部（下の ORDER の順）
     python tools/b3d/render_all.py pon chi        … 名前を並べると、その動画だけ
     python tools/b3d/render_all.py --preview      … 荒い試し（1秒5コマ・8サンプル）。字幕・声・音楽を先に見るとき
  出力: まじゃすこ素材/3d/<名前>-30fps.mp4（試しは <名前>-preview5.mp4）。絵は作業フォルダ（--work、既定は ../3d-work）に置き、本番の動画ができたら消す（試しの絵は残す）
座る4人は Notion「3D動画の出演表」（2026-11-24 時点）。出演表を変えたら CAST も直す
"""
import os, subprocess, sys, shutil, glob, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(os.path.dirname(HERE))
ORDER = ["pon", "dahai", "chi", "kan", "daiminkan", "kakan", "riichi", "tsumo", "ron", "ryukyoku", "furiten", "furiten2", "furiten3"]
CAST = {"chi": "p39,p03,p36,p17", "pon": "p20,p26,p22,p06", "kan": "p24,p30,p01,p33", "daiminkan": "p05,p14,p31,p18", "kakan": "p34,p27,p23,p11",
        "riichi": "p08,p38,p13,p28", "tsumo": "p15,p25,p07,p02", "ron": "p19,p40,p09,p16", "ryukyoku": "p21,p12,p37,p29", "dahai": "p27,p13,p03,p23",
        "furiten": "p12,p36,p40,p31", "furiten2": "p32,p07,p04,p25", "furiten3": "p35,p18,p10,p37"}      # 自家,下家,対面,上家


DISC = ("chi", "pon", "daiminkan", "ron", "kan", "kakan", "riichi")      # ①の前に、他家が牌を切る・自分が山からツモるコマ（scene.py --disc）がある動画


def arg(k, d):
    a = sys.argv; return a[a.index(k) + 1] if k in a else d


def vv_ok():
    try:
        urllib.request.build_opener(urllib.request.ProxyHandler({})).open("http://127.0.0.1:50021/version", timeout=3).read(); return True
    except Exception:
        return False


def main():
    prev = "--preview" in sys.argv
    fps, samples = ("5", "8") if prev else ("30", "24")
    work = os.path.abspath(arg("--work", os.path.join(os.path.dirname(ROOT), "3d-work")))
    names = [a for a in sys.argv[1:] if a in CAST] or ORDER
    py = sys.executable; assets = os.path.join(ROOT, "まじゃすこ素材")
    tex = os.path.join(work, "tex")
    if not glob.glob(os.path.join(tex, "*.png")):
        os.makedirs(tex, exist_ok=True); subprocess.run([py, os.path.join(HERE, "make_tile_tex.py"), tex], check=True, cwd=ROOT)
    if not vv_ok(): sys.exit("VOICEVOX のエンジンが動いていない（127.0.0.1:50021）。起動してからもう一度")
    for n in names:
        out = os.path.join(assets, "3d", f"{n}-{'preview5' if prev else '30fps'}.mp4")
        if os.path.exists(out) and "--force" not in sys.argv: print("できている:", out); continue
        d = os.path.join(work, ("p5-" if prev else "") + n); os.makedirs(d, exist_ok=True)
        base = [py, os.path.join(HERE, "scene.py"), "--tex", tex, "--out", d, "--scene", n, "--fps", fps, "--size", "540x960", "--samples", samples,
                "--roster", os.path.join(assets, "3d", "roster.json"), "--seats", CAST[n], "--anim"]
        for part in (["--intro"], ["--pre"]) + ((["--disc"],) if n in DISC else ()) + ([], ["--outro"]):
            print(n, part or ["本題"], flush=True); subprocess.run(base + part, check=True, cwd=ROOT)
        if not vv_ok(): sys.exit("VOICEVOX が止まった。起動してからもう一度（絵はできているので、すぐ終わる）")
        subprocess.run([py, os.path.join(HERE, "make_clip.py"), d, out, "--script", n, "--voice", "--sfx", "--music"], check=True, cwd=ROOT)
        if not prev: shutil.rmtree(d, ignore_errors=True)      # 試しの絵は残す（字幕や札だけ直すときは make_clip.py をもう一度動かせばよい）
        print("できた:", out, flush=True)


if __name__ == "__main__":
    main()
