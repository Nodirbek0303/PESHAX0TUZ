from __future__ import annotations

import shutil
from dataclasses import dataclass


@dataclass
class GpuStatus:
    available: bool
    device: str
    device_name: str | None
    load_percent: float
    memory_used_mb: float | None
    memory_total_mb: float | None


def resolve_device(preference: str = "auto") -> str:
    if preference != "auto":
        return preference

    try:
        import torch

        if torch.cuda.is_available():
            return "cuda:0"
    except Exception:
        pass

    return "cpu"


def get_gpu_status(device: str | None = None) -> GpuStatus:
    resolved = device or resolve_device()
    load = 0.0
    name: str | None = None
    mem_used: float | None = None
    mem_total: float | None = None
    available = resolved.startswith("cuda")

    try:
        import torch

        if torch.cuda.is_available():
            index = 0
            if ":" in resolved:
                index = int(resolved.split(":")[1])
            name = torch.cuda.get_device_name(index)
            mem_used = round(torch.cuda.memory_allocated(index) / (1024 * 1024), 1)
            mem_total = round(torch.cuda.get_device_properties(index).total_memory / (1024 * 1024), 1)
            load = min(99.0, round((mem_used / mem_total) * 100, 1)) if mem_total else 0.0
            available = True
        else:
            resolved = "cpu"
            available = False
            name = "CPU inference"
    except Exception:
        resolved = "cpu"
        available = False
        name = "CPU inference"

    if shutil.which("nvidia-smi"):
        try:
            import subprocess

            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used,memory.total,name",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=2,
                check=False,
            )
            if result.returncode == 0 and result.stdout.strip():
                util, used, total, gpu_name = [part.strip() for part in result.stdout.split(",")]
                load = float(util)
                mem_used = float(used)
                mem_total = float(total)
                name = gpu_name
                available = True
                if not resolved.startswith("cuda"):
                    resolved = "cuda:0"
        except Exception:
            pass

    return GpuStatus(
        available=available,
        device=resolved,
        device_name=name,
        load_percent=load,
        memory_used_mb=mem_used,
        memory_total_mb=mem_total,
    )
