# ショート動画のネタ帳（記事から抽出・2026-11-06）

全53本の記事の見出しから抜き出した動画のネタ。**まじゃすこの広告にしない回**が中心で、最後に記事へつなぐ。
作り方は `tools/video_topics.py`（台本）と docs/video-plan.md。1本は20〜30秒。

## 型（どの動画も同じ）
- 冒頭＝サムネ: 札＋題名＋絵（文字だけにしない）。リールで並べたときにそろうよう、地の色・字・絵の位置は固定
- 本編: 上に見出し、真ん中に絵、y=1500に字幕（必ず中央。`make_short.build` が確かめて止める）
- 最後: 本物の記事の画面をスマホの中で流す

使う絵の略号: **牌**＝assets/tiles／**卓**＝assets/art（山・王牌・配牌・点棒）／**サ**＝assets/thumbs／**表**＝assets/score の点数表／**ス**＝本物のサイトの画面／**記事**＝記事の図を撮る
形の略号: **Q**＝クイズ（問い→答え）／**数**＝数字が動く／**比**＝2つを比べる／**順**＝手順／**一**＝一覧を1つずつ／**語**＝言葉の意味

## 作成済み（7本＋作り直し）
| 名前 | 題名 | 元の記事 |
|---|---|---|
| t-hai136 | 麻雀の牌、全部で何枚？ | blog-mahjong-suuji |
| t-half | ポイントは2回半分になる | blog-mleague-points |
| t-sanma | 三麻は、どの牌を抜く？ | blog-sanma-yonma |
| t-tsumo70 | 1局でツモれるのは何枚？ | blog-mahjong-suuji |
| t-zure | 1,000点足りない 犯人は？ | blog-score-mismatch |
| t-nichijou | テンパるって、もとは麻雀？ | blog-nichijougo |
| t-haitei | 最後の1枚で、カンできる？ | blog-haitei |

## 初心者向け
| # | 題名（フック） | 形 | 構成 | 絵 | 元の記事 |
|---|---|---|---|---|---|
| 1 | 半荘と東風戦、何が違う？ | 比 | 局の数→親→時間の目安 | 卓 | blog-rule-basics |
| 2 | 親と子、点数はどれだけ違う？ | 比 | 満貫 8,000と12,000→1.5倍 | 表 | blog-score-table |
| 3 | 局ってなに？ | 語 | 東1局→南4局を順に | 卓 | blog-rule-basics |
| 4 | 本場ってなに？ | 語 | 積み棒→300点 | 卓 | blog-rule-basics |
| 5 | 流局したらどうなる？ | 順 | テンパイ→ノーテン罰符 | 牌 | blog-rule-basics |
| 6 | オーラスとトビと西入 | 語 | 3つの終わり方 | 卓 | blog-rule-basics |
| 7 | 席と親はどう決める？ | 順 | サイコロ→起家 | 卓 | blog-rule-basics |
| 8 | 最初に覚える役10個 | 一 | 1本で10役を2秒ずつ | 牌 | blog-yaku-list |
| 9 | リーチの条件は3つ | 一 | 門前・テンパイ・1,000点 | 牌 | blog-yaku-list |
| 10 | タンヤオの作り方 | 一 | 2〜8だけの手を見せる | 牌 | blog-yaku-list |
| 11 | ピンフの条件 | 一 | 4つの条件を手牌で | 牌 | blog-yaku-list |
| 12 | 役牌ってどの牌？ | 一 | 白發中＋風 | 牌 | blog-yaku-list |
| 13 | 役を覚えたのにあがれない4つの原因 | 一 | フリテンなど | 牌 | blog-yaku-list |
| 14 | ドラは役じゃない？ | Q | ドラだけではあがれない | 牌 | blog-yaku-list |
| 15 | 鳴くと役が下がるのはどれ？ | Q | 喰い下がり | 牌 | blog-yaku-ichiran |
| 16 | 麻雀の持ち物リスト | 一 | 準備の一覧 | 卓 | blog-manner |
| 17 | 揉めやすいNG所作3つ | 一 | 所作を1つずつ | サ | blog-manner |
| 18 | チョンボってなに？ | 語 | 主な例→罰符の相場 | サ | blog-manner |
| 19 | 喰い替えって知ってる？ | Q | 切れない牌を手牌で | 牌 | blog-kuikae |
| 20 | 形式テンパイはテンパイ？ | Q | 役なしでも可 | 牌 | blog-keishiki-tenpai |
| 21 | 空テンはテンパイ？ | Q | 待ちが全部見えている | 牌 | blog-keishiki-tenpai |
| 22 | ノーテン罰符3,000点の分け方 | 数 | 1人テンパイ〜3人 | 牌 | blog-keishiki-tenpai |
| 23 | 待ちの基本5つ | 一 | リャンメンなど | 牌 | blog-machi-dojo |
| 24 | この手の待ちは？（シリーズ14本） | Q | 1問1本で答えを見せる | 牌 | blog-machi-dojo |
| 25 | 三面張を見抜くコツ | 一 | 形を2つ | 牌 | blog-machi-dojo |

## 役シリーズ（1役1本・38本）
blog-yaku-ichiran の全38役を1本ずつ。形は同じ: 「この手、何の役？」→牌の絵→翻数と鳴いたときの翻数。
1翻11本／2翻12本前後／3翻3本／6翻1本／役満の順に出すと、1か月以上毎日出せる。

**作成済み（2026-11-09）**: 手の絵がある29役を `y-01`〜`y-29` で自動生成（`tools/video_topics.py` の `_yaku_list` が記事から牌・翻数・説明を読む）。手の絵のない9役（一発・ツモ・海底など）は絵を足してから

## 用語シリーズ（1日1語・137語）
blog-mahjong-yougoshu の137語と Notion の用語辞典56語。形: 「◯◯って読める？」→読み方→意味→牌の絵。
読みが難しい語から出す。blog-mahjong-kanji の「混と清」「么九」「刻・順・対・槓」も各1本。

## 点数・スコア
| # | 題名 | 形 | 構成 | 絵 | 元の記事 |
|---|---|---|---|---|---|
| 26 | 親のツモは「オール」 | 語 | 2,000オールの意味 | 表 | blog-score-table |
| 27 | 満貫・跳満・倍満・三倍満・役満 | 一 | 翻と点数 | 表 | blog-score-table |
| 28 | 符計算はなぜ30符が多い？ | Q | 切り上げ | 表 | blog-score-table |
| 29 | 素点ってなに？ | 語 | 持ち点との差 | ス | blog-uma-oka |
| 30 | スコアは3つの足し算 | 数 | 素点＋ウマ＋オカ | ス | blog-uma-oka |
| 31 | 同点だったらどうする？ | 数 | ウマを分ける | ス | blog-score-examples |
| 32 | トビのスコアは？ | 数 | 実例 | ス | blog-score-examples |
| 33 | 三麻のスコアは？ | 数 | 実例 | ス | blog-score-examples |
| 34 | チョンボが入ったスコアは？ | 数 | 実例 | ス | blog-score-examples |
| 35 | スコアの合計はなぜ0？ | 数 | 足し算 | ス | blog-score-mismatch |
| 36 | 300点のズレは積み棒 | Q | ズレ幅 | 卓 | blog-score-mismatch |
| 37 | 満貫はなぜ8,000点？ | 数 | 2の乗 | 記事 | blog-mahjong-suuji |
| 38 | 場ゾロの＋2ってなに？ | 語 | 式の由来 | 記事 | blog-mahjong-suuji |
| 39 | 王牌はなぜ14枚？ | 数 | 4＋10 | 卓 | blog-mahjong-suuji |
| 40 | 手牌はなぜ13枚？ | 数 | 4面子1雀頭 | 牌 | blog-mahjong-suuji |

## ルールの分かれ目（コメントを呼ぶ回）
| # | 題名 | 形 | 元の記事 |
|---|---|---|---|
| 41 | ダブ東の雀頭は2符？4符？ | 比 | blog-rule-wakareme |
| 42 | ダブロンか頭ハネか | 比 | blog-rule-wakareme |
| 43 | 喰いタンありか、なしか | 比 | blog-rule-wakareme |
| 44 | 九種九牌は採用する？ | 比 | blog-rule-wakareme |
| 45 | 同点の順位はどうする？ | 比 | blog-rule-wakareme |
| 46 | 持ち点マイナスで続ける？ | 比 | blog-rule-wakareme |
| 47 | リーチ後の暗槓、していい？ | Q | blog-riichi-ankan |
| 48 | 待ちが変わる暗槓はなぜだめ？ | Q | blog-riichi-ankan |
| 49 | パオってなに？ | 語 | blog-pao |
| 50 | 大三元のパオ、誰がいくら？（計算問題6本） | Q | blog-pao |
| 51 | 四暗刻単騎はダブル役満？ | 比 | blog-yakuman-rules |
| 52 | 国士無双は暗槓でロンできる？ | Q | blog-yakuman-rules |
| 53 | 数え役満はあり？ | 比 | blog-yakuman-rules |
| 54 | 北抜きってなに？ | 語 | blog-sanma-rules |
| 55 | ツモ損ってなに？ | 語 | blog-sanma-rules |
| 56 | 花牌・白ポッチ・焼き鳥 | 一 | blog-sanma-rules |
| 57 | 打つ前に決める10項目 | 一 | blog-house-rules |
| 58 | 供託のリーチ棒、最後は誰のもの？ | 比 | blog-house-rules |
| 59 | ローカル役満: 八連荘（シリーズ） | 一 | blog-local-yaku |
| 60 | 大車輪・紅孔雀ってどんな手？ | 一 | blog-local-yaku |

## Mリーグ・プロ
チームのロゴと選手の写真は使わない（文字と自作の図だけ）。数字は記事の時点の情報で、シーズンが変わったら作り直す。
| # | 題名 | 形 | 元の記事 |
|---|---|---|---|
| 61 | Mリーグって何チーム？ | 数 | blog-mleague-2026 |
| 62 | Mリーグのシーズンの流れ | 順 | blog-mleague-2026 |
| 63 | Mリーグのルールは一発・裏ドラあり？ | Q | blog-mleague-2026 |
| 64 | 全10チーム紹介（1チーム1本・10本） | 一 | blog-mleague-2026 |
| 65 | 歴代の優勝チーム | 一 | blog-mleague-history |
| 66 | チーム別の優勝回数 | 数 | blog-mleague-history |
| 67 | 知っておくと面白い記録 | 一 | blog-mleague-history |
| 68 | 観戦で見るところ7つ | 一 | blog-mleague-kansen |
| 69 | 実況でよく聞く言葉（シリーズ） | 語 | blog-mleague-kansen |
| 70 | Mリーガーに会える場所 | 一 | blog-meet-mleaguer |
| 71 | プロ団体は5つある | 一 | blog-dantai-rekishi |
| 72 | 団体ができた順番 | 順 | blog-dantai-rekishi |
| 73 | 団体でルールはどう違う？ | 比 | blog-pro-dantai-rules |
| 74 | 鳳凰位・最高位・雀王・最強位ってなに？ | 語 | blog-mahjong-titles |
| 75 | タイトル戦の2つの型 | 比 | blog-mahjong-titles |
| 76 | 麻雀プロになるには | 順 | blog-mahjong-pro |
| 77 | プロテストの例題（シリーズ） | Q | blog-mahjong-yougo・blog-ronjutsu |

## 麻雀AI・ゲーム
NAGAの公式キャラクターと画面は記事の中だけで使う。動画に入れるなら先に利用の条件を確かめる。
| # | 題名 | 形 | 元の記事 |
|---|---|---|---|
| 78 | 麻雀AI、使えるのはどれ？ | 比 | blog-mahjong-ai |
| 79 | 無料で牌譜を見てもらう方法 | 順 | blog-ai-haifu |
| 80 | AIの答えの読み方は「割合」 | 語 | blog-ai-haifu |
| 81 | NAGAの使い方を3ステップで | 順 | blog-naga-guide |
| 82 | NAGAの7タイプ | 一 | blog-naga-guide |
| 83 | 麻雀ゲームアプリの選び方 | 比 | blog-mahjong-game-apps |

## 雑学・カルチャー
| # | 題名 | 形 | 元の記事 |
|---|---|---|---|
| 84 | 日常語になった麻雀用語（残り5語を1語1本） | 語 | blog-nichijougo |
| 85 | 台湾の麻雀は手牌が16枚 | 比 | blog-sekai-mahjong |
| 86 | アメリカの麻雀はジョーカーあり | 比 | blog-sekai-mahjong |
| 87 | 中国の公式ルールは役が81種類 | 数 | blog-sekai-mahjong |
| 88 | 四川は字牌なし、チーなし | 比 | blog-sekai-mahjong |
| 89 | 七対子の「チー」はなぜ七？ | 語 | blog-mahjong-kanji |
| 90 | 「混」と「清」で役がわかる | 語 | blog-mahjong-kanji |
| 91 | 海底摸月の意味 | 語 | blog-haitei |
| 92 | レベル別おすすめ本 | 一 | blog-mahjong-books |
| 93 | 麻雀漫画の最初の1冊 | 一 | blog-mahjong-manga |
| 94 | 麻雀アニメはどこで見られる？ | 一 | blog-mahjong-anime |
| 95 | 強くなるYouTube | 一 | blog-mahjong-youtube |

## 集まりの運営（まじゃすこにつながる回）
| # | 題名 | 形 | 元の記事 |
|---|---|---|---|
| 96 | 5人で打つときの回し方 | 順 | blog-mawashi-uchi |
| 97 | 試合数が違う人の比べ方 | 比 | blog-mawashi-uchi |
| 98 | 16人のチーム戦のやり方 | 順 | blog-team-league |
| 99 | 蛇行ドラフトでチーム分け | 順 | blog-team-tournament |
| 100 | 持ち越し方式で優勝者が変わる | 数 | blog-league-taikai |
| 101 | 決勝の条件戦とは | 語 | blog-league-taikai |
| 102 | 規定試合数を決める理由 | 語 | blog-season-ranking |
| 103 | 相性は「直接対決」で見る | 比 | blog-season-ranking |
| 104 | 集計係を8年やった失敗4つ | 一 | blog-shukei-gakari |
| 105 | 開発者が作らないと決めた機能 | 一 | blog-why-majasco |

## 本数の見積もり
単独のネタ105本＋シリーズの追加（待ち当て13・計算問題5・チーム9・日常語4）＋役38本＋用語137語。
**300本を超えるので、1日1本で10か月以上**。役と用語は台本を表から自動で作れるので、次はこの2つを量産の型にする。
