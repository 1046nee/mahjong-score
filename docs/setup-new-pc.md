# 別PCセットアップ手順（どのPCでも同じ品質で動かすための構成）

> 設計思想: **正の情報はすべてクラウドにある**。コード・ルール・仕様＝GitHub（このリポジトリ）、
> 運用・タスク・投稿文＝Notion運用ハブ、画像素材＝privateリポジトリ majasco-assets。
> PCには「道具」を入れてcloneするだけで、どの端末でも同じ状態になる。

## 1. 道具のインストール（最初の1回だけ）
- **Git**（git-scm.com）
- **Node.js**（LTS）— プレビュー用 http-server に使用
- **Python 3** ＋ Pillow（`pip install pillow`）— 画像生成に使用
- **Claude Code**（デスクトップアプリ / CLI / VS Code拡張のいずれか）→ **同じAnthropicアカウントでログイン**（プランはアカウントに紐づく）

## 2. リポジトリの取得
任意の場所で:
```
git clone https://github.com/1046nee/mahjong-score.git mahjong
cd mahjong
git clone https://github.com/1046nee/majasco-assets.git "まじゃすこ素材"
```
- GitHubのログインを求められたらブラウザ認証（majasco-assetsはprivateのため必須）
- `まじゃすこ素材/` は本体の.gitignore対象なので、この入れ子構成で正しい

## 3. Claude Codeで開く
- **mahjongフォルダをプロジェクトルートとして開く**（CLAUDE.mdが自動で読み込まれ、ルール・ルーティングが効く）
- Notion連携（notion-*ツール）はClaudeアカウントに紐づく。使えない場合はコネクタ設定からNotionを再認証
- プレビューは `.claude/launch.json` の "mahjong" 設定（http-server・port 8081）を使う

## 4. 初回の動作確認（Claudeに順に頼む）
1. 「git pull して、CLAUDE.md と docs の構成を確認して」
2. 「プレビューを起動してトップページを表示して」
3. 「python tools/make_ig1.py を実行して画像が生成できるか確認して」

## 5. 自動pull（リモートセッションの成果物を手元に自動反映・推奨）
Claude Code on the Webなどリモート環境からpushされた変更（画像素材・コード）を、手元PCが自動で取り込む仕組み。
mahjongフォルダでPowerShellを開いて1回だけ実行:
```
powershell -ExecutionPolicy Bypass -File tools\install_auto_pull.ps1
```
- タスクスケジューラに「majasco-auto-pull」を登録（ログオン時＋30分ごと。管理者権限不要）
- 本体と「まじゃすこ素材」など入れ子cloneをまとめて **fast-forwardのみ** でpull。
  mainブランチ以外・未pushのローカルコミット・衝突があるときは**何もせずスキップ**するので手元の作業は壊れない
- ログ: `%LOCALAPPDATA%\majasco\auto-pull.log`（更新・スキップがあったときだけ記録）
- 解除: 同じコマンドに `-Uninstall` を付けて実行
- **注意: 「作業前に必ずpull」の絶対ルールはこれがあっても維持する**（自動pullは30分間隔なので直前の変更は拾えていないことがある）

## 6. 運用ルール（2台で安全に使うために）
- **同期はCLAUDE.mdの絶対ルールで担保**: 作業前に必ずpull・変更ごとにpush。これを守る限り、どちらのPCで作業しても常に最新が正になる
- **同時に2台で作業しない**（交互に使う。万一衝突したらpull時にClaudeが検知して報告する）
- 素材を生成・変更したら `まじゃすこ素材/` の中でも add→commit→push（Claudeが実施）
- 会話履歴とClaudeのローカルメモリは**端末ごとに別**。引き継ぐべき知識は docs/ とNotionに書くのが前提
  （だから「トラブルは落とし穴へ追記」ルールが重要）

## 7. 環境差の注意
- 画像生成ツールはWindowsフォント前提（`C:\Windows\Fonts\NotoSansJP-VF.ttf` / `seguiemj.ttf`。Windows 11なら標準搭載）。
  **Macで使う場合は tools/ 内のFONT/EMOJIパスの変更が必要**
- gitのコミッター名を整えたい場合（任意）: `git config --global user.name "名前"` / `git config --global user.email "メール"`
- この開発用PC（社内ネットワーク）では majasco.jp 自体がZscalerでブロックされる（docs/site-spec.md 落とし穴参照）。
  自宅PCなど別環境なら本番サイトの確認も可能

## 落とし穴
- タスクスケジューラの繰り返し期間に `[TimeSpan]::MaxValue` は使えない（XML値 P99999999DT... が「範囲外」で登録失敗）
  → `New-TimeSpan -Days 3650` など有効な有限値を指定する（install_auto_pull.ps1で対応済み）
