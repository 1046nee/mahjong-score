# まじゃすこ自動pull: リポジトリ本体と入れ子clone（「まじゃすこ素材」等）を最新化する。
# リモートセッション（Claude Code on the Web等）からpushされた変更を手元PCへ自動反映するための仕組み。
# タスクスケジューラから定期実行される想定（登録は tools/install_auto_pull.ps1 を1回実行）。
#
# 安全設計（手元の作業を絶対に壊さない）:
# - fast-forwardできるときだけ進める（git merge --ff-only）。衝突・未pushのローカルコミットがあれば何もしない
# - 現在のブランチがmain以外のときは触らない
# - 問題があった場合だけログに残す: %LOCALAPPDATA%\majasco\auto-pull.log

param(
  # リポジトリルート（省略時はこのスクリプトの親フォルダ=リポジトリ直下）
  [string]$Root = (Split-Path -Parent $PSScriptRoot)
)

$ErrorActionPreference = "Continue"

# ログ準備（Linux等LOCALAPPDATAが無い環境でも動くように）
$appData = $env:LOCALAPPDATA
if (-not $appData) { $appData = Join-Path $HOME ".local/share" }
$logDir = Join-Path $appData "majasco"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$script:LogPath = Join-Path $logDir "auto-pull.log"

function Write-Log([string]$msg) {
  $line = ("{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg)
  Add-Content -Path $script:LogPath -Value $line -Encoding UTF8
}

function Update-Repo([string]$dir) {
  if (-not (Test-Path (Join-Path $dir ".git"))) { return }
  $name = Split-Path -Leaf $dir

  $branch = (git -C $dir rev-parse --abbrev-ref HEAD 2>$null)
  if ($branch -ne "main") {
    Write-Log "[$name] skip: 現在のブランチがmainではない ($branch)"
    return
  }

  git -C $dir fetch origin main 2>&1 | Out-Null
  if ($LASTEXITCODE -ne 0) {
    Write-Log "[$name] skip: fetch失敗（オフライン or 認証切れ）"
    return
  }

  $local = (git -C $dir rev-parse HEAD 2>$null)
  $remote = (git -C $dir rev-parse origin/main 2>$null)
  if ($local -eq $remote) { return } # 最新。ログは残さない（スパム防止）

  $out = (git -C $dir merge --ff-only origin/main 2>&1)
  if ($LASTEXITCODE -eq 0) {
    Write-Log "[$name] 更新: $($local.Substring(0,7)) -> $($remote.Substring(0,7))"
  } else {
    Write-Log "[$name] skip: fast-forward不可（未pushのコミット or 衝突あり）。手動で確認を: $out"
  }
}

# 本体 → 直下の入れ子clone（「まじゃすこ素材」など.gitを持つフォルダ全部）の順にpull
Update-Repo $Root
Get-ChildItem -Path $Root -Directory | ForEach-Object {
  Update-Repo $_.FullName
}

# ログの肥大化防止: 1000行を超えたら新しい500行だけ残す
if (Test-Path $script:LogPath) {
  $lines = @(Get-Content $script:LogPath -Encoding UTF8)
  if ($lines.Count -gt 1000) {
    $lines | Select-Object -Last 500 | Set-Content $script:LogPath -Encoding UTF8
  }
}
