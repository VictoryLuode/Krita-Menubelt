@echo off
rem Deploy this repo's plugin files to the Krita resource directory.
rem Target: %KRITA_RES% when set, otherwise Krita's standard per-user resource dir.
rem For a custom resource folder, create deploy.local.bat next to this file
rem (git-ignored) containing:  set "KRITA_RES=<your resource dir>"
if exist "%~dp0deploy.local.bat" call "%~dp0deploy.local.bat"
if not defined KRITA_RES set "KRITA_RES=%APPDATA%\krita"
set "RES=%KRITA_RES%"
if not exist "%RES%" (
  echo [ERROR] Krita resource directory not found: "%RES%"
  echo         Set it first:  set KRITA_RES=^<path^>
  exit /b 1
)
copy /y pykrita\menubelt.desktop "%RES%\pykrita\" >nul
xcopy /s /y /e /i pykrita\menubelt "%RES%\pykrita\menubelt" >nul
copy /y actions\menubelt.action "%RES%\actions\" >nul
echo Deployed to "%RES%".
