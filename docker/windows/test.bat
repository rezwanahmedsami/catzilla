@echo off
echo 🪟 Testing Catzilla on Windows Server 2022
echo ==========================================
echo.

REM Display environment information
echo 📍 Environment Information:
echo   OS: Windows Server 2022
for /f "tokens=2 delims= " %%i in ('python --version 2^>^&1') do echo   Python: %%i
for /f "tokens=3 delims= " %%i in ('cmake --version 2^>^&1 ^| findstr "cmake version"') do echo   CMake: %%i
if exist "C:\vcpkg\installed\x64-windows\bin\jemalloc.dll" echo   jemalloc: vcpkg installation found
echo.

REM Verify jemalloc configuration
echo 🔍 Verifying jemalloc configuration...
if exist "%CATZILLA_JEMALLOC_PATH%" (
    echo ✅ jemalloc found at: %CATZILLA_JEMALLOC_PATH%
) else (
    echo ⚠️  Running jemalloc helper script...
    call scripts\jemalloc_helper.bat
)

REM Run jemalloc detection
echo 📋 Running jemalloc detection...
python scripts\jemalloc_helper.py --detect
echo.

REM Verify build (should already be built in Docker image)
echo 🔨 Verifying Catzilla build...
if exist "build\_catzilla.pyd" (
    echo ✅ Catzilla already built
) else (
    echo Building Catzilla...
    call scripts\build.bat
)
echo.

REM Run comprehensive tests
echo 🧪 Running comprehensive test suite...
echo ----------------------------------------

REM Run C tests first
echo 🔧 Running C tests...
call scripts\run_tests.bat --c
if %errorlevel% neq 0 (
    echo ❌ C tests failed
    exit /b %errorlevel%
)

REM Run Python tests
echo 🐍 Running Python tests...
call scripts\run_tests.bat --python
if %errorlevel% neq 0 (
    echo ❌ Python tests failed
    exit /b %errorlevel%
)

REM Run cross-platform jemalloc verification
echo 🌍 Running cross-platform jemalloc tests...
if exist "test_cross_platform_jemalloc.py" (
    python test_cross_platform_jemalloc.py
    if %errorlevel% neq 0 (
        echo ❌ Cross-platform jemalloc tests failed
        exit /b %errorlevel%
    )
) else (
    echo ℹ️  Cross-platform jemalloc test not found, skipping...
)

REM Run Windows-specific segfault verification
echo 🛡️  Running Windows segfault prevention verification...
if exist "scripts\verify_segfault_fix_windows.bat" (
    call scripts\verify_segfault_fix_windows.bat
) else if exist "scripts\verify_segfault_fix.py" (
    python scripts\verify_segfault_fix.py
) else (
    echo ℹ️  Segfault verification script not found, skipping...
)
if %errorlevel% neq 0 (
    echo ❌ Segfault verification failed
    exit /b %errorlevel%
)

REM Run memory stress test
echo 🧠 Running memory stress test...
python -c "import gc; import catzilla; print('Testing memory management...'); [None for i in range(100) for app in [catzilla.Catzilla()] if app.add_route('GET', f'/test_{i}', lambda req: {'status': 'ok'}) or gc.collect() if i %% 25 == 0 else None]; print('✅ Memory stress test completed')"
if %errorlevel% neq 0 (
    echo ❌ Memory stress test failed
    exit /b %errorlevel%
)

REM Performance smoke test
echo ⚡ Running performance smoke test...
python -c "import time; import catzilla; app = catzilla.Catzilla(); app.add_route('GET', '/', lambda req: {'message': 'Hello World'}); start = time.time(); [app._router.find_route('GET', '/') for _ in range(10000)]; end = time.time(); print(f'Route matching: {10000/(end-start):.0f} ops/sec'); print('✅ Performance smoke test completed')"
if %errorlevel% neq 0 (
    echo ❌ Performance smoke test failed
    exit /b %errorlevel%
)

echo.
echo ✅ Windows tests completed successfully!
echo 🎉 All systems operational on Windows Server 2022
echo.
echo 📊 Test Summary:
echo   - C tests: ✅
echo   - Python tests: ✅
echo   - Memory tests: ✅
echo   - Performance tests: ✅
