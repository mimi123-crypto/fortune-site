@echo off
REM ============================================================
REM  publish.bat - タスクスケジューラ登録用ラッパー
REM  publish.ps1 を実行ポリシー回避つきで呼び出すだけ。
REM  タスクスケジューラの「操作」にこの .bat を指定すると簡単です。
REM ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish.ps1"
exit /b %ERRORLEVEL%
