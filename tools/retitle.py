# -*- coding: utf-8 -*-
"""記事のタイトルの付け直し（2026-10-30〜・ユーザーの依頼「YouTubeの動画タイトルのように、クリックしたくなる・記事ごとに区別できるタイトル」）。
決まり（docs/blog-spec.md「タイトルの付け方」）: 検索語を先頭／【図解】【保存版】【10分でわかる】など得られるものを短く／数字・固有名で区別／35〜45字ほど。
<title>・h1・og:title・twitter:title・Article の headline・BLOG_POSTS の title をそろえて書きかえる。何度実行しても同じ結果。
実行: python tools/retitle.py
"""
import io, os, re, json

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TITLES = {
 "blog-ai-haifu.html": "【10分でわかる】麻雀AIで牌譜を分析する方法｜雀魂MAKA・Mortal・NAGAの使い方と無料・有料",
 "blog-mahjong-suuji.html": "麻雀の「なぜこの数字？」に全部答える｜136枚・王牌14枚・満貫8,000点の理由【図解】",
 "blog-sekai-mahjong.html": "【世界一周】麻雀は国でこんなに違う｜手牌16枚の台湾・ジョーカーのアメリカ・中国の公式ルール",
 "blog-nichijougo.html": "実は麻雀用語だった！日常語8選｜テンパる・安パイ・連チャンのもとの意味",
 "blog-ronjutsu.html": "【プロテスト対策】麻雀ルールの論述問題8問｜解答例と採点のポイントつき",
 "blog-mleague-points.html": "【図解】Mリーグのポイントは2回半分になる｜大逆転が起きる持ち越しの計算",
 "blog-league-taikai.html": "仲間内の麻雀大会・リーグ戦の作り方｜持ち越し方式で優勝者が変わる！全部・半分・リセットを計算",
 "blog-sanma-rules.html": "三麻のルールの分かれ目【図解】｜北抜き・花牌・白ぽっち・焼き鳥・ツモ損を牌の絵で",
 "blog-haitei.html": "【知らないとチョンボ】海底・河底の決まり｜最後の1枚でカン・リーチ・鳴きはできる？",
 "blog-keishiki-tenpai.html": "形式テンパイ・空テンはテンパイになる？｜流局の3,000点の分け方を図で【ノーテン罰符】",
 "blog-kuikae.html": "【知らないとアガリ放棄】喰い替えとは｜鳴いたあとに切れない牌を図でひと目で",
 "blog-riichi-ankan.html": "リーチ後の暗槓、していい？だめ？｜3つの質問でわかる判定チャート【手牌の例つき】",
 "blog-pao.html": "パオ（責任払い）とは｜大三元・大四喜で誰がいくら払う？計算問題6問【図解】",
 "blog-yakuman-rules.html": "同じ役満でも点数が2倍に!? Mリーグと雀魂の役満ルールの違い｜四暗刻単騎・国士13面",
 "blog-mahjong-anime.html": "麻雀アニメおすすめ7選【2026年】｜咲・アカギ・ぽんのみちはどこで見られる？配信一覧",
 "blog-mahjong-manga.html": "麻雀漫画おすすめ10選｜咲・アカギ・天・哲也…好みで選ぶ最初の1冊",
 "blog-rule-wakareme.html": "麻雀ルールの分かれ目6選【どっち派？】｜ダブ東は2符か4符か・ダブロンか頭ハネか",
 "blog-local-yaku.html": "ローカル役満・ローカル役一覧｜八連荘・大車輪・紅孔雀を牌の絵で【中国・台湾の役も】",
 "blog-mahjong-kanji.html": "麻雀用語の漢字の意味｜「混」と「清」がわかると役の名前が一気に覚えられる",
 "blog-machi-dojo.html": "【練習問題14問】麻雀の待ち当て道場｜三面張・ノベタン・エントツを見抜く",
 "blog-mahjong-yougoshu.html": "麻雀用語集137語【読み方つき・五十音順】｜正式名称・通称・俗語がひと目でわかる",
 "blog-dantai-rekishi.html": "麻雀プロ団体の歴史を年表で｜連盟・最高位戦・協会・RMU・麻将連合の成り立ちと代表",
 "blog-mahjong-yougo.html": "麻雀の正式名称80語【図で覚える】｜漢字と読み方・暗記モードつき（プロテスト対策）",
 "blog-mleague-kansen.html": "【初心者向け】Mリーグ観戦ガイド｜卓の見方7つ・実況の言葉・ポイントのしくみ",
 "blog-yaku-ichiran.html": "麻雀の役一覧 全38役【保存版】｜翻数・鳴いたときの翻数を牌の絵でひと目で",
 "blog-mahjong-game-apps.html": "麻雀ゲームアプリおすすめ7選【2026年】｜雀魂・天鳳・MJ・麻雀格闘倶楽部を目的別に比較",
 "blog-mahjong-youtube.html": "麻雀が強くなるYouTube【レベル別】｜未経験〜上級者の勉強動画とMリーグ公式チャンネル",
 "blog-mahjong-books.html": "麻雀のおすすめ本19冊【レベル別・2026年】｜最初の1冊から上級者の理論書まで",
 "blog-meet-mleaguer.html": "Mリーガーに会える場所まとめ【2026-27】｜パブリックビューイング・撮影会・一緒に打てるイベント",
 "blog-mahjong-pro.html": "麻雀プロになるには【2026年版】｜プロテストの日程・試験内容・費用を団体別に",
 "blog-mahjong-titles.html": "麻雀のタイトル戦と今のタイトル保持者【2026年】｜鳳凰位・最高位・雀王・最強位",
 "blog-mleague-2026.html": "Mリーグ2026-27完全ガイド｜全10チーム40選手・ルール・試合の流れを1ページで",
 "blog-mleague-history.html": "Mリーグの歴史を年表で【2018〜2026】｜歴代優勝チーム・MVP・各シーズンの順位",
 "blog-pro-dantai-rules.html": "麻雀プロ団体のルールの違い【比較表】｜連盟・最高位戦・協会・RMU・麻将連合とMリーグ",
 "blog-mahjong-ai.html": "【5分でわかる】麻雀AIの違い｜NAGA・Mortal・MAKA・Suphx・LuckyJ、使えるのはどれ？",
 "blog-season-ranking.html": "麻雀仲間の通算成績と相性のつけ方｜「あの人に勝てない」を数字で確かめる",
 "blog-house-rules.html": "【揉めない】セット麻雀のルールの決め方｜打つ前に決める10項目チェックリスト",
 "blog-score-mismatch.html": "麻雀の点数が合わない！原因はズレ幅でわかる｜集計係のチェックリスト",
 "blog-mawashi-uchi.html": "5人以上の麻雀の回し方｜抜け番の決め方と、試合数が違っても公平な成績の見方",
 "blog-team-tournament.html": "麻雀を10人以上で楽しむ方法｜チーム対抗戦・トーナメントの開き方【蛇行ドラフト】",
 "blog-manner.html": "麻雀の準備とマナー【初心者向け】｜持ち物リスト・チョンボ・揉めやすいNG所作",
 "blog-rule-basics.html": "【初心者向け】麻雀のルール基本の基本｜半荘・東風戦と牌の種類・読み方を図解",
 "blog-app-guide.html": "麻雀のスコア記録アプリの選び方【2026年】｜5つのポイントと主要アプリの比較",
 "blog-sanma-yonma.html": "3人麻雀（サンマ）と4人麻雀の違い【早見表】｜牌・持ち点・ウマ・ツモ損",
 "blog-yaku-list.html": "【初心者がまず覚える】麻雀の役10個・リーチ・ドラ・鳴き｜全部牌の絵で解説",
 "blog-score-table.html": "麻雀の点数早見表【1枚で見やすい】｜子・親のロン・ツモ（オール）と符計算・満貫以上",
 "blog-uma-oka.html": "麻雀のウマ・オカとは？【図解】｜スコアの計算が3つの足し算でわかる入門",
}
BAN = ("円", "金額", "精算", "賭け", "レート", "収支", "換算", "倍率", "係数", "いま")


def esc(x):
    return x.replace("&", "&amp;").replace('"', "&quot;")


def main():
    for t in TITLES.values():
        for w in BAN:
            assert w not in t, (w, t)
        assert len(t) <= 60, (len(t), t)
    js_p = os.path.join(ROOT, "assets", "blog-site.js")
    js = io.open(js_p, encoding="utf-8").read()
    n = 0
    for f, t in TITLES.items():
        p = os.path.join(ROOT, f)
        s = io.open(p, encoding="utf-8").read()
        o = s
        s = re.sub(r"<title>.*?</title>", f"<title>{t} | まじゃすこ</title>", s, count=1)
        for prop in ('property="og:title"', 'name="twitter:title"'):
            s = re.sub(rf'<meta {prop} content="[^"]*">', f'<meta {prop} content="{esc(t)}">', s, count=1)
        s = re.sub(r'("@type": "Article", "headline": )"(?:[^"\\]|\\.)*"', lambda m: m.group(1) + json.dumps(t, ensure_ascii=False), s, count=1)
        s = re.sub(r"(<article class=\"blog-post\">\s*(?:<[^h][^>]*>\s*)*)<h1>.*?</h1>", lambda m: m.group(1) + f"<h1>{t}</h1>", s, count=1, flags=re.S)
        assert f"<h1>{t}</h1>" in s, ("h1", f)
        if s != o:
            io.open(p, "w", encoding="utf-8", newline="").write(s); n += 1
        js, k = re.subn(r"(\{ url: '/" + re.escape(f) + r"',[^}]*?title: )'[^']*'", lambda m: m.group(1) + "'" + t.replace("'", "\\'") + "'", js, count=1)
        assert k == 1, ("BLOG_POSTS", f)
    io.open(js_p, "w", encoding="utf-8", newline="").write(js)
    print(n, "記事のタイトルを書きかえ")


if __name__ == "__main__":
    main()
