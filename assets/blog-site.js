/* ==========================================================
   まじゃすこ ブログ共通スクリプト（/assets/blog-site.js）
   記事のメタ情報（カテゴリ・公開日・おすすめフラグ）はこのファイルの
   BLOG_POSTS だけで管理する。新しい記事を公開したら、
   ここに1件追加するだけで一覧・カテゴリページ・サイドバーに反映される。
   （お知らせ記事の場合は /news/feed.xml にも <item> を1件追加すること）

   使い方（HTML側）:
   - 一覧を出す場所:      <div class="post-list" data-post-list="all|mahjong|news|blog"></div>
   - カテゴリナビ:        <nav class="cat-nav" data-cat-nav="現在のカテゴリkey"></nav>
   - サイドバー:          <aside class="side" data-sidebar></aside>
   ========================================================== */

const BLOG_CATS = {
  mahjong: { name: '麻雀攻略', url: '/mahjong/' },
  news:    { name: 'お知らせ', url: '/news/' },
  blog:    { name: '雑記',     url: '/blog/' }
};

// 新しい順に並べる。recommended: true の記事が「今月のおすすめ記事」に出る（3〜4件を目安に手動で付け替える）
const BLOG_POSTS = [
  { url: '/blog-mahjong-suuji.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール解説',
    title: '麻雀の数字の理由｜136枚・王牌14枚・満貫8,000点…なぜその数字？',
    desc: '牌136枚、王牌14枚、翻＋2の場ゾロ、親1.5倍、満貫8,000点、積み棒300点、30,000点返し。数字の理由を計算で確かめます。' },
  { url: '/blog-sekai-mahjong.html', cat: 'mahjong', date: '2026.10.27', tag: '楽しむ',
    title: '世界の麻雀｜中国・台湾・香港・アメリカのルールの違い',
    desc: '中国の公式ルール（役81種類・8点縛り）、手牌16枚の台湾、ジョーカーと毎年変わるカードのアメリカなどを比較表で紹介。' },
  { url: '/blog-nichijougo.html', cat: 'mahjong', date: '2026.10.27', tag: '楽しむ',
    title: '日常語になった麻雀用語8選｜テンパる・安パイ・連チャン…もとの意味は？',
    desc: 'テンパる、安パイ、連チャン、メンツ、リーチ、オーラス、チョンボ。麻雀での意味と日常での意味を国語辞典で確かめて紹介。' },
  { url: '/blog-ronjutsu.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: '麻雀ルールの論述問題8問｜ダブ東の符・リーチ後の暗槓・喰い替え・頭ハネ…「それぞれの利点を述べよ」の練習',
    desc: 'ルールの考え方を説明する論述の練習問題8問。解答の例と採点のポイントつき。' },
  { url: '/blog-mleague-points.html', cat: 'mahjong', date: '2026.10.27', tag: 'Mリーグ',
    title: 'Mリーグのポイント持ち越しの計算｜セミファイナル・ファイナルで「半分」になると何が起きる？',
    desc: '半分持ち越しで逆転が起きる仕組みを、架空の6チームで最後まで計算。' },
  { url: '/blog-league-taikai.html', cat: 'mahjong', date: '2026.10.27', tag: '運営',
    title: '仲間内の麻雀大会・リーグ戦の作り方｜予選のポイントは全部持ち越し？半分？リセット？計算で比べる',
    desc: '予選のポイントの持ち越し方で優勝者が変わる。同じ結果で計算して比べます。' },
  { url: '/blog-sanma-rules.html', cat: 'mahjong', date: '2026.10.27', tag: '三麻',
    title: '三麻のルールの分かれ目｜北抜き・ツモ損・抜く牌・チー。ツモの払い方を点数表で比べる',
    desc: '三麻の北抜き・ツモ損・抜く牌・チーの決め方。ツモの払い方を点数表で比べます。' },
  { url: '/blog-haitei.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: '海底・河底の細かい決まり｜最後の1枚でカン・リーチ・鳴きはできる？海底は誰に回る？',
    desc: '最後の1枚でカン・リーチ・鳴きができない理由と、海底が誰に回るかの計算。' },
  { url: '/blog-keishiki-tenpai.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: '形式テンパイと空テン｜役なし・待ちが残っていないテンパイは流局でどう扱う？ノーテン罰符の計算つき',
    desc: '役なしのテンパイ・待ちを使い切ったテンパイの扱いと、ノーテン罰符の分け方。' },
  { url: '/blog-kuikae.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: '喰い替えとは｜現物・スジの喰い替えがだめな理由と、鳴いたあとに切れない牌',
    desc: '鳴いた直後に切れない牌。現物とスジの喰い替えを牌の図と練習問題で。' },
  { url: '/blog-riichi-ankan.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: 'リーチ後の暗槓はどこまでできる？｜待ちが変わる・組み方が変わるカンがだめな理由を手牌の例で',
    desc: 'リーチ後の暗槓は、待ちと組み方が変わらないときだけ。できる例・できない例を手牌で。' },
  { url: '/blog-pao.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: 'パオ（包・責任払い）とは｜大三元・大四喜・四槓子の成立条件と、支払いの計算問題6問',
    desc: '大三元・大四喜・四槓子のパオが成り立つ条件と、ツモ・ロン・積み棒・ダブル役満の払い方を計算問題6問で。' },
  { url: '/blog-yakuman-rules.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: '役満のルールはMリーグと雀魂で違う｜四暗刻単騎・国士無双13面待ちはダブル役満？ 国士の暗槓ロンは？',
    desc: '四暗刻単騎・国士無双13面待ちはダブル役満か、国士無双で暗槓をロンできるか。Mリーグ・雀魂・天鳳の違いを表で比べます。' },
  { url: '/blog-mahjong-anime.html', cat: 'mahjong', date: '2026.10.27', tag: '楽しむ',
    title: '麻雀アニメのおすすめ7選｜咲-Saki-・アカギ・ぽんのみちなど、どの配信サービスで見られるかの一覧',
    desc: '麻雀アニメ7作品と、U-NEXT・dアニメストア・Huluのどこで見られるかを表で整理。' },
  { url: '/blog-mahjong-manga.html', cat: 'mahjong', date: '2026.10.27', tag: '楽しむ',
    title: '麻雀漫画のおすすめ10選｜咲-Saki-・アカギ・天・哲也など有名作の紹介と、アニメ化・どこで読めるかの一覧',
    desc: '有名な麻雀漫画10作品の紹介と、アニメ化・実写化の一覧、紙・電子書籍で読む方法。' },
  { url: '/blog-rule-wakareme.html', cat: 'mahjong', date: '2026.10.27', tag: 'ルール',
    title: '麻雀ルールの分かれ目｜ダブ東の雀頭は2符か4符か、ダブロンか頭ハネか——意見が分かれる6つのルールと、それぞれの理由',
    desc: 'ダブ東の雀頭は2符か4符か、ダブロンか頭ハネか、喰いタン・途中流局・同点・トビ。両方の考え方の良さと点数の例で比べます。' },
  { url: '/blog-local-yaku.html', cat: 'mahjong', date: '2026.10.26', tag: '役',
    title: 'ローカル役満・ローカル役の一覧｜八連荘・大車輪・紅孔雀と、中国・台湾の麻雀の特別な役',
    desc: '八連荘・大車輪・紅孔雀などのローカル役満と、中国・台湾の麻雀の特別な役。牌の並びの例つき。' },
  { url: '/blog-mahjong-kanji.html', cat: 'mahjong', date: '2026.10.23', tag: '用語',
    title: '麻雀用語の漢字の意味｜「混」と「清」、么九と断么九…同じ字でつながる役の名前',
    desc: '混と清、么九と断么九、七対子のチー＝7。同じ字でつながる役や言葉を、漢字の意味で整理。' },
  { url: '/blog-machi-dojo.html', cat: 'mahjong', date: '2026.10.23', tag: '練習問題',
    title: '麻雀の待ち当て道場｜多面張の練習問題14問と、強い待ちの形（三面張・ノベタン・エントツ）',
    desc: '多面張の練習問題14問と、三面張・ノベタン・エントツなど強い形。待ちの牌ごとの分け方つき。' },
  { url: '/blog-mahjong-yougoshu.html', cat: 'mahjong', date: '2026.10.23', tag: '用語集',
    title: '麻雀用語集（137語・五十音順）｜読み方つき・正式名称と通称・俗語の区別',
    desc: '137語を五十音順に。すべて読み方つきで、正式名称・一般的な言い方・俗語を色分け。正式名称とふだんの言い方の対応も。' },
  { url: '/blog-dantai-rekishi.html', cat: 'mahjong', date: '2026.10.23', tag: 'プロ団体',
    title: '麻雀プロ団体の歴史｜5団体の成り立ちと代表の移り変わり（連盟・最高位戦・協会・RMU・麻将連合）',
    desc: '5団体の系譜を年表で。各団体の年表・代表の移り変わり（小島武夫→灘麻太郎→森山茂和など）と、公式サイト・X・YouTube。' },
  { url: '/blog-mahjong-yougo.html', cat: 'mahjong', date: '2026.10.23', tag: '正式名称',
    title: '麻雀の正式名称一覧（80語）｜漢字と読み方を図で覚える（プロテスト対策にも）',
    desc: '洗牌・開門・荘家・副露など80語を漢字・読み方・意味と図で。読み方を隠せる暗記モードつき（プロテスト対策にも）。' },
  { url: '/blog-mleague-kansen.html', cat: 'mahjong', date: '2026.10.23', tag: 'Mリーグ',
    title: 'Mリーグ観戦ガイド｜初めて見る人のための卓の見方・実況でよく聞く言葉・ポイントのしくみ',
    desc: '卓を上から見た図で、見るところを7つにしぼって説明。実況でよく聞く言葉16個と、Mリーグのポイントのしくみも。' },
  { url: '/blog-yaku-ichiran.html', cat: 'mahjong', date: '2026.10.23', tag: '役一覧',
    title: '麻雀の役一覧（全38役）｜翻数・鳴いたときの翻数と牌の並びの例つき早見表',
    desc: '1翻〜役満の全38役を、翻数と鳴いたときの翻数、牌の並びの例つきで。1枚の一覧表（画像・印刷用PDF）つき。' },
  { url: '/blog-mahjong-game-apps.html', cat: 'mahjong', date: '2026.10.21', tag: 'ゲームアプリ',
    title: '麻雀ゲームアプリおすすめ7選｜雀魂・天鳳・MJ・麻雀格闘倶楽部などを比較（2026年版）',
    desc: '雀魂・天鳳・MJ・麻雀格闘倶楽部など7つを、App Storeの評価と特徴で比較。目的別の選び方も。' },
  { url: '/blog-mahjong-youtube.html', cat: 'mahjong', date: '2026.10.21', tag: 'YouTube',
    title: '麻雀のおすすめYouTube｜未経験〜上級者のレベル別勉強動画と、Mリーグ・プロのチャンネル（2026年版）',
    desc: '未経験〜上級者のレベル別に、勉強に使える動画を埋め込みで紹介。Mリーグ・団体の公式とMリーガーのチャンネルも一覧に。' },
  { url: '/blog-mahjong-books.html', cat: 'mahjong', date: '2026.10.21', tag: '麻雀の本',
    title: '麻雀のおすすめ本｜未経験・初心者・中級者・上級者のレベル別19冊（2026年版）',
    desc: '未経験・初心者・中級者・上級者の4段階で19冊。入門書から何切る、押し引き、データの戦術書、2026年の新刊まで。' },
  { url: '/blog-meet-mleaguer.html', cat: 'mahjong', date: '2026.10.21', tag: 'Mリーグ',
    title: 'Mリーガーに会う・一緒に打つ方法｜パブリックビューイング、撮影会、イベント、雀荘のゲスト（2026-27）',
    desc: 'PVツアーと撮影会、全40選手が登場するプレミアムナイト、一緒に打てるイベント、雀荘のゲスト来店。情報の集め方とマナーも。' },
  { url: '/blog-mahjong-pro.html', cat: 'mahjong', date: '2026.10.21', tag: '麻雀プロ',
    title: '麻雀プロになるには｜プロテストの日程・試験内容・費用と、プロになってからの道（2026年版）',
    desc: '5団体の入り方と試験の実施例、必要な知識と例題（点数計算・何切る）、プロになってからリーグを上がる道まで。' },
  { url: '/blog-mahjong-titles.html', cat: 'mahjong', date: '2026.10.21', tag: 'タイトル戦',
    title: '麻雀の主なタイトル戦と現在のタイトル保持者（2026年版）｜鳳凰位・最高位・雀王・最強位ほか',
    desc: '各団体の最高峰から団体をこえる大会まで、主なタイトル戦と2026年10月時点の保持者を表でまとめました。' },
  { url: '/blog-mleague-2026.html', cat: 'mahjong', date: '2026.10.21', tag: 'Mリーグ',
    title: 'Mリーグ2026-27 完全ガイド｜全10チーム・40選手、ルール、試合の流れと見方',
    desc: '今季の全10チーム・40選手、ドラフトでの入れ替わり、ルール、シーズンの流れと見方。各チームの公式ページへのリンクつき。' },
  { url: '/blog-mleague-history.html', cat: 'mahjong', date: '2026.10.21', tag: 'Mリーグ',
    title: 'Mリーグの歴史｜歴代優勝チーム・MVP・各シーズンの順位とルールの移り変わり',
    desc: '歴代優勝チームとMVP、各シーズンのファイナル順位、チーム数・試合数・勝ち上がりの仕組みの変化を表で振り返ります。' },
  { url: '/blog-pro-dantai-rules.html', cat: 'mahjong', date: '2026.10.21', tag: 'プロ団体',
    title: '麻雀プロ団体とルールの違い｜連盟・最高位戦・協会・RMU・麻将連合とMリーグを比較',
    desc: '5つのプロ団体の特徴と、一発・裏ドラ・順位点・持ち点の違いを比較表で。友人同士で試すときの設定まで。' },
  { url: '/blog-mahjong-ai.html', cat: 'mahjong', date: '2026.10.21', tag: '麻雀AI',
    title: '麻雀AIの比較｜NAGA・Mortal・MAKA・Suphx・LuckyJの違いと、セット麻雀での振り返り方',
    desc: '使えるAIと記録を残したAIの違い、対応する牌譜と料金の形、遊んでいる場所ごとの使い分け、牌譜が残らない対面のセット麻雀の振り返り方まで。' },
  { url: '/news/nakama-page.html', cat: 'news', date: '2026.10.13', tag: '新機能',
    title: '仲間ページを追加しました｜定例会の通算順位・成績表・総当たり表をみんなで見る',
    desc: 'いつものメンバーで打った複数のゲームを1つのページにまとめ、通算順位・成績表・総当たり表・2人の対戦をメンバー全員で見られる「仲間ページ」を追加しました。作り方、名簿と連携の考え方、権限の違いまで説明します。' },
  { url: '/news/mypage-stats.html', cat: 'news', date: '2026.10.13', tag: '新機能',
    title: 'マイページを追加しました｜Googleログインで記録を残し、自分の成績とスコアの推移を見る',
    desc: 'Googleでログインすると、参加したゲームが機種変更しても消えずに残り、平均着順・通算スコア・トップ率などの成績と、年・月・日ごとのスコアの推移、相手ごとの対戦成績が見られるようになりました。' },
  { url: '/news/kiroku-kakutei.html', cat: 'news', date: '2026.10.13', tag: '新機能',
    title: '記録の確定を追加しました｜対局の終了から12時間で、試合の結果は誰も書き換えられなくなります',
    desc: '共有URLを知っている人なら誰でも入力できる仕組みのまま、終わった試合の結果を守るため、対局の終了から12時間（終了しなくても最後の入力から24時間）で記録が確定し、誰も書き換えられなくなるようにしました。' },
  { url: '/blog-season-ranking.html', cat: 'mahjong', date: '2026.09.25', tag: '遊び方ガイド', tagStyle: 'orange', recommended: true,
    title: '麻雀仲間の通算成績と相性のつけ方｜日をまたいだ順位と対戦成績の読み方',
    desc: '何日分かの成績を1年分・大会の2日間分としてまとめるときの決め方と、相手ごとの成績（相性）の読み方を計算例つきで解説。三麻・四麻の分け方、ルールが違う日の扱い、規定試合数、直接対決とスコア差の違いまで。' },
  { url: '/blog-score-examples.html', cat: 'mahjong', date: '2026.08.25', tag: 'スコア計算入門', recommended: true,
    title: '麻雀のスコア計算 実例12パターン｜同点・トビ・三麻・チョンボまで全部計算してみた',
    desc: 'ウマ・オカ込みのスコア計算を、実際の持ち点から途中式ごと12パターン計算しました。同点の山分け、トビ、三麻、チョンボ罰符、複数試合の累計まで。数字はすべてアプリの計算ロジックと突き合わせて検証済みです。' },
  { url: '/blog-house-rules.html', cat: 'mahjong', date: '2026.08.25', tag: '遊び方ガイド', tagStyle: 'orange', recommended: true,
    title: 'セット麻雀のルールの決め方｜打ち始める前に決める10項目チェックリスト',
    desc: '仲間内の麻雀で揉めるのは、始まる前に決めていなかったことが原因です。持ち点・返し点・ウマ・同点の扱い・終了時の供託など、打ち始める前に決めるべき10項目を判断材料つきでまとめました。' },
  { url: '/blog-score-mismatch.html', cat: 'mahjong', date: '2026.08.25', tag: 'スコア計算入門',
    title: '麻雀の点数が合わないときのチェックリスト｜集計係が使う原因の切り分け方',
    desc: '半荘の点棒の合計が合わない、スコアの合計が0にならない。そんなときに上から順に潰していける実践チェックリストです。ズレ幅から原因を特定する方法と、二度と起こさないための予防策をまとめました。' },
  { url: '/blog-mawashi-uchi.html', cat: 'mahjong', date: '2026.08.25', tag: '遊び方ガイド', tagStyle: 'orange',
    title: '5人以上で麻雀を打つときの回し方｜抜け番の決め方と成績が不公平にならない見方',
    desc: '5人・6人・7人と卓が1つのときの抜け番の回し方を、人数別の一巡表つきで解説します。試合数が違う人同士の成績をどう比べるか（合計・平均・平均着順の使い分け）まで扱います。' },
  { url: '/news/hikitsugi-url.html', cat: 'news', date: '2026.08.07', tag: '新機能',
    title: '機種変更しても履歴が引き継げる「引き継ぎURL」を追加しました',
    desc: '「引き継ぎURL」を作っておけば、機種変更やブラウザの変更をしてもURLを開くだけで履歴がまるごと戻ります。会員登録は不要。あわせて、うっかり削除を「元に戻す」機能も追加しました。' },
  { url: '/blog-shukei-gakari.html', cat: 'blog', date: '2026.07.13', tag: '体験談', tagStyle: 'orange', recommended: true,
    title: '麻雀の集計係を8年やってわかった、手書きスコア記録の限界',
    desc: '暗算が得意な私でも、8年間で何度も集計を間違えました。合計が合わない・犯人さがし・読めない字・ぐちゃぐちゃの修正跡……手書きスコア記録の失敗談と解決策を実体験で語ります。' },
  { url: '/blog-team-tournament.html', cat: 'mahjong', date: '2026.07.13', tag: '遊び方ガイド', tagStyle: 'orange',
    title: '麻雀を10人以上で楽しむ方法｜チーム対抗戦・トーナメントの開き方',
    desc: 'お盆や年末年始に10人以上で麻雀を楽しむには？チーム対抗戦・トーナメント・回し打ちランキングの3つの遊び方と、卓割り・抜け番・集計など運営のコツを実体験から紹介します。' },
  { url: '/news/csv-export.html', cat: 'news', date: '2026.07.14', tag: '新機能',
    title: '試合結果をCSVで書き出せるようになりました',
    desc: '試合結果をワンタップでCSVファイルとしてダウンロードできるようになりました。Excelやスプレッドシートに取り込んで、オリジナルの集計表や年間ランキングづくりに使えます。' },
  { url: '/news/update-2026-07.html', cat: 'news', date: '2026.07.10', tag: 'アップデート',
    title: '大型アップデートのお知らせ｜チーム戦・チップ記録・最大40人の回し打ちに対応しました',
    desc: 'チーム戦モード、チップの記録、メンバー3〜40人の回し打ち対応など、まじゃすこの大型アップデート内容を紹介します。' },
  { url: '/blog-manner.html', cat: 'mahjong', date: '2026.07.08', tag: 'ルール解説',
    title: '麻雀の準備とマナー｜持ち物リスト・チョンボ・途中流局まで',
    desc: '友人と麻雀を始めるときの持ち物リストと幹事の段取り、打つときのマナー、チョンボと途中流局の扱いを1ページにまとめました。' },
  { url: '/blog-rule-basics.html', cat: 'mahjong', date: '2026.07.08', tag: 'ルール解説',
    title: '麻雀のルール基本の基本｜半荘・東風戦と牌の種類・読み方（初心者向け入門）',
    desc: '半荘・東風戦の違い、局・親・本場・流局といった対局の流れと、萬子・索子・筒子・字牌の種類と読み方、136枚そろっているかの確かめ方まで。' },
  { url: '/blog-app-guide.html', cat: 'mahjong', date: '2026.07.07', tag: 'アプリの選び方', tagStyle: 'orange',
    title: '麻雀のスコア記録アプリの選び方｜5つのポイントと主なアプリの比較（2026年版）',
    desc: '比較すべき5つの軸と、主なスコア記録アプリ7つを実際に比べた表（2026年10月時点）。目的別の選び方まで。' },
  { url: '/blog-sanma-yonma.html', cat: 'mahjong', date: '2026.07.07', tag: 'ルール解説',
    title: '3人麻雀（サンマ）と4人麻雀の違いとは？ルール・点数の変更点を解説',
    desc: '牌の構成、持ち点・返し点、ウマの設定まで、3人麻雀ならではの違いを4人麻雀と比較しながら解説します。' },
  { url: '/blog-yaku-list.html', cat: 'mahjong', date: '2026.07.07', tag: '役一覧',
    title: '麻雀の役・リーチ・ドラ・鳴きの基本｜初心者がまず覚える4つ',
    desc: '麻雀を始めたらまず覚えたい、役・リーチ・ドラ・鳴きの4つを1ページにまとめました。基本の役10選、リーチのかけ方とフリテン、ドラの種類と数え方、ポン・チー・カンの違いまで。' },
  { url: '/blog-score-table.html', cat: 'mahjong', date: '2026.07.07', tag: '点数表',
    title: '麻雀の点数早見表｜子・親のロン・ツモ（オール）と符計算のやり方・満貫以上',
    desc: '子・親のロン・ツモを20〜110符で一覧。親のツモ（○○オール）、符計算のやり方と計算ツール、満貫以上も1ページで。' },
  { url: '/blog-uma-oka.html', cat: 'mahjong', date: '2026.07.06', tag: 'スコア計算入門',
    title: '麻雀のウマ・オカとは？初心者向けスコア計算入門',
    desc: 'ウマ・オカ・返し点・素点とは何かを、具体的な数字の例つきで初心者向けに解説します。' },
  { url: '/blog-why-majasco.html', cat: 'blog', date: '2026.07.06', tag: '開発ストーリー', tagStyle: 'orange',
    title: '麻雀のスコア計算がめんどうで『まじゃすこ』を作った話',
    desc: '対局後の計算が面倒、紙のスコアシートは読みにくい……。そんな不満から無料の麻雀スコア記録アプリを作りました。' }
];

(function () {
  const escHtml = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  const byDateDesc = (a, b) => b.date.localeCompare(a.date);

  function cardHtml(p) {
    // 左の絵＝記事ごとの絵（assets/thumbs/・tools/make_thumbs.py）。カテゴリの色は名前の色で見せる
    const th = '/assets/thumbs/' + p.url.split('/').pop().replace('.html', '') + '.svg';
    return `<a class="post-card has-thumb cat-${p.cat}" href="${p.url}">
      <span class="pc-thumb"><img src="${th}" alt="" width="320" height="240" loading="lazy" decoding="async"></span>
      <div class="pc-body"><span class="pc-meta"><span class="pc-cat">${BLOG_CATS[p.cat].name}</span>${p.tag ? `<span class="post-tag">${escHtml(p.tag)}</span>` : ''}<span class="date">${p.date}</span></span>
      <h2>${escHtml(p.title)}</h2>
      <p class="excerpt">${escHtml(p.desc)}</p></div>
    </a>`;
  }
  // カテゴリのタブ（すべて/麻雀攻略/お知らせ/雑記）。記事の数つき。tools/build_post_lists.js と同じマークアップ
  function catNavHtml(active) {
    const items = [['all', 'すべて', '/blog.html']].concat(Object.keys(BLOG_CATS).map(k => [k, BLOG_CATS[k].name, BLOG_CATS[k].url]));
    const count = k => BLOG_POSTS.filter(p => k === 'all' || p.cat === k).length;
    return '<div class="cat-nav-inner">' + items.map(([k, label, url]) =>
      `<a class="cat-tab cat-${k}${k === active ? ' on' : ''}" href="${url}"${k === active ? ' aria-current="page"' : ''}>${label}<span class="cnt">${count(k)}</span></a>`).join('') + '</div>';
  }
  function sideItem(p) {
    return `<li><a class="sb-link" href="${p.url}">${escHtml(p.title)}</a><span class="sb-date">${p.date}・${BLOG_CATS[p.cat].name}</span></li>`;
  }

  // 全ブログ/固定ページ共通: LP（トップ）と同じ見た目のヘッダー・フッターに差し替える。
  // 各HTMLに書かれた静的なヘッダー/フッターはJS無効時のフォールバック。
  // デザインを変えるときはこの関数だけ直せば全ページに反映される
  // ---- SNSアカウント（2026-10-22）: 記事で紹介する公式アカウント。URLは公式サイト・記事で確かめたものだけ足す ----
  // アイコンは App Store の公式のアプリのアイコン（Apple の Search API の画像。2026-10-22 ユーザーの依頼）
  const SNS_ICON = {
    x: '<img src="https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/21/99/a9/2199a9db-0dc2-305f-7b8f-a5bc80258dbf/ProductionAppIcon-0-0-1x_U007emarketing-0-8-0-0-0-85-220.png/128x128bb.jpg" alt="X" width="40" height="40" loading="lazy">',
    ig: '<img src="https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/01/2d/b1/012db1a7-249a-86e8-f025-72491c2a6475/Prod-0-0-1x_U007epad-0-0-0-1-0-0-sRGB-85-220.png/128x128bb.jpg" alt="Instagram" width="40" height="40" loading="lazy">',
  };
  const SNS_ACCOUNTS = {
    majasco_x: { pf: 'x', name: 'まじゃすこ', tag: 'このサイトの公式', handle: '@majasco_jp', url: 'https://x.com/majasco_jp',
      desc: '新しい機能のお知らせ、集計を楽にする使い方のコツ、ブログの新しい記事', go: 'Xでフォローする' },
    majasco_ig: { pf: 'ig', name: 'まじゃすこ', tag: 'このサイトの公式', handle: '@majasco_jp', url: 'https://www.instagram.com/majasco_jp/',
      desc: '画面の画像で見る使い方（入力・共有・成績）、ウマ・オカなどの用語の図解', go: 'Instagramでフォローする' },
    mleague_x: { pf: 'x', name: 'Mリーグ', tag: 'リーグ公式', handle: '@m_league_', url: 'https://x.com/m_league_',
      desc: '試合の予定と結果、イベント・チケットの発表。会場の解説者など直前のお知らせもここに出る', go: 'Xでアカウントを見る' },
  };
  function snsCardHtml(key) {
    const a = SNS_ACCOUNTS[key];
    if (!a) return '';
    const host = a.url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '');
    return `<div class="sns-card"><span class="sns-ic ${a.pf}">${SNS_ICON[a.pf]}</span><div class="sns-body">`
      + `<div class="sns-top"><b>${a.name}</b><span class="sns-tag">${a.tag}</span></div>`
      + `<span class="sns-handle">${a.pf === 'x' ? 'X' : 'Instagram'}・${a.handle}</span>`
      + `<p class="sns-desc">${a.desc}</p>`
      + `<a class="sns-url" href="${a.url}" target="_blank" rel="noopener"><small>${a.go}</small>${host}</a></div></div>`;
  }
  // フッターの中身（2026-10-27〜）。tools/site_footer.py の FOOT と1文字も違わないこと（あちらが assert で確かめる）。見た目は /assets/site-foot.css
  const FOOT_HTML = '<div class="ft"><a class="ft-brand" href="/"><img src="/assets/favicon.png" alt="" width="40" height="40"><span><b>まじゃすこ</b><small>麻雀のスコア記録を、スマホでかんたんに</small></span></a><div class="ft-sns"><a href="https://x.com/majasco_jp" target="_blank" rel="noopener" aria-label="まじゃすこ公式X（@majasco_jp）"><img src="https://is1-ssl.mzstatic.com/image/thumb/Purple221/v4/21/99/a9/2199a9db-0dc2-305f-7b8f-a5bc80258dbf/ProductionAppIcon-0-0-1x_U007emarketing-0-8-0-0-0-85-220.png/128x128bb.jpg" alt="X" width="40" height="40" loading="lazy"></a><a href="https://www.instagram.com/majasco_jp/" target="_blank" rel="noopener" aria-label="まじゃすこ公式Instagram（@majasco_jp）"><img src="https://is1-ssl.mzstatic.com/image/thumb/Purple211/v4/01/2d/b1/012db1a7-249a-86e8-f025-72491c2a6475/Prod-0-0-1x_U007epad-0-0-0-1-0-0-sRGB-85-220.png/128x128bb.jpg" alt="Instagram" width="40" height="40" loading="lazy"></a></div><nav class="ft-cols" aria-label="サイトのリンク"><div><b>使う</b><a href="/">トップ</a><a href="/score-basics.html">スコア計算の基本</a><a href="/faq.html">よくある質問</a></div><div><b>読む</b><a href="/blog.html">ブログ</a><a href="/news/">お知らせ</a><a href="/news/feed.xml">お知らせRSS</a></div><div><b>このサイトについて</b><a href="/about.html">運営者について</a><a href="/contact.html">お問い合わせ</a><a href="/terms.html">利用規約</a><a href="/privacy.html">プライバシーポリシー</a></div></nav><div class="ft-copy">© 2026 まじゃすこ</div></div>';
  // 公式SNS（記事の最後・右の列）: アイコンだけ（2026-10-27 ユーザーの依頼「説明文はいらない」）
  const SNS_ICONS_HTML = (size) => `<div class="sns-icons">`
    + `<a href="https://x.com/majasco_jp" target="_blank" rel="noopener" aria-label="まじゃすこ公式X（@majasco_jp）">${SNS_ICON.x.replace(/40/g, size)}</a>`
    + `<a href="https://www.instagram.com/majasco_jp/" target="_blank" rel="noopener" aria-label="まじゃすこ公式Instagram（@majasco_jp）">${SNS_ICON.ig.replace(/40/g, size)}</a></div>`;
  function renderChrome() {
    if (!document.querySelector('link[href="/assets/site-foot.css"]')) {
      const ln = document.createElement('link'); ln.rel = 'stylesheet'; ln.href = '/assets/site-foot.css'; document.head.appendChild(ln);
    }
    const st = document.createElement('style');
    st.textContent = `
      .site-head { background: #fff; border-bottom: 1px solid #eef3f2; position: sticky; top: 0; z-index: 50; }
      .site-head .site-head-inner { position: relative; max-width: 960px; margin: 0 auto; padding: 8px 56px; display: flex; align-items: center; justify-content: center; transition: padding .2s; }
      .site-head .brand img { height: 48px; vertical-align: middle; transition: height .2s; }
      .site-head.compact .site-head-inner { padding: 4px 56px; }
      .site-head.compact .brand img { height: 36px; }
      .site-head .head-app-link { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); font-size: 12px; font-weight: 700; color: #177083; background: #E4F3EC; border-radius: 20px; padding: 7px 14px; text-decoration: none; }
      .site-head .read-bar { position: absolute; left: 0; bottom: -1px; height: 3px; width: 0; background: #E75620; border-radius: 0 2px 2px 0; transition: width .1s linear; }
      .sns-icons { display: flex; gap: 12px; }
      .sns-icons a { display: block; border-radius: 12px; overflow: hidden; line-height: 0; box-shadow: 0 0 0 1px #E2E8E6; transition: transform .15s; }
      .sns-icons a:hover { transform: translateY(-2px); }
      .sns-follow.mini { display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap; }
      .sns-follow.mini .sns-follow-title { margin: 0; }
      .author-box { display: flex; gap: 14px; margin: 36px 0 0; padding: 18px; background: #f4faf7; border: 1px solid #e2ece7; border-radius: 12px; }
      .author-box .a-icon { width: 60px; height: 60px; flex-shrink: 0; border-radius: 50%; background: #E4F3EC; display: flex; align-items: center; justify-content: center; overflow: hidden; }
      .author-box .a-icon img { width: 100%; height: 100%; display: block; }
      .author-box .a-body { min-width: 0; }
      .author-box .a-name { font-weight: 800; font-size: 14px; color: #177083; margin-bottom: 6px; }
      .author-box p { font-size: 13px; color: #444; margin: 0 0 8px; line-height: 1.8; }
      .author-box a { font-size: 13px; color: #177083; font-weight: 700; }`;
    document.head.appendChild(st);
    const head = document.querySelector('.site-head');
    if (head) {
      // 左上は戻るボタン用に空けておく（padding 56px）。右上はマイページ。ロゴは真ん中
      head.innerHTML = `<div class="site-head-inner">
        <a href="/" class="brand"><img src="/assets/logo.png" alt="まじゃすこ / majasco"></a>
        <a class="head-app-link" href="/#mypage">マイページ</a>
      </div>`;
      // ヘッダーは上に残し、下へ読み進めたら少し細くする（2026-10-27）。記事では読んだところまでオレンジの線
      const art = document.querySelector('.blog-post');
      if (art) head.insertAdjacentHTML('beforeend', '<div class="read-bar" aria-hidden="true"></div>');
      const bar = head.querySelector('.read-bar');
      let ticking = false;
      const onScroll = () => {
        ticking = false;
        head.classList.toggle('compact', window.scrollY > 40);
        if (bar && art) {
          const r = art.getBoundingClientRect();
          const total = r.height - window.innerHeight * 0.6;
          const p = total > 0 ? Math.min(1, Math.max(0, -r.top / total)) : 0;
          bar.style.width = (p * 100).toFixed(1) + '%';
        }
      };
      window.addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(onScroll); } }, { passive: true });
      onScroll();
    }
    const foot = document.querySelector('.site-foot');
    if (foot) foot.innerHTML = FOOT_HTML;   // 静的HTMLのフッターも同じ中身（tools/site_footer.py）
  }

  document.addEventListener('DOMContentLoaded', () => {
    renderChrome();

    // 記事内の表: モバイルで列が潰れて読みにくくならないよう、横スクロールの入れ物に包む
    // （列が多い表は最低幅を確保して、画面外はスクロールで見る）
    document.querySelectorAll('.blog-post table').forEach(tb => {
      if (tb.parentElement.classList.contains('table-scroll')) return;
      const wrap = document.createElement('div');
      wrap.className = 'table-scroll';
      tb.parentNode.insertBefore(wrap, tb);
      wrap.appendChild(tb);
      if (tb.rows[0] && tb.rows[0].cells.length >= 4) tb.style.minWidth = '520px';
    });

    // 記事の中の <div class="sns-list" data-sns="mleague_x,majasco_x"></div> をアカウントのカードにする
    document.querySelectorAll('.blog-post [data-sns]').forEach(el => {
      if (el.children.length) return; // 静的に書いてあるカードはそのまま
      el.innerHTML = el.getAttribute('data-sns').split(',').map(k => snsCardHtml(k.trim())).join('');
    });

    // 記事の最後の「まじゃすこの公式SNS」（全記事共通。著者ブロックの前）
    const ctaBox = document.querySelector('.blog-post .cta-wrap');
    if (ctaBox && !document.querySelector('.sns-follow')) {
      const f = document.createElement('div');
      f.className = 'sns-follow mini';
      f.innerHTML = `<p class="sns-follow-title">まじゃすこの公式SNS</p>${SNS_ICONS_HTML(44)}`;
      ctaBox.parentNode.insertBefore(f, ctaBox);
    }

    // Xのポストの埋め込み: 公式の埋め込みコード（blockquote.twitter-tweet）があるページだけ、画面に近づいたら widgets.js を読む
    // （読めない環境では blockquote が引用の形のまま残る。読み込みはポストのあるページだけ＝ほかの記事には X のスクリプトを入れない）
    const tweets = document.querySelectorAll('.blog-post blockquote.twitter-tweet');
    if (tweets.length) {
      let loaded = false;
      const load = () => {
        if (loaded) return; loaded = true;
        const sc = document.createElement('script');
        sc.src = 'https://platform.twitter.com/widgets.js'; sc.async = true; sc.charset = 'utf-8';
        document.body.appendChild(sc);
      };
      if ('IntersectionObserver' in window) {
        const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); load(); } }, { rootMargin: '600px 0px' });
        tweets.forEach(t => io.observe(t));
      } else load();
    }

    // 記事末尾の著者ブロック（E-E-A-T対策: 全記事共通でCTAの直前に自動挿入）
    const cta = document.querySelector('.blog-post .cta-wrap');
    if (cta && !document.querySelector('.author-box')) {
      const box = document.createElement('div');
      box.className = 'author-box';
      box.innerHTML = `<div class="a-icon" aria-hidden="true"><img src="/assets/munii.svg" alt="" width="60" height="60"></div>
        <div class="a-body">
          <div class="a-name">この記事を書いた人：むにぃ</div>
          <p>麻雀スコア記録アプリ「まじゃすこ」の開発・運営者。仲間内のセット麻雀で長らく「集計係」を担当してきた経験から、点数を打つだけで集計が終わる無料アプリを個人開発しました。当ブログでは、初心者向けのルール解説とスコア計算の話を書いています。</p>
          <a href="/about.html">運営者について詳しく ›</a>
        </div>`;
      cta.parentNode.insertBefore(box, cta);
    }

    // 正式名称のページの暗記モード: 隠した読み方を押すと、その1つだけ見える
    document.addEventListener('click', e => {
      const y = e.target.closest('.yg-hide .ym');
      if (y) y.classList.toggle('show');
    });

    // 記事一覧（カテゴリ別・新しい順）
    document.querySelectorAll('[data-post-list]').forEach(el => {
      const cat = el.getAttribute('data-post-list');
      const posts = BLOG_POSTS.filter(p => cat === 'all' || p.cat === cat).sort(byDateDesc);
      el.innerHTML = posts.map(cardHtml).join('') || '<p class="bs-empty">このカテゴリの記事はまだありません。</p>';
    });

    // カテゴリナビ（すべて / 麻雀攻略 / お知らせ / 雑記）
    // 一覧ページはHTMLに書いてある（tools/build_post_lists.js）。空のときだけここで描く
    document.querySelectorAll('[data-cat-nav]').forEach(el => {
      if (el.children.length) return;
      el.innerHTML = catNavHtml(el.getAttribute('data-cat-nav'));
    });

    // サイドバー: 今月のおすすめ記事 ＋ 最新のアップデート（/news/の新着）
    document.querySelectorAll('[data-sidebar]').forEach(el => {
      const here = location.pathname;
      const rec = BLOG_POSTS.filter(p => p.recommended && p.url !== here).sort(byDateDesc).slice(0, 4);
      const news = BLOG_POSTS.filter(p => p.cat === 'news' && p.url !== here).sort(byDateDesc).slice(0, 3);
      let html = '';
      if (rec.length) {
        html += `<div class="side-box"><h2>今月のおすすめ記事</h2><ul>${rec.map(sideItem).join('')}</ul></div>`;
      }
      html += `<div class="side-box"><h2>最新のアップデート</h2>`
        + (news.length ? `<ul>${news.map(sideItem).join('')}</ul>` : '<p class="bs-empty">お知らせは準備中です。</p>')
        + `<a class="sb-more" href="/news/">お知らせ一覧 ›</a>　<a class="sb-more" href="/news/feed.xml">RSS</a></div>`;
      html += `<div class="side-box"><h2>公式SNS</h2>${SNS_ICONS_HTML(40)}</div>`;
      el.innerHTML = html;
    });

    // 左の列（PCの広い画面＝1,200px以上だけ見える。2026-10-26〜・記事を画面の真ん中に置くため）:
    // 記事ページ＝この記事の目次（読んでいる所に色）＋あわせて読みたい（絵つき3本）＋広告枠／一覧ページ＝人気の記事＋広告枠
    document.querySelectorAll('.post-layout').forEach(lay => {
      if (lay.querySelector('.side-l')) return;
      const art = lay.querySelector('.blog-post, .post-list');
      if (!art) return;
      const isList = art.classList.contains('post-list');
      const here = location.pathname;
      const cur = BLOG_POSTS.find(p => p.url === here);
      const thumbOf = p => '/assets/thumbs/' + p.url.split('/').pop().replace('.html', '') + '.svg';
      let html = '';
      let heads = [];
      if (!isList) {
        heads = [...art.querySelectorAll('h2')].filter(h => h.textContent.trim());
        heads.forEach((h, i) => { if (!h.id) h.id = 'sec' + (i + 1); });
        const label = h => { const c = h.cloneNode(true); c.querySelectorAll('rt').forEach(r => r.remove()); return escHtml(c.textContent.trim()); };
        if (heads.length >= 3) html += `<div class="side-box sl-toc"><h2>この記事の目次</h2><ol>${heads.map(h => `<li><a href="#${h.id}">${label(h)}</a></li>`).join('')}</ol></div>`;
      }
      let rel;
      if (isList) rel = BLOG_POSTS.filter(p => p.recommended).sort(byDateDesc).slice(0, 4);
      else {
        const pool = BLOG_POSTS.filter(p => p.url !== here && (!cur || p.cat === cur.cat));
        const same = cur ? pool.filter(p => p.tag && p.tag === cur.tag) : [];
        rel = same.concat(pool.filter(p => !same.includes(p)).sort(byDateDesc)).slice(0, 3);
      }
      if (rel.length) html += `<div class="side-box sl-rel"><h2>${isList ? '人気の記事' : 'あわせて読みたい'}</h2><ul>`
        + rel.map(p => `<li><a href="${p.url}"><img src="${thumbOf(p)}" alt="" width="320" height="240" loading="lazy" decoding="async"><span>${escHtml(p.title.split('｜')[0])}</span></a></li>`).join('') + '</ul></div>';
      html += '<div class="ad-slot" data-ad="side_left"></div>';
      const aside = document.createElement('aside');
      aside.className = 'side side-l';
      aside.setAttribute('aria-label', isList ? '人気の記事' : 'この記事の目次とあわせて読みたい記事');
      aside.innerHTML = `<div class="sl-in">${html}</div>`;
      lay.insertBefore(aside, lay.firstChild);
      // 読んでいる所の目次に色を付ける（画面の上から3割の位置を過ぎた見出し）
      const links = [...aside.querySelectorAll('.sl-toc a')];
      if (links.length && 'IntersectionObserver' in window) {
        const mark = () => {
          let on = 0;
          heads.forEach((h, i) => { if (h.getBoundingClientRect().top < window.innerHeight * 0.3) on = i; });
          links.forEach((a, i) => a.classList.toggle('on', i === on));
        };
        window.addEventListener('scroll', mark, { passive: true });
        mark();
      }
    });
  });
})();
