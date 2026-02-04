# Platform-Specific Optimization Guide

## macOS (Apple Silicon)

### System Requirements
- macOS Sonoma 14.0+ (recommended)
- Apple Silicon (M1/M2/M3/M4) for GPU acceleration
- Intel Macs: CPU-only, no Metal acceleration

### Optimization Checklist

1. **Enable Metal GPU acceleration** (automatic on Apple Silicon)
   - Verify: `system_profiler SPDisplaysDataType | grep Metal`

2. **Memory pressure management**
   - Close memory-intensive apps before running large models
   - Monitor with Activity Monitor > Memory > Memory Pressure

3. **Thermal management**
   - Ensure adequate ventilation
   - Consider external cooling for sustained workloads
   - M1/M2 MacBook Air may throttle under load

4. **Recommended environment variables**
   ```bash
   export OLLAMA_FLASH_ATTENTION=1
   # For 8GB Macs running 7B models:
   export OLLAMA_KV_CACHE_TYPE=q8_0
   ```

5. **Model recommendations by Mac**
   | Mac | RAM | Max Model |
   |-----|-----|-----------|
   | M1/M2 MacBook Air 8GB | 8GB | 7B Q4_K_M |
   | M1/M2 Pro 16GB | 16GB | 14B Q4_K_M |
   | M1/M2 Max 32GB | 32GB | 32B Q4_K_M |
   | M2/M3 Ultra 64GB+ | 64GB+ | 70B Q4_K_M |

### Persistent Environment Variables
```bash
# Add to ~/.zshrc or ~/.bashrc
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0

# For Ollama.app (GUI version)
launchctl setenv OLLAMA_FLASH_ATTENTION 1
```

---

## Linux

### System Requirements
- Ubuntu 20.04+, Debian 11+, Fedora 36+, or equivalent
- NVIDIA GPU: Driver 450.80.02+ and CUDA 11.0+
- AMD GPU: ROCm 5.0+

### NVIDIA Setup

1. **Install NVIDIA drivers**
   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt install nvidia-driver-535

   # Verify
   nvidia-smi
   ```

2. **Install CUDA (optional, for development)**
   ```bash
   # Download from NVIDIA
   wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
   sudo dpkg -i cuda-keyring_1.1-1_all.deb
   sudo apt update
   sudo apt install cuda-toolkit-12-4
   ```

3. **Verify GPU detection**
   ```bash
   ollama run llama3.2:3b --verbose 2>&1 | grep -i gpu
   ```

### AMD ROCm Setup

1. **Install ROCm**
   ```bash
   # Ubuntu 22.04
   wget https://repo.radeon.com/amdgpu-install/latest/ubuntu/jammy/amdgpu-install_6.0.60000-1_all.deb
   sudo apt install ./amdgpu-install_6.0.60000-1_all.deb
   sudo amdgpu-install --usecase=rocm
   ```

2. **Add user to render group**
   ```bash
   sudo usermod -aG render,video $USER
   # Log out and back in
   ```

### Systemd Service Optimization
Edit `/etc/systemd/system/ollama.service`:

```ini
[Unit]
Description=Ollama Service
After=network-online.target

[Service]
ExecStart=/usr/local/bin/ollama serve
User=ollama
Group=ollama
Restart=always
RestartSec=3
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
Environment="OLLAMA_HOST=0.0.0.0:11434"

[Install]
WantedBy=default.target
```

Reload and restart:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### CPU-Only Linux Optimization
```bash
export OLLAMA_NUM_PARALLEL=1
export CUDA_VISIBLE_DEVICES=-1  # Force CPU
# Set thread count to physical cores (not hyperthreads)
# Use Modelfile: PARAMETER num_thread 8
```

---

## Windows

### System Requirements
- Windows 10 22H2+ or Windows 11
- NVIDIA GPU: Driver 452.39+
- AMD GPU: Limited support via DirectML

### NVIDIA Setup

1. **Install latest NVIDIA drivers**
   - Download from: https://www.nvidia.com/drivers
   - Or via GeForce Experience

2. **Verify installation**
   ```powershell
   nvidia-smi
   ```

### Environment Variables (PowerShell)

Temporary (current session):
```powershell
$env:OLLAMA_FLASH_ATTENTION = "1"
$env:OLLAMA_KV_CACHE_TYPE = "q8_0"
```

Permanent (user level):
```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "1", "User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_KV_CACHE_TYPE", "q8_0", "User")
```

### Windows-Specific Tips

1. **Disable Windows Defender real-time scanning for model directory**
   - Add exclusion for `%USERPROFILE%\.ollama`

2. **Move models to faster drive**
   ```powershell
   $env:OLLAMA_MODELS = "D:\ollama\models"
   ```

3. **WSL2 considerations**
   - If running Ollama in WSL2, GPU passthrough requires WSL2 GPU support
   - Native Windows installation often performs better

---

## Docker

### NVIDIA GPU Support
```bash
# Install NVIDIA Container Toolkit
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Run Ollama with GPU
docker run -d --gpus all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```

### Docker Compose with Optimization
```yaml
version: '3.8'
services:
  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    environment:
      - OLLAMA_FLASH_ATTENTION=1
      - OLLAMA_KV_CACHE_TYPE=q8_0
      - OLLAMA_HOST=0.0.0.0:11434
    volumes:
      - ollama:/root/.ollama
    ports:
      - "11434:11434"

volumes:
  ollama:
```

### CPU-Only Docker
```bash
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama
```
