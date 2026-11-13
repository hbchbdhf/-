@echo off
chcp 65001 >nul
cd /d "%~dp0"
setlocal enabledelayedexpansion

set "GIT=D:\LenovoSoftstore\Install\WorkBuddy\resources\vendor\PortableGit\cmd\git.exe"
if not exist "%GIT%" set "GIT=git"

echo ============================================================
echo   Upload project to GitHub:  https://github.com/hbchbdhf/-
echo   A browser window will open - just log in and click Authorize.
echo ============================================================
echo.

"%GIT%" remote set-url origin https://github.com/hbchbdhf/-.git

set OK=0
for /l %%i in (1,1,10) do (
  if !OK!==0 (
    echo -- attempt %%i --
    "%GIT%" -c http.sslBackend=openssl push -u origin main --force
    if !errorlevel!==0 ( set OK=1 ) else ( timeout /t 5 >nul )
  )
)

echo.
if "!OK!"=="1" (
  echo [OK] Pushed. GitHub Actions is building now:
  echo      https://github.com/hbchbdhf/-/actions
  start "" https://github.com/hbchbdhf/-/actions
) else (
  echo [FAILED] Please tell me the error above.
)
echo.
pause
