# サイト共通仕様（ファイル構成・SEO・広告・計測・固定ページ）

## ファイル構成
- `index.html` — アプリ本体（SPA・全画面が1ファイル → docs/app-spec.md / docs/lp-spec.md）
- `blog.html` / `blog-*.html` / `mahjong/` `news/` `blog/` — ブログ（→ docs/blog-spec.md）
- `score-basics.html` — スコア計算の基本（Article JSON-LD・関連記事への内部リンク・lp_bottom枠）
- `faq.html` — よくある質問7問（**FAQPage JSON-LDはここ。本文と一致させる**）
- `terms.html` / `privacy.html` — 規約・PP（AdSense必須文言含む。広告枠は置かない）
- `404.html` — カスタム404（noindex。blog-site.jsは読み込む）
- `tests.html` — 計算ロジックの単体テスト（noindex → docs/app-spec.md）
- `sitemap.xml` / `robots.txt` — **新ページを追加したらsitemap.xmlに`<url>`を1件追加**
- `assets/` — favicon.png(512) / logo.png(800×250透過) / ogp2.png(現行OGP) / ogp.png(旧・残置) / blog.css / blog-site.js / ads.js
- `favicon.ico` — ルート直下16/32/48px（→ docs/image-tools.md）
- `manifest.json` — PWA最小構成
- `docs/` `tools/` `CLAUDE.md` — 開発用。**firebase.jsonのignoreで配信除外済み**
- `まじゃすこ素材/` — 画像素材の元データ（本体リポジトリには含めない=.gitignore。
  **privateリポジトリ 1046nee/majasco-assets で管理**（→ docs/image-tools.md）。firebase.jsonのignoreでも配信除外）

## デプロイ
- mainへpush → GitHub Actions（.github/workflows/firebase-hosting-merge.yml）→ Firebase Hosting自動デプロイ
- Firebase設定は firebase.json / .firebaserc にコミット済み

## 新ページのheadチェックリスト（blog記事のheadを参照）
1. GTMスクリプト（viewport直後・titleより上）+ body直後にGTM noscript
2. AdSenseメタタグ＋adsbygoogle.js（GTM直後）
3. title / meta description / canonical
4. favicon（/favicon.ico + /assets/favicon.png）+ apple-touch-icon + manifest
5. OGP（og:title/description/url/type/site_name/locale/image+width+height）
6. twitter:card(summary_large_image) + twitter:site(@majasco_jp) + twitter:image + **twitter:title + twitter:description**
7. sitemap.xmlに追加

## 構造化データ
- 全記事: Article JSON-LD（headline/description/datePublished/mainEntityOfPage）
- faq.html: FAQPage（7問・本文一致）／ index: WebSite + Organization（検索のサイト名・ロゴ向け）

## 広告（AdSense）
- パブリッシャーID `ca-pub-9998035509478799`。ads.txt設置済み
- **サイト審査: 2026-07-10申請、審査待ち（「準備中」）**。「準備完了」になるまで広告は配信されない（実装が正しくてもunfilledが返る）。
  審査は通常数日〜2/4週間。承認を確認したらこの行を「承認済み」に更新する
- 枠は `/assets/ads.js` の AD_SLOTS で管理: article_top / article_bottom / list_bottom / lp_bottom（4枠配信中）
- スロットID空欄=非表示。追加時はAdSenseでディスプレイ広告ユニット作成→IDをAD_SLOTSへ（min-height:280px自動でCLS対策）
- **置かない場所**: スコア入力・ゲーム画面・設定モーダル・privacy/terms・404（誤クリック防止）

## 計測
- GTM `GTM-KMRMGKKV` 全ページ設置済み。index.htmlの`track()`がdataLayerへ送信
  （group_create / group_join / round_submit / share_copy）
- GA4はGTM経由で配信する構成を推奨（GTM管理画面でGA4タグを追加。コード変更不要）

## ブログ系ページの共通ヘッダー/フッター
- `/assets/blog-site.js` の `renderChrome()` が一元描画（LPと同じ見た目=中央ロゴ64px・右上「使い方」・緑2列フッター）
- 各HTMLの静的.site-head/.site-footはJS無効時のフォールバック。**デザイン変更はrenderChromeだけ直す**

## 検索まわりの注意
- 検索結果のfavicon・サイトリンクはGoogle側依存。新ページはSearch Consoleでインデックス登録リクエスト推奨
- XのOGPカードはURL単位で約1週間キャッシュ（→ docs/image-tools.md）

## 落とし穴
- firebase.jsonのpublicは「.」= リポジトリ全部配信。**開発用ファイルを増やしたらignoreに追加すること**
- アセット（blog.css/blog-site.js）はブラウザキャッシュが強い。検証時は fetch(url, {cache:'reload'}) やクエリ付きで確認
- **アプリのUI名・文言を変えたら faq / score-basics / news記事などの外部ページの言及も同時に更新する**
  （2026.07: 「変更」ボタン→設定の編集、対局形式→試合形式、レート、旧倍率例示、個人成績→その他成績 が外部ページに残っていた。
  faq.htmlはFAQPage JSON-LDも本文とセットで直す）
