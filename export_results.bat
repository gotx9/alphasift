@echo off
cd /d %~dp0
call .venv\Scripts\python.exe export_results.py
pause
