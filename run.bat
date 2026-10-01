@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv || goto :error
)

echo Installing dependencies...
".venv\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check -r requirements.txt || goto :error

echo.
echo SnapShelf is starting at http://localhost:8000
echo Press Ctrl+C to stop.
echo.
start "" http://localhost:8000
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
goto :eof

:error
echo.
echo Setup failed. Check that Python 3.10+ is installed and you are online.
pause
