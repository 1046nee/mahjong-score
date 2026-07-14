# ブログ仕様・記事運用

## 構成
- カテゴリ: `/mahjong/`（麻雀攻略）・`/news/`（お知らせ）・`/blog/`（雑記）。`blog.html`=全記事一覧
- **既存記事のURL（ルート直下のblog-*.html）は変えない**（インデックス維持）。お知らせだけ `/news/xxx.html`
- 記事メタは `/assets/blog-site.js` の **BLOG_POSTS で一元管理**（url/cat/date/tag/title/desc/recommended）。
  一覧・カテゴリ・サイドバー・カテゴリナビはここから自動描画
- 共通スタイル `/assets/blog.css`（一覧=body.bs-list、記事=.post-layout/.side/.cat-nav。PC=右サイドバー、900px以下=縦積み）
- RSS: `/news/feed.xml`（手書きRSS2.0）。ブラウザで開くと `/news/feed.xsl` がデザイン付きで描画

## モバイル表示ルール（右切れ対策）
- `.post-layout > * { min-width: 0 }` 必須（グリッドが幅広コンテンツで広がるのを防ぐ）
- 記事内の表はblog-site.jsが `.table-scroll` に包む。**4列以上はmin-width:520pxで横スクロール**（潰さない）
- body { overflow-x: hidden } の保険つき

## 記事のイラスト（3点構成）
- 冒頭（.post-illust 340×150）＋中盤（.post-illust.small 340×84）＋締め（トロフィー共通SVG・article_bottom枠の直前）
- 絵文字は使わずインラインSVG（フラットトーン: #177083・#9fc3bd・#E4F3EC・差し色#E75620）
- **イラスト内のスマホに「まじゃすこ」等の文字は入れない**（サイズが合わない）

## CTA
- 記事末尾 `.cta-link`・一覧 `.app-btn` はLPのCTAと同形（影なし・ピルradius50px・max-width380px・blog.cssの!importantで統一済み）

## 記事の追加手順
1. 既存の `blog-*.html`（お知らせは `news/update-2026-07.html`）をコピーして執筆。
   head一式（docs/site-spec.mdのチェックリスト）・パンくず・.post-layout＋sidebar・広告枠（article_top/bottom）・末尾CTA・
   blog.css/blog-site.js/ads.jsの読み込みを維持。**Article JSON-LDを新記事の内容に書き換える**
2. BLOG_POSTSの**先頭**に1件追加
3. sitemap.xmlに`<url>`追加
4. お知らせなら `/news/feed.xml` に`<item>`追加（lastBuildDateも更新）
5. 関連記事と内部リンクを張り合う。このdocの記事一覧を更新

## 執筆の用語注意
- 符・翻・役を解説する記事は「点数計算」をテーマにしてよいが、**アプリの守備範囲の説明は「半荘の集計」「スコア計算」**に切り替える
- NG例: 「点数計算の基本」という見出しでウマ・オカを説明（→見出しは「スコア計算」に）
- OK例: 「符・翻の点数計算は自分で。半荘のスコア集計は、まじゃすこで。」

## 公開済み記事一覧（16記事）
1. blog-why-majasco.html — 開発ストーリー
2. blog-uma-oka.html — ウマ・オカ入門
3. blog-score-table.html — 翻・符の点数早見表
4. blog-yaku-list.html — 基本役10選
5. blog-fu-han.html — 符と翻の仕組み
6. blog-sanma-yonma.html — 三麻と四麻の違い
7. blog-app-guide.html — スコア記録アプリの選び方
8. blog-hai-types.html — 麻雀牌の種類と名前
9. blog-rule-basics.html — 半荘・東風戦とは
10. blog-riichi.html — リーチとは
11. blog-manner.html — マナーとチョンボ・途中流局
12. blog-starter-kit.html — 持ち物リスト
13. blog-dora.html — ドラの仕組み
14. blog-naki.html — 鳴きの基本
15. news/update-2026-07.html — 大型アップデートのお知らせ
16. news/csv-export.html — 対局履歴のCSVエクスポート対応のお知らせ

## 記事アイデア（候補）
- 麻雀の歴史・起源／オンライン麻雀と対面の違い／点数申告の言い方

## 落とし穴
- グリッドのmin-width:auto問題（上記）。過去に右切れの原因になった
- blog-site.js/blog.cssはキャッシュされやすい（検証はcache:'reload'）
