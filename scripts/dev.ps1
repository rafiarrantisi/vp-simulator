# Qora local dev — seeds a demo user, starts backend (:8000) + frontend (:5173).
# Usage:  ./scripts/dev.ps1
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$py = Join-Path $root "backend\.venv\Scripts\python.exe"

Write-Host "[dev] seeding demo user (demo@qora.app / demo1234)..."
& $py -m scripts.seed_dev_user
# run from backend/ so relative sqlite path + module imports resolve
Push-Location (Join-Path $root "backend")
Start-Process -FilePath $py -ArgumentList "-m","uvicorn","app.main:app","--port","8000" -WorkingDirectory (Join-Path $root "backend")
Pop-Location
Write-Host "[dev] backend -> http://localhost:8000"

$env:VITE_API_BASE = "http://localhost:8000"
Push-Location (Join-Path $root "sistemnya")
Write-Host "[dev] frontend -> http://localhost:5173  (login demo@qora.app / demo1234)"
npm run dev
Pop-Location
