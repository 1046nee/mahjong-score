# 画像生成ガイド（OGP・SNS画像・イラスト）

## ブランド設定（PIL用）
- 本文フォント: `C:\Windows\Fonts\NotoSansJP-VF.ttf`（可変フォント。`f.set_variation_by_axes([weight])` で太さ指定。**見出しは900=Black**＝サイトのヒーローh1相当）
- 絵文字: `C:\Windows\Fonts\seguiemj.ttf` を `d.text(..., embedded_color=True)` でカラー描画
- パレット（RGB）:
  緑 (23,112,131) ／ サンマ青 (66,97,170) ／ オレンジ (231,86,32) ／ ダーク (31,42,40) ／ グレー文字 (85,99,95)
  薄グレー (154,168,164) ／ 枠線 (226,236,231) ／ 淡緑 (228,243,236) ／ 淡背景 (242,247,246)
  プラス青 (26,35,126) ／ マイナス赤 (198,40,40)
  チームカラー: 赤(230,0,18) 青(0,117,194) 緑(0,160,64) 橙(243,152,0)

## 定番モチーフ（サイトと世界観を揃える）
- iPhone風スマホ: 角丸ダークフレーム＋白画面＋ダイナミックアイランド。中身は「スコア収支」（🥇🥈🥉＋名前＋±値＋折れ線グラフ）や各画面
- 4方向に尖った✨スパークル（Q曲線 or 8頂点ポリゴン、waist≈R×0.22）・淡い光の円・小さなドット
- majasco.jp 表記（薄グレー・隅）

## スクリプト（tools/。出力先はすべて「まじゃすこ素材/」）
- `tools/make_ogp.py` — OGP画像 2100×1103
- `tools/make_xheader.py` — Xヘッダー 1500×500
- `tools/make_ig1.py` — Instagram初投稿 1080×1350（縦5:横4）
- `tools/make_ig_series.py` — IG使い方カルーセル6枚＋機能紹介6枚（共通ヘルパー: phone_frame/screen_*/sparkle/slide）
- `tools/make_ig_feature7.py` — 機能紹介feature-7「CSVで書き出せる」単発
- `tools/make_ig_daily.py` — IG毎日投稿用: 麻雀用語ミニ解説カード4枚（glossary-*）＋小ワザTips3枚（tips-*）
- `tools/make_threads_icon.py` — Threads/IG個人（@munii_dev）プロフィールアイコン3案 1080×1080
- `tools/shoot_app_screens.py` — 実アプリ画面のスマホ実寸スクショ撮影（index.htmlをローカル起動＋Firebaseを最小スタブ化。本番に触れない。出力: まじゃすこ素材/ig/shots/）
- `tools/make_ig_v2.py` — IGフィードv2 1080×1350（実画面スクショ×カラー背景の濃色デザイン。白基調シリーズがグリッドで沈む対策。要: shoot_app_screens.py を先に実行）
- `tools/record_app_demo.py` — 操作デモ動画の録画（LP→グループ作成→URL共有→点数入力→成績・グラフ。
  ローカル起動＋Firebaseスタブ＋タップ可視化。出力: demo-raw.mp4=素の縦長録画／demo-short-9x16.mp4=1080×1920ショート用合成。要: pip install imageio-ffmpeg）
- 新しい画像は既存スクリプトをコピーして作る。**サイトで使う画像だけ assets/ にコピーしてコミット**
- **「まじゃすこ素材/」は本体リポジトリに入れない**（.gitignore済み。公開リポジトリで画像を見られないように、
  **privateリポジトリ `1046nee/majasco-assets` にネストしたgitとして管理**。素材を作ったら まじゃすこ素材/ 内で add→commit→push。
  別PCでは mahjong/ 直下に `git clone https://github.com/1046nee/majasco-assets "まじゃすこ素材"`）

## サイト画像のルール
- favicon: `/favicon.ico`（16/32/48。favicon.pngからPIL生成）＋ `/assets/favicon.png`（512）
- OGP: 現行 `/assets/ogp2.png`。**差し替えるときはファイル名を変えて全ページのog:image/twitter:imageを書き換える**（Xが画像URL単位でキャッシュするため同名上書きは反映されない）。旧ogp.pngは残置
- ロゴ: `/assets/logo.png`（800×250透過・全ページヘッダー）

## 牌姿図（ブログ用インラインSVG）
- **tools/make_tile_svg.py** で生成（hand_svg=手牌1列／dora_map_svg=表示牌→ドラ対応図）。
  牌コード: m1..m9/p1..p9/s1..s9/E,S,W,N/Wh(白)/Gr(發)/Rd(中)。1索は鳥柄のため図では使わない（避けた手牌例を作る）
- 13〜14枚の手牌はmin-width:520px前後を持たせ、**必ず`<div style="overflow-x:auto">`で包む**（スマホは横スクロールで見せる）
- レイアウト確認はscratchpadのPILプレビュー（同じ座標表を描画）をReadで目視
- 掲載済み: リーチ記事=テンパイ例／役一覧=タンヤオ・役牌の完成形／ドラ記事=表示牌→ドラ対応図

## アプリ実画面のスクショ（IG v2・テーマWeek用）
- `tools/shoot_app_screens.py` で撮影し `まじゃすこ素材/ig/shots/` へ。make_ig_v2.py / make_ig_team.py がこれを合成する
- **アプリのカード名やUIを変えたらスクショを撮り直す**（画像内の文字が古いまま残る。
  例: 2026.08にカード名を 総合順位／チーム順位／個人成績 へ変更した）

## 実写真（ブログ用）
- **原本はまじゃすこ素材/写真/（private）**。公開するのはPIL加工後の `/assets/photo-*.jpg` のみ
- 加工手順: **人名・個人情報をPILの黒塗りで必ずマスク**（加工後にReadで目視確認）→ 幅1200pxへ縮小 → JPEG quality=82
- 記事への挿入は `<figure>`＋`loading="lazy"`＋altとfigcaption必須。キャプションに「（名前は伏せています）」を明記
- 公開済み: photo-score-notebook.jpg（集計係記事）／photo-score-sheets.jpg（集計係・ウマオカ記事）／
  photo-jantaku-hand.jpg（牌の種類記事）／photo-kotatsu-mahjong.jpg（持ち物リスト記事）
- 写真を差し込んだ記事はJSON-LDのdateModifiedを更新する

## セーフゾーン
- OGP（X表示）: 2:1で中央トリミング → 2100×1103は上下約26pxずつ切れる
- Xヘッダー: プロフィールアイコンが左下に重なる／端末により上下約60px切れる → 文字は中央帯に
- IG: **フィード画像は縦5:横4（1080×1350）で作る**（プロフィールグリッドが縦5:横4表示のため。1:1は使わない）。ストーリーズは1080×1920

## QA（生成後に必ず）
1. ClaudeがReadで画像を開いて目視確認
2. 文字がフレーム・カード・画面の内側に収まっているか（PILは自動折返ししない）
3. 装飾と文字の重なりがないか
4. docs/sns-ops.md のチェックリストも通す

## 落とし穴
- リモート実行環境（Claude Code on the Web等）からは majasco.jp / Firebase への接続がegressポリシーでブロックされることがある
  → 実画面スクショは tools/shoot_app_screens.py のローカル起動＋Firebaseスタブ方式で撮る（本番データにも一切触れないので検証セッションの削除も不要）
- フォントパスはOS依存（Windows: C:\Windows\Fonts\NotoSansJP-VF.ttf ／ Linux: /usr/share/fonts/truetype/noto-jp/NotoSansJP.ttf に配置）。make_ig_v2.pyは両対応済み
- 可変フォントのweight指定を忘れると細字になる（try/exceptで握りつぶしているため気づきにくい）
- bashヒアドキュメント内のWindowsパス（\U等）はエスケープ事故のもと → スクリプトはファイルに書いて実行する
- 生成スクリプトはtools/に置く（scratchpadはセッションが変わると消える）
- **キャンバス比率の変更**はW,H定数の変更＋縦座標の再配分（glow中心・sparkle位置・phone_frameのy0・footer・closingのy）で対応する。
  過去に1080×1080→1440→1350と2回実施。変更後は**全枚数をReadで目視QA**（はみ出し・装飾かぶり・「ちょい見え」の見切れ装飾）
