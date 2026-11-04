# -*- coding: utf-8 -*-
"""tools/shoot_lp_live_plan.py が書き出した lp-live-*.html（匿名化済みデータのみ）を、
LPの「これまでの成績が一目でわかる。」の4枚（成績表・通算順位・総当たり表・過去の試合）に埋めこむ。
実行: python tools/splice_lp_live.py（先に shoot_lp_live_plan.py を実行しておくこと）"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "まじゃすこ素材", "ig", "shots")
IDX = os.path.join(BASE, "index.html")


def read(name):
    return open(os.path.join(SHOTS, name), encoding="utf-8").read().strip()


def main():
    s = open(IDX, encoding="utf-8").read()

    grid_html = read("lp-live-grid.html")
    pat = re.compile(r'<figure class="lp-show"><figcaption><b>全員の成績を、1枚の表で</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>全員の成績を、1枚の表で</b>'
           '<span>試合数・着順の回数・トップ率・通算スコアまで、メンバーを横に並べて比べられます。'
           '指で横にスクロールできます。</span><a href="/news/nakama-page.html">くわしく見る ›</a></figcaption>'
           '<div class="lp-shot lp-touch"><div class="lp-live-in">' + grid_html + '</div></div></figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "grid"

    h2h_html = read("lp-live-h2h.html")
    pat = re.compile(r'<figure class="lp-show"><figcaption><b>あの人には勝ち越してる？</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>あの人には勝ち越してる？</b>'
           '<span>全員の総当たりを、1枚の表に。同じ試合で上だった回数で、相性が数字で出ます。'
           '指で横にスクロールできます。</span><a href="/news/nakama-page.html#h2h">くわしく見る ›</a></figcaption>'
           '<div class="lp-shot lp-touch"><div class="lp-live-in">' + h2h_html + '</div></div></figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "h2h"

    rank_panes = ''.join(
        f'<div class="lp-live-pane"><div class="lp-live-in">{read(f"lp-live-rank-{mk}.html")}</div></div>'
        for mk in ("score", "avg", "top", "las")
    )
    pat = re.compile(r'<figure class="lp-show"><figcaption><b>仲間の順位が、表彰台で</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>仲間の順位が、表彰台で</b>'
           '<span>通算スコアも平均着順もトップ率も。指で横にスワイプすると切りかわります。</span>'
           '<a href="/news/nakama-page.html">くわしく見る ›</a></figcaption>'
           '<div class="lp-shot lp-touch-multi" id="lp-live-rank"><div class="lp-live-swipe">' + rank_panes + '</div></div></figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "rank"

    games_panes = ''.join(
        f'<div class="lp-live-pane"><div class="lp-live-in">{read(f"lp-live-games-{k}.html")}</div></div>'
        for k in ("tile", "list")
    )
    pat = re.compile(r'<figure class="lp-show"><figcaption><b>その日の順位とスコアが、ずらり</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>その日の順位とスコアが、ずらり</b>'
           '<span>タイルの一覧から切りかえると、打った日ごとに自分の順位とスコアが並びます。'
           '指で横にスワイプ・縦にスクロールできます。</span><a href="/news/mypage-stats.html">くわしく見る ›</a></figcaption>'
           '<div class="lp-shot lp-touch-multi" id="lp-live-games"><div class="lp-live-swipe">' + games_panes + '</div></div></figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "games"

    open(IDX, "w", encoding="utf-8").write(s)
    print("spliced ok, index.html size:", len(s))


if __name__ == "__main__":
    main()
