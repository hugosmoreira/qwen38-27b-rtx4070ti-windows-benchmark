[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Test-CommandAvailable {
    param([Parameter(Mandatory)][string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Get-OptionalCommandVersion {
    param(
        [Parameter(Mandatory)][string]$Name,
        [string[]]$ArgumentList = @('--version')
    )

    if (-not (Test-CommandAvailable -Name $Name)) {
        return $null
    }

    try {
        return ((& $Name @ArgumentList 2>&1 | Select-Object -First 1) -join '').Trim()
    }
    catch {
        return $null
    }
}

if (-not ('LocalMemoryStatus' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class LocalMemoryStatus {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    public class MEMORYSTATUSEX {
        public uint dwLength;
        public uint dwMemoryLoad;
        public ulong ullTotalPhys;
        public ulong ullAvailPhys;
        public ulong ullTotalPageFile;
        public ulong ullAvailPageFile;
        public ulong ullTotalVirtual;
        public ulong ullAvailVirtual;
        public ulong ullAvailExtendedVirtual;
        public MEMORYSTATUSEX() {
            dwLength = (uint)Marshal.SizeOf(typeof(MEMORYSTATUSEX));
        }
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool GlobalMemoryStatusEx([In, Out] MEMORYSTATUSEX buffer);
}
'@
}

$memoryStatus = New-Object LocalMemoryStatus+MEMORYSTATUSEX
if (-not [LocalMemoryStatus]::GlobalMemoryStatusEx($memoryStatus)) {
    throw 'GlobalMemoryStatusEx failed.'
}

$windows = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
$cpuName = (Get-ItemPropertyValue 'HKLM:\HARDWARE\DESCRIPTION\System\CentralProcessor\0' -Name 'ProcessorNameString').Trim()

$gpu = $null
if (Test-CommandAvailable -Name 'nvidia-smi') {
    $gpuFields = (& nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,driver_version,pstate,temperature.gpu,power.limit --format=csv,noheader,nounits 2>$null | Select-Object -First 1) -split ','
    if ($gpuFields.Count -ge 8) {
        $gpu = [ordered]@{
            name = $gpuFields[0].Trim()
            vram_total_mib = [int]$gpuFields[1].Trim()
            vram_used_mib = [int]$gpuFields[2].Trim()
            vram_free_mib = [int]$gpuFields[3].Trim()
            driver_version = $gpuFields[4].Trim()
            performance_state = $gpuFields[5].Trim()
            temperature_c = [int]$gpuFields[6].Trim()
            power_limit_w = [double]$gpuFields[7].Trim()
        }
    }
}

$drives = Get-PSDrive -PSProvider FileSystem | ForEach-Object {
    [ordered]@{
        drive = $_.Name
        used_gb = [math]::Round($_.Used / 1GB, 2)
        free_gb = [math]::Round($_.Free / 1GB, 2)
    }
}

$snapshot = [ordered]@{
    captured_at = (Get-Date).ToString('o')
    operating_system = [ordered]@{
        product_name_registry = $windows.ProductName
        display_version = $windows.DisplayVersion
        current_build = $windows.CurrentBuild
        update_build_revision = $windows.UBR
        edition_id = $windows.EditionID
    }
    cpu = [ordered]@{
        name = $cpuName
        logical_processors = [int]$env:NUMBER_OF_PROCESSORS
    }
    memory = [ordered]@{
        total_physical_gb = [math]::Round($memoryStatus.ullTotalPhys / 1GB, 2)
        available_physical_gb = [math]::Round($memoryStatus.ullAvailPhys / 1GB, 2)
    }
    gpu = $gpu
    drives = @($drives)
    commands = [ordered]@{
        git = Get-OptionalCommandVersion -Name 'git'
        python = Get-OptionalCommandVersion -Name 'python'
        py = Get-OptionalCommandVersion -Name 'py'
        winget = Get-OptionalCommandVersion -Name 'winget'
        llama_cli = Get-OptionalCommandVersion -Name 'llama-cli'
        llama_server = Get-OptionalCommandVersion -Name 'llama-server'
        docker = Get-OptionalCommandVersion -Name 'docker'
    }
}

$snapshot | ConvertTo-Json -Depth 6
