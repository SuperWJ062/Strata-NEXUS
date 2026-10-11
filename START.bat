@echo off
title Strata NEXUS
cd /d "%~dp0"
if not exist "engine\\run-iq2_xs.bat" (
  echo  engine\run-iq2_xs.bat Not found. Run engine\START-HERE.bat first.
  pause
  exit /b 1
)
call engine\run-iq2_xs.bat
