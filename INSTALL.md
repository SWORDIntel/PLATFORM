# SWORD Coder MoE Router - Installation Guide

Complete installation guide for the SWORD Coder MoE Router platform with Intel hardware acceleration.

## Table of Contents

- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Verification](#verification)
- [Optional Components](#optional-components)
- [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements

**Minimum:**
- Intel CPU (12th gen Alder Lake or newer recommended for optimal performance)
- 16GB RAM (32GB+ recommended for larger models)
- 50GB free disk space for base installation
- 200GB+ for models (see [Storage Estimates](#storage-estimates))

**Recommended Hardware (for full acceleration):**
- Intel Arc GPU (iGPU or discrete)
- Intel NPU (Neural Processing Unit)
- Intel AMX (Advanced Matrix Extensions) support
- Movidius VPU (optional)
- Hailo-8 accelerator (optional)

### Software Requirements

**Operating System:**
- Ubuntu 22.04 LTS or 24.04 LTS (recommended)
- Fedora 38+
- Arch Linux (rolling release)

**Required:**
- Python 3.8 or higher
- GCC 12 or higher (GCC 13 preferred)
- CMake 3.20 or higher
- Git

**Optional but Recommended:**
- LLVM 16 (will be installed automatically if not present)
- aria2c (for fast parallel downloads)
- Ollama (for uncensored inference via Heretic server)

## Quick Start

### Option 1: Automated Installation (Recommended)

```bash
# Clone the repository
git clone https://github.com/your-org/PLATFORM.git
cd PLATFORM

# Install all system dependencies
bash scripts/install_system_deps.sh

# Verify installation prerequisites
bash scripts/verify_installation.sh

# Run full bootstrap (Python env + Intel stack)
bash bootstrap.sh

# Launch the interactive launcher
./sword_launcher.sh
```

### Option 2: Manual Step-by-Step

```bash
# 1. Install system dependencies
bash scripts/install_system_deps.sh

# 2. Set up Python environment
bash scripts/setup.sh

# 3. Activate virtual environment
source venv/bin/activate

# 4. Build Intel compute stack (optional but recommended for Intel GPUs)
cd IntelStack
bash build_gmmlib.sh
bash build_igc.sh
bash build_compute_runtime.sh
bash install_ipex.sh
cd ..

# 5. Start the router
python main.py
```

## Detailed Installation

### Step 1: System Dependencies

The `install_system_deps.sh` script installs all required system packages:

```bash
bash scripts/install_system_deps.sh
```

This installs:
- **Build tools:** gcc, g++, make, cmake, ninja
- **Development libraries:** libdrm-dev, libpciaccess-dev, libelf-dev
- **Python:** python3, pip, venv
- **Utilities:** git, wget, curl, aria2c, dialog
- **LLVM 16:** Toolchain for Intel Graphics Compiler (IGC)

**Manual installation** (if you prefer):

<details>
<summary>Ubuntu/Debian</summary>

```bash
sudo apt-get update
sudo apt-get install -y \
    build-essential git cmake pkg-config ninja-build \
    python3 python3-pip python3-venv python3-dev \
    gcc-12 g++-12 gcc-13 g++-13 \
    libdrm-dev libpciaccess-dev libelf-dev \
    wget curl aria2 dialog \
    llvm-16 llvm-16-dev clang-16 lld-16
```
</details>

<details>
<summary>Fedora/RHEL</summary>

```bash
sudo dnf install -y \
    @development-tools git cmake pkgconf-pkg-config ninja-build \
    python3 python3-pip python3-virtualenv python3-devel \
    gcc gcc-c++ \
    libdrm-devel libpciaccess-devel libelf-devel \
    wget curl aria2 dialog \
    llvm16.0 llvm16.0-devel clang16 lld16
```
</details>

<details>
<summary>Arch Linux</summary>

```bash
sudo pacman -Sy --noconfirm \
    base-devel git cmake pkgconf ninja \
    python python-pip python-virtualenv \
    gcc \
    libdrm libpciaccess libelf \
    wget curl aria2 dialog \
    llvm16 clang16 lld
```
</details>

### Step 2: Verify Prerequisites

Run the verification script to check if all dependencies are installed:

```bash
bash scripts/verify_installation.sh
```

This script checks:
- ✓ System tools and compilers
- ✓ Python environment
- ✓ Development libraries
- ✓ Hardware detection (GPU, NPU, VPU)
- ✓ Intel compute stack components
- ✓ Optional tools (Ollama, Docker, etc.)

**Expected output:**
- **0 errors, 0 warnings**: Perfect! Ready to install.
- **0 errors, N warnings**: Ready to install, some optional components missing.
- **N errors**: Fix the errors before proceeding.

### Step 3: Python Environment Setup

Create and configure the Python virtual environment:

```bash
bash scripts/setup.sh
```

This script:
- Creates a Python virtual environment (`venv/`)
- Installs all Python dependencies from `requirements.txt`
- Detects available hardware (NPU, GPU, Movidius, Hailo)
- Verifies MCP servers and quantization pipeline
- Creates necessary directories (`logs/`, `cache/`, `models/`)

**Activate the environment:**
```bash
source venv/bin/activate
```

### Step 4: Intel Compute Stack (Optional)

**Skip this step if:**
- You don't have an Intel GPU
- You only plan to use CPU inference
- You already have Intel drivers installed

**Required for:**
- Intel Arc GPU acceleration
- Intel iGPU (integrated graphics) acceleration
- Intel NPU offloading
- PyTorch XPU support via IPEX

#### Build Order (Important!)

The Intel compute stack has dependencies that must be built in this order:

1. **GMMLIB** (Graphics Memory Management Library)
2. **IGC** (Intel Graphics Compiler) - requires LLVM 16
3. **Compute Runtime** (NEO) - the OpenCL/Level Zero runtime
4. **IPEX** (Intel Extension for PyTorch)

```bash
cd IntelStack

# 1. Build GMMLIB
bash build_gmmlib.sh

# 2. Build IGC (this takes 30-60 minutes on first build)
bash build_igc.sh

# 3. Build Compute Runtime
bash build_compute_runtime.sh

# 4. Install IPEX
bash install_ipex.sh

cd ..
```

**What each script does:**

- **`build_gmmlib.sh`**: Builds the Graphics Memory Management Library
  - Clones from: https://github.com/intel/gmmlib
  - Build time: ~5 minutes
  - Output: `/usr/local/lib/libigdgmm.so`

- **`build_igc.sh`**: Builds the Intel Graphics Compiler
  - Automatically installs LLVM 16 if not present
  - Tries prebuilt binaries first, then falls back to source build
  - Build time: 30-60 minutes (source), 5 minutes (prebuilt)
  - Output: `/usr/local/lib/libigc.so`, `/usr/local/lib/libiga64.so`

- **`build_compute_runtime.sh`**: Builds the Intel OpenCL/Level Zero runtime
  - Clones from: https://github.com/intel/compute-runtime
  - Build time: ~15 minutes
  - Output: `/usr/local/lib/intel-opencl/libigdrcl.so`

- **`install_ipex.sh`**: Installs PyTorch 2.8.0 and IPEX 2.8.0
  - Downloads from PyPI
  - Install time: ~5 minutes
  - Output: Python packages in venv

**Total build time:** 1-2 hours (first time), 30 minutes (with prebuilt LLVM)

#### Verify Intel Stack

```bash
# Check if libraries are installed
ldconfig -p | grep -E "igdgmm|igc|igdrcl"

# Verify PyTorch XPU support
python IntelStack/verify_xpu.py
```

**Expected output:**
```
PyTorch version: 2.8.0
IPEX version: 2.8.0
XPU available: True
XPU device count: 1
XPU device name: Intel(R) Arc(TM) Graphics
```

### Step 5: Make Scripts Executable

Ensure all scripts have execute permissions:

```bash
chmod +x bootstrap.sh sword_launcher.sh
chmod +x scripts/*.sh
chmod +x IntelStack/*.sh
chmod +x IntelStack/meteor_lake_flags_ultimate/*.sh
```

### Step 6: Start the Platform

#### Option A: Interactive Launcher (Recommended)

```bash
./sword_launcher.sh
```

Features:
- **Run**: Start the MoE Router
- **IDE**: Launch the Self-Coding IDE (Textual TUI)
- **SelfCode**: Interactive self-coding session
- **Codebreaker**: Analyze encoded payloads
- **Download**: Download models from registry
- **Quantize**: Run quantization pipeline
- **Bootstrap**: Build Intel compute stack
- **Test**: Test MCP servers

#### Option B: Direct Commands

```bash
# Start router
python main.py

# Launch IDE
python main.py --ide

# Self-coding session
python main.py --self-code

# Run benchmarks
python main.py --benchmark

# Codebreaker mode
python main.py --codebreaker --devices all
```

## Verification

### Health Check

```bash
# Check if router is running
curl http://127.0.0.1:8000/docs

# Test MCP servers
python main.py --mcp-test

# Run benchmarks
python main.py --benchmark
```

### Storage Estimates

```bash
python main.py --storage
```

**Example output:**
```
Storage Estimates:
============================================================
Total FP32: 1369.0 GB (1.34 TB)
Total INT4: 171.0 GB
Savings:    1198.0 GB
Compression: 8.0x

Per-model breakdown:
  deepseek-r1-1.5b                6.0 GB ->  0.75 GB (8.0x)
  phi-3-mini                     15.2 GB ->  1.90 GB (8.0x)
  deepseek-coder-6.7b            26.8 GB ->  3.35 GB (8.0x)
  ...
```

## Optional Components

### Ollama (for Heretic Server)

Ollama provides uncensored inference capabilities via the Heretic MCP server.

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Start Ollama service
ollama serve

# Pull recommended models
ollama pull wizardlm-uncensored:13b
ollama pull dolphin-mixtral:8x7b
```

Verify:
```bash
curl http://localhost:11434/api/tags
```

### SUPERCOP (for Crypto Benchmarking)

Required for Simon/Speck cipher benchmarking in Codebreaker mode.

```bash
# Clone SUPERCOP
git clone https://github.com/crypto-rb/supercop ~/supercop

# Build (this takes a while)
cd ~/supercop
./do
```

Usage:
```bash
python main.py --codebreaker --crypto-bench --supercop-path ~/supercop
```

### Meteor Lake Optimization Flags

Install CPU-specific optimization flags for Meteor Lake processors:

```bash
bash IntelStack/meteor_lake_flags_ultimate/install.sh
source ~/.bashrc
```

This sets up:
- `-march=meteorlake`
- AVX-512 optimizations
- Cache prefetch tuning
- Intel AMX flags

## Troubleshooting

### Common Issues

<details>
<summary><strong>Issue:</strong> <code>ModuleNotFoundError: No module named 'openvino'</code></summary>

**Solution:**
```bash
source venv/bin/activate
pip install -r requirements.txt
```
</details>

<details>
<summary><strong>Issue:</strong> <code>libigdgmm.so: cannot open shared object file</code></summary>

**Solution:**
```bash
# Add /usr/local/lib to library path
echo 'export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
source ~/.bashrc

# Update ldconfig
sudo ldconfig
```
</details>

<details>
<summary><strong>Issue:</strong> <code>Intel GPU not detected</code></summary>

**Solutions:**
1. Check if kernel module is loaded:
   ```bash
   lsmod | grep -E "i915|xe"
   ```
   If not loaded:
   ```bash
   sudo modprobe i915  # or: sudo modprobe xe
   ```

2. Check if GPU is visible:
   ```bash
   lspci | grep -i "intel.*graphics"
   ```

3. Reboot after driver installation
</details>

<details>
<summary><strong>Issue:</strong> <code>LLVM 16 not found during IGC build</code></summary>

**Solution:**
The IGC build script will automatically download and build LLVM 16 from source. This is normal and takes 30-60 minutes. Alternatively, install manually:

```bash
# Ubuntu
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 16
```
</details>

<details>
<summary><strong>Issue:</strong> <code>aria2c not found</code></summary>

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install -y aria2

# Fedora
sudo dnf install -y aria2

# Arch
sudo pacman -S aria2
```

Or use wget/curl instead (slower):
```bash
# Downloads will work but be slower
```
</details>

<details>
<summary><strong>Issue:</strong> <code>dialog not found</code></summary>

**Solution:**
```bash
# Ubuntu/Debian
sudo apt-get install -y dialog

# Fedora
sudo dnf install -y dialog

# Arch
sudo pacman -S dialog
```
</details>

### Getting Help

1. **Run verification script:**
   ```bash
   bash scripts/verify_installation.sh
   ```

2. **Check logs:**
   ```bash
   tail -f logs/*.log
   ```

3. **Report issues:**
   - GitHub Issues: https://github.com/your-org/PLATFORM/issues
   - Include output from `verify_installation.sh`
   - Include OS version: `cat /etc/os-release`

## Advanced Configuration

### Custom Model Registry

Edit `config/models.yaml` to add custom models:

```yaml
models:
  custom:
    my-model:
      canonical: "namespace/model-name"
      params_b: 7.0
      fp32_gb: 28.0
      quantization: "int4"
      device_pool: ["igpu", "amx"]
```

### Hardware Configuration

Edit `config/hardware.yaml` to configure device priorities and thresholds.

### MCP Server Configuration

Edit `config/mcp_servers.yaml` to configure Model Context Protocol servers.

## Next Steps

1. **Download models:**
   ```bash
   ./sword_launcher.sh
   # Select "Download" from menu
   ```

2. **Quantize models:**
   ```bash
   python scripts/run_quantization.py
   ```

3. **Start coding:**
   ```bash
   python main.py --ide
   ```

4. **Read the docs:**
   - [SELF_CODING.md](SELF_CODING.md) - Self-coding agent guide
   - [GEMINI.md](GEMINI.md) - Full documentation
   - [AGENTS.md](AGENTS.md) - Agent architecture

## License

See [LICENSE](LICENSE) for details.
