# 自動pull（tools/auto_pull.ps1）をWindowsタスクスケジューラに登録する。1回実行すればOK。
#   登録:   powershell -ExecutionPolicy Bypass -File tools\install_auto_pull.ps1
#   解除:   powershell -ExecutionPolicy Bypass -File tools\install_auto_pull.ps1 -Uninstall
# スケジュール: ログオン時＋30分ごと。管理者権限は不要（現在のユーザーのタスクとして登録）

param([switch]$Uninstall)

$taskName = "majasco-auto-pull"

if ($Uninstall) {
  Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
  Write-Host "タスク '$taskName' を解除しました"
  exit 0
}

$pullScript = Join-Path $PSScriptRoot "auto_pull.ps1"
if (-not (Test-Path $pullScript)) { Write-Error "auto_pull.ps1 が見つかりません: $pullScript"; exit 1 }

$action = New-ScheduledTaskAction -Execute "powershell.exe" `
  -Argument ("-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"{0}`"" -f $pullScript)

# ログオン時＋30分間隔の2本立て（間隔はここを変えて再実行すれば上書き登録される）
$trigLogon = New-ScheduledTaskTrigger -AtLogOn
$trigRepeat = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) `
  -RepetitionInterval (New-TimeSpan -Minutes 30) -RepetitionDuration ([TimeSpan]::MaxValue)

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName $taskName -Action $action `
  -Trigger $trigLogon, $trigRepeat -Settings $settings -Force | Out-Null

Write-Host "タスク '$taskName' を登録しました（ログオン時＋30分ごと）"
Write-Host "ログ: $env:LOCALAPPDATA\majasco\auto-pull.log（更新・スキップがあったときだけ記録）"

# 動作確認のため1回すぐ実行する
Start-ScheduledTask -TaskName $taskName
Write-Host "初回実行を開始しました。数十秒後にログを確認してください"
