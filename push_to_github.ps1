# Push 03_llm_observability to Remote GitHub Repository
param(
    [string]$RepoUrl = ""
)

$ErrorActionPreference = "Stop"

if (-not $RepoUrl) {
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "🚀 Push 03_llm_observability to GitHub" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
    $RepoUrl = Read-Host "Enter your GitHub repository URL (e.g., https://github.com/username/litellm-observability-gateway.git)"
}

if (-not $RepoUrl.Trim()) {
    Write-Error "No repository URL provided. Aborting."
    exit 1
}

$RepoUrl = $RepoUrl.Trim()

Write-Host "`n[1/3] Configuring git remote 'origin' -> $RepoUrl..." -ForegroundColor Yellow
$existingRemote = git remote
if ($existingRemote -contains "origin") {
    git remote set-url origin $RepoUrl
} else {
    git remote add origin $RepoUrl
}

Write-Host "[2/3] Ensuring current branch is 'main'..." -ForegroundColor Yellow
git branch -M main

# Stage any untracked or modified files if present
$status = git status --porcelain
if ($status) {
    Write-Host "Staging recent changes..." -ForegroundColor Yellow
    git add .
    git commit -m "chore: update repository files and configuration"
}

Write-Host "[3/3] Pushing to GitHub (origin main)..." -ForegroundColor Green
git push -u origin main

Write-Host "`n✅ Successfully pushed 03_llm_observability to $RepoUrl!`n" -ForegroundColor Green
