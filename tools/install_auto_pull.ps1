# 自動pull（tools/auto_pull.ps1）を登録する。1回実行すればOK。
#   登録:   powershell -ExecutionPolicy Bypass -File tools\install_auto_pull.ps1
#   解除:   powershell -ExecutionPolicy Bypass -File tools\install_auto_pull.ps1 -Uninstall
#
# 登録方式は2段構え（どちらも管理者権限不要）:
#   方式1: タスクスケジューラ（ログオン時＋30分ごと）
#   方式2: 会社PCなどで方式1が「アクセス拒否」される場合、スタートアップフォルダの
#          常駐スクリプト（ログオン時に起動し30分ごとにpull）へ自動フォールバック

param([switch]$Uninstall)

# 登録に失敗したら成功メッセージを出さずに止める
$ErrorActionPreference = "Stop"

$taskName = "majasco-auto-pull"
$pullScript = Join-Path $PSScriptRoot "auto_pull.ps1"
$startupDir = [Environment]::GetFolderPath("Startup")
$vbsPath = Join-Path $startupDir "majasco-auto-pull.vbs"

# 常駐モードで動いているauto_pullプロセスを止める（ベストエフォート）
function Stop-LoopProcess {
  Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "auto_pull\.ps1" -and $_.CommandLine -match "-Loop" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

if ($Uninstall) {
  Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
  if (Test-Path $vbsPath) { Remove-Item $vbsPath -Force }
  Stop-LoopProcess
  Write-Host "自動pullを解除しました（タスク・スタートアップ登録・常駐プロセスすべて）"
  exit 0
}

if (-not (Test-Path $pullScript)) { Write-Error "auto_pull.ps1 が見つかりません: $pullScript"; exit 1 }

# ---- 方式1: タスクスケジューラ ----
$registered = $false
try {
  $action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument ("-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"{0}`"" -f $pullScript)
  # 注意: 繰り返し期間に [TimeSpan]::MaxValue は使えない（XML値が範囲外で拒否される）→ 有限値（10年）
  $trigLogon = New-ScheduledTaskTrigger -AtLogOn
  $trigRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration (New-TimeSpan -Days 3650)
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable
  Register-ScheduledTask -TaskName $taskName -Action $action `
    -Trigger $trigLogon, $trigRepeat -Settings $settings -Force | Out-Null
  $registered = $true
} catch {
  Write-Host "タスクスケジューラへの登録ができませんでした: $($_.Exception.Message.Trim())"
  Write-Host "→ 代替方式（スタートアップフォルダの常駐スクリプト）で登録します"
}

if ($registered) {
  Start-ScheduledTask -TaskName $taskName
  Write-Host "タスク '$taskName' を登録し、初回実行を開始しました（ログオン時＋30分ごと）"
} else {
  # ---- 方式2: スタートアップフォルダ ----
  # ログオン時にVBSが隠しウィンドウで auto_pull.ps1 -Loop（常駐・30分間隔）を起動する。
  # 多重起動はauto_pull.ps1側のミューテックスで防止される
  $cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File "{0}" -Loop' -f $pullScript
  $vbs = 'CreateObject("WScript.Shell").Run "' + $cmd.Replace('"', '""') + '", 0, False'
  # 日本語パス対応のためUTF-16（BOM付き）で書く。WSHはUnicodeのVBSを読める
  Set-Content -Path $vbsPath -Value $vbs -Encoding Unicode
  Start-Process -FilePath "wscript.exe" -ArgumentList ('"{0}"' -f $vbsPath)
  Write-Host "スタートアップに登録し、常駐を開始しました: $vbsPath"
  Write-Host "（ログオン中のみ動作。ログオン時に自動起動し、30分ごとにpullします）"
}

Write-Host "ログ: $env:LOCALAPPDATA\majasco\auto-pull.log（更新・スキップがあったときだけ記録）"
