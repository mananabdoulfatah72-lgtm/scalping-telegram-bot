@echo off
if not exist "%~dp0installer.ps1" (
  echo ERREUR : installer.ps1 est introuvable a cote de installer.bat.
  echo Le dossier est sans doute encore dans le ZIP : clic droit sur le ZIP, puis Extraire tout, puis relance installer.bat depuis le dossier extrait.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1" %1
echo.
echo Lis les messages ci-dessus AVANT d appuyer sur une touche (une touche ferme la fenetre).
pause
