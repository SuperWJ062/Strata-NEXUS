@echo off
setlocal enabledelayedexpansion
title Strata Local - build portable package
cd /d "%~dp0"

rem ============================================================
rem  Strata Local: build the no-install portable package
rem   Strata-Portable-<ver>.zip
rem    - bundled embeddable Python + all pinned dependencies
rem    - prebuilt engine (engine\)
rem    - repo sources + portable start scripts
rem  Recipient: unzip, drop model files into Strata-data\, run
rem  START-PORTABLE.bat. No Python install, no compiler, no
rem  system changes.
rem ============================================================

where python >nul 2>nul
if errorlevel 1 (
  echo  A local Python is needed to BUILD the package ^(the recipient
  echo  does not need one^). Install Python 3.12 or use START-HERE.bat.
  pause
  exit /b 1
)

for /f "usebackq tokens=2 delims=: " %%v in (`findstr /b "version" "%~dp0engine\engine\BUILD.json"`) do set "ENGVER=%%~v"
set "ENGVER=%ENGVER: =%"
set "PKGVER=%ENGVER:-=%"
set "OUT=Strata-Portable-%PKGVER%"
set "STAGE=portable\%OUT%"
set "ZIP=%OUT%.zip"

echo  == [1/6] staging %STAGE% ...
if exist "%STAGE%" rmdir /s /q "%STAGE%"
mkdir "%STAGE%" 2>nul
robocopy "%~dp0engine\serve" "%STAGE%\serve" /e /xd __pycache__ >nul
robocopy "%~dp0engine\engine" "%STAGE%\engine" /e >nul
robocopy "%~dp0engine\data" "%STAGE%\data" /e >nul
robocopy "%~dp0docs" "%STAGE%\docs" /e >nul
robocopy "%~dp0engine\tools" "%STAGE%\tools" /e /xd __pycache__ >nul
for %%f in (setup.py chat.py LICENSE) do copy /y "%~dp0engine\%%f" "%STAGE%\" >nul
if exist "%~dp0engine\cmake" robocopy "%~dp0engine\cmake" "%STAGE%\cmake" /e >nul
if exist "%~dp0engine\CMakeLists.txt" copy /y "%~dp0engine\CMakeLists.txt" "%STAGE%\" >nul
if errorlevel 1 echo  (note: some optional files may be missing)

echo  == [2/6] fetching embeddable Python 3.12.10 ...
if not exist "portable\python-embed.zip" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip -OutFile 'portable\python-embed.zip'" || goto :fail
)
if not exist "portable\get-pip.py" (
  powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol='Tls12'; Invoke-WebRequest -UseBasicParsing https://bootstrap.pypa.io/get-pip.py -OutFile 'portable\get-pip.py'" || goto :fail
)
mkdir "%STAGE%\python" 2>nul
powershell -NoProfile -ExecutionPolicy Bypass -Command "Expand-Archive -Force portable\python-embed.zip '%STAGE%\python'" || goto :fail

echo  == [3/6] enabling site-packages in embedded Python ...
>> "%STAGE%\python\python312._pth" echo Lib\site-packages
>> "%STAGE%\python\python312._pth" echo import site

echo  == [4/6] installing pinned dependencies into bundled Python (~700 MB) ...
"%STAGE%\python\python.exe" portable\get-pip.py --no-warn-script-location || goto :fail
"%STAGE%\python\python.exe" -m pip install --no-warn-script-location --disable-pip-version-check ^
  "numpy==2.5.3; python_version >= '3.12'" "jinja2==3.1.6" "regex==2026.9.10" "pyyaml==6.0.3" ^
  "tqdm==4.70.1" "requests==2.34.2" "cmake==4.4.3" "ninja==1.13.2" "pillow==12.3.0" "psutil==7.2.2" ^
  "markupsafe==3.0.3" "certifi==2026.7.22" "charset-normalizer==3.5.1" "idna==3.20" "urllib3==2.8.0" ^
  "colorama==0.4.6; sys_platform == 'win32'" || goto :fail

echo  == [5/6] writing portable start scripts ...
> "%STAGE%\START-PORTABLE.bat" (
  @echo @echo off
  @echo title Strata Portable
  @echo cd /d "%%~dp0"
  @echo if not exist "Strata-data\models\IQ2_XS\Qwen3.8-Flash-Next-GSQ-RCO-IQ2_XS-00001-of-00002.gguf" ^(
  @echo   echo  Model files missing. Read GET-MODEL.md, put the two IQ2_XS shards into
  @echo   echo  Strata-data\models\IQ2_XS\ , then run this again.
  @echo   pause
  @echo   exit /b 1
  @echo ^)
  @echo if not exist ".venv-ok" (
  @echo   echo  First run: preparing model pack + config ^(local CPU work, a few minutes^) ...
  @echo   "python\python.exe" setup.py --yes --family qwen --model IQ2_XS --context 131072 --vision yes --data-dir "%%~dp0Strata-data"
  @echo   if errorlevel 1 ^( pause ^& exit /b 1 ^)
  @echo   echo ok> .venv-ok
  @echo ^)
  @echo "python\python.exe" serve\server.py --engine strata --config strata-iq2_xs.json --port 8080 --open
  @echo if errorlevel 1 pause
)
copy /y "%~dp0docs\README-PORTABLE.md" "%STAGE%\" >nul 2>nul
copy /y "%~dp0docs\GET-MODEL.md" "%STAGE%\" >nul 2>nul

echo  == [6/6] compressing %ZIP% ...
if exist "%ZIP%" del /q "%ZIP%"
powershell -NoProfile -ExecutionPolicy Bypass -Command "Compress-Archive -Force -Path '%STAGE:\=\\%\*' -DestinationPath '%ZIP%'" || goto :fail

echo.
echo  Done: %ZIP%  ^(stage kept in %STAGE%^)
pause
exit /b 0

:fail
echo.
echo  BUILD FAILED - see messages above. Network steps can be retried: just run again.
pause
exit /b 1
