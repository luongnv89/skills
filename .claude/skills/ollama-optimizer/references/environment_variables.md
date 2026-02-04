# Ollama Environment Variables Reference

## Memory Optimization Variables

### OLLAMA_FLASH_ATTENTION
Enable Flash Attention for faster inference and reduced memory usage.

```bash
# macOS/Linux
export OLLAMA_FLASH_ATTENTION=1

# Windows PowerShell
$env:OLLAMA_FLASH_ATTENTION = "1"
```

**Effect**: Reduces memory footprint by ~10-20%, required for KV cache quantization.

### OLLAMA_KV_CACHE_TYPE
Quantize the key-value cache for aggressive memory reduction.

```bash
# Half memory usage
export OLLAMA_KV_CACHE_TYPE=q8_0

# ~1/3 memory usage (more aggressive)
export OLLAMA_KV_CACHE_TYPE=q4_0
```

**Prerequisite**: Requires `OLLAMA_FLASH_ATTENTION=1`

### OLLAMA_GPU_OVERHEAD
Reserve GPU memory for system overhead (prevents OOM errors).

```bash
export OLLAMA_GPU_OVERHEAD=256m  # Reserve 256MB
```

## GPU Configuration

### CUDA_VISIBLE_DEVICES (NVIDIA)
Select which GPUs Ollama uses.

```bash
export CUDA_VISIBLE_DEVICES=0      # Use first GPU only
export CUDA_VISIBLE_DEVICES=0,1    # Use GPUs 0 and 1
export CUDA_VISIBLE_DEVICES=-1     # Force CPU-only mode
```

### ROCR_VISIBLE_DEVICES (AMD)
Select AMD GPUs for Ollama.

```bash
export ROCR_VISIBLE_DEVICES=0,1
```

## Server Configuration

### OLLAMA_HOST
Configure the server address and port.

```bash
export OLLAMA_HOST=0.0.0.0:11434    # Allow external connections
export OLLAMA_HOST=127.0.0.1:11434  # Localhost only (default)
```

### OLLAMA_ORIGINS
Set CORS allowed origins (for web applications).

```bash
export OLLAMA_ORIGINS="http://localhost:3000,https://myapp.com"
```

### OLLAMA_KEEP_ALIVE
Control how long models stay loaded in memory.

```bash
export OLLAMA_KEEP_ALIVE=5m    # Keep for 5 minutes (default)
export OLLAMA_KEEP_ALIVE=0     # Unload immediately after request
export OLLAMA_KEEP_ALIVE=-1    # Keep loaded forever
```

### OLLAMA_NUM_PARALLEL
Maximum concurrent requests per model.

```bash
export OLLAMA_NUM_PARALLEL=4   # Allow 4 concurrent requests
```

### OLLAMA_MAX_LOADED_MODELS
Maximum models loaded simultaneously.

```bash
export OLLAMA_MAX_LOADED_MODELS=2
```

## Model Storage

### OLLAMA_MODELS
Custom location for model storage.

```bash
export OLLAMA_MODELS=/path/to/models
```

Default locations:
- macOS: `~/.ollama/models`
- Linux: `~/.ollama/models`
- Windows: `%USERPROFILE%\.ollama\models`

## Debug and Logging

### OLLAMA_DEBUG
Enable verbose debug logging.

```bash
export OLLAMA_DEBUG=1
```

## Setting Variables Permanently

### macOS/Linux (bash/zsh)
Add to `~/.bashrc`, `~/.zshrc`, or `~/.profile`:

```bash
export OLLAMA_FLASH_ATTENTION=1
export OLLAMA_KV_CACHE_TYPE=q8_0
```

### macOS (launchd for Ollama.app)
```bash
launchctl setenv OLLAMA_FLASH_ATTENTION 1
```

### Linux (systemd service)
Edit `/etc/systemd/system/ollama.service`:

```ini
[Service]
Environment="OLLAMA_FLASH_ATTENTION=1"
Environment="OLLAMA_KV_CACHE_TYPE=q8_0"
```

Then reload:
```bash
sudo systemctl daemon-reload
sudo systemctl restart ollama
```

### Windows (System Environment Variables)
Use Settings > System > About > Advanced system settings > Environment Variables, or:

```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_FLASH_ATTENTION", "1", "User")
```
