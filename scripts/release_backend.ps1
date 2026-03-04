param(
    [string]$Tag = "v1-backend-stable",
    [string]$Branch = "main",
    [switch]$Commit,
    [switch]$Push
)

$ErrorActionPreference = "Stop"

function Run-Step([string]$name, [scriptblock]$action) {
    Write-Host "==> $name"
    & $action
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

Run-Step "Lint" { python -m ruff check api_server.py pipeline.py modules tests scripts train_model.py }
Run-Step "Tests" { .\.venv311\Scripts\python.exe -m pytest -q }

if ($Commit) {
    Run-Step "Commit changes" {
        git add .
        git commit -m "release: backend stable with monitoring and quality tooling"
    }
} else {
    Write-Host "Skipping commit (use -Commit to include)."
}

Run-Step "Check clean git state" {
    $dirty = git status --porcelain
    if ($dirty) {
        throw "Working tree is not clean. Commit/stash changes before tagging."
    }
}

Run-Step "Create/refresh tag $Tag" {
    if ((git tag --list $Tag) -contains $Tag) {
        git tag -d $Tag | Out-Null
    }
    git tag $Tag
}

if ($Push) {
    Run-Step "Push branch and tag" {
        git push origin $Branch
        git push origin $Tag
    }
} else {
    Write-Host "Skipping push (use -Push to publish)."
}

Write-Host "Release lock complete."
