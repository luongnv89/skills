#!/usr/bin/env python3
"""
Detect system hardware and software for Ollama optimization.
Outputs JSON with system specs relevant to Ollama configuration.
"""

import json
import platform
import subprocess
import os
import re
from pathlib import Path


def run_command(cmd, shell=False):
    """Run a command and return output, or None on failure."""
    try:
        result = subprocess.run(
            cmd if shell else cmd.split(),
            capture_output=True,
            text=True,
            timeout=30,
            shell=shell
        )
        return result.stdout.strip() if result.returncode == 0 else None
    except Exception:
        return None


def get_macos_info():
    """Get macOS-specific hardware info."""
    info = {"gpu": [], "metal_support": False, "apple_silicon": False}

    # Check for Apple Silicon
    chip_info = run_command("sysctl -n machdep.cpu.brand_string")
    if chip_info and "Apple" in chip_info:
        info["apple_silicon"] = True
        info["metal_support"] = True
        info["chip"] = chip_info

        # Get unified memory (Apple Silicon shares RAM with GPU)
        mem_bytes = run_command("sysctl -n hw.memsize")
        if mem_bytes:
            info["unified_memory_gb"] = int(mem_bytes) // (1024**3)
            info["gpu"].append({
                "name": chip_info,
                "type": "apple_silicon",
                "vram_gb": info["unified_memory_gb"],  # Unified memory
                "metal": True
            })
    else:
        # Intel Mac - check for discrete GPU
        gpu_info = run_command("system_profiler SPDisplaysDataType")
        if gpu_info:
            info["gpu_raw"] = gpu_info
            if "Metal" in gpu_info:
                info["metal_support"] = True

    return info


def get_linux_gpu_info():
    """Get Linux GPU information."""
    gpus = []

    # Check NVIDIA GPUs
    nvidia_smi = run_command("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits")
    if nvidia_smi:
        for line in nvidia_smi.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                gpus.append({
                    "name": parts[0],
                    "type": "nvidia",
                    "vram_mb": int(parts[1]),
                    "vram_gb": round(int(parts[1]) / 1024, 1),
                    "driver_version": parts[2]
                })

    # Check AMD GPUs (ROCm)
    rocm_info = run_command("rocm-smi --showmeminfo vram --csv")
    if rocm_info:
        amd_name = run_command("rocm-smi --showproductname")
        for line in rocm_info.strip().split('\n')[1:]:  # Skip header
            if line.strip():
                gpus.append({
                    "name": amd_name or "AMD GPU",
                    "type": "amd_rocm",
                    "rocm_available": True
                })

    return gpus


def get_windows_gpu_info():
    """Get Windows GPU information."""
    gpus = []

    # Try nvidia-smi first
    nvidia_smi = run_command("nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader,nounits")
    if nvidia_smi:
        for line in nvidia_smi.strip().split('\n'):
            parts = [p.strip() for p in line.split(',')]
            if len(parts) >= 3:
                gpus.append({
                    "name": parts[0],
                    "type": "nvidia",
                    "vram_mb": int(parts[1]),
                    "vram_gb": round(int(parts[1]) / 1024, 1),
                    "driver_version": parts[2]
                })

    # Fallback to WMIC
    if not gpus:
        wmic = run_command("wmic path win32_VideoController get name,adapterram", shell=True)
        if wmic:
            gpus.append({"raw_info": wmic, "type": "unknown"})

    return gpus


def get_memory_info():
    """Get system memory information."""
    system = platform.system()
    info = {}

    if system == "Darwin":
        mem_bytes = run_command("sysctl -n hw.memsize")
        if mem_bytes:
            info["total_gb"] = int(mem_bytes) // (1024**3)
    elif system == "Linux":
        meminfo = Path("/proc/meminfo").read_text() if Path("/proc/meminfo").exists() else ""
        match = re.search(r"MemTotal:\s+(\d+)", meminfo)
        if match:
            info["total_gb"] = int(match.group(1)) // (1024**2)
        match = re.search(r"MemAvailable:\s+(\d+)", meminfo)
        if match:
            info["available_gb"] = int(match.group(1)) // (1024**2)
    elif system == "Windows":
        wmic = run_command("wmic computersystem get totalphysicalmemory", shell=True)
        if wmic:
            match = re.search(r"(\d+)", wmic)
            if match:
                info["total_gb"] = int(match.group(1)) // (1024**3)

    return info


def get_cpu_info():
    """Get CPU information."""
    info = {
        "cores": os.cpu_count(),
        "architecture": platform.machine()
    }

    system = platform.system()
    if system == "Darwin":
        brand = run_command("sysctl -n machdep.cpu.brand_string")
        if brand:
            info["model"] = brand
        perf_cores = run_command("sysctl -n hw.perflevel0.physicalcpu")
        eff_cores = run_command("sysctl -n hw.perflevel1.physicalcpu")
        if perf_cores:
            info["performance_cores"] = int(perf_cores)
        if eff_cores:
            info["efficiency_cores"] = int(eff_cores)
    elif system == "Linux":
        cpuinfo = Path("/proc/cpuinfo").read_text() if Path("/proc/cpuinfo").exists() else ""
        match = re.search(r"model name\s*:\s*(.+)", cpuinfo)
        if match:
            info["model"] = match.group(1).strip()
    elif system == "Windows":
        wmic = run_command("wmic cpu get name", shell=True)
        if wmic:
            lines = [l.strip() for l in wmic.split('\n') if l.strip() and l.strip() != "Name"]
            if lines:
                info["model"] = lines[0]

    return info


def get_storage_info():
    """Get storage information for the Ollama models directory."""
    info = {}
    system = platform.system()

    # Common Ollama model paths
    if system == "Darwin" or system == "Linux":
        model_path = Path.home() / ".ollama" / "models"
        df_output = run_command(f"df -h {Path.home()}")
    else:
        model_path = Path.home() / ".ollama" / "models"
        df_output = run_command("wmic logicaldisk get size,freespace,caption", shell=True)

    info["ollama_models_path"] = str(model_path)
    info["models_path_exists"] = model_path.exists()

    if df_output:
        info["disk_info_raw"] = df_output

    return info


def check_ollama_installation():
    """Check if Ollama is installed and get version."""
    info = {"installed": False}

    version = run_command("ollama --version")
    if version:
        info["installed"] = True
        info["version"] = version

        # Check running models
        ps_output = run_command("ollama ps")
        if ps_output:
            info["running_models"] = ps_output

        # List available models
        list_output = run_command("ollama list")
        if list_output:
            info["installed_models"] = list_output

    return info


def check_cuda_installation():
    """Check CUDA installation on Linux/Windows."""
    info = {"installed": False}

    nvcc = run_command("nvcc --version")
    if nvcc:
        info["installed"] = True
        match = re.search(r"release (\d+\.\d+)", nvcc)
        if match:
            info["version"] = match.group(1)

    # Check CUDA libraries
    cuda_path = os.environ.get("CUDA_HOME") or os.environ.get("CUDA_PATH")
    if cuda_path:
        info["cuda_path"] = cuda_path

    return info


def get_current_ollama_env():
    """Get current Ollama-related environment variables."""
    ollama_vars = {}
    relevant_vars = [
        "OLLAMA_HOST", "OLLAMA_MODELS", "OLLAMA_KEEP_ALIVE",
        "OLLAMA_NUM_PARALLEL", "OLLAMA_MAX_LOADED_MODELS",
        "OLLAMA_FLASH_ATTENTION", "OLLAMA_KV_CACHE_TYPE",
        "OLLAMA_GPU_OVERHEAD", "OLLAMA_DEBUG",
        "CUDA_VISIBLE_DEVICES", "ROCR_VISIBLE_DEVICES"
    ]

    for var in relevant_vars:
        value = os.environ.get(var)
        if value:
            ollama_vars[var] = value

    return ollama_vars


def main():
    """Main function to collect all system information."""
    system = platform.system()

    result = {
        "os": {
            "system": system,
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine()
        },
        "cpu": get_cpu_info(),
        "memory": get_memory_info(),
        "storage": get_storage_info(),
        "ollama": check_ollama_installation(),
        "current_env_vars": get_current_ollama_env()
    }

    # OS-specific GPU detection
    if system == "Darwin":
        macos_info = get_macos_info()
        result["gpu"] = macos_info.get("gpu", [])
        result["apple_silicon"] = macos_info.get("apple_silicon", False)
        result["metal_support"] = macos_info.get("metal_support", False)
        if macos_info.get("unified_memory_gb"):
            result["unified_memory_gb"] = macos_info["unified_memory_gb"]
    elif system == "Linux":
        result["gpu"] = get_linux_gpu_info()
        result["cuda"] = check_cuda_installation()
    elif system == "Windows":
        result["gpu"] = get_windows_gpu_info()
        result["cuda"] = check_cuda_installation()

    # Calculate recommendations tier
    result["hardware_tier"] = determine_hardware_tier(result)

    print(json.dumps(result, indent=2))


def determine_hardware_tier(info):
    """Determine hardware tier for model recommendations."""
    tier = {
        "category": "cpu_only",
        "max_model_size": "3B",
        "recommended_quant": "Q4_K_M"
    }

    gpus = info.get("gpu", [])

    if info.get("apple_silicon"):
        unified_mem = info.get("unified_memory_gb", 8)
        if unified_mem >= 64:
            tier = {"category": "high_end", "max_model_size": "70B+", "recommended_quant": "Q5_K_M"}
        elif unified_mem >= 32:
            tier = {"category": "workstation", "max_model_size": "32B", "recommended_quant": "Q4_K_M"}
        elif unified_mem >= 16:
            tier = {"category": "prosumer", "max_model_size": "14B", "recommended_quant": "Q4_K_M"}
        else:
            tier = {"category": "entry", "max_model_size": "8B", "recommended_quant": "Q4_K_M"}
    elif gpus:
        max_vram = max((g.get("vram_gb", 0) for g in gpus), default=0)
        if max_vram >= 48:
            tier = {"category": "high_end", "max_model_size": "70B+", "recommended_quant": "Q5_K_M"}
        elif max_vram >= 16:
            tier = {"category": "workstation", "max_model_size": "32B", "recommended_quant": "Q4_K_M"}
        elif max_vram >= 10:
            tier = {"category": "prosumer", "max_model_size": "14B", "recommended_quant": "Q4_K_M"}
        elif max_vram >= 6:
            tier = {"category": "entry", "max_model_size": "8B", "recommended_quant": "Q4_K_M"}
        else:
            tier = {"category": "low_vram", "max_model_size": "3B", "recommended_quant": "Q4_K_M"}

    return tier


if __name__ == "__main__":
    main()
