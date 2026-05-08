@echo off
REM Local wheel building script for Catzilla on Windows
REM Usage: scripts\build_wheels_local.bat

setlocal enabledelayedexpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"

echo Building Catzilla wheels locally on Windows...

call :detect_python
if errorlevel 1 exit /b 1

for /f "tokens=2 delims= " %%I in ('"%PYTHON_EXE%" --version 2^>^&1') do set "PYTHON_VERSION=%%I"
echo Using Python %PYTHON_VERSION%

echo.
echo Step 1: Preparing optional jemalloc support...
set "CATZILLA_USE_JEMALLOC="
if exist "%PROJECT_ROOT%\.catzilla-cache\jemalloc-windows\lib\jemalloc.lib" (
    echo Found staged Windows jemalloc library.
    set "CATZILLA_USE_JEMALLOC=1"
) else if exist "%PROJECT_ROOT%\deps\jemalloc\Makefile.in" (
    echo No staged jemalloc library found. Attempting to build it...
    pushd "%PROJECT_ROOT%\deps\jemalloc"
    call "%SCRIPT_DIR%build_jemalloc.bat"
    set "JEMALLOC_RESULT=!errorlevel!"
    popd
    if !JEMALLOC_RESULT! equ 0 (
        echo jemalloc build completed successfully.
        set "CATZILLA_USE_JEMALLOC=1"
    ) else (
        echo Warning: jemalloc build failed with exit code !JEMALLOC_RESULT!.
        echo Continuing with the standard allocator for this wheel build.
    )
) else (
    echo jemalloc sources are not available. Building wheel without staged jemalloc.
)

echo.
echo Step 2: Cleaning previous builds...
if exist "%PROJECT_ROOT%\build" rmdir /s /q "%PROJECT_ROOT%\build"
if exist "%PROJECT_ROOT%\dist" rmdir /s /q "%PROJECT_ROOT%\dist"
if exist "%PROJECT_ROOT%\wheelhouse" rmdir /s /q "%PROJECT_ROOT%\wheelhouse"
for /d %%D in ("%PROJECT_ROOT%\*.egg-info") do (
    if exist "%%~fD" rmdir /s /q "%%~fD"
)

mkdir "%PROJECT_ROOT%\dist" >nul 2>&1

echo.
echo Step 3: Installing build dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip "packaging>=24.2" setuptools wheel build
if errorlevel 1 (
    echo Error: failed to install wheel build dependencies.
    exit /b 1
)

echo.
echo Step 4: Building wheel and sdist...
"%PYTHON_EXE%" -m build --wheel --sdist
if errorlevel 1 (
    echo Error: wheel build failed.
    exit /b 1
)

echo Wheel artifacts:
dir "%PROJECT_ROOT%\dist"

echo.
echo Step 5: Locating built wheel...
set "WHEEL_FILE="
for %%F in ("%PROJECT_ROOT%\dist\*.whl") do (
    set "WHEEL_FILE=%%~fF"
    goto :wheel_found
)

echo Error: no wheel file was produced in dist\.
exit /b 1

:wheel_found
echo Using wheel: %WHEEL_FILE%

echo.
echo Step 6: Reinstalling the built wheel...
"%PYTHON_EXE%" -m pip install "%WHEEL_FILE%" --force-reinstall --no-deps
if errorlevel 1 (
    echo Error: wheel installation failed.
    exit /b 1
)

echo.
echo Step 7: Testing wheel import and basic app setup...
"%PYTHON_EXE%" -c "from catzilla import Catzilla, JSONResponse; print('Wheel import successful'); app = Catzilla(auto_validation=True, memory_profiling=False, show_banner=False, log_requests=False); app.get('/')(lambda request: JSONResponse({'status': 'ok', 'version': '0.1.0'})); print('Wheel functionality test passed'); print('Local wheel build and test completed successfully')"
if errorlevel 1 (
    echo Error: wheel smoke test failed.
    exit /b 1
)

echo.
echo Step 8: Showing installed package details...
"%PYTHON_EXE%" -m pip show catzilla
if errorlevel 1 (
    echo Warning: pip show catzilla failed.
)

echo.
echo Script: %~nx0
for %%F in ("%WHEEL_FILE%") do set "WHEEL_NAME=%%~nxF"
echo Built wheel file: %WHEEL_NAME%

"%PYTHON_EXE%" -c "import platform, sys; print('This wheel will install on:'); print(f'  Python: {sys.version_info.major}.{sys.version_info.minor}'); print(f'  Platform: {platform.system()}'); print(f'  Architecture: {platform.machine()}')"
if errorlevel 1 (
    echo Warning: wheel metadata summary failed.
)

echo.
echo Local Windows wheel build completed.
exit /b 0

:detect_python
set "PYTHON_EXE="
if exist "%PROJECT_ROOT%\venv\Scripts\python.exe" (
    set "PYTHON_EXE=%PROJECT_ROOT%\venv\Scripts\python.exe"
    goto :python_found
)

if defined VIRTUAL_ENV (
    if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
        set "PYTHON_EXE=%VIRTUAL_ENV%\Scripts\python.exe"
        goto :python_found
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%I in ('where python') do (
        set "PYTHON_EXE=%%I"
        goto :python_found
    )
)

where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "delims=" %%I in ('where python3') do (
        set "PYTHON_EXE=%%I"
        goto :python_found
    )
)

echo Error: Python was not found. Use the repo venv or install Python first.
exit /b 1

:python_found
echo Using Python executable: %PYTHON_EXE%
exit /b 0