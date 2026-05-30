@echo off
setlocal

set "ROOT=D:\OneDrive\Desktop\pinecode rsi\PYTHON AUTOMATE\NSE DATA automation\NEW_PROJECT"
set "PYBIND11_DIR=C:\Users\sahil\AppData\Local\Programs\Python\Python313\Lib\site-packages\pybind11\share\cmake\pybind11"

echo ================================================================
echo  Building C++ engines for NIFTY Straddle Strategies
echo ================================================================

:: ── DIRECTIONAL ENGINE ──────────────────────────────────────────
echo.
echo [1/2] Building DIRECTIONAL_STRADDLE engine...
if not exist "%ROOT%\DIRECTIONAL_STRADDLE\cpp_engine\build" (
    mkdir "%ROOT%\DIRECTIONAL_STRADDLE\cpp_engine\build"
)
:: Delete old CMakeCache so config changes take effect
if exist "%ROOT%\DIRECTIONAL_STRADDLE\cpp_engine\build\CMakeCache.txt" (
    del /f "%ROOT%\DIRECTIONAL_STRADDLE\cpp_engine\build\CMakeCache.txt"
)
cd /d "%ROOT%\DIRECTIONAL_STRADDLE\cpp_engine\build"
cmake .. -Dpybind11_DIR="%PYBIND11_DIR%"
if errorlevel 1 ( echo CMake configure FAILED for DIRECTIONAL & goto :err )
cmake --build . --config Release
if errorlevel 1 ( echo CMake build FAILED for DIRECTIONAL & goto :err )
echo DIRECTIONAL engine built successfully!

:: ── NEUTRAL ENGINE ───────────────────────────────────────────────
echo.
echo [2/2] Building NEUTRAL_STRADDLE engine...
if not exist "%ROOT%\NEUTRAL_STRADDLE\cpp_engine\build" (
    mkdir "%ROOT%\NEUTRAL_STRADDLE\cpp_engine\build"
)
:: Delete old CMakeCache so config changes take effect
if exist "%ROOT%\NEUTRAL_STRADDLE\cpp_engine\build\CMakeCache.txt" (
    del /f "%ROOT%\NEUTRAL_STRADDLE\cpp_engine\build\CMakeCache.txt"
)
cd /d "%ROOT%\NEUTRAL_STRADDLE\cpp_engine\build"
cmake .. -Dpybind11_DIR="%PYBIND11_DIR%"
if errorlevel 1 ( echo CMake configure FAILED for NEUTRAL & goto :err )
cmake --build . --config Release
if errorlevel 1 ( echo CMake build FAILED for NEUTRAL & goto :err )
echo NEUTRAL engine built successfully!

echo.
echo ================================================================
echo  Both engines built! .pyd files are in their strategy folders.
echo ================================================================
goto :done

:err
echo.
echo !! Build failed. Check the output above for details. !!
exit /b 1

:done
endlocal
