@echo off
call "C:\Program Files (x86)\Microsoft Visual Studio\18\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x64
cd /d "%~dp0"
if not exist build mkdir build
cd build
echo [1] Configuring...
cmake .. -Dpybind11_DIR="C:\Users\sahil\AppData\Local\Programs\Python\Python313\Lib\site-packages\pybind11\share\cmake\pybind11" -A x64
echo [2] Building...
cmake --build . --config Release
echo DONE
pause
