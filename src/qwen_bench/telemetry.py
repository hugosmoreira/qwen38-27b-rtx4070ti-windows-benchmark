"""NVIDIA GPU and Windows process telemetry with observed cadence reporting."""

from __future__ import annotations

import ctypes
import os
import subprocess
import threading
import time
from collections.abc import Callable
from ctypes import wintypes
from datetime import datetime, timezone
from typing import Any


class TelemetryError(RuntimeError):
    """Raised when the required telemetry collector cannot be initialized."""


def parse_nvidia_smi_row(row: str) -> dict[str, int | float]:
    fields = [field.strip() for field in row.strip().split(",")]
    if len(fields) != 6:
        raise ValueError("Expected six NVIDIA telemetry fields.")
    return {
        "vram_total_mib": int(fields[0]),
        "vram_used_mib": int(fields[1]),
        "vram_free_mib": int(fields[2]),
        "utilization_percent": int(fields[3]),
        "temperature_c": int(fields[4]),
        "power_draw_w": float(fields[5]),
    }


def query_nvidia_gpu() -> dict[str, int | float]:
    command = [
        "nvidia-smi",
        "--id=0",
        "--query-gpu=memory.total,memory.used,memory.free,utilization.gpu,temperature.gpu,power.draw",
        "--format=csv,noheader,nounits",
    ]
    creation_flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
        timeout=5.0,
        creationflags=creation_flags,
    )
    first_row = next((line for line in completed.stdout.splitlines() if line.strip()), "")
    if not first_row:
        raise TelemetryError("nvidia-smi returned no GPU telemetry row.")
    return parse_nvidia_smi_row(first_row)


class WindowsProcessProbe:
    """Read memory and CPU time from one process using documented Win32 APIs."""

    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    STILL_ACTIVE = 259

    class FILETIME(ctypes.Structure):
        _fields_ = [("dwLowDateTime", wintypes.DWORD), ("dwHighDateTime", wintypes.DWORD)]

    class PROCESS_MEMORY_COUNTERS_EX(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
            ("PrivateUsage", ctypes.c_size_t),
        ]

    def __init__(self, process_id: int) -> None:
        if os.name != "nt":
            raise TelemetryError("Process telemetry currently requires Windows.")
        if process_id <= 0:
            raise TelemetryError("Process ID must be positive.")

        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._psapi = ctypes.WinDLL("psapi", use_last_error=True)
        self._configure_signatures()
        access = self.PROCESS_QUERY_INFORMATION | self.PROCESS_VM_READ
        self._handle = self._kernel32.OpenProcess(access, False, process_id)
        if not self._handle:
            code = ctypes.get_last_error()
            raise TelemetryError(f"Could not open target process for telemetry (Win32 error {code}).")
        self._previous_cpu_seconds: float | None = None
        self._previous_monotonic_ns: int | None = None
        self._logical_processors = os.cpu_count() or 1

    def _configure_signatures(self) -> None:
        self._kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL
        self._kernel32.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        self._kernel32.GetExitCodeProcess.restype = wintypes.BOOL
        self._kernel32.GetProcessTimes.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(self.FILETIME),
            ctypes.POINTER(self.FILETIME),
            ctypes.POINTER(self.FILETIME),
            ctypes.POINTER(self.FILETIME),
        ]
        self._kernel32.GetProcessTimes.restype = wintypes.BOOL
        self._psapi.GetProcessMemoryInfo.argtypes = [
            wintypes.HANDLE,
            ctypes.POINTER(self.PROCESS_MEMORY_COUNTERS_EX),
            wintypes.DWORD,
        ]
        self._psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

    def sample(self, monotonic_ns: int) -> tuple[bool, dict[str, int | float | None] | None]:
        exit_code = wintypes.DWORD()
        if not self._kernel32.GetExitCodeProcess(self._handle, ctypes.byref(exit_code)):
            raise TelemetryError("GetExitCodeProcess failed.")
        if exit_code.value != self.STILL_ACTIVE:
            return False, None

        counters = self.PROCESS_MEMORY_COUNTERS_EX()
        counters.cb = ctypes.sizeof(counters)
        if not self._psapi.GetProcessMemoryInfo(self._handle, ctypes.byref(counters), counters.cb):
            raise TelemetryError("GetProcessMemoryInfo failed.")

        creation = self.FILETIME()
        exited = self.FILETIME()
        kernel = self.FILETIME()
        user = self.FILETIME()
        if not self._kernel32.GetProcessTimes(
            self._handle,
            ctypes.byref(creation),
            ctypes.byref(exited),
            ctypes.byref(kernel),
            ctypes.byref(user),
        ):
            raise TelemetryError("GetProcessTimes failed.")

        cpu_seconds = (_filetime_ticks(kernel) + _filetime_ticks(user)) / 10_000_000.0
        cpu_percent: float | None = None
        if self._previous_cpu_seconds is not None and self._previous_monotonic_ns is not None:
            elapsed_seconds = (monotonic_ns - self._previous_monotonic_ns) / 1_000_000_000.0
            if elapsed_seconds > 0:
                delta_cpu = max(0.0, cpu_seconds - self._previous_cpu_seconds)
                cpu_percent = round((delta_cpu / (elapsed_seconds * self._logical_processors)) * 100.0, 3)
        self._previous_cpu_seconds = cpu_seconds
        self._previous_monotonic_ns = monotonic_ns

        return True, {
            "working_set_bytes": int(counters.WorkingSetSize),
            "private_memory_bytes": int(counters.PrivateUsage),
            "cpu_total_seconds": round(cpu_seconds, 6),
            "cpu_percent_of_machine": cpu_percent,
        }

    def close(self) -> None:
        if getattr(self, "_handle", None):
            self._kernel32.CloseHandle(self._handle)
            self._handle = None


def _filetime_ticks(value: WindowsProcessProbe.FILETIME) -> int:
    return (int(value.dwHighDateTime) << 32) | int(value.dwLowDateTime)


class TelemetryCollector:
    """Collect samples in a helper thread while inference is in progress."""

    def __init__(
        self,
        process_id: int,
        interval_milliseconds: int = 250,
        gpu_query: Callable[[], dict[str, int | float]] = query_nvidia_gpu,
        process_probe_factory: Callable[[int], WindowsProcessProbe] = WindowsProcessProbe,
    ) -> None:
        if not 100 <= interval_milliseconds <= 5_000:
            raise TelemetryError("Telemetry interval must be between 100 and 5000 milliseconds.")
        self.process_id = process_id
        self.interval_milliseconds = interval_milliseconds
        self._gpu_query = gpu_query
        self._process_probe = process_probe_factory(process_id)
        self._samples: list[dict[str, Any]] = []
        self._errors: list[str] = []
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._ready_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._started_ns: int | None = None

    def start(self) -> None:
        if self._thread is not None:
            raise TelemetryError("Telemetry collector cannot be started twice.")
        self._started_ns = time.perf_counter_ns()
        self._thread = threading.Thread(target=self._run, name="benchmark-telemetry", daemon=True)
        self._thread.start()

    def wait_until_ready(self, timeout_seconds: float = 5.0) -> bool:
        return self._ready_event.wait(timeout_seconds)

    def stop(self, timeout_seconds: float = 10.0) -> None:
        self._stop_event.set()
        if self._thread is not None:
            self._thread.join(timeout_seconds)
            if self._thread.is_alive():
                raise TelemetryError("Telemetry collector did not stop within the timeout.")
        self._process_probe.close()

    @property
    def samples(self) -> list[dict[str, Any]]:
        with self._lock:
            return list(self._samples)

    @property
    def errors(self) -> list[str]:
        with self._lock:
            return list(self._errors)

    def _run(self) -> None:
        assert self._started_ns is not None
        interval_seconds = self.interval_milliseconds / 1_000.0
        while not self._stop_event.is_set():
            cycle_started_ns = time.perf_counter_ns()
            gpu: dict[str, int | float] | None = None
            process_running = False
            process: dict[str, int | float | None] | None = None
            try:
                gpu = self._gpu_query()
            except Exception as error:  # telemetry failures are recorded, not hidden
                self._record_error(f"GPU telemetry failed: {type(error).__name__}.")
            try:
                process_running, process = self._process_probe.sample(cycle_started_ns)
            except Exception as error:
                self._record_error(f"Process telemetry failed: {type(error).__name__}.")

            sample = {
                "timestamp_utc": _utc_now(),
                "monotonic_elapsed_milliseconds": round(
                    (cycle_started_ns - self._started_ns) / 1_000_000.0, 3
                ),
                "target_process_id": self.process_id,
                "process_running": process_running,
                "gpu": gpu,
                "process": process,
            }
            with self._lock:
                self._samples.append(sample)
            self._ready_event.set()

            cycle_seconds = (time.perf_counter_ns() - cycle_started_ns) / 1_000_000_000.0
            remaining = max(0.0, interval_seconds - cycle_seconds)
            self._stop_event.wait(remaining)

    def _record_error(self, message: str) -> None:
        with self._lock:
            if message not in self._errors:
                self._errors.append(message)


def summarize_telemetry(
    samples: list[dict[str, Any]], target_interval_milliseconds: int
) -> dict[str, int | float | None]:
    elapsed = [float(sample["monotonic_elapsed_milliseconds"]) for sample in samples]
    intervals = [elapsed[index] - elapsed[index - 1] for index in range(1, len(elapsed))]

    def gpu_values(field: str) -> list[float]:
        return [float(sample["gpu"][field]) for sample in samples if isinstance(sample.get("gpu"), dict)]

    def process_values(field: str) -> list[float]:
        return [
            float(sample["process"][field])
            for sample in samples
            if isinstance(sample.get("process"), dict) and sample["process"].get(field) is not None
        ]

    return {
        "target_interval_milliseconds": target_interval_milliseconds,
        "sample_count": len(samples),
        "observed_span_milliseconds": round(elapsed[-1] - elapsed[0], 3) if len(elapsed) >= 2 else None,
        "observed_mean_interval_milliseconds": _rounded_mean(intervals),
        "observed_minimum_interval_milliseconds": round(min(intervals), 3) if intervals else None,
        "observed_maximum_interval_milliseconds": round(max(intervals), 3) if intervals else None,
        "peak_vram_used_mib": _rounded_max(gpu_values("vram_used_mib")),
        "minimum_vram_free_mib": _rounded_min(gpu_values("vram_free_mib")),
        "peak_gpu_utilization_percent": _rounded_max(gpu_values("utilization_percent")),
        "peak_gpu_temperature_c": _rounded_max(gpu_values("temperature_c")),
        "peak_gpu_power_draw_w": _rounded_max(gpu_values("power_draw_w")),
        "peak_process_working_set_bytes": _rounded_max(process_values("working_set_bytes")),
        "peak_process_private_memory_bytes": _rounded_max(process_values("private_memory_bytes")),
        "peak_process_cpu_percent_of_machine": _rounded_max(process_values("cpu_percent_of_machine")),
    }


def _rounded_mean(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 3) if values else None


def _rounded_max(values: list[float]) -> float | None:
    return round(max(values), 3) if values else None


def _rounded_min(values: list[float]) -> float | None:
    return round(min(values), 3) if values else None


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
