# まじゃすこ / majasco

麻雀のスコア集計・共有ができる無料のWebアプリ。ビルド不要の静的サイト（Vanilla JS + Firebase Realtime Database）。

## 公開URL
- 本番: https://majasco.jp （Firebase Hosting）
- Firebaseデフォルト: https://mahjong-score-2e8aa.web.app
- 旧URL（現在は使わない）: https://1046nee.github.io/mahjong-score/

## リポジトリ
- https://github.com/1046nee/mahjong-score （ブランチ: main）
- mainにpushすると GitHub Actions が自動で Firebase Hosting へデプロイする
  （`.github/workflows/firebase-hosting-merge.yml`）
- Firebase設定は `firebase.json` / `.firebaserc` にコミット済み。作り直し不要。

## ファイル構成
- `index.html` — アプリ本体（SPA、全画面がこの1ファイルに入っている）
- `blog.html` — ブログ一覧（カード型、緑/オレンジのキャッチーなデザイン）
- `blog-*.html` — 個別記事（本文はシンプルな黒文字＋緑の見出し・左バー、オレンジのハイライト）
- `sitemap.xml` / `robots.txt` — SEO用。**新しいページ（記事・固定ページ）を追加したら sitemap.xml にも `<url>` を1件追加すること**
- `terms.html` — 利用規約（禁止事項・賭博否定・免責・サービス変更等。2026.07.08追加）
- `assets/` — 画像素材ディレクトリ（2026.07.10導入）: `favicon.png`（512×512、favicon/apple-touch-icon/manifest共用）、`logo.png`（透過ロゴ800×250、全ページのヘッダーで使用）、`ogp.png`（OGP画像2100×1103）。素材の元データはリポジトリ直下の`まじゃすこ素材/`（.gitignore済み・コミットされない）
- `manifest.json` — PWA用の最小構成（アイコンは/assets/favicon.png）
- 新しいページを追加したら、`<head>`に以下を必ず入れる（blog記事のheadを参照）: **GTMスクリプト（viewport直後・titleより上）**, **AdSenseメタタグ＋スクリプト（GTMの直後）**, meta description, canonical, favicon（/assets/favicon.png）+apple-touch-icon+manifest link, OGP（og:title/description/url/type/site_name/locale/**image+width+height**）, twitter:card（summary_large_image）+twitter:image。さらに`<body>`直後に**GTMのnoscript**を入れること
- **GTM（Googleタグマネージャー）導入済み（2026.07.10）**: コンテナID `GTM-KMRMGKKV`。全16ページに設置済み
- **Google AdSense導入済み（2026.07.10）**: パブリッシャーID `ca-pub-9998035509478799`。
  全16ページのheadにメタタグ＋adsbygoogle.jsスクリプト設置済み、ルートに `ads.txt` 設置済み。
  **審査待ちの状態**。合格したら手動広告ユニットで広告枠を実装する（配置方針: ブログ記事内・記事末尾CTA上・LP下部。
  スコア入力シート・ゲーム画面・設定モーダル周辺とprivacy/termsには置かない。CLS対策でmin-height確保）
- GA4の直書きgtagは未導入（実測定ID `G-...` が未取得のため）。**推奨はGTM経由でGA4を配信する構成**（GTM管理画面でGA4設定タグを追加すればコード変更不要）。直書きする場合は実IDを取得後、GTMスクリプトの直前に挿入すること
- `privacy.html` — プライバシーポリシー（AdSense審査用の必須文言を含む）

## デザインシステム
- メインカラー（濃い緑・信頼感）: `#177083`
- アクセントカラー（オレンジ・CTA限定）: `#E75620`
- 背景の薄緑: `#E4F3EC` / 薄青: `#EAF0FB` / 明るい水色背景: `#DBF4F9`
- 3人麻雀（サンマ）モード時は緑を `#4261AA`（青）に置き換える配色ルールがある（`.sanma` クラス）
- CTAボタンはオレンジに限定し、他の場所では使わない

## 用語ルール（AdSense対策・超重要）
- 「円」「金額」「精算」「賭け」など現実の金銭を連想させる語は禁止
- **「倍率」「収支」は使用OK**（2026.07.10ユーザー確認済み。ギャンブル語彙には該当しない扱い）
- **統一用語（2026.07.10「収支」モデルで確定。UI・コード・記事すべてこれに従う）**:
  - 「スコア倍率」（旧: スコア係数/レート。ptに掛ける倍率。保存キーは互換性のため `settings.rate` のまま変更しない）
  - 「チップ倍率」（チップ差に掛ける倍率。保存キー `settings.chipRate`）
  - 「ゲーム開始時チップ数」（保存キー `settings.startChips`。未設定は0）
  - 「チップ差」＝ 終了時チップ数 − 開始時チップ数（旧: ボーナス枚数。試合ごとの保存キーは `round.chips` のまま）
  - 計算後の値は「スコア収支」（pts×スコア倍率）「チップ収支」（チップ差×チップ倍率）「合計収支」（両者の合計）
  - **収支の単位は「bonus」**（2026.07.10確定）。「スコア収支」「チップ収支」は値の名称であって単位ではない。
    数値には小さく `bonus` を付けて表示（例: `+7,000bonus`）。
    倍率の例示は「チップ倍率が500倍なら、チップ1枚 → 500bonus」「スコア倍率が10倍なら、1.0pt → 10bonus」の形式で書く
  - 「レート」「係数」「チップ換算」「〜ボーナス」という表記は使わない
- 麻雀の「点数計算（符・翻から1局のアガり点を出す、手役の計算）」と
  「スコア計算/集計（対局後に持ち点→返し点・ウマ・オカを反映して順位・ptを出す）」は別物。
  **このアプリが解決するのは後者のみ**。前者（符・翻・役の計算）はアプリの対象外で、ユーザー自身が数える前提。
  - NG例: 「点数計算がめんどうだからアプリで解決」「点数計算の基本（初心者向け）」という見出しでウマ・オカ・返し点を説明する
    → 中身がウマ・オカ・返し点の話なら、見出しは必ず「スコア計算」にする（2026.07に index.html の見出しで実際に混同があり修正した前例あり）
  - OK例: 「符・翻の点数計算は自分で。半荘のスコア集計は、まじゃすこで。」のように明確に切り分けて併記するのはよい
  - 符・翻・役・点数表を解説する記事（blog-score-table.html, blog-fu-han.html, blog-yaku-list.html等）はテーマとして「点数計算」を扱ってよいが、
    本文中でアプリの守備範囲を説明する箇所は必ず「半荘の集計」「スコア計算」という語に切り替えること

## LP（トップページ index.html）の構成方針
逆ピラミッド型。ファーストビューに必須文言を必ず入れる:
「まじゃすこ / majascoは、電卓と紙の代わりにスマホ1台で、麻雀スコア計算のわずらわしさをシンプルに解決してくれる無料のサービスです。」
フック見出しは「麻雀の"スコア集計係"、卒業しませんか。」（"卒業"だけオレンジ）。
共感・ペインの長い物語は下部に短く圧縮し、離脱防止のため上部は簡潔に。

## 開発の進め方（重要な癖）
- ユーザーはGitHub Web UIで直接コードを編集することがある。作業開始前に必ず `git pull origin main` して最新を取り込むこと。古い状態に巻き戻さない。
- コード変更後は `mcp__Claude_Browser__preview_*` ツールで実際に画面を確認してから完了報告する（見た目・動作・横スクロールの有無など）。
  スクリーンショットはタイムアウトしやすいので `preview_eval` によるDOM検証を主とする。測定前に `preview_resize` で正常なビューポートにする（幅0の偽陽性に注意）。
  検証で作ったFirebaseセッションは終わったら `db.ref('sessions/ID').remove()` で削除する。
- 変更ごとに `git add` → `git commit`（変更内容と理由を日本語で説明）→ `git push origin main` まで行う。
- Firebase Hosting へのデプロイはmainへのpushで自動的に走るため、追加作業は不要。

## よくある要望の傾向
- LPのコピーライティングは、行動経済学・心理学の手法（損失回避、アンカリング、フット・イン・ザ・ドアなど）を意識して提案してほしい
- デザインは「Walicaのようなシンプルで丸みのあるフラットデザイン」を参考にしつつ模倣はしない
- 3人麻雀・4人麻雀の同点処理、ウマ・オカの計算ロジックは `rankGroups()` という共通関数に集約されている（同点グループ化→順位範囲→ウマ按分→オカ按分、を一箇所で計算し全機能が参照する設計）

## ブログの構成と運用（2026.07.10にカテゴリ制へ再構成）
- **カテゴリ**: `/mahjong/`（麻雀攻略）・`/news/`（お知らせ=アップデート情報）・`/blog/`（雑記）。
  `blog.html` は全記事一覧。**既存記事のURL（ルート直下のblog-*.html）は変えない**（インデックス維持のため）。
  お知らせ記事だけは `/news/xxx.html` に置く
- **記事メタは `/assets/blog-site.js` の BLOG_POSTS で一元管理**（カテゴリ・公開日・タグ・recommended=おすすめフラグ）。
  一覧・カテゴリページ・サイドバー（今月のおすすめ記事／最新のアップデート）・カテゴリナビはここから自動描画される
- 共通スタイルは `/assets/blog.css`（一覧ページは `body.bs-list`、記事ページは .post-layout/.side/.cat-nav のみ利用。
  PC=右サイドバー、900px以下=本文の下に縦積み）
- **RSS**: `/news/feed.xml`（RSS 2.0・手書き）。全ブログページのheadに `rel="alternate"`、フッターに「お知らせRSS」リンク済み

### 記事の追加手順（チェックリスト）
1. 既存の `blog-*.html`（お知らせなら `news/update-2026-07.html`）をコピーして執筆。
   head一式・パンくず（トップ＞ブログ＞カテゴリ＞記事名）・`.post-layout`＋`<aside class="side" data-sidebar>`・
   末尾CTA（`.cta-link`）・`/assets/blog.css`と`/assets/blog-site.js`の読み込みを維持する
2. `/assets/blog-site.js` の BLOG_POSTS の**先頭**に1件追加（url/cat/date/tag/title/desc、推したい記事はrecommended: true）
3. `sitemap.xml` に `<url>` を1件追加
4. お知らせ記事の場合は `/news/feed.xml` に `<item>` を1件追加（lastBuildDateも更新）
5. 関連記事同士で本文中の内部リンクを張り合う。CLAUDE.mdの記事一覧も更新

### 公開済みの記事一覧（2026.07時点、計14記事）
1. `blog-why-majasco.html` — 開発ストーリー「まじゃすこを作った話」
2. `blog-uma-oka.html` — ウマ・オカとは？初心者向けスコア計算入門
3. `blog-score-table.html` — 翻・符の点数早見表
4. `blog-yaku-list.html` — 初心者向け基本役10選
5. `blog-fu-han.html` — 符と翻の仕組みをやさしく解説
6. `blog-sanma-yonma.html` — 3人麻雀と4人麻雀の違い
7. `blog-app-guide.html` — スコア管理アプリの選び方（比較記事・コンバージョン狙い）
8. `blog-hai-types.html` — 麻雀牌の種類と名前一覧（萬子・索子・筒子・字牌）
9. `blog-rule-basics.html` — 半荘・東風戦とは？ルール基本の基本
10. `blog-riichi.html` — リーチとは？ルールとメリット・デメリット
11. `blog-manner.html` — 麻雀のマナーと見落としがちなルール（チョンボ・途中流局）
12. `blog-starter-kit.html` — 友人と麻雀を始めるのに必要な持ち物リスト（企画記事）
13. `blog-dora.html` — ドラとは？裏ドラ・カンドラ・赤ドラの仕組み
14. `blog-naki.html` — 鳴き（ポン・チー・カン）の基本ルールと使いどころ
15. `news/update-2026-07.html` — 【お知らせ】大型アップデート（チーム戦・チップ収支・回し打ち）

### 追加の記事アイデア（次に書く候補、決まったものはない）
- 麻雀の歴史・起源についての雑学記事
- オンライン麻雀（天鳳・雀魂など）と対面麻雀の違い
- 点数申告の言い方（「ロン、8000」等の実践的な流れ）
- 新しい記事を追加したら、このリストと上の「公開済みの記事一覧」を更新すること。

## アプリの現行仕様（index.html）
※過去の経緯・改修履歴はgit logを参照。ここには「今の正」だけを書く。更新したらこのセクションも直すこと。

### データモデルと計算
- Firebase `sessions/{10文字ID}`（URL共有モデル）＋ localStorage `mahjong-v3`（履歴最大20件・登録名）
- `settings`: playerNames（3〜40人=MAX_MEMBERS）/ numPlayers（3|4）/ startPoints / returnPoints / uma[] /
  rate（スコア倍率）/ bonusEnabled / chipRate（チップ倍率）/ startChips（開始時チップ数）/ yakitori /
  teamMode / teams=[{name, members:[playerNamesのindex]}]
- `rounds[]`: points[] / scores[] / members[]（参加者index配列）/ chips[]（**チップ差**）/ yakitori[]（0/1）/ at / edited
- 計算: スコア収支 = pts×rate ／ チップ収支 = チップ差×chipRate ／ 合計収支 = 両者の和
- **互換性ルール（最重要）**: 旧データはキー無し=無効・0枚・1倍扱いで計算に一切影響を出さない。
  members無しの旧ラウンドは「先頭numPlayers人が参加」とみなす（`roundMembers(r,s)`に集約）。
  保存キー名・コード上の関数名は bonus 系のまま変えない（settings.rate も不変）

### 主要関数マップ
- 同点処理は `rankGroups(values)` に一元化（ウマ・オカ按分・平均順位すべてこれを参照）
- 集計: `gameTotals` / `playedFlags` / `chipTotals`。シートのチップ基準値は `chipBaseline(m)` = 開始時 + それまでの試合のチップ差累計（修正時は対象試合より前まで）
- 結果カード: `scoreMainHtml(g)`（ゲーム=`#score-main-body`、詳細=`renderDetailBody(g)`。`viewDetail`=renderDetailBody+showViewのラッパ。収支内訳は`bonusTableHtml(g)`）
- チーム: `normalizedTeams` / `teamStandingsHtml` / 編成エディタは `teamEditorCtx` でセットアップ・設定変更モーダル共用。
  `syncTeamsWithIds` が「存在しないid除去＋未所属idを人数最少チームへ」を一元処理。**エディタ再初期化前に必ずcaptureTeamNames()**（入力中のチーム名が消える）

### セットアップ画面（構成順序は固定）
グループ名 → 対局形式（4人/3人麻雀トグル・常時表示、自動切替なし） → 対戦形式（個人戦/チーム戦。チーム戦時のみ直下に編成エディタ） → メンバー名（最大40人） → ルール設定 → 収支オプション
- 開始条件: メンバー数 ≥ numPlayers。不足時は「ゲームを開始するにはあと[X]名必要です」＋開始ボタン無効。チーム戦は4人以上必須
- チップ倍率はスコア倍率と同じセレクト＋カスタム形式（デフォルト×500）。開始時チップ数の初期値は20
- チーム編成: 名前をタップで次のチームへ移動（ガイドはタップのみ表記。D&Dも動くが案内しない）・チーム追加/削除（最低2）・🎲ランダム編成・チーム名編集可
- 登録名管理モーダル: 各名前に[ゲームに追加]ボタン（追加済みはラベル表示）

### スコア入力シート
- メンバー数>numPlayersのグループのみ「今回の対局メンバー」選択チップを表示（デフォルトは直前試合のメンバー）
- タイトルは収支ONで「点数 / チップ入力」。行は「名前｜チップ（左）｜点数（右）｜🐔」の1行レイアウト
- チップは「現在のチップ数」のみ入力。`chipBaseline`を初期値に自動参照し、保存は差分（round.chips）
- バリデーション: 点数合計=持ち点×人数、かつ参加者のチップ合計=基準合計（チップは参加者間の移動なので合計不変）でないと入力完了をブロック（`#chip-check`）
- 入力途中の値はメンバーindexキー（sheetPrefill/sheetChips/sheetYaki）で保持し、対局メンバー切替でも消えない

### 結果表示（ゲーム画面・結果詳細で共通）
- カード順: チーム成績（チーム戦のみ）→ スコア収支 → 対局履歴 → 個人成績 → スコア推移 →（詳細のみ）設定
- スコア収支カード: デフォルトはpts順位。右上ミニトグルで「チップ最終枚数」順位に切替（`scoreMetric`・フェード`.score-swap`・モードラベル「順位（スコア）」等を表示）。
  収支ONならカード下部の大きめトグル「合計収支 ▾」で内訳を展開＝合計収支ミニカード（bonus単位付き）＋「内訳を表示」詳細表。開閉状態は`bonusSectionOpen`で保持
- 対局履歴: 通常グループ（メンバー数=numPlayers）は表形式、回し打ちグループは`roundListHtml`のカード形式（試合ごとに参加者のみ順位順）。行/カードのタップで修正・削除
- 個人成績（`rankCountHtml`・転置）: 行=メンバー、列=1着..n着/試合数/平均着順/ラス回避。名前列はsticky固定。
  ベスト（1着最多〔全員0回は対象外〕・平均着順最小・ラス回避最大。同値は該当者全員）は**文字色オレンジ#E75620のみ**で強調（背景・枠線は付けない）。
  チーム戦はチームごとにグループ化（チーム見出し行つき）
- チーム識別は記号 `TEAM_MARKS = ['◯','△','◻','✕','◇','☆']`（色ドットは使わない。ヘッダー背景色と被るため）
- 未参加メンバー: スコアカード「未参加」・表「—」・グラフから除外

### 設定変更モーダル（ゲーム中の「変更」）
- 対局形式（3人/4人）は変更不可（モーダルに明記）。ルール変更は過去試合を全再計算（⚠警告を表示）
- メンバー追加可。削除は「対局済み」「最低N人」の場合ラベル表示で不可。削除時はrounds[].membersとチームのindexを振り直す
- チーム戦OFFでも`settings.teams`は保持し再ONで復元。収支OFF中に試合を修正しても記録済みchips/🐔は引き継ぐ
- 新機能を追加したらLPの「使い方」「3つの価値」セクションも更新すること
