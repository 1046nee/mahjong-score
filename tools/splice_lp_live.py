# -*- coding: utf-8 -*-
"""tools/shoot_lp_live_plan.py が書き出した lp-live-*.html（匿名化済みデータのみ）を、
LPの「これまでの成績が一目でわかる。」の4枚（成績表・通算順位・総当たり表・過去の試合）に埋めこむ。
どのカードもタブのタップで切りかえる（横スワイプは付けない）。通算順位の個人戦・チーム戦と、
過去の試合の個人戦・チーム戦はLPのJS（initLpRank・initLpGames）が組み立てる。
実行: python tools/splice_lp_live.py（先に shoot_lp_live_plan.py を実行しておくこと）"""
import os
import re

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHOTS = os.path.join(BASE, "まじゃすこ素材", "ig", "shots")
IDX = os.path.join(BASE, "index.html")


def read(name):
    return open(os.path.join(SHOTS, name), encoding="utf-8").read().strip()


def kind_wrap_html(prefix):
    """合計/個人戦/チーム戦の3状態を、本物のsk-segボタンをタップして切りかえる1枚にまとめる"""
    panes = ''.join(
        f'<div class="lp-live-in lp-kind-st{" on" if k == "all" else ""}" data-k="{k}">{read(f"lp-live-{prefix}-{k}.html")}</div>'
        for k in ("all", "ind", "team")
    )
    return '<div class="lp-shot lp-touch lp-kind-wrap">' + panes + '</div>'


def main():
    s = open(IDX, encoding="utf-8").read()

    pat = re.compile(r'<figure class="lp-show"><figcaption><b>全員の成績、見比べる？</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>全員の成績、見比べる？</b>'
           '<span>25人でも1枚の表に</span><a href="/news/nakama-page.html">くわしく見る ›</a></figcaption>'
           + kind_wrap_html("grid") + '</figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "grid"

    pat = re.compile(r'<figure class="lp-show"><figcaption><b>あの人に勝ち越してる？</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>あの人に勝ち越してる？</b>'
           '<span>相性が数字でわかる</span><a href="/news/nakama-page.html#h2h">くわしく見る ›</a></figcaption>'
           + kind_wrap_html("h2h") + '</figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "h2h"

    rank_panes = ''.join(
        f'<div class="lp-live-pane{" on" if mk == "score" else ""}"><div class="lp-live-in">{read(f"lp-live-rank-{mk}.html")}</div></div>'
        for mk in ("score", "avg", "top", "las", "pmax", "pmin")
    )
    pat = re.compile(r'<figure class="lp-show"><figcaption><b>仲間の中で何位？</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>仲間の中で何位？</b>'
           '<span>指標を変えると順位も変わる</span>'
           '<a href="/news/nakama-page.html">くわしく見る ›</a></figcaption>'
           '<div class="lp-shot lp-touch-multi" id="lp-live-rank"><div class="lp-live-swipe">' + rank_panes + '</div></div></figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "rank"

    games_panes = ''.join(
        f'<div class="lp-live-pane{" on" if k == "tile" else ""}"><div class="lp-live-in">{read(f"lp-live-games-{k}.html")}</div></div>'
        for k in ("tile", "list", "cal")
    )
    pat = re.compile(r'<figure class="lp-show"><figcaption><b>あの日、どうだった？</b>.*?</figure>', re.S)
    new = ('<figure class="lp-show"><figcaption><b>あの日、どうだった？</b>'
           '<span>打った日ごとに全部残る</span><a href="/news/mypage-stats.html">くわしく見る ›</a></figcaption>'
           '<div class="lp-shot lp-touch-multi" id="lp-live-games"><div class="lp-live-swipe">' + games_panes + '</div></div></figure>')
    s, n = pat.subn(new, s, count=1)
    assert n == 1, "games"

    open(IDX, "w", encoding="utf-8").write(s)
    print("spliced ok, index.html size:", len(s))


def splice_team():
    """チーム戦のデモ（tools/shoot_team_demo.py が書き出す）だけを埋めこむ。実行: python tools/splice_lp_live.py team"""
    s = open(IDX, encoding="utf-8", newline="").read()
    fig = ('<figure class="lp-show" data-team-demo><figcaption><b>どのチームが勝ってる？</b>'
           '<span>4チーム16人の対戦のデモ</span><a href="/blog-team-league.html">くわしく見る ›</a></figcaption>'
           '<div class="lp-shot lp-touch"><div class="lp-live-in">' + read("lp-live-team.html") + '</div></div></figure>')
    pat = re.compile(r'<figure class="lp-show" data-team-demo>.*?</figure>', re.S)
    if pat.search(s):
        s = pat.sub(lambda m: fig, s, count=1)
    else:
        m = re.search(r'<figure class="lp-show"><figcaption><b>あの日、どうだった？</b>.*?</figure>', s, re.S)
        assert m, "games"
        s = s[:m.end()] + "\n        " + fig + s[m.end():]
    open(IDX, "w", encoding="utf-8", newline="").write(s)
    print("team demo ok, index.html size:", len(s))


if __name__ == "__main__":
    import sys
    splice_team() if sys.argv[1:] == ["team"] else main()
