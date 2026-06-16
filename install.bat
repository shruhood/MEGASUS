@echo off
echo ==================================================
echo   MEGASUS Installer (Windows)
echo ==================================================
echo.
where python >nul 2>nul
if %errorlevel% neq 0 (
    where python3 >nul 2>nul
    if %errorlevel% neq 0 (
        echo ERROR: Python not found.
        pause
        exit /b 1
    )
    set PYTHON=python3
) else (
    set PYTHON=python
)
echo Using: %PYTHON%
%PYTHON% --version
echo.
%PYTHON% install.py
if %errorlevel% neq 0 (
    echo Failed. Check errors above.
    pause
    exit /b 1
)
echo.
pause
