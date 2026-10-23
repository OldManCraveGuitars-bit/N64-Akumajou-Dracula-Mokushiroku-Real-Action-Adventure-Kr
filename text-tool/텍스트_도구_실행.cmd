@echo off
cd /d "%~dp0"
python -X utf8 tools\launch_editor.py
if errorlevel 1 pause
