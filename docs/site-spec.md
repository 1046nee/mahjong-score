# サイト共通仕様（ファイル構成・SEO・広告・計測・固定ページ）

## ファイル構成
- `index.html` — アプリ本体（SPA・全画面が1ファイル → docs/app-spec.md / docs/lp-spec.md）
- `blog.html` / `blog-*.html` / `mahjong/` `news/` `blog/` — ブログ（→ docs/blog-spec.md）
- `about.html` — 運営者情報（むにぃ名義・ProfilePage JSON-LD。著者ブロック/フッターからリンク。広告枠は置かない）
- `score-basics.html` — スコア計算の基本（Article JSON-LD・関連記事への内部リンク・lp_bottom枠）
- `faq.html` — よくある質問7問（**FAQPage JSON-LDはここ。本文と一致させる**）
- `terms.html` / `privacy.html` — 規約・PP（AdSense必須文言含む。広告枠は置かない）
- `404.html` — カスタム404（noindex。blog-site.jsは読み込む）
- `tests.html` — 計算ロジックの単体テスト（noindex → docs/app-spec.md）
- `sitemap.xml` / `robots.txt` — **新ページを追加したらsitemap.xmlに`<url>`を1件追加**（`<lastmod>`付き。既存ページも大きく更新したらlastmodを更新）
- `assets/` — favicon.png(512) / logo.png(800×250透過) / ogp2.png(現行OGP) / ogp.png(旧・残置) / blog.css / blog-site.js / ads.js
- `favicon.ico` — ルート直下16/32/48px（→ docs/image-tools.md）
- `manifest.json` — PWA最小構成
- `docs/` `tools/` `CLAUDE.md` — 開発用。**firebase.jsonのignoreで配信除外済み**
- `まじゃすこ素材/` — 画像素材の元データ（本体リポジトリには含めない=.gitignore。
  **privateリポジトリ 1046nee/majasco-assets で管理**（→ docs/image-tools.md）。firebase.jsonのignoreでも配信除外）

## デプロイ
- mainへpush → GitHub Actions（.github/workflows/firebase-hosting-merge.yml）→ **スモークテスト → 合格時のみ**Firebase Hosting自動デプロイ
- スモークテスト = tools/smoke_test.py（LP表示→グループ作成→URL共有→別タブで自動参加→点数入力→結果表示の主要動線を実ブラウザで検証。
  2026-07-18の「共有URLで開くとLPしか出ない」障害の再発防止。落ちたらActionsのログで原因を確認して修正後に再push）
- Firebase設定は firebase.json / .firebaserc にコミット済み

## RTDBセキュリティルール（database.rules.json）
- **正はリポジトリの database.rules.json**。ただしGitHub ActionsはHostingしかデプロイしないので、
  変更したら**Firebaseコンソール（Realtime Database → ルール）に手動で貼り付けて「公開」**が必要（ユーザー作業）
- 内容: ルート読み書き禁止／`sessions/$id`のみ読み書き可／IDは10桁または**22桁**（初期のIDは22桁だった。10桁だけにすると旧グループが書き込み不能になる）／
  新規作成は id・name・settings 必須（updateによる部分書き込みでの新規作成も`.write`側で拒否）／
  name≤120字・playerNames≤60字・rounds/logは最大10,000件（インデックス4桁まで）／**未知のトップレベルキーは拒否（$other: false）**
- **セッションに新しいトップレベルキーを追加するときは、必ずdatabase.rules.jsonにも追加してコンソールに再適用する**（忘れると保存が全部失敗する）
- 認証なし運用のため完全な防御ではない（本命はApp Check）。目的は「sessions外への書き込み禁止」「ゴミデータの容量攻撃の抑止」

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
- **サイト審査: 2026-07-10申請 → 2026-07-17不合格（「有用性の低いコンテンツ」）→ 対策実施中**。
  実施済み: 記事増強（全14記事を2,300〜3,000字）・運営者ページ/著者ブロック（E-E-A-T）・新規記事追加。
  **Phase 1（技術・構造対策）は2026-07-13完了**: 一覧4ページの静的HTML化+カテゴリ説明文（tools/build_post_lists.js）／
  全ページのフッター12リンク統一（運営者について含む）／faq 13問化・score-basics増補（計算実例・チップ収支・よくあるミス）／
  news記事2本をnoindex+sitemap除外／ads.jsの可視ビュー限定初期化。
  **残り=Phase 2（記事の独自性注入）**: 全記事が同一テンプレ量産に見える問題への対策。記事ごとに固有の図版（牌姿図・実画面）・
  体験談・独自データを注入し、開発ログ/体験記型の新規記事を2〜3本追加してから再申請。
  **再申請に「2週間空ける」公式ルールはない**（修正の質が全て）。全対策完了後に1回で申請する（ユーザー操作）。承認されたらこの行を「承認済み」に更新
- 枠は `/assets/ads.js` の AD_SLOTS で管理: article_top / article_bottom / list_bottom / lp_bottom（4枠配信中）
- スロットID空欄=非表示。追加時はAdSenseでディスプレイ広告ユニット作成→IDをAD_SLOTSへ（min-height:280px自動でCLS対策）
- **置かない場所**: スコア入力・ゲーム画面・設定モーダル・privacy/terms・404（誤クリック防止）

## 計測
- GTM `GTM-KMRMGKKV` 全ページ設置済み。index.htmlの`track()`がdataLayerへ送信
  （group_create / group_join / round_submit / share_copy）
- GA4はGTM経由で配信する構成を推奨（GTM管理画面でGA4タグを追加。コード変更不要）

## ブログ系ページの共通ヘッダー/フッター
- `/assets/blog-site.js` の `renderChrome()` が一元描画（LPと同じ見た目=中央ロゴ48px・右上「使い方」・緑2列フッター）
- 各HTMLの静的.site-head/.site-footはJS無効時のフォールバック。デザイン変更はrenderChromeを直す
- **フッターは全ページ標準12リンク・同一順序**: トップ/スコア計算の基本/よくある質問/ブログ/お知らせ/お知らせRSS/
  利用規約/プライバシーポリシー/運営者について/お問い合わせ/X（公式）/Instagram（公式）。
  **renderChromeと静的HTML（.site-foot・固定ページの.footer・index.htmlの.footer-links）の両方を同じ内容に保つ**
  （静的側はAdSense/クローラー対策の本体。リンクを増減するときは全部直す）
- **一覧4ページ（blog.html・/mahjong/・/news/・/blog/）の記事カードは静的HTML**。
  新記事公開時は BLOG_POSTS 追加後に `node tools/build_post_lists.js` を実行して再生成（→ docs/blog-spec.md）。
  各一覧の冒頭には200字以上のカテゴリ説明文（.cat-intro）を置く（空のJSシェルに戻さない）

## 検索まわりの注意
- **サイト内リンクは `/`（トップ）表記で統一。`index.html` と書かない**（重複URLがクロールされ
  Search Consoleの未登録一覧に出続ける。2026-07-28に96箇所を一括修正済み。canonicalは`/`）
- 検索結果のfavicon・サイトリンクはGoogle側依存。新ページはSearch Consoleでインデックス登録リクエスト推奨
- XのOGPカードはURL単位で約1週間キャッシュ（→ docs/image-tools.md）

## 落とし穴
- **AdSense審査は「形式要件OK」でも通らない**（2026-07-17に「有用性の低いコンテンツ」で不合格）。
  効くのは記事の量（2,500字級）・独自性（実体験・独自データ）・E-E-A-T（運営者ページ・著者表記）。再申請は2〜4週間空ける
- 全記事のArticle JSON-LDのauthorは Person（むにぃ・/about.htmlへリンク）で統一。著者ブロックはblog-site.jsが自動挿入（HTML個別編集不要）
- firebase.jsonのpublicは「.」= リポジトリ全部配信。**開発用ファイルを増やしたらignoreに追加すること**
- アセット（blog.css/blog-site.js）はブラウザキャッシュが強い。検証時は fetch(url, {cache:'reload'}) やクエリ付きで確認
- **Hostingのキャッシュヘッダー未設定だとデフォルトmax-age=3600**で、不具合修正が最大1時間ユーザーに届かない
- SPAのビュー切替は非同期なので、広告の可視判定はDOMContentLoaded時点のactiveクラスだけでは不十分
  → ads.jsは「共有URL起動（location.hashが9文字以上）」も見て先回りでスキップする
- news/のお知らせ記事は本文が短いためnoindex+sitemap非掲載で運用（一覧経由でユーザーには届く。増補して記事化するならnoindexを外す）
  → firebase.jsonのheadersで全ファイルCache-Control: no-cacheに設定済み（ETag再検証・304なら転送なし。2026-07-18）
- **アプリのUI名・文言を変えたら faq / score-basics / news記事などの外部ページの言及も同時に更新する**
  （2026.07: 「変更」ボタン→設定の編集、対局形式→試合形式、レート、旧倍率例示、個人成績→その他成績 が外部ページに残っていた。
  faq.htmlはFAQPage JSON-LDも本文とセットで直す）
- **この開発PC（社内ネットワーク）からは majasco.jp 自体がZscalerでブロックされ閲覧不可**（新規登録ドメインカテゴリ）。
  本番の見た目確認はユーザーのスマホ回線に依頼し、開発検証はlocalhostプレビューで行う
- **公開リポジトリに一度pushしたファイルは履歴に残る**（2026.07に素材画像で発生→履歴書き換え+force pushで除去した）。
  非公開にしたいものは最初から majasco-assets（private）へ。force pushはユーザーの明示承認が必要
