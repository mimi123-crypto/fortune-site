@echo off
REM ============================================================
REM  publish.bat - wrapper for Windows Task Scheduler
REM  Calls publish.ps1 with execution policy bypass.
REM  Register THIS .bat as the scheduler action (simplest).
REM ============================================================
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0publish.ps1"
exit /b %ERRORLEVEL%
