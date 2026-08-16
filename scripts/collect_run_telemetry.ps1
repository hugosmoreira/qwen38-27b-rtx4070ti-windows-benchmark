[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidateRange(1, 2147483647)][int]$TargetProcessId,
    [Parameter(Mandatory)][string]$OutputPath,
    [Parameter(Mandatory)][string]$StopSignalPath,
    [ValidateRange(100, 5000)][int]$IntervalMilliseconds = 250
)

$ErrorActionPreference = 'Stop'

$outputFullPath = [System.IO.Path]::GetFullPath($OutputPath)
$stopFullPath = [System.IO.Path]::GetFullPath($StopSignalPath)
$outputDirectory = Split-Path -Parent $outputFullPath
if (Test-Path -LiteralPath $outputFullPath) {
    throw "Refusing to overwrite telemetry output: $outputFullPath"
}
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory | Out-Null
}

$encoding = [System.Text.UTF8Encoding]::new($false)
$logicalProcessors = [Environment]::ProcessorCount
$previousCpuSeconds = $null
$previousSampleAt = $null

while (-not (Test-Path -LiteralPath $stopFullPath -PathType Leaf)) {
    $sampleAt = [DateTimeOffset]::UtcNow
    $gpuLine = & nvidia-smi --query-gpu=memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw --format=csv,noheader,nounits 2>$null | Select-Object -First 1
    $gpu = $null
    if (-not [string]::IsNullOrWhiteSpace($gpuLine)) {
        $fields = $gpuLine -split ','
        if ($fields.Count -ge 6) {
            $gpu = [ordered]@{
                vram_total_mib = [int]$fields[0].Trim()
                vram_used_mib = [int]$fields[1].Trim()
                vram_free_mib = [int]$fields[2].Trim()
                utilization_percent = [int]$fields[3].Trim()
                temperature_c = [int]$fields[4].Trim()
                power_draw_w = [double]$fields[5].Trim()
            }
        }
    }

    $process = Get-Process -Id $TargetProcessId -ErrorAction SilentlyContinue
    $processRecord = $null
    if ($null -ne $process) {
        $cpuSeconds = [double]$process.TotalProcessorTime.TotalSeconds
        $cpuPercent = $null
        if ($null -ne $previousCpuSeconds -and $null -ne $previousSampleAt) {
            $elapsedSeconds = ($sampleAt - $previousSampleAt).TotalSeconds
            if ($elapsedSeconds -gt 0) {
                $cpuPercent = [math]::Max(0.0, [math]::Round((($cpuSeconds - $previousCpuSeconds) / ($elapsedSeconds * $logicalProcessors)) * 100.0, 3))
            }
        }
        $processRecord = [ordered]@{
            working_set_bytes = [long]$process.WorkingSet64
            private_memory_bytes = [long]$process.PrivateMemorySize64
            cpu_total_seconds = [math]::Round($cpuSeconds, 6)
            cpu_percent_of_machine = $cpuPercent
            thread_count = [int]$process.Threads.Count
        }
        $previousCpuSeconds = $cpuSeconds
        $previousSampleAt = $sampleAt
    }

    $sample = [ordered]@{
        timestamp_utc = $sampleAt.ToString('o')
        target_process_id = $TargetProcessId
        process_running = $null -ne $process
        gpu = $gpu
        process = $processRecord
    }
    [System.IO.File]::AppendAllText($outputFullPath, ($sample | ConvertTo-Json -Depth 6 -Compress) + [Environment]::NewLine, $encoding)
    Start-Sleep -Milliseconds $IntervalMilliseconds
}
