# ============================================
# Project Structure Auto Fix Script (Stable)
# No Chinese, No Unicode issues
# ============================================

function Info($msg)  { Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function OK($msg)    { Write-Host "[OK]    $msg" -ForegroundColor Green }
function Warn($msg)  { Write-Host "[WARN]  $msg" -ForegroundColor Yellow }
function Err($msg)   { Write-Host "[ERR]   $msg" -ForegroundColor Red }

$ErrorActionPreference = "Stop"

Info "Switching to script directory..."
Set-Location -Path $PSScriptRoot

# ============================================
# 1. Create src directory
# ============================================
if (-not (Test-Path "src")) {
    Info "Creating src directory..."
    mkdir src | Out-Null
    OK "src directory created"
} else {
    Warn "src directory already exists"
}

# ============================================
# 2. Move Python package directories into src/
# ============================================
$packageDirs = @(
    "async_runner", "browser_pool", "checkpoint", "config",
    "core", "crawler", "gui", "proxy_pool"
)

foreach ($dir in $packageDirs) {
    if (Test-Path $dir) {
        Info "Moving $dir to src/$dir"
        Move-Item $dir src\ -Force
        OK "$dir moved"
    } else {
        Warn "$dir not found, skipped"
    }
}

# ============================================
# 3. Ensure __init__.py exists
# ============================================
Info "Ensuring __init__.py exists in all packages..."
Get-ChildItem src -Directory | ForEach-Object {
    $init = Join-Path $_.FullName "__init__.py"
    if (-not (Test-Path $init)) {
        New-Item $init -ItemType File | Out-Null
        OK "Created: $init"
    }
}

# ============================================
# 4. Write pyproject.toml
# ============================================
Info "Writing pyproject.toml..."
@"
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "sql_safe_project"
version = "0.1.0"
description = "Playwright GUI crawler with async runner, browser pool, proxy pool, and SQL-safe utilities."
authors = [
    { name = "Bei" }
]
readme = "README.md"
requires-python = ">=3.8"

[project.optional-dependencies]
dev = [
    "pytest",
    "pytest-cov",
    "sqlalchemy",
    "pymysql"
]

[tool.setuptools.packages.find]
where = ["src"]
"@ | Set-Content -Encoding UTF8 pyproject.toml
OK "pyproject.toml updated"

# ============================================
# 5. Write pytest.ini
# ============================================
Info "Writing pytest.ini..."
@"
[pytest]
addopts = -q
testpaths = tests
pythonpath = src
"@ | Set-Content -Encoding UTF8 pytest.ini
OK "pytest.ini updated"

# ============================================
# 6. Write VSCode settings
# ============================================
if (-not (Test-Path ".vscode")) {
    mkdir .vscode | Out-Null
}

Info "Writing .vscode/settings.json..."
@"
{
    "python.analysis.extraPaths": [
        "./src"
    ],
    "python.testing.pytestArgs": [
        "tests"
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true,
    "python.defaultInterpreterPath": "\${workspaceFolder}/.venv/Scripts/python.exe"
}
"@ | Set-Content -Encoding UTF8 .vscode/settings.json
OK "VSCode settings updated"

# ============================================
# 7. pip install -e .
# ============================================
Info "Running pip install -e . ..."
pip install -e .
OK "Editable install completed"

OK "All tasks completed successfully!"
