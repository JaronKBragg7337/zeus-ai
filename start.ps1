# Zeus AI Workbench Startup Script
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                                                  ║" -ForegroundColor Cyan
Write-Host "║     Zeus AI Workbench v1.0.0                    ║" -ForegroundColor Cyan
Write-Host "║     100% Local • Private • Open Source           ║" -ForegroundColor Cyan
Write-Host "║                                                  ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Check Ollama
try {
    $ollama = ollama --version 2>$null
    Write-Host "  ✅ Ollama detected" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Ollama not found! Install from https://ollama.ai" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Check Python
try {
    $py = python --version 2>$null
    Write-Host "  ✅ Python detected: $py" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Python not found! Install Python 3.10+" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

# Install backend deps
if (-not (Test-Path "backend\.deps_installed")) {
    Write-Host "  📦 Installing backend dependencies..." -ForegroundColor Yellow
    Set-Location backend
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  ❌ Failed to install backend dependencies" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    "" | Out-File -FilePath ".deps_installed" -Encoding utf8
    Set-Location ..
}

# Start backend
Write-Host "  🚀 Starting backend server..." -ForegroundColor Yellow
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\backend
    python main.py
}

Start-Sleep -Seconds 4

# Verify backend
$health = try { Invoke-RestMethod -Uri "http://localhost:8000/api/health" -TimeoutSec 5 } catch { $null }
if ($health) {
    Write-Host "  ✅ Backend running at http://localhost:8000" -ForegroundColor Green
} else {
    Write-Host "  ⚠️  Backend starting (may need a moment)..." -ForegroundColor Yellow
}

# Start frontend
Write-Host "  🌐 Starting frontend..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Zeus AI Workbench is starting!" -ForegroundColor Green
Write-Host ""
Write-Host "  📱 Open http://localhost:3000 in your browser" -ForegroundColor White
Write-Host "  🔧 API running at http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "  Features:" -ForegroundColor Yellow
Write-Host "    • Chat with local AI models" -ForegroundColor Gray
Write-Host "    • Agent mode with tool use" -ForegroundColor Gray
Write-Host "    • Document Q&A with RAG" -ForegroundColor Gray
Write-Host "    • File browser and editor" -ForegroundColor Gray
Write-Host "    • Model manager" -ForegroundColor Gray
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop all services" -ForegroundColor DarkGray

# Keep running
while ($true) {
    Start-Sleep -Seconds 1
    $backendOutput = Receive-Job -Job $backendJob
    $frontendOutput = Receive-Job -Job $frontendJob
    if ($backendOutput) { Write-Host "[BACKEND] $backendOutput" -ForegroundColor DarkGray }
    if ($frontendOutput) { Write-Host "[FRONTEND] $frontendOutput" -ForegroundColor DarkBlue }
}
