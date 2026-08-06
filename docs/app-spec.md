# アプリ仕様（index.html）

※「今の正」だけを書く。経緯・改修履歴はgit log。仕様を変えたらこのdocも更新すること。

## データモデルと計算
- Firebase `sessions/{10文字ID}`（URL共有モデル）＋ localStorage `mahjong-v3`（履歴最大20件・登録名）
- **セッションIDは`newSessionId()`で発行**（生成→既存チェック→被っていたら作り直し、最大5回。誕生日問題による他人のセッション上書きを防ぐ）。
  初期のIDは22桁だったため、既存データには22桁IDも混在する（セキュリティルールは両方許可）
- **起動時のセッション判定は「ハッシュ8文字以上」**（ページ内アンカー #howto をセッションIDと誤認しないため）
- `settings`: playerNames（3〜40人=MAX_MEMBERS）/ numPlayers（3|4）/ startPoints / returnPoints / uma[] /
  rate（スコア倍率）/ bonusEnabled / chipRate（チップ倍率）/ startChips（持ちチップ）/ yakitori /
  chombo / chomboPenalty（罰符pts・0=マークのみ）/ teamMode / teams=[{name, members:[playerNamesのindex]}]
- `rounds[]`: points[] / scores[]（チョンボ罰符適用後）/ members[]（参加者index）/ chips[]（**チップ差**）/ yakitori[] / chombo[] / at / edited
- 計算: スコア収支 = pts×rate ／ チップ収支 = チップ差×chipRate ／ 合計収支 = 両者の和
- チョンボ💩: `applyChombo(scores, chomboArr, s)` が罰符ptsを減算。**submitRoundとsaveGameEditの両方で必ず通す**。焼き鳥🐔はマークのみ
- **名前の文字数上限**: プレイヤー名・チーム名=`MAX_NAME_LEN`**16**／グループ名=`MAX_GROUP_LEN`**40**。
  入力欄の`maxlength`＋保存時の`clampName`（**書記素クラスタ単位**で切るので絵文字が割れない）の二段構え。
  かける場所はセットアップ／設定変更モーダル／チーム編成エディタ／過去の試合の編集の全入力。
  **既存データに上限超えの名前があっても切り詰めない**（表示は従来どおり＝互換性を壊さない）。
  サーバー側の上限はdatabase.rules.jsonのname≤120・playerNames各≤60（こちらは変更していない）
- **互換性ルール（最重要）**: 旧データはキー無し=無効・0枚・1倍扱い。members無しの旧ラウンドは先頭numPlayers人参加とみなす（`roundMembers(r,s)`に集約）。保存キー名・関数名はbonus系のまま変えない（settings.rateも不変）

## 主要関数マップ
- 同点処理は `rankGroups(values)` に一元化（ウマ・オカ按分・平均順位すべてこれ）
- 集計: `gameTotals` / `playedFlags` / `chipTotals`。チップ基準値は `chipBaseline(m)` = 持ちチップ + 過去試合のチップ差累計（修正時は対象試合より前まで）
- 結果カード: `scoreMainHtml(g)`（ゲーム=#score-main-body、詳細=`renderDetailBody(g)`。`viewDetail`=そのラッパ。内訳は`bonusTableHtml(g)`）
- チーム: `normalizedTeams` / `teamStandingsHtml` / `memberDisplayOrder`（チームA→B…の表示順）/ `teamColorOf` / `teamDotHtml`。
  編成エディタは `teamEditorCtx` でセットアップ・設定変更モーダル共用。`syncTeamsWithIds`が同期を一元処理
- **チーム戦の制約**: 同チーム同士は対局不可。最低チーム数=1試合の人数（四麻4・三麻3、`teamEditorCtx.minTeams`）。
  ガード: toggleSheetMember / submitRound / defaultParticipants
- ログ: `renderLogModal`（フィルタlogFilter）/ `renderLogList(log, g)`。新規ログは`e.names`に参加者名を保存
- 画像出力とプレビュー: `imgSectionBodyCanvas` / `buildResultCanvas` / `buildComposedCanvas` / `openImagePreview`（→ その他の機能）
- カード開閉: `collapsedCards` + `toggleCard(key)`（key: team/score/rounds/rank/chart/ichart/settings）
- 計測: `track(event, params)` → dataLayer（group_create / group_join / round_submit / share_copy）

## セットアップ画面
- 統合カード（グループ名 → メンバー名 → **試合形式**=四麻/三麻＋個人戦/チーム戦の2トグル1ラベル）→ ルール設定 → オプション
- プレースホルダーは例の値をそのまま（まじゃすこ学園サッカー部／山田先輩／150等。「（例）」は付けない）。グループ名初期値は空（未入力ならstartGameで日付名）
- **作成日はゲーム画面・結果詳細のタイトル下に自動表示**（#game-date / #detail-date）
- 「登録名の管理」ボタンはメンバー名ラベルの右（常時表示）。モーダル: [ゲームに追加]/[取り消し]、右上[編集]で↑↓並び替え・削除
- **三麻選択でview-setupに.sanma**（トグル・カード枠が青#4261AAに）
- **オプションカードはデフォルトで閉じた状態**（右上の▸/▾トグルで開閉。`toggleSetupOptions`。画面を開くたびinitSetupFormで閉じ直す）
- オプション名: 「チップあり🍪」「焼き鳥あり🐔」「チョンボあり💩」。説明は「本文。<br>※注意書き。」の2行形式。
  倍率例示: 「例：スコア倍率が×100の場合、+123.0pts → +12,300bonus」「例：チップ倍率が×500の場合、+5枚 → +2,500bonus」
- 「持ちチップ（枚）」（左）・チップ倍率（右）。チップ倍率デフォルト×500・持ちチップ初期値20
- チョンボ罰符セレクト: 0/−10/−20/−30/−50/カスタム。デフォルト−20pts
- チーム編成エディタ: 各ボックスにチームカラー（左5pxボーダー＋●）。タップで次チームへ・🎲ランダム・チーム名編集

## スコア入力シート
- **「設定の編集」と同じ中央モーダル形式**（.sheet=暗背景オーバーレイ、.sheet-box=白パネル max-width:430px・パネル内スクロール・transformなし・背景タップで閉じる）
- **パネルは上端固定**（.sheetはalign-items:flex-start＋padding-top:6vh。縦中央揃えにしない）:
  対局メンバーの選択人数で中身の高さが変わっても上側の位置は動かず、下だけが伸縮する（メンバーチップの位置が上下にぶれない）
- タイトル右に小「キャンセル/完了」＋最下部に「入力完了/キャンセル」（#confirm-btn-topは下と活性同期）。タイトルに試合番号
- **列順は左から 名前｜焼き鳥🐔｜チョンボ💩｜チップ｜点数**。入力欄・ボタンは固定幅で右詰
  （焼き鳥/チョンボ42px・チップ68px・点数104px・gap6px）、名前が残り幅（可変・ellipsis）
- オプションが1つでも有効なら列見出し行を表示。**見出しは文字（「焼き鳥」「チョンボ」）、ボタンは絵文字のまま**
- **整数のみ**（blockNonInt。マイナスは箱下用に許可）。点数placeholderは持ち点連動（startPoints/100）。チップは「現在のチップ数」を入力し差分保存
- バリデーション: 点数合計=持ち点×人数 かつ チップ合計=基準合計。**チェック表示はチップが上・点数が下**（同サイズ13px）
- 入力途中値はメンバーindexキーで保持（sheetPrefill/sheetChips/sheetYaki/sheetChombo）
- チーム戦では対局メンバーチップもチームA→B…順＋チームカラー●
- 対局メンバー選択欄に**独自スクロールは付けない**（全員分を表示し、パネル全体のスクロールに任せる）

## 結果表示（ゲーム画面・結果詳細共通）
- カード順: チーム順位（チーム戦のみ）→ 総合順位 → 対局履歴 → 個人成績 → スコア推移 →
  個人スコア推移（チーム戦のみ）→（詳細のみ）設定
- 全カード右上に開閉トグル（▾/▸）。開き直すと全開にリセット。たたむとアクションボタンも隠す
- **0試合の間は順位バッジを出さない**（灰色「—」。1試合目から順位・メダル表示）
- 総合順位: pts順位がデフォルト。ミニトグル「スコア/チップ」はチップあり🍪のときだけ。
  **「合計収支 ▾」セクションの表示条件は`bonusVisible(s)`＝チップあり または スコア倍率が実質有効（>0かつ≠1）**
  （スコア倍率だけのグループでも収支を表示する。チップ差・チップ収支の内訳行はチップあり🍪のときだけ。開始時チップ行は置かない）
- 対局履歴: 常に表形式。行タップで修正・削除。全体を見たいときは**画像プレビュー**（下記）。
  **列幅・先頭列の体裁は個人成績と完全に統一**（メンバー列58px。上下に並ぶ2表の列位置がそろう）。
  先頭列幅は`firstColW(forImage)`: **画面64px（小さめ・最長ラベル「平均着順」「メンバー」=48pxがぎりぎり収まる幅）／画像出力86px**。
  試合番号の列は項目列と同じ`.sticky-col`（12px・weight600・標準色・左詰め・横スクロール時固定）
- **見出し行の先頭セルは「列の見出し」ではなく「行の見出し」**（転置レイアウトなので、その行が何の行かを示す）:
  プレイヤー名の行＝**「メンバー」**（対局履歴・個人成績とも。旧「試合」「項目」）／チーム名の行＝**「チーム」**。
  4文字がちょうど収まる幅なので、これより長いラベルにするなら`firstColW`も広げること
- 個人成績: **対局履歴と同じ転置レイアウト（列=メンバー・行=成績項目、1行目にプレイヤー名）**。項目列はsticky。
  行=上から **試合数/平均着順**（全体像）→ **1着..n着**（内訳）→ **トップ率/連対率/ラス回避**（率。トップ率と
  ラス回避の間に連対率）→ スコア/素点/順位点/最高点数/最低点数（平均点数は載せない）。
  **`statLabels`とセルを積む順は必ず一致させる**（`rankCountHtml`。片方だけ直すと値と項目名がずれる）。
  試合数も太字（数値の行はすべてweight700で統一）。
  素点=(持ち点−返し点)÷1000合計、順位点=スコア−素点、連対率=(1着+2着)÷試合数、トップ率=1着÷試合数。
  ベスト（平均着順min・連対率/トップ率/ラス回避/最高点数max）は文字色オレンジのみ
- **チーム戦のチーム名行**: 対局履歴・個人成績の両表とも、プレイヤー名行の上に`teamNameRowHtml`のチーム名行を置く
  （チームごとにcolspanで1セル・プレイヤー名と同じ文字サイズ・TEAM_HEAD_BG背景）。
  チームの境目は縦区切り線クラス`.tb`（**1px**=本文の横罫線と同じ太さ。見出し=白 rgba(255,255,255,.85)・
  本文=薄グレー #e3eaea）をチーム名行/名前行/本文の全セルに付けて示す
  （境目列の算出は`teamBoundarySet`、グループは`teamGroupsOf`）。
  **同じ線を2か所にも引く**: ①先頭列（試合番号・項目）の右 ②チーム名行の下（`tr.team-row th`のborder-bottom）。
  ①は`border`ではなく`box-shadow: inset -1px 0 0`で描く（border-collapse:collapseの表では罫線が表側に属するため、
  横スクロールするとsticky列の罫線だけ取り残される）。①はチーム戦・個人戦の両方で出す
  **長いチーム名・プレイヤー名は何度でも折り返す**（`.rounds-table th`にword-break:break-all。列幅を押し広げて表を横長にしない）
- **カード上の表は自動縮小しない＝横スクロールで見る**（`overflow-x:auto`＋`tableStyleFor`のmin-width）。
  一時期zoomで1画面に収める実装を入れたが、モバイルで文字がセルからはみ出すため撤去した（下の落とし穴参照）。
  「全体を1枚で見たい」ニーズは**画像出力ボタン**が担う
- **長い名前への耐性**（プレイヤー名・チーム名）: 区切りのない半角英数字（`aaaa…`）が最も崩れやすい。
  日本語・全角英数・韓国語などはブラウザが自動で折り返すが、半角の連続は折り返されず横に伸びる。
  対策は2つセットで必要:
  ①折り返しを許す`overflow-wrap: anywhere`（`.score-name` `.team-members-line` `.score-bonus` `.chart-legend span`
  `.sel-chip` `.team-chip` `.rounds-table th/td.sticky-col`）
  ②**flexアイテムに`min-width: 0`**（`.score-info`）。これが無いと最小幅が中身に引きずられ、
  右のスコア値が画面外へ押し出されて見えなくなる。値側は`flex-shrink: 0`＋`white-space: nowrap`で守る
- チーム識別: TEAM_COLORSは**40色**（1-8は赤#e60012/青#0075c2/緑#00a040/橙#f39800/紫#9b26b6/黄#e6b400/桃#ff5ca8/茶#8b5a2b で不変。
  9色目以降も白以外の互いに異なる色）。名前の前に`.team-dot`●（文字色は変えない）。チーム戦の表見出しは灰色TEAM_HEAD_BG=#5f6e6b。
  列と合計収支はチームA→B…順（個人戦の合計収支は値の大きい順）
- グラフの縦軸グリッド: 通常50刻み。**表示範囲（プラス域＋マイナス域の絶対値合計=max−min、パディング込み）が600以上なら100刻み**。
  系列・目盛りの計算は`chartData(rounds,s,indiv)`に集約し、画面のSVG（`chartHtml`）と画像出力（`imgChartBodyCanvas`）が共用する
- グラフ: 個人戦「スコア推移」／チーム戦「チームスコア推移」（チーム合算・チームカラー）＋その下に
  「個人スコア推移」（`chartHtml(rounds, s, true)`。**個人の線の色は表示順（memberDisplayOrder）のn番目の人＝TEAM_COLORSのn色目**。
  個人戦のスコア推移も同じ割当。凡例も表示順に並ぶ）
- 順位バッジ: 1〜3位のみ🥇🥈🥉、4位以下は灰色数字
- タイトル横ボタンは「設定の編集」（.title-edit-btn・三麻で青）
- **「もっと見る」（全画面モーダル）は廃止**（2026-08-06）。全体を1画面で見る用途は画像プレビューが完全に置き換えたため、
  対局履歴・個人成績・グラフの4か所すべてから削除し、代わりに「画像」を置いた。
  画像出力用の広い版を作るフラグ名は`forImage`（旧`forModal`）。
  **画像の対局履歴は画面と同じくスコアの下に薄い点数・チップ差を出す**（`roundRowHtml(..., forImage=true)`。
  絵文字🐔💩だけ画像では出さない＝Canvasで環境差が出るため）、
  **個人成績は`rankCountHtml(…, true)`でtable-layout:auto**（列幅が内容基準になり項目ラベルが省略されない）

## その他の機能
- **結果の画像出力**: **画面の見え方（横スクロール中かどうか等）に関係なく、Canvasに描き直した一枚絵PNG**を生成。
  DOMスクショ方式ではなくCanvas直描画（iOS SafariのforeignObject非互換を避ける＋常に崩れない絵にするため）。
  出力はスマホ=共有シート（navigator.share・キャンセル時は何もしない）／非対応=PNGダウンロード（`shareCanvasImage`）。track('image_export')
  - **対象6セクション**（`IMG_SECTIONS`）: 総合順位`score`／チーム順位`team`／対局履歴`rounds`／個人成績`stats`／
    スコア推移`chart`／個人スコア推移`ichart`。team・ichartはチーム戦のみ。
    各カードに**「プレビュー」ボタン**（ゲーム画面・結果詳細の両方。個人戦・チーム戦、三麻・四麻すべてで出る）
  - **構造**: `imgSectionBodyCanvas(g,kind)`が**本体だけのCanvas**を返し、
    単体出力`buildResultCanvas`＝ブランド帯＋本体＋フッター、まとめ出力`buildComposedCanvas`＝全体ヘッダー＋［見出し＋本体］×n＋フッター、
    と共用する（見た目の一貫性と実装の一元化）
  - 本体の描き方は3種: 表（`imgTableBodyCanvas`＝画面と同じHTMLを非表示DOMに展開してセル情報を抽出）／
    順位リスト（`imgRankingBodyCanvas`＝`.score-card`から抽出。**順位は絵文字でなく金銀銅の丸バッジ**で描く＝環境差なく同じ絵になる）／
    グラフ（`imgChartBodyCanvas`＝`chartData`の計算結果からCanvasに直接線を引く）
  - **画像の折り返しは書記素クラスタ単位**（`imgGraphemes`＝Intl.Segmenter、非対応環境はコードポイント）。
    コードポイントで切るとタイ語の母音記号・アラビア語の連結・ZWJ絵文字（👨‍👩‍👧）が壊れて重なって描かれる。
    入りきらない場合は最終行の末尾を「…」にする（`imgWrap`が付けるので呼び出し側で足さないこと）
  - **区切り線は画面と同じ3種を描く**: チームの境目（`c.tb`）／先頭列の右（`c.left`）／チーム名行の下（`c.teamRow`）。
    色は見出し行=rgba(255,255,255,.85)・本文=#dfe8e6（CSSのborderはCanvasに反映されないので自前で引く）
  - 対局履歴は画面と同じ「スコア＋薄い点数＋チップ差」の縦積み＋合計行
    （セル内の2行目以降は`subs`として9pxで描く。列幅・行高もsubsを含めて計算する）。
    チーム順位はメンバー名と合計収支を2行のサブ行で表示
- **画像プレビュー**（`openImagePreview`）: カードの「プレビュー」ボタン（`showResultImage`）とまとめ作成は、
  **まず全画面プレビューを開く**（保存せずその場で結果を確認するため）。書き出したCanvasをそのまま表示するので保存物と同一の絵。
  中身: タップで幅フィット⇄等倍のズーム切替、「PDF・印刷」（`printPreviewImage`＝`@media print`で画像だけを紙面に出す。
  スマホの印刷画面から「PDFとして保存」できる）、「保存・共有」（`shareCanvasImage`）。
  画像はblob URLで渡し、閉じるときにrevoke（`img.src=''`はページURLを読みに行くので`removeAttribute`で外す）
- **まとめ画像**（`openComposeModal`→`runCompose`→`buildComposedCanvas`）: 入れる項目をチェックで選び、
  **縦長1枚（幅1080px）**に連結する。ゲーム画面と結果詳細の末尾に「結果をまとめてプレビュー」ボタン。
  各セクションは内側幅に収まるよう縮小して白い角丸カードに載せ、上に見出しを付ける。
  **iOS Safariのcanvas上限（総ピクセル数16.7M・1辺）を超えると保存が丸ごと失敗する**ため、
  超えるときだけ解像度を落として収める（通常は幅1080pxを維持。400試合でも安全に生成できることを確認済み）
- **CSVエクスポート**（「CSV」ボタン→`openCsvModal`→`runCsvExport`→`exportCsv(g, opts)`/`buildCsv(g, opts)`）:
  ゲーム画面と結果詳細の対局履歴カードに「CSV」ボタン（履歴・プレビューの隣）。
  押すと**項目選択モーダル**（`csv-modal`）が開く。選べるのは
  スコア／点数（素点）／チップ／焼き鳥／チョンボ／日時／合計行／グループ情報の8つ。
  **既定は最低限＝スコアと合計行だけON**（`CSV_DEFAULT`）。選択は`mahjong-csv-opts-v1`に記憶し次回も同じ状態で開く。
  チップ/焼き鳥/チョンボは**設定有効または記録ありのときだけ**選択肢に出す（旧データ互換）。
  そのとき出さなかった項目のON/OFFは保存時に書き換えない（`csvItemKeys`にある分だけ更新）。
  値の列が0個なら書き出さず注意を出す。試合番号は常に入る。
  **1人あたりの値列が1つだけのときは見出しを名前だけにする**（「山田 スコア」ではなく「山田」）。
  メタ（グループ名/作成日/試合形式/チーム編成※チーム戦のみ）を選ぶと先頭に4行＋空行が付く。
  **UTF-8 BOM付き**（Excel日本語環境の文字化け対策。ソース中のBOMは`﻿`のエスケープ表記で書く=生文字は編集事故のもと）。
  列順は対局履歴と同じ（チームA→B…）。不参加は空欄・マークは○。
  ファイル名「まじゃすこ_グループ名_YYYYMMDD.csv」（禁止文字は_に置換）。track('csv_export')
- 過去の試合: カードは**グループ名・日付・総試合数・四麻/三麻・個人戦/チーム戦・プレイヤー名のみ**（結果のプレビューは載せない）。
  文字は13pxで統一、グループ名はellipsis・.history-infoにmin-width:0（枠はみ出し防止）。絞り込み=キーワード+四麻/三麻
- 履歴ログ: フィルタタブ（すべて/入力/修正/削除。タグと同配色=緑/オレンジ/赤）。点数は「名前 点数」ペア表示
- **変更をもとに戻す（端末内バックアップ）**: 削除・修正・設定変更・名前編集の**直前の状態**（name/settings/rounds）を
  localStorage `mahjong-backup-v1` に控える（`takeBackup(g, label, expect)`）。
  **Firebaseには一切書かない**＝保存容量・通信コスト・セキュリティルールは一切変わらない（rules更新も不要）。
  保持は**1グループ5世代・全体900KBまで**（超えたら古いものから捨てる。QuotaExceededでも丸ごと失敗しないよう
  減らして再試行する`writeBackups`）。
  導線は2つ: ①操作直後のトーストの「元に戻す」（`showUndoToast`。8秒表示。`.toast.act`でpointer-eventsを有効化）
  ②履歴モーダル上部の一覧（`backupSectionHtml`。タブより上に置く＝フィルタの対象ではないため）。
  戻すと`sessions/{id}`にname/settings/roundsを書き戻す＝**全員の画面に反映される**。復元自体も直前を控えるのでやり直せる。
  **他の人の入力を巻き戻さないためのガード**: 控えた時点で想定した試合数（`expect`）と現在の試合数が食い違うときは
  即時復元せず確認ダイアログに回す（`restoreBackupById(key, false)` → `confirmRestore`）。履歴からの復元は常に確認あり。
  過去の試合（結果詳細）から戻す場合はlocalStorageの控えを書き換える（行き先の判定は`restoreTargetOf`）
- 設定変更モーダル: 試合形式は変更不可（文言も「試合形式」で統一。対局形式/対戦形式とは書かない）。ルール変更は全再計算（⚠表示）。ヘッダー右に小「キャンセル/保存」（closeFormModalがクリア）。
  メンバー削除は対局済み/最低N人なら不可。チーム戦OFFでもteams保持

## テスト
- /tests.html = index.htmlをiframeで読み実物関数を18ケース検証。**計算ロジック変更時はALL PASS確認必須**
- tools/smoke_test.py = 主要動線のE2E（デプロイ時にCIが自動実行。ローカルは PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 tools/smoke_test.py）

## 落とし穴
- **起動時のhistory.replaceStateで第3引数にlocation.pathnameだけを渡すと、共有URLの#セッションIDが消えて自動参加が壊れる**
  （2026-07-18に発生。「共有URLを開いてもLPしか出ない」の原因。必ず `location.pathname + location.hash` にする）
- iOSで transform＋fixed＋input はタップ不良を起こす（ボトムシート廃止の理由）。モーダルはtransformなしで
- requestAnimationFrameは非表示タブで発火しない → UI更新に使わない（カルーセルのドットで事故った）
- .toggle-btnはbackgroundにtransitionがあり、切替直後のgetComputedStyleは中間色を返す（検証時の偽陽性）
- ブラウザ検証: プレビューのモバイルエミュレーションではfixed要素の幅がペイン実幅になる（scrollWidth偽陽性。実スクロールはwindow.scrollXで判定）
- チーム編成エディタ再初期化前に必ず captureTeamNames()（入力中のチーム名が消える）
- 確認モーダルのOKボタン（#confirm-modal-ok）は使い回し。文言も用途ごとに毎回textContentでセットし直す
  （削除=「削除する」／復元=「戻す」。片方だけ書き換えると次の削除で「戻す」と表示される）
- `.toast`はleft:50%だけだと使える幅が画面の半分（187px）に制限され、長い文言が折り返して2行になる
  → `width: max-content` ＋ `max-width: calc(100vw - 24px)` で内容なりの幅にする
- グリッド／flexアイテムはmin-width:autoで内容に引きずられて広がる → min-width:0 を忘れない
  （2026-08: 区切りのない長い半角英数字のチーム名で、順位カードのスコア値が画面外に押し出された）
- Canvasで長文を手で折り返すときは書記素クラスタ単位で切る（コードポイント単位だと結合文字が壊れる）
- CSS zoomを小さくすると、ブラウザの最小フォントサイズ設定で文字だけ縮まなくなり、table-layout:fixed＋ellipsisのセルは文字が消える
  → 縮小しうる表はtable-layout:autoにし、消えて困るラベルにellipsisを使わない（画像出力の`forImage=true`がこれ）
- **表の縮小にCSS zoomを使ってはいけない**（2026-08-06に実機で発覚）。zoomはレイアウトごと縮むため、
  モバイルの最小フォントサイズ制限で「セルは縮むのに文字は縮みきらない」＝文字がセルからはみ出す。
  縮小は必ず`transform:scale`（見た目だけ縮み、レイアウトは不変なので構造的にはみ出さない）
- **iOS Safariの自動文字拡大（text autosizing）**は、横幅が画面より広いブロック＝横スクロールする表があると発動し、
  文字だけ勝手に大きくなってセルから溢れる → `html { -webkit-text-size-adjust: 100% }` で抑止済み（消さないこと）
- `.rounds-table th.sticky-col`（0,2,1）はクラス2つの上書き（0,2,0）に勝つ → 上書きは同じくth/td付きで書く（lp-specのbm-noteと同じ詳細度事故）
- paddingのあるスクロールコンテナ直下でposition:sticky; left:0を使うと、固定位置はpadding端ではなくコンテナ端＝スクロール開始時にpadding分ジャンプする
  → sticky列の横スクロールはpadding無しの内側ラッパー（overflow-x:auto）に担わせる
- 画像出力は非表示DOMにHTMLを展開して読み取る方式なので、**三麻は`.sanma`クラスをそのコンテナに付ける**
  （付け忘れると画面は青なのに画像の表ヘッダーだけ緑になる）
- セッションに新しいトップレベルキーを足すときはdatabase.rules.jsonの許可リストにも追加（$other:falseのため、忘れると保存が全部失敗する。→ docs/site-spec.md）
- HTML→画像はSVG foreignObject+canvas方式だとiOS Safariで壊れる/汚染される → 表の画像化はCanvasに自前描画する（buildResultCanvasの方式を踏襲）
- 検証でcanvasの絵をClaudeが目視したいときは、scratchpadのワンショット受信サーバー(save-server.js)へfetch POSTしてファイル化→Read（クリップボードはフォーカス制約で不可）
- 画像出力に絵文字（🥇🥈🥉等）をfillTextで描かない。環境によってモノクロ/豆腐になる → 色付きの図形で表現する
- Canvasには端末ごとの上限がある（iOS Safariは総ピクセル数約16.7M）。縦に伸びる画像は必ず上限チェックを入れる。
  超えたときは黙ってtoBlobがnullを返し、保存が丸ごと失敗する
