# -*- coding: utf-8 -*-
"""Instagram用：点数早見表のカルーセル7枚（1080×1350）を作る（2026-11-11〜）。2枚目は全部をまとめた1枚（ユーザーの指定）。
中身は tools/score_sheet.py が作る assets/score/ の画像をそのまま使う（先に python tools/score_sheet.py）。
出力: まじゃすこ素材/ig/score/score-1〜7.png
実行: python tools/make_ig_score.py
"""
import io, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCORE = "file:///" + os.path.join(ROOT, "assets", "score").replace("\\", "/")
LOGO = "file:///" + os.path.join(ROOT, "assets", "favicon.png").replace("\\", "/")
OUT = os.path.join(ROOT, "まじゃすこ素材", "ig", "score")

CSS = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { width: 1080px; height: 1350px; overflow: hidden; }
body { font-family: 'Noto Sans JP', sans-serif; background: #E4F3EC; color: #1F2A28; position: relative; font-feature-settings: "palt"; }
.band { background: #177083; color: #fff; padding: 34px 60px 30px; }
.band .no { display: inline-block; background: #E75620; color: #fff; font-size: 30px; font-weight: 900; border-radius: 8px; padding: 2px 16px; margin-right: 14px; vertical-align: 6px; line-height: 1.4; }
.band h1 { font-size: 64px; font-weight: 900; letter-spacing: .02em; line-height: 1.2; }
.band p { font-size: 30px; font-weight: 700; color: #DDF0EC; margin-top: 8px; }
.pic { position: absolute; left: 0; right: 0; top: 214px; bottom: 96px; display: flex; align-items: center; justify-content: center; }
.pic img { max-width: 960px; max-height: 100%; border-radius: 14px; box-shadow: 0 0 0 3px #9FC3BD; background: #fff; }
.foot { position: absolute; left: 60px; right: 60px; bottom: 28px; display: flex; align-items: center; justify-content: space-between; font-size: 26px; font-weight: 800; color: #177083; }
.foot span { display: flex; align-items: center; gap: 12px; } .foot img { width: 44px; height: 44px; border-radius: 10px; }
.foot small { font-size: 24px; color: #4F7F77; font-weight: 700; }
/* 表紙 */
.cover { padding: 80px 70px 0; }
.cover .kicker { display: inline-block; background: #E75620; color: #fff; font-size: 40px; font-weight: 900; border-radius: 10px; padding: 4px 22px; }
.cover h1 { font-size: 116px; font-weight: 900; color: #177083; line-height: 1.15; margin-top: 26px; letter-spacing: .02em; }
.cover h2 { font-size: 40px; font-weight: 800; margin-top: 18px; line-height: 1.5; }
.sheet { position: absolute; right: 64px; bottom: 112px; width: 470px; transform: rotate(4deg); border-radius: 12px; box-shadow: 0 0 0 4px #177083, 14px 16px 0 #9FC3BD; }
.cover ul { list-style: none; margin-top: 44px; }
.cover li { font-size: 38px; font-weight: 900; margin: 0 0 18px; padding-left: 50px; position: relative; }
.cover li::before { content: ""; position: absolute; left: 0; top: 14px; width: 30px; height: 30px; border-radius: 50%; background: #177083; }
.swipe { position: absolute; left: 70px; bottom: 140px; font-size: 34px; font-weight: 900; color: #E75620; }
/* 締め */
.close { padding: 120px 80px 0; text-align: center; }
.close h1 { font-size: 72px; font-weight: 900; line-height: 1.35; color: #177083; }
.close .box { margin: 54px auto 0; background: #fff; border: 4px solid #177083; border-radius: 18px; padding: 40px 30px; }
.close .q { display: inline-block; font-size: 54px; font-weight: 900; border: 4px solid #1F2A28; border-radius: 60px; padding: 10px 46px; background: #fff; }
.close .box p { font-size: 38px; font-weight: 800; margin-top: 28px; line-height: 1.6; }
.close .box b { color: #E75620; }
.close .app { margin-top: 56px; font-size: 38px; font-weight: 800; line-height: 1.7; }
.close .app em { font-style: normal; display: inline-block; background: #E75620; color: #fff; border-radius: 50px; padding: 8px 40px; margin-top: 18px; font-size: 40px; font-weight: 900; }
"""

FOOT = f'<div class="foot"><span><img src="{LOGO}">まじゃすこ majasco.jp</span><small>麻雀のスコア記録アプリ</small></div>'


def page(body):
    return (f'<!doctype html><html lang="ja"><head><meta charset="utf-8">'
            f'<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;700;800;900&display=block" rel="stylesheet">'
            f'<style>{CSS}</style></head><body>{body}</body></html>')


def part(no, title, sub, img):
    return page(f'<div class="band"><h1><span class="no">{no}</span>{title}</h1><p>{sub}</p></div>'
                f'<div class="pic"><img src="{SCORE}/{img}"></div>{FOOT}')


SLIDES = [
    ("score-1.png", page(
        f'<div class="cover"><span class="kicker">完全版</span><h1>麻雀<br>点数早見表</h1>'
        f'<h2>子・親のロン・ツモを<br>1枚にまとめました</h2>'
        f'<ul><li>20符〜110符・1〜4翻</li><li>満貫から役満まで</li><li>符の数え方を牌の絵で</li></ul></div>'
        f'<img class="sheet" src="{SCORE}/tensu-hayamihyo-web.png"><p class="swipe">スワイプして見る →</p>{FOOT}')),
    ("score-2.png", page(f'<div class="band"><h1>全部まとめて1枚</h1><p>子・親・満貫から上・符の数え方（次から1つずつ大きく）</p></div>'
                         f'<div class="pic"><img src="{SCORE}/tensu-hayamihyo.png"></div>{FOOT}')),
    ("score-3.png", part("1", "子の点数", "上がロン、下がツモ（子の払い-親の払い）", "tensu-ko.png")),
    ("score-4.png", part("2", "親の点数", "上がロン、下がツモ（ALL＝子3人が同じ額）", "tensu-oya.png")),
    ("score-5.png", part("3", "満貫から上", "符に関係なく、翻だけで決まる", "tensu-mangan.png")),
    ("score-6.png", part("4", "符の数え方", "足して、10の位で切り上げ", "fu-keisan.png")),
    ("score-7.png", page(
        '<div class="close"><h1>保存しなくて<br>大丈夫です</h1>'
        '<div class="box"><span class="q">麻雀　点数表</span><p>と検索すれば、<br><b>この早見表がいつでも出てきます</b></p></div>'
        '<p class="app">半荘が終わったら、スコアの集計は<br><em>まじゃすこ</em></p></div>' + FOOT)),
]


def main():
    from playwright.sync_api import sync_playwright
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=os.environ.get("PW_CHROMIUM") or None)
        for name, html in SLIDES:
            hp = os.path.join(OUT, "_tmp.html")
            io.open(hp, "w", encoding="utf-8").write(html)
            pg = b.new_page(viewport={"width": 1080, "height": 1350})
            pg.goto("file:///" + hp.replace("\\", "/")); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(900)
            pg.screenshot(path=os.path.join(OUT, name))
            pg.close(); os.remove(hp)
            print(name)
        b.close()


if __name__ == "__main__":
    main()
