@echo off
setlocal EnableExtensions

cd /d "%~dp0"
set "INTERACTIVE=0"
set "PYTHON_CMD="

call :find_python
if not defined PYTHON_CMD (
    echo [ERROR] Python was not found.
    echo Install Python 3.11+ or add it to PATH, then run this file again.
    exit /b 1
)

if /i "%~1"=="app" goto run_app
if /i "%~1"=="gui" goto run_app
if /i "%~1"=="check" goto run_checks
if /i "%~1"=="test" goto run_checks

set "INTERACTIVE=1"
echo PDF2Obsidian test launcher
echo.
echo 1. Run GUI for manual testing
echo 2. Run pytest and ruff
echo.
set /p "CHOICE=Select 1 or 2: "

if "%CHOICE%"=="1" goto run_app
if "%CHOICE%"=="2" goto run_checks

echo [ERROR] Invalid selection.
goto finish_error

:run_app
echo.
call :ensure_import PySide6
if errorlevel 1 goto dependency_error

echo [INFO] Running PDF2Obsidian GUI...
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
%PYTHON_CMD% -m pdf2obsidian.main
if errorlevel 1 goto dependency_error
goto finish_ok

:run_checks
echo.
call :ensure_import pytest
if errorlevel 1 goto dependency_error
call :ensure_import ruff
if errorlevel 1 goto dependency_error

echo [INFO] Running pytest...
set "PYTHONPATH=%CD%\src;%PYTHONPATH%"
%PYTHON_CMD% -m pytest
if errorlevel 1 goto dependency_error

echo.
echo [INFO] Running ruff check...
%PYTHON_CMD% -m ruff check .
if errorlevel 1 goto dependency_error

goto finish_ok

:dependency_error
echo.
echo [ERROR] Command failed.
echo If dependencies are missing, run:
echo %PYTHON_CMD% -m pip install -r "%CD%\requirements.txt"
goto finish_error

:finish_ok
echo.
echo [OK] Done.
if "%INTERACTIVE%"=="1" pause
exit /b 0

:finish_error
echo.
echo [FAILED]
if "%INTERACTIVE%"=="1" pause
exit /b 1

:find_python
if exist "%~dp0.venv\Scripts\python.exe" (
    "%~dp0.venv\Scripts\python.exe" -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD="%~dp0.venv\Scripts\python.exe""
        exit /b 0
    )
)

py -3 -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

python -c "import sys" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe""
        exit /b 0
    )
)

if exist "C:\Program Files\Python312\python.exe" (
    "C:\Program Files\Python312\python.exe" -c "import sys" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD="C:\Program Files\Python312\python.exe""
        exit /b 0
    )
)

exit /b 0

:ensure_import
%PYTHON_CMD% -c "import %~1" >nul 2>nul
if not errorlevel 1 exit /b 0

set "OLD_PYTHON_CMD=%PYTHON_CMD%"
set "PYTHON_CMD="

call :find_python_with_import %~1
if defined PYTHON_CMD exit /b 0

set "PYTHON_CMD=%OLD_PYTHON_CMD%"
exit /b 1

:find_python_with_import
py -3 -c "import %~1" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
    exit /b 0
)

python -c "import %~1" >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=python"
    exit /b 0
)

if exist "%LocalAppData%\Programs\Python\Python312\python.exe" (
    "%LocalAppData%\Programs\Python\Python312\python.exe" -c "import %~1" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD="%LocalAppData%\Programs\Python\Python312\python.exe""
        exit /b 0
    )
)

if exist "C:\Program Files\Python312\python.exe" (
    "C:\Program Files\Python312\python.exe" -c "import %~1" >nul 2>nul
    if not errorlevel 1 (
        set "PYTHON_CMD="C:\Program Files\Python312\python.exe""
        exit /b 0
    )
)

exit /b 1
