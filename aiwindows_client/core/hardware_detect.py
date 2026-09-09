"""Lightweight cross-platform hardware detection for the Windows client."""
from __future__ import annotations
import os, platform
try:
    import psutil
except ImportError:
    psutil = None

class HardwareDetector:
    def snapshot(self):
        logical = os.cpu_count() or 1
        physical = psutil.cpu_count(logical=False) if psutil else None
        mem = psutil.virtual_memory().total if psutil else 0
        return {
            "platform": platform.platform(), "processor": platform.processor(),
            "physical_cores": physical or logical, "logical_cores": logical,
            "memory_bytes": mem,
        }
    def get_summary(self):
        i=self.snapshot()
        gib=i["memory_bytes"]/(1024**3) if i["memory_bytes"] else 0
        return f"{i['platform']}\nCPU: {i['processor'] or 'unknown'}\nCores: {i['physical_cores']} physical / {i['logical_cores']} logical\nRAM: {gib:.1f} GiB"

hardware_detector=HardwareDetector()

def get_qt_hints():
    i=hardware_detector.snapshot()
    mem_gib=i["memory_bytes"]/(1024**3) if i["memory_bytes"] else 8
    tier="high" if i["logical_cores"] >= 8 and mem_gib >= 16 else ("low" if i["logical_cores"] <= 2 or mem_gib < 4 else "medium")
    return {"use_opengl": True, "performance_tier": tier, "thread_count": max(2,min(i["logical_cores"],16)), "enable_vsync": True}
