# アプリ仕様（index.html）

※「今の正」だけを書く。経緯・改修履歴はgit log。仕様を変えたらこのdocも更新すること。

## データモデルと計算
- Firebase `sessions/{10文字ID}`（URL共有モデル）＋ localStorage `mahjong-v3`（履歴最大20件・登録名）
- **起動時のセッション判定は「ハッシュ8文字以上」**（ページ内アンカー #howto をセッションIDと誤認しないため）
- `settings`: playerNames（3〜40人=MAX_MEMBERS）/ numPlayers（3|4）/ startPoints / returnPoints / uma[] /
  rate（スコア倍率）/ bonusEnabled / chipRate（チップ倍率）/ startChips（持ちチップ）/ yakitori /
  chombo / chomboPenalty（罰符pts・0=マークのみ）/ teamMode / teams=[{name, members:[playerNamesのindex]}]
- `rounds[]`: points[] / scores[]（チョンボ罰符適用後）/ members[]（参加者index）/ chips[]（**チップ差**）/ yakitori[] / chombo[] / at / edited
- 計算: スコア収支 = pts×rate ／ チップ収支 = チップ差×chipRate ／ 合計収支 = 両者の和
- チョンボ💩: `applyChombo(scores, chomboArr, s)` が罰符ptsを減算。**submitRoundとsaveGameEditの両方で必ず通す**。焼き鳥🐔はマークのみ
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
- 全画面モーダル: `openTableModal` / `openStatsModal` / `openChartModal`（#table-modal・zoom共用 40〜200%）
- カード開閉: `collapsedCards` + `toggleCard(key)`（key: team/score/rounds/rank/chart/ichart/settings）
- 計測: `track(event, params)` → dataLayer（group_create / group_join / round_submit / share_copy）

## セットアップ画面
- 統合カード（グループ名 → メンバー名 → **試合形式**=四麻/三麻＋個人戦/チーム戦の2トグル1ラベル）→ ルール設定 → オプション
- プレースホルダーは例の値をそのまま（まじゃすこ学園サッカー部／山田先輩／150等。「（例）」は付けない）。グループ名初期値は空（未入力ならstartGameで日付名）
- **作成日はゲーム画面・結果詳細のタイトル下に自動表示**（#game-date / #detail-date）
- 「登録名の管理」ボタンはメンバー名ラベルの右（常時表示）。モーダル: [ゲームに追加]/[取り消し]、右上[編集]で↑↓並び替え・削除
- **三麻選択でview-setupに.sanma**（トグル・カード枠が青#4261AAに）
- オプション名: 「チップあり🍪」「焼き鳥あり🐔」「チョンボあり💩」。説明は「本文。<br>※注意書き。」の2行形式。
  倍率例示: 「例：スコア倍率が×100の場合、+123.0pts → +12,300bonus」「例：チップ倍率が×500の場合、+5枚 → +2,500bonus」
- 「持ちチップ（枚）」（左）・チップ倍率（右）。チップ倍率デフォルト×500・持ちチップ初期値20
- チョンボ罰符セレクト: 0/−10/−20/−30/−50/カスタム。デフォルト−20pts
- チーム編成エディタ: 各ボックスにチームカラー（左5pxボーダー＋●）。タップで次チームへ・🎲ランダム・チーム名編集

## スコア入力シート
- **「設定の編集」と同じ中央モーダル形式**（.sheet=暗背景オーバーレイ、.sheet-box=白パネル max-width:430px・パネル内スクロール・transformなし・背景タップで閉じる）
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
- カード順: チーム成績（チーム戦のみ）→ 総合成績 → 対局履歴 → その他成績 → スコア推移 →
  個人スコア推移（チーム戦のみ）→（詳細のみ）設定
- 全カード右上に開閉トグル（▾/▸）。開き直すと全開にリセット。たたむとアクションボタンも隠す
- **0試合の間は順位バッジを出さない**（灰色「—」。1試合目から順位・メダル表示）
- 総合成績: pts順位がデフォルト。ミニトグル「スコア/チップ」。収支ONなら「合計収支 ▾」で内訳展開（開始時チップ行は置かない）
- 対局履歴: 常に表形式。行タップで修正・削除。「もっと見る」で全画面モーダル（コンパクト列幅+ズーム）
- その他成績: **対局履歴と同じ転置レイアウト（列=メンバー・行=成績項目、1行目にプレイヤー名）**。項目列はsticky。
  行=上から 1着..n着/試合数/平均着順/連対率/トップ率/ラス回避/スコア/素点/順位点/最高点数/最低点数（平均点数は載せない）。
  素点=(持ち点−返し点)÷1000合計、順位点=スコア−素点、連対率=(1着+2着)÷試合数、トップ率=1着÷試合数。
  ベスト（平均着順min・連対率/トップ率/ラス回避/最高点数max）は文字色オレンジのみ。
  チーム名の行は置かない（所属はプレイヤー名のチームカラー●のみで示す）
- チーム識別: TEAM_COLORSは**40色**（1-8は赤#e60012/青#0075c2/緑#00a040/橙#f39800/紫#9b26b6/黄#e6b400/桃#ff5ca8/茶#8b5a2b で不変。
  9色目以降も白以外の互いに異なる色）。名前の前に`.team-dot`●（文字色は変えない）。チーム戦の表1行目は灰色TEAM_HEAD_BG=#5f6e6b。
  列と合計収支はチームA→B…順（個人戦の合計収支は値の大きい順）
- グラフ: 個人戦「スコア推移」／チーム戦「チームスコア推移」（チーム合算・チームカラー）＋その下に
  「個人スコア推移」（`chartHtml(rounds, s, true)`。色はチームカラーと独立にCHART_COLORS 20色を個人単位で割当）
- 順位バッジ: 1〜3位のみ🥇🥈🥉、4位以下は灰色数字
- タイトル横ボタンは「設定の編集」（.title-edit-btn・三麻で青）
- モーダル（もっと見る）: ヘッダー2段構成（タイトル+閉じる／ズーム±+注意書き）＝長い名前でも切れない

## その他の機能
- 過去の試合: カードは**グループ名・日付・総試合数・四麻/三麻・個人戦/チーム戦・プレイヤー名のみ**（結果のプレビューは載せない）。
  文字は13pxで統一、グループ名はellipsis・.history-infoにmin-width:0（枠はみ出し防止）。絞り込み=キーワード+四麻/三麻
- 履歴ログ: フィルタタブ（すべて/入力/修正/削除。タグと同配色=緑/オレンジ/赤）。点数は「名前 点数」ペア表示
- 設定変更モーダル: 試合形式は変更不可（文言も「試合形式」で統一。対局形式/対戦形式とは書かない）。ルール変更は全再計算（⚠表示）。ヘッダー右に小「キャンセル/保存」（closeFormModalがクリア）。
  メンバー削除は対局済み/最低N人なら不可。チーム戦OFFでもteams保持

## テスト
- /tests.html = index.htmlをiframeで読み実物関数を18ケース検証。**計算ロジック変更時はALL PASS確認必須**

## 落とし穴
- iOSで transform＋fixed＋input はタップ不良を起こす（ボトムシート廃止の理由）。モーダルはtransformなしで
- requestAnimationFrameは非表示タブで発火しない → UI更新に使わない（カルーセルのドットで事故った）
- .toggle-btnはbackgroundにtransitionがあり、切替直後のgetComputedStyleは中間色を返す（検証時の偽陽性）
- ブラウザ検証: プレビューのモバイルエミュレーションではfixed要素の幅がペイン実幅になる（scrollWidth偽陽性。実スクロールはwindow.scrollXで判定）
- チーム編成エディタ再初期化前に必ず captureTeamNames()（入力中のチーム名が消える）
- グリッドアイテムはmin-width:autoで内容に引きずられて広がる → min-width:0 を忘れない
