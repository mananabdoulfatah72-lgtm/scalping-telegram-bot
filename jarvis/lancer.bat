@echo off
rem Lance Jarvis. Options : --texte (clavier dans le terminal), --demo, --verifier.
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
"%LOCALAPPDATA%\Jarvis\venv\Scripts\python.exe" -m jarvis %*
if errorlevel 1 pause
