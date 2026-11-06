@echo off
rem まじゃすこの投稿用の素材を Google ドライブへコピーする（中身は copy_to_drive.ps1）。実行の制限に止められないよう -ExecutionPolicy Bypass で呼ぶ
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0copy_to_drive.ps1" %*
pause
