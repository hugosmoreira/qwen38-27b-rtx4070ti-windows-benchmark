[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$virtualPython = Join-Path $repositoryRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $virtualPython -PathType Leaf)) {
    throw 'The isolated .venv is missing. Run .\scripts\setup_python.ps1 first.'
}

$env:PYTHONPATH = Join-Path $repositoryRoot 'src'
& $virtualPython -m unittest discover -s (Join-Path $repositoryRoot 'tests') -v
if ($LASTEXITCODE -ne 0) { throw 'Python tests failed.' }
