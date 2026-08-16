[CmdletBinding()]
param(
    [string]$BaseUri = 'http://127.0.0.1:8090',
    [ValidatePattern('^[A-Za-z0-9._-]+$')][string]$ModelAlias = 'Qwen3.8-27B-UD-IQ2_XXS',
    [string]$PromptFile = 'prompts/phase4-baseline.json',
    [string]$ModelManifest = 'environment/model-download-manifest.json',
    [string]$OutputDirectory = 'results/raw',
    [ValidateRange(0, 5)][int]$WarmupCount = 1,
    [ValidateRange(1, 20)][int]$Repetitions = 3,
    [ValidateRange(100, 2000)][int]$TelemetryIntervalMilliseconds = 250,
    [ValidateRange(0, 30)][int]$InterRunDelaySeconds = 2,
    [ValidateRange(0, 2147483647)][int]$ServerProcessId = 0
)

$ErrorActionPreference = 'Stop'

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$runtimeRoot = Join-Path $repositoryRoot 'runtimes\llama.cpp\b10448'
$expectedServerPath = Join-Path $runtimeRoot 'bin\llama-server.exe'
$promptPath = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot $PromptFile)).Path
$modelManifestPath = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot $ModelManifest)).Path
$runtimeRecordPath = (Resolve-Path -LiteralPath (Join-Path $repositoryRoot 'environment\phase3-native-runtime-2026-08-15.json')).Path
$telemetryScriptPath = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot 'collect_run_telemetry.ps1')).Path
$resolvedOutputDirectory = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot $OutputDirectory))

function Get-Statistics {
    param([Parameter(Mandatory)][object[]]$Values)

    $numbers = @($Values | Where-Object { $null -ne $_ } | ForEach-Object { [double]$_ })
    if ($numbers.Count -eq 0) { return $null }
    $mean = ($numbers | Measure-Object -Average).Average
    $minimum = ($numbers | Measure-Object -Minimum).Minimum
    $maximum = ($numbers | Measure-Object -Maximum).Maximum
    $standardDeviation = 0.0
    if ($numbers.Count -gt 1) {
        $sumSquared = 0.0
        foreach ($number in $numbers) { $sumSquared += [math]::Pow($number - $mean, 2) }
        $standardDeviation = [math]::Sqrt($sumSquared / ($numbers.Count - 1))
    }
    return [ordered]@{
        count = $numbers.Count
        mean = [math]::Round($mean, 3)
        sample_standard_deviation = [math]::Round($standardDeviation, 3)
        coefficient_of_variation_percent = if ($mean -ne 0) { [math]::Round(($standardDeviation / $mean) * 100.0, 3) } else { $null }
        minimum = [math]::Round($minimum, 3)
        maximum = [math]::Round($maximum, 3)
    }
}

function Get-MaximumOrNull {
    param([object[]]$Values)
    $numbers = @($Values | Where-Object { $null -ne $_ } | ForEach-Object { [double]$_ })
    if ($numbers.Count -eq 0) { return $null }
    return ($numbers | Measure-Object -Maximum).Maximum
}

function Get-MinimumOrNull {
    param([object[]]$Values)
    $numbers = @($Values | Where-Object { $null -ne $_ } | ForEach-Object { [double]$_ })
    if ($numbers.Count -eq 0) { return $null }
    return ($numbers | Measure-Object -Minimum).Minimum
}

function Read-TelemetrySamples {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return @() }
    return @(Get-Content -LiteralPath $Path | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | ForEach-Object { $_ | ConvertFrom-Json -DateKind String })
}

function Get-TelemetryCadence {
    param([Parameter(Mandatory)][object[]]$Samples)
    if ($Samples.Count -lt 2) { return $null }
    $timestamps = @($Samples | ForEach-Object { [DateTimeOffset]::Parse([string]$_.timestamp_utc) })
    $intervals = @()
    for ($index = 1; $index -lt $timestamps.Count; $index++) {
        $intervals += ($timestamps[$index] - $timestamps[$index - 1]).TotalMilliseconds
    }
    return [ordered]@{
        observed_span_milliseconds = [math]::Round(($timestamps[-1] - $timestamps[0]).TotalMilliseconds, 3)
        observed_mean_interval_milliseconds = [math]::Round((($intervals | Measure-Object -Average).Average), 3)
        observed_minimum_interval_milliseconds = [math]::Round((($intervals | Measure-Object -Minimum).Minimum), 3)
        observed_maximum_interval_milliseconds = [math]::Round((($intervals | Measure-Object -Maximum).Maximum), 3)
    }
}

if (-not (Test-Path -LiteralPath $expectedServerPath -PathType Leaf)) {
    throw "Pinned llama-server executable not found: $expectedServerPath"
}
if ($ServerProcessId -eq 0) {
    $candidates = @(Get-Process -Name 'llama-server' -ErrorAction SilentlyContinue | Where-Object {
        $null -ne $_.Path -and $_.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)
    })
    if ($candidates.Count -ne 1) {
        throw "Expected exactly one pinned native llama-server process; found $($candidates.Count)."
    }
    $ServerProcessId = $candidates[0].Id
}
$serverProcess = Get-Process -Id $ServerProcessId -ErrorAction Stop
if (-not $serverProcess.Path.Equals($expectedServerPath, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Process $ServerProcessId is not the pinned llama-server executable."
}

$health = Invoke-RestMethod -Uri "$BaseUri/health" -Method Get -TimeoutSec 10
if ([string]$health.status -ne 'ok') { throw "Server health check failed at $BaseUri." }
$modelsResponse = Invoke-RestMethod -Uri "$BaseUri/v1/models" -Method Get -TimeoutSec 10
if (@($modelsResponse.data.id) -notcontains $ModelAlias) { throw "Expected served alias '$ModelAlias' was not found." }
$props = Invoke-RestMethod -Uri "$BaseUri/props" -Method Get -TimeoutSec 10
$modelManifestObject = Get-Content -LiteralPath $modelManifestPath -Raw | ConvertFrom-Json
$expectedModelPath = [System.IO.Path]::GetFullPath((Join-Path $repositoryRoot ([string]$modelManifestObject.relative_local_path)))
if (-not $expectedModelPath.Equals([string]$props.model_path, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "The served model does not match the pinned model manifest."
}
if ([int]$props.total_slots -ne 1 -or [int]$props.default_generation_settings.n_ctx -ne 4096) {
    throw "The server is not using the controlled one-slot, 4K configuration."
}

$launchRecords = @(Get-ChildItem -LiteralPath (Join-Path $runtimeRoot 'runs') -Filter 'launch.json' -File -Recurse | ForEach-Object {
    try { Get-Content -LiteralPath $_.FullName -Raw | ConvertFrom-Json } catch { $null }
} | Where-Object { $null -ne $_ -and [int]$_.process_id -eq $ServerProcessId })
if ($launchRecords.Count -ne 1) { throw "Could not identify one launch record for llama-server PID $ServerProcessId." }
$launchRecord = $launchRecords[0]
$requiredArguments = @(
    '--host', '127.0.0.1', '--port', '8090', '--cors-origins', 'localhost', '--device', 'CUDA0',
    '--ctx-size', '4096', '--parallel', '1', '--batch-size', '512', '--ubatch-size', '128',
    '--threads', '2', '--threads-batch', '2', '--gpu-layers', '-1', '--fit', 'off',
    '--flash-attn', 'on', '--cache-type-k', 'q8_0', '--cache-type-v', 'q8_0', '--cache-ram', '0',
    '--ctx-checkpoints', '0', '--no-context-shift', '--no-mmproj', '--reasoning', 'off',
    '--reasoning-format', 'deepseek', '--no-reasoning-preserve', '--no-agent'
)
$missingArguments = @($requiredArguments | Where-Object { @($launchRecord.arguments) -notcontains $_ } | Select-Object -Unique)
if ($missingArguments.Count -gt 0) {
    throw "The active launch record is missing required controlled arguments: $($missingArguments -join ', ')"
}

$suite = Get-Content -LiteralPath $promptPath -Raw | ConvertFrom-Json
$settings = $suite.settings
$workload = $suite.workload
$gitCommit = (& git -c "safe.directory=$($repositoryRoot.Replace('\', '/'))" rev-parse HEAD 2>$null | Select-Object -First 1).Trim()
$startedAt = Get-Date
$runId = 'phase4-iq2-baseline-' + $startedAt.ToUniversalTime().ToString('yyyyMMddTHHmmssZ')
$temporaryRoot = Join-Path $repositoryRoot "results\tmp\$runId"
New-Item -ItemType Directory -Path $temporaryRoot | Out-Null

$client = [System.Net.Http.HttpClient]::new()
$client.Timeout = [TimeSpan]::FromMinutes(10)
$runs = @()
$totalRuns = $WarmupCount + $Repetitions

try {
    for ($index = 0; $index -lt $totalRuns; $index++) {
        $isWarmup = $index -lt $WarmupCount
        $repetition = if ($isWarmup) { $index + 1 } else { $index - $WarmupCount + 1 }
        $runLabel = if ($isWarmup) { "warmup-$repetition" } else { "measured-$repetition" }
        $telemetryDirectory = Join-Path $temporaryRoot $runLabel
        New-Item -ItemType Directory -Path $telemetryDirectory | Out-Null
        $telemetryPath = Join-Path $telemetryDirectory 'telemetry.jsonl'
        $stopSignalPath = Join-Path $telemetryDirectory 'stop.signal'
        $collectorStdout = Join-Path $telemetryDirectory 'collector.stdout.log'
        $collectorStderr = Join-Path $telemetryDirectory 'collector.stderr.log'
        $collectorArguments = @(
            '-NoLogo', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"' + $telemetryScriptPath + '"'),
            '-TargetProcessId', [string]$ServerProcessId,
            '-OutputPath', ('"' + $telemetryPath + '"'),
            '-StopSignalPath', ('"' + $stopSignalPath + '"'),
            '-IntervalMilliseconds', [string]$TelemetryIntervalMilliseconds
        )
        $collector = Start-Process -FilePath (Join-Path $PSHOME 'pwsh.exe') `
            -ArgumentList ($collectorArguments -join ' ') `
            -WindowStyle Hidden `
            -RedirectStandardOutput $collectorStdout `
            -RedirectStandardError $collectorStderr `
            -PassThru
        Start-Sleep -Milliseconds ($TelemetryIntervalMilliseconds + 100)

        $requestBody = [ordered]@{
            model = $ModelAlias
            messages = @(
                [ordered]@{ role = 'system'; content = [string]$workload.system },
                [ordered]@{ role = 'user'; content = [string]$workload.user }
            )
            stream = $true
            stream_options = [ordered]@{ include_usage = $true }
            max_tokens = [int]$settings.max_tokens
            temperature = [double]$settings.temperature
            top_p = [double]$settings.top_p
            top_k = [int]$settings.top_k
            min_p = [double]$settings.min_p
            seed = [int]$settings.seed
            cache_prompt = $false
            chat_template_kwargs = [ordered]@{
                enable_thinking = $false
                preserve_thinking = $false
            }
        }

        $timer = [System.Diagnostics.Stopwatch]::StartNew()
        $headersMs = $null
        $ttftMs = $null
        $finishReason = $null
        $usage = $null
        $timings = $null
        $systemFingerprint = $null
        $contentBuilder = [System.Text.StringBuilder]::new()
        $reasoningBuilder = [System.Text.StringBuilder]::new()
        $requestError = $null
        $request = $null
        $response = $null
        $reader = $null

        try {
            $request = [System.Net.Http.HttpRequestMessage]::new([System.Net.Http.HttpMethod]::Post, "$BaseUri/v1/chat/completions")
            $request.Content = [System.Net.Http.StringContent]::new(($requestBody | ConvertTo-Json -Depth 12 -Compress), [System.Text.Encoding]::UTF8, 'application/json')
            $response = $client.SendAsync($request, [System.Net.Http.HttpCompletionOption]::ResponseHeadersRead).GetAwaiter().GetResult()
            $headersMs = [math]::Round($timer.Elapsed.TotalMilliseconds, 3)
            $response.EnsureSuccessStatusCode() | Out-Null
            $reader = [System.IO.StreamReader]::new($response.Content.ReadAsStream())
            while (-not $reader.EndOfStream) {
                $line = $reader.ReadLine()
                if ([string]::IsNullOrWhiteSpace($line) -or -not $line.StartsWith('data: ')) { continue }
                $data = $line.Substring(6)
                if ($data -eq '[DONE]') { break }
                $chunk = $data | ConvertFrom-Json
                if ($null -ne $chunk.system_fingerprint) { $systemFingerprint = [string]$chunk.system_fingerprint }
                if ($chunk.choices.Count -gt 0) {
                    $delta = $chunk.choices[0].delta
                    if ($null -ne $delta.content -and [string]$delta.content -ne '') {
                        if ($null -eq $ttftMs) { $ttftMs = [math]::Round($timer.Elapsed.TotalMilliseconds, 3) }
                        $null = $contentBuilder.Append([string]$delta.content)
                    }
                    if ($null -ne $delta.reasoning_content -and [string]$delta.reasoning_content -ne '') {
                        $null = $reasoningBuilder.Append([string]$delta.reasoning_content)
                    }
                    if ($null -ne $chunk.choices[0].finish_reason) { $finishReason = [string]$chunk.choices[0].finish_reason }
                }
                if ($null -ne $chunk.usage) { $usage = $chunk.usage }
                if ($null -ne $chunk.timings) { $timings = $chunk.timings }
            }
        }
        catch {
            $requestError = $_.Exception.Message
        }
        finally {
            $timer.Stop()
            if ($null -ne $reader) { $reader.Dispose() }
            if ($null -ne $response) { $response.Dispose() }
            if ($null -ne $request) { $request.Dispose() }
            [System.IO.File]::WriteAllText($stopSignalPath, "stop`n", [System.Text.UTF8Encoding]::new($false))
            if (-not $collector.WaitForExit(10000)) {
                Stop-Process -Id $collector.Id -ErrorAction SilentlyContinue
                $requestError = if ($null -eq $requestError) { 'Telemetry collector did not stop within 10 seconds.' } else { $requestError }
            }
        }

        $samples = Read-TelemetrySamples -Path $telemetryPath
        $cadence = Get-TelemetryCadence -Samples $samples
        $telemetrySummary = [ordered]@{
            target_interval_milliseconds = $TelemetryIntervalMilliseconds
            sample_count = $samples.Count
            observed_span_milliseconds = $cadence.observed_span_milliseconds
            observed_mean_interval_milliseconds = $cadence.observed_mean_interval_milliseconds
            observed_minimum_interval_milliseconds = $cadence.observed_minimum_interval_milliseconds
            observed_maximum_interval_milliseconds = $cadence.observed_maximum_interval_milliseconds
            peak_vram_used_mib = Get-MaximumOrNull @($samples.gpu.vram_used_mib)
            minimum_vram_free_mib = Get-MinimumOrNull @($samples.gpu.vram_free_mib)
            peak_gpu_utilization_percent = Get-MaximumOrNull @($samples.gpu.utilization_percent)
            peak_gpu_temperature_c = Get-MaximumOrNull @($samples.gpu.temperature_c)
            peak_gpu_power_draw_w = Get-MaximumOrNull @($samples.gpu.power_draw_w)
            peak_process_working_set_bytes = Get-MaximumOrNull @($samples.process.working_set_bytes)
            peak_process_private_memory_bytes = Get-MaximumOrNull @($samples.process.private_memory_bytes)
            peak_process_cpu_percent_of_machine = Get-MaximumOrNull @($samples.process.cpu_percent_of_machine)
        }

        $content = $contentBuilder.ToString()
        $reasoningContent = $reasoningBuilder.ToString()
        $validation = [ordered]@{
            request_succeeded = $null -eq $requestError
            first_content_observed = $null -ne $ttftMs
            usage_observed = $null -ne $usage
            timings_observed = $null -ne $timings
            prompt_cache_disabled = $null -ne $timings -and [int]$timings.cache_n -eq 0
            minimum_completion_tokens_met = $null -ne $usage -and [int]$usage.completion_tokens -ge [int]$workload.acceptance.minimum_completion_tokens
            expected_finish_reason = $finishReason -eq [string]$workload.acceptance.expected_finish_reason
            reasoning_empty = [string]::IsNullOrEmpty($reasoningContent)
            telemetry_observed = $samples.Count -gt 0
        }
        $valid = $validation.Values -notcontains $false
        $runs += [ordered]@{
            run_label = $runLabel
            warmup = $isWarmup
            repetition = $repetition
            status = if ($valid) { 'completed' } else { 'failed_validation' }
            error = $requestError
            client_measurements = [ordered]@{
                response_headers_ms = $headersMs
                time_to_first_content_token_ms = $ttftMs
                total_latency_ms = [math]::Round($timer.Elapsed.TotalMilliseconds, 3)
            }
            server_measurements = [ordered]@{
                usage = $usage
                timings = $timings
                system_fingerprint = $systemFingerprint
            }
            response = [ordered]@{
                finish_reason = $finishReason
                content = $content
                reasoning_content = if ([string]::IsNullOrEmpty($reasoningContent)) { $null } else { $reasoningContent }
            }
            telemetry_summary = $telemetrySummary
            telemetry_samples = $samples
            validation = $validation
        }

        if (-not $valid) { break }
        if ($index -lt ($totalRuns - 1) -and $InterRunDelaySeconds -gt 0) { Start-Sleep -Seconds $InterRunDelaySeconds }
    }
}
finally {
    $client.Dispose()
}

$measuredRuns = @($runs | Where-Object { -not $_.warmup -and $_.status -eq 'completed' })
$allExpectedRunsCompleted = $runs.Count -eq $totalRuns -and @($runs | Where-Object { $_.status -ne 'completed' }).Count -eq 0
$record = [ordered]@{
    schema_version = 'phase4-baseline-1.0'
    run_id = $runId
    timestamp = $startedAt.ToString('o')
    git_commit = $gitCommit
    classification = 'phase4_repeated_iq2_baseline'
    hardware_snapshot = 'environment/machine-snapshot-2026-08-15.json'
    runtime_record = [System.IO.Path]::GetRelativePath($repositoryRoot, $runtimeRecordPath).Replace('\', '/')
    model_manifest = [System.IO.Path]::GetRelativePath($repositoryRoot, $modelManifestPath).Replace('\', '/')
    prompt_suite = [System.IO.Path]::GetRelativePath($repositoryRoot, $promptPath).Replace('\', '/')
    runtime = [ordered]@{
        name = 'llama.cpp'
        release_tag = 'b10448'
        commit = 'ad1de39e0708e3ced9c71bb3c82d93a2c046a73f'
        backend = 'CUDA'
        system_fingerprint = if ($runs.Count -gt 0) { $runs[-1].server_measurements.system_fingerprint } else { $null }
    }
    model = [ordered]@{
        repository = [string]$modelManifestObject.repository
        revision = [string]$modelManifestObject.repository_commit
        filename = [string]$modelManifestObject.filename
        quantization = 'UD-IQ2_XXS'
        file_size_bytes = [long]$modelManifestObject.size_bytes
        sha256 = [string]$modelManifestObject.sha256
        served_alias = $ModelAlias
    }
    configuration = [ordered]@{
        context_size = 4096
        parallel_slots = 1
        device = 'CUDA0'
        gpu_layers = -1
        fit = 'off'
        flash_attention = 'on'
        prompt_batch_size = 512
        prompt_micro_batch_size = 128
        threads = 2
        threads_batch = 2
        kv_cache_k_type = 'q8_0'
        kv_cache_v_type = 'q8_0'
        cache_ram_mib = 0
        context_checkpoints = 0
        context_shift = $false
        thinking_mode = $false
        preserve_thinking = $false
        reasoning_format = 'deepseek'
        mtp_enabled = $false
        tools_enabled = $false
        mcp_enabled = $false
        vision_enabled = $false
        max_output_tokens = [int]$settings.max_tokens
        temperature = [double]$settings.temperature
        top_p = [double]$settings.top_p
        top_k = [int]$settings.top_k
        min_p = [double]$settings.min_p
        seed = [int]$settings.seed
        prompt_cache = $false
    }
    methodology = [ordered]@{
        warmup_runs = $WarmupCount
        measured_repetitions = $Repetitions
        streaming = $true
        ttft_definition = 'Elapsed wall time from HTTP send until the first non-empty assistant content delta was read.'
        total_latency_definition = 'Elapsed wall time from HTTP send through the SSE done marker.'
        prompt_cache_disabled = $true
        telemetry_target_interval_milliseconds = $TelemetryIntervalMilliseconds
        telemetry_scope = 'NVIDIA GPU plus the pinned llama-server process'
        inter_run_delay_seconds = $InterRunDelaySeconds
    }
    runs = $runs
    measured_summary = [ordered]@{
        expected_repetitions = $Repetitions
        completed_repetitions = $measuredRuns.Count
        time_to_first_content_token_ms = Get-Statistics @($measuredRuns.client_measurements.time_to_first_content_token_ms)
        total_latency_ms = Get-Statistics @($measuredRuns.client_measurements.total_latency_ms)
        server_prompt_tokens_per_second = Get-Statistics @($measuredRuns.server_measurements.timings.prompt_per_second)
        server_generation_tokens_per_second = Get-Statistics @($measuredRuns.server_measurements.timings.predicted_per_second)
        peak_vram_used_mib = Get-Statistics @($measuredRuns.telemetry_summary.peak_vram_used_mib)
        minimum_vram_free_mib = Get-Statistics @($measuredRuns.telemetry_summary.minimum_vram_free_mib)
        peak_gpu_utilization_percent = Get-Statistics @($measuredRuns.telemetry_summary.peak_gpu_utilization_percent)
        peak_process_working_set_bytes = Get-Statistics @($measuredRuns.telemetry_summary.peak_process_working_set_bytes)
        peak_process_private_memory_bytes = Get-Statistics @($measuredRuns.telemetry_summary.peak_process_private_memory_bytes)
        peak_process_cpu_percent_of_machine = Get-Statistics @($measuredRuns.telemetry_summary.peak_process_cpu_percent_of_machine)
        all_expected_runs_completed = $allExpectedRunsCompleted
    }
}

if (-not (Test-Path -LiteralPath $resolvedOutputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $resolvedOutputDirectory | Out-Null
}
$outputPath = Join-Path $resolvedOutputDirectory "$runId.json"
if (Test-Path -LiteralPath $outputPath) { throw "Refusing to overwrite result: $outputPath" }
$record | ConvertTo-Json -Depth 30 | Set-Content -LiteralPath $outputPath -Encoding utf8

[ordered]@{
    output_path = $outputPath
    warmup_runs = @($runs | Where-Object { $_.warmup }).Count
    measured_repetitions = $measuredRuns.Count
    all_expected_runs_completed = $allExpectedRunsCompleted
    generation_tokens_per_second = $record.measured_summary.server_generation_tokens_per_second
    time_to_first_content_token_ms = $record.measured_summary.time_to_first_content_token_ms
} | ConvertTo-Json -Depth 6

if (-not $allExpectedRunsCompleted) {
    throw "Phase 4 baseline did not complete every expected run. Partial evidence was written to $outputPath"
}
