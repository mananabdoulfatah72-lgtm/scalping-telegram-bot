@echo off
rem Installe Jarvis (double-clic). Le détail est dans installer.ps1.
chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer.ps1"
