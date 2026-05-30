@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64

set PYBIND11_DIR=C:\Users\sahil\AppData\Local\Programs\Python\Python313\Lib\site-packages\pybind11\share\cmake\pybind11

cd /d "%~dp0"
if not exist build mkdir build
cd build

echo [1] Configuring with CMake...
cmake .. -Dpybind11_DIR="%PYBIND11_DIR%" -G "Visual Studio 18 2025" -A x64
if %ERRORLEVEL% NEQ 0 (
    echo CMAKE CONFIGURE FAILED
    pause
    exit /b 1
)

echo [2] Building (Release)...
cmake --build . --config Release
if %ERRORLEVEL% NEQ 0 (
    echo CMAKE BUILD FAILED
    pause
    exit /b 1
)

echo.
echo BUILD COMPLETE
echo The .pyd file should be in the cpp_engine's parent folder.
pause
