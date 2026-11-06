# まじゃすこの投稿用の素材（声入りのショート動画・SNS画像・Instagram画像）を、Google ドライブ パソコン版のフォルダへコピーする（2026-11-06〜）
# 使い方: tools\copy_to_drive.bat をダブルクリック（またはコマンドで  tools\copy_to_drive.bat "G:\マイドライブ"）
# 先に「まじゃすこ素材」を git pull して最新にしてからコピーする。コピー先は「<ドライブ>\まじゃすこ 投稿素材」だけ（ほかのフォルダには触らない）
param([string]$Drive)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root 'まじゃすこ素材'
if (-not (Test-Path $src)) { Write-Host "まじゃすこ素材 が見つかりません: $src"; exit 1 }

if (-not $Drive) {
  # Google ドライブ パソコン版のマイドライブを探す（ふつうは G: ドライブ）
  foreach ($d in (Get-PSDrive -PSProvider FileSystem)) {
    foreach ($n in @('マイドライブ', 'My Drive')) {
      $p = Join-Path $d.Root $n
      if (Test-Path $p) { $Drive = $p; break }
    }
    if ($Drive) { break }
  }
}
if (-not $Drive -or -not (Test-Path $Drive)) { Write-Host 'Google ドライブのフォルダが見つかりません。Google ドライブ パソコン版を入れてログインしてから、もう一度実行してください。'; exit 1 }

Write-Host '素材を最新にしています（git pull）…'
git -C $src pull --ff-only

$base = Join-Path $Drive 'まじゃすこ 投稿素材'
$jobs = @(
  @{ From = 'video'; To = 'ショート動画';   Files = @('voice-*-zundamon.mp4', 'voice-*-zundamon-thumb.jpg') },
  @{ From = 'v3';    To = 'SNS画像';        Files = @('*.png') },
  @{ From = 'ig';    To = 'Instagram画像';  Files = @('*.png') }
)
foreach ($j in $jobs) {
  $from = Join-Path $src $j.From
  $to = Join-Path $base $j.To
  # /MIR＝コピー先をコピー元と同じにする（消えた素材はドライブからも消える）。/LEV:1＝下のフォルダ（録画のコマなど）は入れない
  robocopy $from $to $j.Files /MIR /LEV:1 /NJH /NJS /NDL /NP | Out-Null
  $n = (Get-ChildItem $to -File | Measure-Object).Count
  Write-Host ("{0} … {1} 個" -f $j.To, $n)
}
Write-Host "できました: $base"
Write-Host 'Google ドライブが自動でアップロードします（画面右下のドライブのアイコンで進み具合が見られます）'
