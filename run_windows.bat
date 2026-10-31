@echo off
setlocal EnableExtensions
cd /d "%~dp0"

echo ================================================
echo  Genshin Growth Database
echo  Open http://127.0.0.1:8765 in your browser.
echo  Press Ctrl+C to stop the server.
echo ================================================

if not exist "genshin_growth.db" goto missing_db

where python.exe >nul 2>&1
if errorlevel 1 goto check_py
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 goto run_python

:check_py
where py.exe >nul 2>&1
if errorlevel 1 goto missing_python
py -3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>&1
if not errorlevel 1 goto run_py

:missing_python
echo ERROR: No working Python 3.10 or newer was found.
echo Please check "python --version" and "py -0p" in Command Prompt.
echo If the Python launcher uses a deleted path, repair your Python installation.
pause
exit /b 1

:missing_db
echo ERROR: genshin_growth.db was not found.
echo Please extract the entire ZIP file before running this script.
pause
exit /b 1

:run_python
echo Starting with python.exe ...
python app.py
goto finished

:run_py
echo Starting with py -3 ...
py -3 app.py
goto finished

:finished
if errorlevel 1 echo ERROR: Server stopped with an error. Please copy the message above.
pause
endlocal
