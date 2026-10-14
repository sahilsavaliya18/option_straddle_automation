@echo off
echo ========================================
echo   NIFTY Strategy Lab — Starting...
echo ========================================
echo.

:: Start the FastAPI backend
echo [1/2] Starting backend server on port 8000...
start "StrategyLab-Backend" cmd /k "cd /d %~dp0 && cd .. && python -m uvicorn STRATEGY_LAB.backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: Wait for backend to initialize
timeout /t 3 /nobreak > nul

:: Start the frontend dev server
echo [2/2] Starting frontend dev server on port 5173...
start "StrategyLab-Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ========================================
echo   Dashboard will open at:
echo   http://localhost:5173
echo ========================================
echo.
timeout /t 3 /nobreak > nul
start http://localhost:5173
