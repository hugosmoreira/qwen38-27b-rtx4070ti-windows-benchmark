[CmdletBinding()]
param(
    [string]$PythonPath = ''
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$virtualEnvironment = Join-Path $repositoryRoot '.venv'
$virtualPython = Join-Path $virtualEnvironment 'Scripts\python.exe'

if ([string]::IsNullOrWhiteSpace($PythonPath)) {
    $candidates = @(
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python313\python.exe'),
        (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python314\python.exe')
    )
    $pathPython = Get-Command python -ErrorAction SilentlyContinue
    if ($null -ne $pathPython) { $candidates += $pathPython.Source }
    $PythonPath = @($candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -Unique)[0]
}

if ([string]::IsNullOrWhiteSpace($PythonPath) -or -not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    throw 'Python was not found. Install a supported CPython 3.11 through 3.14 release, or pass -PythonPath.'
}

$version = & $PythonPath -c 'import json, sys; print(json.dumps(list(sys.version_info[:3])))' | ConvertFrom-Json
if ([int]$version[0] -ne 3 -or [int]$version[1] -lt 11 -or [int]$version[1] -ge 15) {
    throw "Unsupported Python version $($version -join '.'). Use CPython 3.11 through 3.14."
}

if (-not (Test-Path -LiteralPath $virtualPython -PathType Leaf)) {
    & $PythonPath -m venv $virtualEnvironment
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}

$env:PYTHONPATH = Join-Path $repositoryRoot 'src'
& $virtualPython -m qwen_bench --version
if ($LASTEXITCODE -ne 0) { throw 'The qwen-bench source package did not import from the virtual environment.' }

[ordered]@{
    python_version = $version -join '.'
    virtual_environment = '.venv'
    runtime_dependencies = @()
    ready = $true
} | ConvertTo-Json -Depth 4
