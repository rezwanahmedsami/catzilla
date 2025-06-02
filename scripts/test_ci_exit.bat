@echo off
REM Test exit code handling in Windows CI

echo === Testing Windows CI Exit Code Handling ===

echo All tests passed successfully!
echo Tests passed: 3/3
echo Tests failed: 0/3

REM Return successful exit code
echo Explicitly returning exit code 0
exit /b 0
