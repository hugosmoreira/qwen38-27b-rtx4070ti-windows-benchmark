[CmdletBinding()]
param(
    [string]$ModelManifest = 'environment/phase13-iq4-xs-download-manifest.json',
    [ValidateRange(1, 66)][int]$InitialGpuLayers = 25,
    [ValidateRange(1, 32)][int]$LayerStep = 8,
    [ValidateRange(1, 66)][int]$MaximumGpuLayers = 66,
    [ValidateRange(256, 4096)][int]$MinimumFreeVramMiB = 1024,
    [ValidateRange(1024, 262144)][int]$ContextSize = 4096,
    [ValidateSet('q8_0', 'q4_0')][string]$KvCacheType = 'q8_0',
    [ValidateRange(1024, 65535)][int]$Port = 8090,
    [ValidateRange(30, 600)][int]$StartupTimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'

if ($InitialGpuLayers -gt $MaximumGpuLayers) {
    throw 'InitialGpuLayers cannot exceed MaximumGpuLayers.'
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$userProfilePath = [Environment]::GetFolderPath('UserProfile')
$expectedServerPath = Join-Path $repositoryRoot 'runtimes\llama.cpp\b10448\bin\llama-server.exe'
$launcherPath = Join-Path $repositoryRoot 'scripts\start_native_llama_server.ps1'
$manifestPath = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $ModelManifest))
foreach ($requiredPath in @($expectedServerPath, $launcherPath, $manifestPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath -PathType Leaf)) {
        throw "Required file not found: $requiredPath"
    }
}

$existingServers = @(Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue | Where-Object {
    $null -ne $_.Path -and $_.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)
})
if ($existingServers.Count -ne 0) {
    throw "Phase 13 requires a clean pinned-runtime state; found $($existingServers.Count) existing llama-server process(es)."
}

$model = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
$modelPath = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot ([string]$model.relative_local_path)))
if (-not (Test-Path -LiteralPath $modelPath -PathType Leaf)) {
    throw "Pinned IQ4_XS model is missing: $modelPath"
}
$modelFile = Get-Item -LiteralPath $modelPath
if ($modelFile.Length -ne [long]$model.size_bytes) {
    throw "Model size mismatch. Expected $($model.size_bytes); found $($modelFile.Length)."
}
$modelHash = (Get-FileHash -LiteralPath $modelPath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($modelHash -cne ([string]$model.sha256).ToLowerInvariant()) {
    throw "Model SHA-256 mismatch. Expected $($model.sha256); found $modelHash."
}

function Get-GpuSnapshot {
    $line = & nvidia-smi --query-gpu=name,driver_version,memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader,nounits 2>$null | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($line)) { return $null }
    $fields = $line -split ','
    if ($fields.Count -lt 8) { return $null }
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

function ConvertTo-SafeMessage {
    param([Parameter(Mandatory)][string]$Message)
    $safe = $Message.Replace($repositoryRoot, '<repository-root>')
    if (-not [string]::IsNullOrWhiteSpace($userProfilePath)) {
        $safe = $safe.Replace($userProfilePath, '<user-profile>')
    }
    return $safe
}

function Stop-OwnedPinnedServer {
    param([Parameter(Mandatory)][int]$ProcessId)

    $candidate = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
    if ($null -eq $candidate) { return }
    if ($null -eq $candidate.Path -or -not $candidate.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to stop PID $ProcessId because it is not the pinned llama-server executable."
    }
    Stop-Process -Id $ProcessId -ErrorAction Stop
    Wait-Process -Id $ProcessId -Timeout 30 -ErrorAction SilentlyContinue
}

$probes = [System.Collections.Generic.List[object]]::new()
$probeSequence = 0

function Invoke-OffloadProbe {
    param([Parameter(Mandatory)][int]$GpuLayers)

    $script:probeSequence++
    $startedAt = Get-Date
    $before = Get-GpuSnapshot
    $serverProcessId = 0
    $launch = $null
    $offloadedLayers = $null
    $totalLayers = $null
    $response = $null
    $after = $null
    $privateBytes = $null
    $failureType = $null
    $failureMessage = $null
    $logEvidence = @()

    try {
        $launchText = & $launcherPath `
            -ModelManifest $ModelManifest `
            -ModelAlias 'Qwen3.8-27B-IQ4_XS' `
            -ContextSize $ContextSize `
            -Port $Port `
            -Threads 2 `
            -GpuLayers $GpuLayers `
            -KvCacheKType $KvCacheType `
            -KvCacheVType $KvCacheType `
            -SpeculativeType 'none' `
            -StartupTimeoutSeconds $StartupTimeoutSeconds `
            -SkipModelHashValidation | Out-String
        $launch = $launchText | ConvertFrom-Json
        $serverProcessId = [int]$launch.process_id

        $payload = [ordered]@{
            model = 'Qwen3.8-27B-IQ4_XS'
            messages = @(
                [ordered]@{ role = 'system'; content = 'Complete a short controlled inference probe. Return plain text.' },
                [ordered]@{ role = 'user'; content = 'Explain write-ahead logging in one compact paragraph.' }
            )
            max_tokens = 64
            temperature = 0.0
            seed = 42
            stream = $false
            cache_prompt = $false
        }
        $response = Invoke-RestMethod `
            -Uri "http://127.0.0.1:$Port/v1/chat/completions" `
            -Method Post `
            -ContentType 'application/json' `
            -Body ($payload | ConvertTo-Json -Depth 8) `
            -TimeoutSec 600

        $serverProcess = Get-Process -Id $serverProcessId -ErrorAction Stop
        $privateBytes = [long]$serverProcess.PrivateMemorySize64
        $after = Get-GpuSnapshot

        $serverLog = [string]$launch.server_log
        $matches = @(Select-String -LiteralPath $serverLog -Pattern 'offloaded\s+(\d+)/(\d+)\s+layers to GPU' -AllMatches)
        if ($matches.Count -gt 0) {
            $last = $matches[-1].Matches[-1]
            $offloadedLayers = [int]$last.Groups[1].Value
            $totalLayers = [int]$last.Groups[2].Value
        }
        $logEvidence = @(Get-Content -LiteralPath $serverLog | Where-Object {
            $_ -match 'offloaded\s+\d+/\d+\s+layers to GPU|CUDA0 model buffer size|CPU_Mapped model buffer size'
        } | ForEach-Object { $_.Trim() })
    }
    catch {
        $failureType = $_.Exception.GetType().Name
        $failureMessage = ConvertTo-SafeMessage -Message $_.Exception.Message
    }
    finally {
        if ($serverProcessId -gt 0) {
            Stop-OwnedPinnedServer -ProcessId $serverProcessId
        }
        else {
            $unexpected = @(Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue | Where-Object {
                $null -ne $_.Path -and $_.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)
            })
            foreach ($process in $unexpected) {
                Stop-OwnedPinnedServer -ProcessId $process.Id
            }
        }
    }

    $requestSucceeded = $null -ne $response -and $null -ne $response.choices -and $response.choices.Count -ge 1
    $placementEvidenced = $null -ne $offloadedLayers -and $offloadedLayers -eq $GpuLayers
    $headroomPassed = $null -ne $after -and [int]$after.vram_free_mib -ge $MinimumFreeVramMiB
    $practical = $null -eq $failureType -and $requestSucceeded -and $placementEvidenced -and $headroomPassed
    $relativeLog = if ($null -ne $launch) {
        [System.IO.Path]::GetRelativePath($repositoryRoot, [string]$launch.server_log).Replace('\', '/')
    } else { $null }
    $timings = if ($null -ne $response) { $response.timings } else { $null }
    $usage = if ($null -ne $response) { $response.usage } else { $null }

    $record = [ordered]@{
        sequence = $script:probeSequence
        started_at = $startedAt.ToString('o')
        gpu_layers_requested = $GpuLayers
        gpu_layers_offloaded = $offloadedLayers
        total_layers_reported = $totalLayers
        practical = $practical
        gates = [ordered]@{
            startup_and_request_succeeded = $null -eq $failureType -and $requestSucceeded
            requested_placement_evidenced = $placementEvidenced
            minimum_free_vram_mib = $MinimumFreeVramMiB
            vram_headroom_passed = $headroomPassed
        }
        gpu_before = $before
        gpu_after_request = $after
        process_private_bytes_after_request = $privateBytes
        request = [ordered]@{
            prompt_tokens = if ($null -ne $usage) { $usage.prompt_tokens } else { $null }
            completion_tokens = if ($null -ne $usage) { $usage.completion_tokens } else { $null }
            prompt_tokens_per_second = if ($null -ne $timings) { $timings.prompt_per_second } else { $null }
            generation_tokens_per_second = if ($null -ne $timings) { $timings.predicted_per_second } else { $null }
            finish_reason = if ($requestSucceeded) { $response.choices[0].finish_reason } else { $null }
        }
        startup_log = $relativeLog
        startup_evidence = $logEvidence
        failure = if ($null -eq $failureType) { $null } else { [ordered]@{ type = $failureType; message = $failureMessage } }
    }
    $script:probes.Add($record)
    return $record
}

$lastPractical = $null
$firstNonPractical = $null
$candidate = $InitialGpuLayers
while ($candidate -le $MaximumGpuLayers) {
    $probe = Invoke-OffloadProbe -GpuLayers $candidate
    if ([bool]$probe.practical) {
        $lastPractical = $candidate
        if ($candidate -eq $MaximumGpuLayers) { break }
        $candidate = [math]::Min($candidate + $LayerStep, $MaximumGpuLayers)
        if ($candidate -eq $lastPractical) { break }
    }
    else {
        $firstNonPractical = $candidate
        break
    }
}

if ($null -ne $lastPractical -and $null -ne $firstNonPractical) {
    while (($firstNonPractical - $lastPractical) -gt 1) {
        $candidate = [math]::Floor(($lastPractical + $firstNonPractical) / 2)
        $probe = Invoke-OffloadProbe -GpuLayers $candidate
        if ([bool]$probe.practical) {
            $lastPractical = $candidate
        }
        else {
            $firstNonPractical = $candidate
        }
    }
}

$completedAt = Get-Date
$contextLabel = [string]$ContextSize
$kvLabel = $KvCacheType.Replace('_', '-')
$runId = "phase13-iq4-offload-frontier-$contextLabel-$kvLabel-" + $completedAt.ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$outputDirectory = Join-Path $repositoryRoot 'results\raw'
$outputPath = Join-Path $outputDirectory ($runId + '.json')
if (Test-Path -LiteralPath $outputPath) {
    throw "Refusing to overwrite an existing frontier result: $outputPath"
}
$safeDirectory = 'safe.directory=' + $repositoryRoot.Replace('\', '/')
$gitCommit = (& git -c $safeDirectory -C $repositoryRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $gitCommit -notmatch '^[0-9a-f]{40}$') {
    throw 'Could not record the repository commit for the frontier result.'
}

$result = [ordered]@{
    schema_version = 'phase13-offload-frontier-1.0'
    run_id = $runId
    recorded_at = $completedAt.ToString('o')
    git_commit = $gitCommit
    classification = 'phase13_iq4_xs_offload_frontier'
    protocol = 'environment/phase13-iq4-xs-protocol-2026-08-16.json'
    model_manifest = 'environment/phase13-iq4-xs-download-manifest.json'
    runtime_manifest = 'environment/llama-cpp-b10448-manifest.json'
    controls = [ordered]@{
        context_size = $ContextSize
        kv_cache_k = $KvCacheType
        kv_cache_v = $KvCacheType
        mtp = $false
        minimum_free_vram_mib = $MinimumFreeVramMiB
        initial_gpu_layers = $InitialGpuLayers
        layer_step = $LayerStep
        maximum_gpu_layers = $MaximumGpuLayers
        fresh_process_per_probe = $true
    }
    probes = @($probes)
    selection = [ordered]@{
        largest_practical_gpu_layers = $lastPractical
        first_non_practical_gpu_layers = $firstNonPractical
        practical_definition = 'Healthy request, exact startup-log layer evidence, and at least the frozen post-request VRAM headroom.'
        baseline_authorized = $null -ne $lastPractical
    }
    limitations = @(
        "The frontier is local to this driver, WDDM state, runtime build, IQ4_XS artifact, $ContextSize context, and $KvCacheType K/V cache.",
        'Each probe contains one short request and is placement evidence, not a repeated performance benchmark.',
        'A higher layer count that starts but misses the VRAM-headroom gate is classified as non-practical rather than as an out-of-memory failure.'
    )
}
[System.IO.File]::WriteAllText($outputPath, ($result | ConvertTo-Json -Depth 12), [System.Text.UTF8Encoding]::new($false))

[ordered]@{
    result = [System.IO.Path]::GetRelativePath($repositoryRoot, $outputPath).Replace('\', '/')
    probes = $probes.Count
    largest_practical_gpu_layers = $lastPractical
    first_non_practical_gpu_layers = $firstNonPractical
} | ConvertTo-Json -Depth 5
