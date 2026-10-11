@echo off
setlocal
title Strata NEXUS - sync upstream
cd /d "%~dp0"

rem ============================================================
rem  Strata NEXUS (D:\Strata 主目录) - sync upstream source
rem  结构：本目录 = 自主项目（启动/升级/文档）；engine\ = 官方上游运行环境
rem  本脚本：在 engine\ 内 fetch + merge 官方 main，然后走官方
rem  UPDATE 流程刷新引擎与依赖。模型文件（Strata-data）不动。
rem ============================================================

where git >nul 2>nul || (
  echo  Git for Windows is required: winget install Git.Git
  pause
  exit /b 1
)
if not exist "engine\.git" (
  echo  engine\ is not a git clone. Restore it first:
  echo    git clone https://github.com/Niko1221/Strata.git engine
  pause
  exit /b 1
)

echo.
echo  [1/3] Fetching official main ...
git -C engine fetch origin main
if errorlevel 1 (
  echo  fetch failed - check network / proxy, then run again.
  pause
  exit /b 1
)

echo.
echo  [2/3] Merging official main into engine ...
git -C engine merge origin/main --no-edit
if errorlevel 1 (
  echo.
  echo  ============================================================
  echo  Merge conflict inside engine\. Two ways out:
  echo    a) fix conflicts, then: git -C engine add -A ^&^& git -C engine merge --continue
  echo    b) give up this sync:   git -C engine merge --abort
  echo  ============================================================
  pause
  exit /b 1
)

echo.
echo  [3/3] Refreshing engine + Python packages (official UPDATE path) ...
pushd engine
call UPDATE.bat %*
popd
echo.
echo  Sync complete.
pause
