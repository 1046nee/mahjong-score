# -*- coding: utf-8 -*-
"""ブログのカテゴリー（テーマ）の一覧ページ・記事のパンくず・サイトマップ・ブログのトップの「テーマから探す」を作る（2026-10-28〜）。
カテゴリーの正は assets/blog-site.js の BLOG_CATS（名前・URL）と BLOG_POSTS（記事ごとの cat）。ここには各テーマの説明文と、
初めて分けたときの記事の振り分け（MAP）を置く。何度実行しても同じ結果。

新しい記事を足したら: BLOG_POSTS の cat をテーマのどれかにして → python tools/blog_cats.py → node tools/build_post_lists.js
新しいテーマを足すときは: BLOG_CATS に1行（group: 'mahjong'）・THEMES に説明・assets/blog.css に色（.cat-キー と .hero-キー）
実行: python tools/blog_cats.py
"""
import io, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hero_ill import ILL  # テーマごとの見出しの絵（2026-10-31〜）

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def rd(p): return io.open(os.path.join(ROOT, p), encoding="utf-8").read()
def wr(p, s): io.open(os.path.join(ROOT, p), "w", encoding="utf-8", newline="").write(s)

# テーマ: キー → (名前, ディレクトリ, meta の説明, 見出しの下の一言, 一覧の上の紹介文, テーマから探すの短い説明)
THEMES = {
    "beginner": ("はじめての麻雀", "beginner",
                 "麻雀をこれから始める人のための入門記事の一覧です。ルールの基本、役、点数の数え方、用語とマナーまで、やさしく解説します。",
                 "ルール・役・点数・用語。まずはここから。",
                 "麻雀をこれから始める人、覚え直したい人のための入門のテーマです。半荘や牌の種類といったルールの基本から、役の覚え方、点数の早見表、用語や漢字の読み方、卓でのマナーまで、図と例でやさしく解説しています。",
                 "ルール・役・点数・用語・マナー"),
    "rules": ("ルールの深掘り", "rules",
              "麻雀のルールの分かれ目、ローカル役、パオや喰い替えなどの細かい決まりを、理由と計算つきで深掘りする記事の一覧です。",
              "「なぜそう決まっているの？」に答える記事",
              "基本を覚えた人が次に出会う「細かい決まり」を深掘りするテーマです。ダブ東の符や頭ハネのような意見が分かれるルール、ローカル役、パオや喰い替え、三麻のルール、麻雀の数字の理由まで、なぜそう決まっているのかを計算と例で確かめています。待ち当てや論述の練習問題もここにあります。",
              "分かれ目・ローカル役・細かい決まり・練習問題"),
    "score": ("スコア・集計", "score",
              "ウマ・オカの計算、通算成績のつけ方、大会やリーグ戦の運営など、仲間内の麻雀の集計を楽にする記事の一覧です。",
              "集計係の悩みを、計算と仕組みで解決",
              "仲間内のセット麻雀の「集計係」のためのテーマです。ウマ・オカのスコア計算、点数が合わないときの確かめ方、日をまたいだ通算成績や相性のつけ方、5人以上の回し打ち、大会・リーグ戦の作り方、スコア記録アプリの選び方までまとめています。",
              "ウマオカ・通算成績・大会の運営・アプリ"),
    "pro": ("Mリーグ・プロ", "pro",
            "Mリーグなど放送対局の見方、プロ団体やタイトル戦、プロになる方法まで、プロの麻雀の世界を紹介する記事の一覧です。",
            "放送対局がもっと面白くなる",
            "Mリーグをはじめとする放送対局と、プロの麻雀の世界のテーマです。観戦の仕方、チームとルール、ポイントの持ち越し、歴代の結果、プロ団体の歴史とルールの違い、タイトル戦、プロになる方法、Mリーガーに会える場所まで紹介しています。",
            "放送対局・Mリーグ・プロ団体・タイトル戦"),
    "ai": ("AI・ゲーム", "ai",
           "麻雀AIの比較と牌譜の分析方法、麻雀ゲームアプリの選び方など、デジタルで麻雀を楽しむための記事の一覧です。",
           "AIとゲームで、麻雀をもっと深く",
           "麻雀AIとゲームのテーマです。NAGA・Mortalなどの麻雀AIの違い、自分の牌譜をAIで分析する手順、雀魂や天鳳などの麻雀ゲームアプリの選び方を紹介しています。これからも新しいAIやサービスが出るたびに記事を増やしていきます。",
           "麻雀AI・牌譜の分析・ゲームアプリ"),
    "culture": ("作品・カルチャー", "culture",
                "麻雀漫画・アニメ・本・YouTube、世界の麻雀や日常語になった麻雀用語など、麻雀のカルチャーを楽しむ記事の一覧です。",
                "読む・観る・知る。麻雀の楽しみ方いろいろ",
                "麻雀を「読む・観る・知る」楽しみのテーマです。麻雀漫画やアニメ、レベル別のおすすめの本、勉強になるYouTube、世界の国や地域の麻雀、日常語になった麻雀用語まで、卓の外の麻雀を紹介しています。",
                "漫画・アニメ・本・YouTube・世界の麻雀"),
}
# 初めて分けたときの振り分け（cat が 'mahjong' のまま残っている記事だけに使う）
MAP = {
    "beginner": "rule-basics yaku-list yaku-ichiran score-table manner sanma-yonma mahjong-yougoshu mahjong-yougo mahjong-kanji",
    "rules": "rule-wakareme local-yaku yakuman-rules pao riichi-ankan kuikae keishiki-tenpai haitei sanma-rules mahjong-suuji house-rules machi-dojo ronjutsu",
    "score": "uma-oka score-examples score-mismatch season-ranking mawashi-uchi team-tournament league-taikai app-guide",
    "pro": "mleague-2026 mleague-history mleague-kansen mleague-points meet-mleaguer mahjong-pro mahjong-titles dantai-rekishi pro-dantai-rules",
    "ai": "mahjong-ai ai-haifu mahjong-game-apps",
    "culture": "mahjong-manga mahjong-anime mahjong-books mahjong-youtube sekai-mahjong nichijougo",
}
URL2THEME = {f"/blog-{slug}.html": k for k, v in MAP.items() for slug in v.split()}


def posts_of(js):
    return re.findall(r"\{ url: '([^']+)', cat: '([a-z]+)'", js)


def main():
    # 1) BLOG_POSTS: まだ 'mahjong' の記事をテーマに振り分ける
    js = rd("assets/blog-site.js")
    def fix(m):
        url = m.group(1)
        assert url in URL2THEME, "テーマが決まっていない記事: " + url
        return f"{{ url: '{url}', cat: '{URL2THEME[url]}'"
    js2 = re.sub(r"\{ url: '([^']+)', cat: 'mahjong'", fix, js)
    if js2 != js:
        wr("assets/blog-site.js", js2)
    posts = posts_of(js2)
    for k in THEMES:
        assert f"{k}:" in js2.split("const BLOG_POSTS")[0], "BLOG_CATS にテーマがない: " + k

    # 2) テーマの一覧ページ（/mahjong/index.html をひな形に）
    tpl = rd("mahjong/index.html")
    old_desc = re.search(r'<meta name="description" content="([^"]+)">', tpl).group(1)
    old_intro = re.search(r'(<p class="cat-intro"[^>]*>)(.*?)(</p>)', tpl, re.S)
    hero_p = re.search(r"<h1>麻雀攻略</h1>\s*<p>(.*?)</p>", tpl, re.S).group(1)
    for k, (name, d, desc, hero, intro, _short) in THEMES.items():
        s = tpl.replace(old_desc, desc).replace("https://majasco.jp/mahjong/", f"https://majasco.jp/{d}/")
        s = s.replace(old_intro.group(0), old_intro.group(1) + intro + old_intro.group(3))
        s = s.replace(f"<h1>麻雀攻略</h1>", f"<h1>{name}</h1>").replace(f"<p>{hero_p}</p>", f"<p>{hero}</p>", 1)
        s = s.replace('data-cat-nav="mahjong"', f'data-cat-nav="{k}"').replace('data-post-list="mahjong"', f'data-post-list="{k}"')
        s = s.replace("hero-mahjong", f"hero-{k}").replace("麻雀攻略", name)
        s = re.sub(r'<div class="hero-ill" aria-hidden="true">.*?</svg></div>', lambda _: f'<div class="hero-ill" aria-hidden="true">{ILL[k]}</div>', s, count=1, flags=re.S)
        os.makedirs(os.path.join(ROOT, d), exist_ok=True)
        wr(f"{d}/index.html", s)

    # 3) /mahjong/ は6テーマをまとめた入口（見出しの下と紹介文にテーマへのリンク）
    links = "・".join(f'<a href="/{d}/">{name}</a>' for name, d, *_ in THEMES.values())
    intro_m = (f"麻雀の記事を、6つのテーマに分けています（{links}）。"
               "このページには、すべてのテーマの記事を新しい順に並べています。ルールの入門から細かい決まりの深掘り、仲間内のスコア計算と集計、Mリーグなどの放送対局、麻雀AIとゲーム、漫画やアニメまで、仲間内の麻雀がもっと楽しくなる記事を開発者のむにぃが書いています。")
    m = rd("mahjong/index.html")
    m2 = re.sub(r'(<p class="cat-intro"[^>]*>)(.*?)(</p>)', lambda x: x.group(1) + intro_m + x.group(3), m, count=1, flags=re.S)
    if m2 != m:
        wr("mahjong/index.html", m2)

    # 4) 記事のパンくず: トップ ＞ ブログ ＞ テーマ ＞ 記事
    for url, cat in posts:
        if cat not in THEMES:
            continue
        f = url.lstrip("/")
        if not os.path.exists(os.path.join(ROOT, f)):
            continue
        s = rd(f)
        name, d = THEMES[cat][0], THEMES[cat][1]
        t = re.sub(r'(<nav class="crumbs"><a href="/">トップ</a> ＞ <a href="/blog.html">ブログ</a> ＞ )<a href="/[a-z]+/">[^<]+</a>',
                   lambda x: x.group(1) + f'<a href="/{d}/">{name}</a>', s, count=1)
        assert f'<a href="/{d}/">{name}</a>' in t, "パンくずが見つからない: " + f
        if t != s:
            wr(f, t)

    # 5) サイトマップにテーマのページ
    sm = rd("sitemap.xml")
    for _n, d, *_ in THEMES.values():
        if f"https://majasco.jp/{d}/</loc>" not in sm:
            sm = sm.replace("</urlset>", f"  <url>\n    <loc>https://majasco.jp/{d}/</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.7</priority>\n  </url>\n</urlset>")
    wr("sitemap.xml", sm)

    # 6) ブログのトップ（blog.html）の「テーマから探す」は2026-10-31に消した（上のテーマのタブと重なるため。カードの格子は使わない）。残っていたら消す
    b = rd("blog.html")
    b2 = re.sub(r"<!--themes-->.*?<!--/themes-->\n*", "", b, flags=re.S)
    # 紹介文の「3カテゴリ」の言い方
    b2 = re.sub(r"記事は<a href=\"/mahjong/\">麻雀攻略</a>・<a href=\"/news/\">お知らせ</a>・<a href=\"/blog/\">雑記</a>の3カテゴリに分かれています。",
                "麻雀の記事は6つのテーマ（下の「テーマから探す」）と、お知らせ・雑記に分かれています。", b2)
    wr("blog.html", b2)
    print("テーマ", len(THEMES), "・記事", sum(1 for _, c in posts if c in THEMES), "本")


if __name__ == "__main__":
    main()
