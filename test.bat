@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" python -m venv .venv
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt
".venv\Scripts\python.exe" -m pytest -v
pause
