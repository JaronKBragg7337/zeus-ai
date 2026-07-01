@echo off
chcp 65001 >nul
echo ╔══════════════════════════════════════════════════╗
echo ║                                                  ║
echo ║     🤖 OmniLocal AI Workbench v1.0.0            ║
echo ║     100%% Local • Private • Open Source           ║
echo ║                                                  ║
echo ╚══════════════════════════════════════════════════╝
echo.

REM Check Ollama
ollama --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Ollama not found! Install from https://ollama.ai
    pause
    exit /b 1
)

echo  ✅ Ollama detected

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo  ❌ Python not found! Install Python 3.10+
    pause
    exit /b 1
)

echo  ✅ Python detected

REM Install backend deps if needed
if not exist "backend\.deps_installed" (
    echo  📦 Installing backend dependencies...
    cd backend
    pip install -r requirements.txt
    if errorlevel 1 (
        echo  ❌ Failed to install backend dependencies
        pause
        exit /b 1
    )
    echo. > .deps_installed
    cd ..
)

REM Start backend
echo  🚀 Starting backend server...
cd backend
start "OmniLocal Backend" cmd /k "python main.py"
cd ..

timeout /t 3 /nobreak >nul

REM Check if backend started
curl -s http://localhost:8000/api/health >nul 2>&1
if errorlevel 1 (
    echo  ⚠️  Backend might still be starting...
    timeout /t 3 /nobreak >nul
)

echo  ✅ Backend running at http://localhost:8000

REM Check frontend deps
if not exist "frontend\node_modules" (
    echo  📦 Installing frontend dependencies...
    cd frontend
    call npm install --no-bin-links
    cd ..
)

REM Start frontend
echo  🌐 Starting frontend...
cd frontend
start "OmniLocal Frontend" cmd /k "npm run dev"
cd ..

timeout /t 2 /nobreak >nul

echo.
echo ════════════════════════════════════════════════════
echo  🎉 OmniLocal AI Workbench is starting!
echo.
echo  📱 Open http://localhost:3000 in your browser
echo  🔧 API running at http://localhost:8000
echo.
echo  Features:
echo    • Chat with local AI models
echo    • Agent mode with tool use (files, shell, search)
echo    • Document Q&A with local RAG
echo    • File browser and editor
echo    • Model manager (install new models)
echo.
echo  Press any key to open the browser...
echo ════════════════════════════════════════════════════
pause >nul
start http://localhost:3000
