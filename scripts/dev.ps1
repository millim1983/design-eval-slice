# scripts/dev.ps1  (robust version)
$ScriptDir = $PSScriptRoot
$root      = (Resolve-Path (Join-Path $ScriptDir '..')).Path
$backend   = Join-Path $root 'backend'
$frontend  = Join-Path $root 'frontend'
$venvPy    = Join-Path $backend '.venv\Scripts\python.exe'

# venv가 없으면 자동 생성 + 의존성 설치
if (!(Test-Path $venvPy)) {
  Write-Host "No venv detected → creating and installing deps..." -ForegroundColor Yellow
  Push-Location $backend
  python -m venv .venv
  & "$venvPy" -m pip install --upgrade pip
  & "$venvPy" -m pip install -r requirements.txt
  Pop-Location
}

# 백엔드: venv 파이썬으로 직접 uvicorn 실행 (활성화 불필요)
$backendCmd = @"
cd "$backend"
& "$venvPy" -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
"@

# 프론트: node_modules 없으면 자동 설치 후 dev 서버
$frontendCmd = @"
cd "$frontend"
if (!(Test-Path node_modules)) { npm install }
npm run dev
"@

Start-Process powershell -ArgumentList '-NoExit','-Command', $backendCmd
Start-Process powershell -ArgumentList '-NoExit','-Command', $frontendCmd

Write-Host "API:   http://localhost:8000/docs"
Write-Host "WEB:   http://localhost:5173"
