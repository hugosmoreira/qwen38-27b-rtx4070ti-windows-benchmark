[CmdletBinding()]
param(
    [string]$ModelManifest = 'environment/model-download-manifest.json',
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$ModelAlias = 'Qwen3.8-27B-UD-IQ2_XXS',
    [ValidateRange(1024, 262144)][int]$ContextSize = 4096,
    [ValidateRange(1024, 65535)][int]$Port = 8090,
    [ValidateRange(1, 64)][int]$Threads = 2,
    [ValidateSet('none', 'draft-mtp')][string]$SpeculativeType = 'none',
    [ValidateRange(0, 16)][int]$SpeculativeDraftMaximum = 2,
    [ValidateRange(0, 16)][int]$SpeculativeDraftMinimum = 0,
    [ValidateRange(30, 600)][int]$StartupTimeoutSeconds = 180,
    [switch]$SkipModelHashValidation
)

$ErrorActionPreference = 'Stop'

if ($SpeculativeType -eq 'draft-mtp' -and $SpeculativeDraftMaximum -lt 1) {
    throw 'draft-mtp requires SpeculativeDraftMaximum of at least 1.'
}
if ($SpeculativeDraftMinimum -gt $SpeculativeDraftMaximum) {
    throw 'SpeculativeDraftMinimum cannot exceed SpeculativeDraftMaximum.'
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$releaseTag = 'b10448'
$runtimeRoot = Join-Path $repositoryRoot "runtimes\llama.cpp\$releaseTag"
$binaryDirectory = Join-Path $runtimeRoot 'bin'
$cudaDirectory = Join-Path $runtimeRoot 'cuda-13.3'
$serverPath = Join-Path $binaryDirectory 'llama-server.exe'
$releaseManifestPath = Join-Path $repositoryRoot 'environment\llama-cpp-b10448-manifest.json'
$resolvedModelManifest = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot $ModelManifest)).Path

foreach ($requiredPath in @($serverPath, $releaseManifestPath, $resolvedModelManifest)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required file not found: $requiredPath"
    }
}
if (-not (Test-Path -LiteralPath $cudaDirectory -PathType Container)) {
    throw "CUDA runtime directory not found: $cudaDirectory"
}

function Test-LocalPortAvailable {
    param([Parameter(Mandatory)][int]$CandidatePort)

    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $CandidatePort)
    try {
        $listener.Start()
        return $true
    }
    catch [System.Net.Sockets.SocketException] {
        return $false
    }
    finally {
        $listener.Stop()
    }
}

function Get-GpuSnapshot {
    $line = & nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader,nounits 2>$null | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($line)) {
        return $null
    }
    $fields = $line -split ','
    if ($fields.Count -lt 8) {
        return $null
    }
    return [ordered]@{
        name = $fields[0].Trim()
        driver_version = $fields[1].Trim()
        vram_total_mib = [int]$fields[2].Trim()
        vram_used_mib = [int]$fields[3].Trim()
        vram_free_mib = [int]$fields[4].Trim()
        utilization_percent = [int]$fields[5].Trim()
        temperature_c = [int]$fields[6].Trim()
        power_draw_w = [double]$fields[7].Trim()
    }
}

if (-not (Test-LocalPortAvailable -CandidatePort $Port)) {
    throw "TCP port $Port is already in use on 127.0.0.1."
}

$modelManifestObject = Get-Content -LiteralPath $resolvedModelManifest -Raw | ConvertFrom-Json
$modelPath = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot ([string]$modelManifestObject.relative_local_path)))
if (-not (Test-Path -LiteralPath $modelPath -PathType Leaf)) {
    throw "Model file not found: $modelPath"
}
$modelFile = Get-Item -LiteralPath $modelPath
if ($modelFile.Length -ne [long]$modelManifestObject.size_bytes) {
    throw "Model size mismatch. Expected $($modelManifestObject.size_bytes) bytes; found $($modelFile.Length)."
}
if (-not $SkipModelHashValidation) {
    $actualHash = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHash -cne ([string]$modelManifestObject.sha256).ToLowerInvariant()) {
        throw "Model SHA-256 mismatch. Expected $($modelManifestObject.sha256); found $actualHash."
    }
}

$previousPath = $env:PATH
try {
    $env:PATH = "$cudaDirectory;$binaryDirectory;$previousPath"
    $versionOutput = (& $serverPath --version 2>&1) -join "`n"
    $deviceOutput = (& $serverPath --list-devices 2>&1) -join "`n"
}
finally {
    $env:PATH = $previousPath
}
if ($versionOutput -notmatch 'build 10448, commit ad1de39e0') {
    throw "Unexpected llama.cpp build: $versionOutput"
}
if ($deviceOutput -notmatch 'CUDA0:\s+NVIDIA GeForce RTX 4070 Ti') {
    throw "Expected CUDA0 RTX 4070 Ti was not detected: $deviceOutput"
}

$startedAt = Get-Date
$runId = 'native-server-' + $startedAt.ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$runDirectory = Join-Path $runtimeRoot "runs\$runId"
if (Test-Path -LiteralPath $runDirectory) {
    throw "Refusing to reuse an existing runtime directory: $runDirectory"
}
New-Item -ItemType Directory -Path $runDirectory | Out-Null

$stdoutPath = Join-Path $runDirectory 'stdout.log'
$stderrPath = Join-Path $runDirectory 'stderr.log'
$serverLogPath = Join-Path $runDirectory 'llama-server.log'
$launchRecordPath = Join-Path $runDirectory 'launch.json'
$pidPath = Join-Path $runDirectory 'server.pid'
$arguments = @(
    '--model', ('"' + $modelPath + '"'),
    '--alias', $ModelAlias,
    '--host', '127.0.0.1',
    '--port', [string]$Port,
    '--cors-origins', 'localhost',
    '--device', 'CUDA0',
    '--ctx-size', [string]$ContextSize,
    '--parallel', '1',
    '--batch-size', '512',
    '--ubatch-size', '128',
    '--threads', [string]$Threads,
    '--threads-batch', [string]$Threads,
    '--gpu-layers', '-1',
    '--fit', 'off',
    '--flash-attn', 'on',
    '--cache-type-k', 'q8_0',
    '--cache-type-v', 'q8_0',
    '--cache-ram', '0',
    '--ctx-checkpoints', '0',
    '--no-context-shift',
    '--no-mmproj',
    '--jinja',
    '--reasoning', 'off',
    '--reasoning-format', 'deepseek',
    '--no-reasoning-preserve',
    '--no-agent',
    '--metrics',
    '--log-verbosity', '4',
    '--log-colors', 'off',
    '--log-timestamps',
    '--log-file', ('"' + $serverLogPath + '"')
)
if ($SpeculativeType -eq 'draft-mtp') {
    $arguments += @(
        '--spec-type', 'draft-mtp',
        '--spec-draft-n-max', [string]$SpeculativeDraftMaximum,
        '--spec-draft-n-min', [string]$SpeculativeDraftMinimum,
        '--spec-draft-type-k', 'f16',
        '--spec-draft-type-v', 'f16'
    )
}

try {
    $env:PATH = "$cudaDirectory;$binaryDirectory;$previousPath"
    $process = Start-Process -FilePath $serverPath `
        -ArgumentList ($arguments -join ' ') `
        -WorkingDirectory $repositoryRoot `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath `
        -PassThru
}
finally {
    $env:PATH = $previousPath
}

[System.IO.File]::WriteAllText($pidPath, [string]$process.Id + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
$baseUri = "http://127.0.0.1:$Port"
$deadline = (Get-Date).AddSeconds($StartupTimeoutSeconds)
$health = $null
while ((Get-Date) -lt $deadline) {
    if ($process.HasExited) {
        $tail = if (Test-Path -LiteralPath $serverLogPath) { (Get-Content -LiteralPath $serverLogPath -Tail 40) -join "`n" } else { '' }
        throw "llama-server exited during startup with code $($process.ExitCode).`n$tail"
    }
    try {
        $health = Invoke-RestMethod -Uri "$baseUri/health" -Method Get -TimeoutSec 2
        if ([string]$health.status -eq 'ok') {
            break
        }
    }
    catch {
        Start-Sleep -Milliseconds 500
    }
}
if ($null -eq $health -or [string]$health.status -ne 'ok') {
    throw "llama-server did not become healthy within $StartupTimeoutSeconds seconds."
}

$launchRecord = [ordered]@{
    schema_version = 'native-server-launch-1.0'
    run_id = $runId
    started_at = $startedAt.ToString('o')
    process_id = $process.Id
    base_uri = $baseUri
    release_manifest = 'environment/llama-cpp-b10448-manifest.json'
    model_manifest = [System.IO.Path]::GetRelativePath($repositoryRoot, $resolvedModelManifest).Replace('\', '/')
    model_alias = $ModelAlias
    model_hash_validated = -not $SkipModelHashValidation
    speculative_decoding = [ordered]@{
        type = $SpeculativeType
        draft_n_max = if ($SpeculativeType -eq 'draft-mtp') { $SpeculativeDraftMaximum } else { 0 }
        draft_n_min = if ($SpeculativeType -eq 'draft-mtp') { $SpeculativeDraftMinimum } else { 0 }
        draft_cache_k = if ($SpeculativeType -eq 'draft-mtp') { 'f16' } else { $null }
        draft_cache_v = if ($SpeculativeType -eq 'draft-mtp') { 'f16' } else { $null }
    }
    version_output = $versionOutput
    device_output = $deviceOutput
    arguments = @($arguments | ForEach-Object { $_.Trim('"') } | ForEach-Object { if ($_ -eq $modelPath) { [System.IO.Path]::GetRelativePath($repositoryRoot, $modelPath).Replace('\', '/') } elseif ($_ -eq $serverLogPath) { '<ignored-runtime>/llama-server.log' } else { $_ } })
    health = $health
    gpu_after_load = Get-GpuSnapshot
    log_files = [ordered]@{
        server = $serverLogPath
        stdout = $stdoutPath
        stderr = $stderrPath
    }
}
$launchRecord | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $launchRecordPath -Encoding utf8

[ordered]@{
    run_id = $runId
    process_id = $process.Id
    base_uri = $baseUri
    launch_record = $launchRecordPath
    server_log = $serverLogPath
    gpu_after_load = $launchRecord.gpu_after_load
} | ConvertTo-Json -Depth 6
