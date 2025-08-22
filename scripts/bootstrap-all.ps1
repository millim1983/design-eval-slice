Param(
  [string]$Py = "$PSScriptRoot\..\backend\.venv\Scripts\python.exe"
)

# 백엔드: venv 없으면 생성
if (!(Test-Path "$PSScriptRoot\..\backend\.venv\Scripts\python.exe")) {
  Write-Host ">> Create venv"
  Push-Location "$PSScriptRoot\..\backend"
  python -m venv .venv
  Pop-Location
}

# 백엔드: 패키지 설치
Write-Host ">> Install backend deps"
& "$PSScriptRoot\..\backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "$PSScriptRoot\..\backend\.venv\Scripts\python.exe" -m pip install -r "$PSScriptRoot\..\backend\requirements.txt"

# 프론트엔드: npm 설치
Write-Host ">> Install frontend deps"
Push-Location "$PSScriptRoot\..\frontend"
if (Test-Path package-lock.json) { npm ci } else { npm install }
Pop-Location

Write-Host "`n✅ Done. Next:"
Write-Host "  scripts\dev.ps1  # 개발 서버 2개 실행"
Write-Host "  scripts\docker-up.ps1  # Docker로 실행"
