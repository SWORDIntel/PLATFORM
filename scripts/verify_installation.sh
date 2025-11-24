#!/usr/bin/env bash
# SWORD Coder Installation Verification Script
# Comprehensive pre-flight and post-installation checks

set -eo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

check_pass() {
    echo -e "${GREEN}✓${NC} $1"
}

check_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

check_fail() {
    echo -e "${RED}✗${NC} $1"
    ((ERRORS++))
}

check_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# ============================================================
# 1. SYSTEM REQUIREMENTS
# ============================================================
header "System Requirements"

# Check OS
if [[ -f /etc/os-release ]]; then
    . /etc/os-release
    check_pass "OS: $NAME $VERSION"
else
    check_warn "Could not detect OS version"
fi

# Check architecture
ARCH=$(uname -m)
if [[ "$ARCH" == "x86_64" ]]; then
    check_pass "Architecture: $ARCH"
else
    check_warn "Architecture: $ARCH (Intel optimizations target x86_64)"
fi

# Check kernel
KERNEL=$(uname -r)
check_info "Kernel: $KERNEL"

# ============================================================
# 2. PACKAGE MANAGERS
# ============================================================
header "Package Managers"

if command -v apt-get &>/dev/null; then
    check_pass "apt-get available"
elif command -v dnf &>/dev/null; then
    check_pass "dnf available"
elif command -v pacman &>/dev/null; then
    check_pass "pacman available"
else
    check_fail "No supported package manager found (apt-get, dnf, or pacman)"
fi

# ============================================================
# 3. SYSTEM TOOLS
# ============================================================
header "Essential System Tools"

# Build tools
for tool in gcc g++ make cmake git; do
    if command -v "$tool" &>/dev/null; then
        VERSION=$($tool --version 2>/dev/null | head -1)
        check_pass "$tool: $VERSION"
    else
        check_fail "$tool not found"
    fi
done

# GCC versions
for gcc_ver in gcc-12 g++-12 gcc-13 g++-13; do
    if command -v "$gcc_ver" &>/dev/null; then
        VERSION=$($gcc_ver --version 2>/dev/null | head -1)
        check_pass "$gcc_ver: $VERSION"
    else
        check_warn "$gcc_ver not found (recommended but not required)"
    fi
done

# pkg-config
if command -v pkg-config &>/dev/null; then
    check_pass "pkg-config available"
else
    check_fail "pkg-config not found"
fi

# Ninja (optional but recommended)
if command -v ninja &>/dev/null; then
    VERSION=$(ninja --version 2>/dev/null)
    check_pass "ninja: $VERSION (optional build accelerator)"
else
    check_warn "ninja not found (optional, but speeds up builds)"
fi

# ============================================================
# 4. PYTHON ENVIRONMENT
# ============================================================
header "Python Environment"

# Python
if command -v python3 &>/dev/null; then
    PY_VERSION=$(python3 --version 2>&1)
    check_pass "$PY_VERSION"

    # Check Python version is >= 3.8
    PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
    PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
    if [[ $PY_MAJOR -ge 3 ]] && [[ $PY_MINOR -ge 8 ]]; then
        check_pass "Python version >= 3.8"
    else
        check_fail "Python 3.8+ required (found $PY_MAJOR.$PY_MINOR)"
    fi
else
    check_fail "python3 not found"
fi

# pip
if command -v pip3 &>/dev/null; then
    PIP_VERSION=$(pip3 --version 2>&1)
    check_pass "pip3: $PIP_VERSION"
else
    check_fail "pip3 not found"
fi

# Virtual environment
if [[ -d "venv" ]] || [[ -d ".venv" ]]; then
    VENV_DIR="venv"
    [[ -d ".venv" ]] && VENV_DIR=".venv"
    check_pass "Virtual environment found: $VENV_DIR"

    # Check if activated
    if [[ -n "${VIRTUAL_ENV:-}" ]]; then
        check_pass "Virtual environment activated: $VIRTUAL_ENV"
    else
        check_warn "Virtual environment not activated (run: source $VENV_DIR/bin/activate)"
    fi
else
    check_warn "No virtual environment found (will be created by setup.sh)"
fi

# ============================================================
# 5. DOWNLOAD TOOLS
# ============================================================
header "Download Tools"

for tool in wget curl; do
    if command -v "$tool" &>/dev/null; then
        check_pass "$tool available"
    else
        check_fail "$tool not found"
    fi
done

if command -v aria2c &>/dev/null; then
    VERSION=$(aria2c --version 2>/dev/null | head -1)
    check_pass "aria2c: $VERSION (for fast parallel downloads)"
else
    check_warn "aria2c not found (recommended for model downloads)"
fi

# ============================================================
# 6. TUI TOOLS
# ============================================================
header "TUI Tools"

if command -v dialog &>/dev/null; then
    check_pass "dialog available (required for launcher TUI)"
else
    check_warn "dialog not found (required for ./sword_launcher.sh)"
fi

# ============================================================
# 7. DEVELOPMENT LIBRARIES
# ============================================================
header "Development Libraries"

# Check for library headers via pkg-config
for lib in libdrm; do
    if pkg-config --exists "$lib" 2>/dev/null; then
        VERSION=$(pkg-config --modversion "$lib" 2>/dev/null)
        check_pass "$lib: $VERSION"
    else
        check_warn "$lib development files not found (required for Intel stack builds)"
    fi
done

# Check for specific header files
HEADERS=(
    "/usr/include/drm/drm.h:libdrm-dev"
    "/usr/include/pciaccess.h:libpciaccess-dev"
    "/usr/include/libelf.h:libelf-dev"
)

for entry in "${HEADERS[@]}"; do
    IFS=':' read -r header package <<< "$entry"
    if [[ -f "$header" ]]; then
        check_pass "$(basename $header) found"
    else
        check_warn "$package not installed (required for Intel stack)"
    fi
done

# ============================================================
# 8. LLVM TOOLCHAIN
# ============================================================
header "LLVM Toolchain"

# Check for LLVM 16
if [[ -d "/usr/lib/llvm-16" ]]; then
    check_pass "LLVM 16 system installation found"
    if [[ -f "/usr/lib/llvm-16/bin/clang" ]]; then
        VERSION=$(/usr/lib/llvm-16/bin/clang --version | head -1)
        check_pass "clang-16: $VERSION"
    fi
elif command -v llvm-config-16 &>/dev/null; then
    VERSION=$(llvm-config-16 --version)
    check_pass "LLVM 16: $VERSION"
else
    check_warn "LLVM 16 not found (will be installed by IGC build script)"
fi

# ============================================================
# 9. PYTHON PACKAGES
# ============================================================
header "Python Packages"

if [[ -n "${VIRTUAL_ENV:-}" ]] || command -v python3 &>/dev/null; then
    # Core packages
    for package in fastapi uvicorn pydantic yaml rich textual anthropic; do
        if python3 -c "import $package" 2>/dev/null; then
            VERSION=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "installed")
            check_pass "$package: $VERSION"
        else
            check_warn "$package not installed (will be installed by setup.sh)"
        fi
    done

    # Intel packages
    for package in openvino torch transformers; do
        if python3 -c "import $package" 2>/dev/null; then
            VERSION=$(python3 -c "import $package; print($package.__version__)" 2>/dev/null || echo "installed")
            check_pass "$package: $VERSION"
        else
            check_warn "$package not installed (will be installed by setup.sh)"
        fi
    done

    # Check for intel_extension_for_pytorch (IPEX)
    if python3 -c "import intel_extension_for_pytorch as ipex" 2>/dev/null; then
        VERSION=$(python3 -c "import intel_extension_for_pytorch as ipex; print(ipex.__version__)" 2>/dev/null || echo "installed")
        check_pass "intel-extension-for-pytorch: $VERSION"
    else
        check_warn "IPEX not installed (will be installed by IntelStack/install_ipex.sh)"
    fi
else
    check_info "Skipping Python package checks (no active environment)"
fi

# ============================================================
# 10. HARDWARE DETECTION
# ============================================================
header "Hardware Detection"

# lspci check
if ! command -v lspci &>/dev/null; then
    check_warn "lspci not found (install pciutils for hardware detection)"
else
    # Intel GPU
    if lspci 2>/dev/null | grep -qi "intel.*graphics\|intel.*arc"; then
        GPU_INFO=$(lspci 2>/dev/null | grep -i "intel.*graphics\|intel.*arc" | head -1)
        check_pass "Intel GPU detected: $GPU_INFO"
    else
        check_warn "Intel GPU not detected"
    fi

    # NPU
    if lspci 2>/dev/null | grep -qi "neural\|npu"; then
        NPU_INFO=$(lspci 2>/dev/null | grep -i "neural\|npu" | head -1)
        check_pass "NPU detected: $NPU_INFO"
    else
        check_warn "NPU not detected"
    fi

    # Movidius VPU
    MOVIDIUS_COUNT=$(lspci 2>/dev/null | grep -ci "movidius\|myriad" || echo "0")
    if [ "$MOVIDIUS_COUNT" -gt 0 ]; then
        check_pass "Movidius VPU detected: ${MOVIDIUS_COUNT}x"
    else
        check_warn "Movidius VPU not detected"
    fi

    # Hailo-8
    if lspci 2>/dev/null | grep -qi "hailo"; then
        HAILO_INFO=$(lspci 2>/dev/null | grep -i "hailo" | head -1)
        check_pass "Hailo-8 detected: $HAILO_INFO"
    else
        check_warn "Hailo-8 not detected"
    fi
fi

# Kernel modules
if command -v lsmod &>/dev/null; then
    if lsmod | grep -q "^i915\|^xe"; then
        MODULE=$(lsmod | grep "^i915\|^xe" | awk '{print $1}')
        check_pass "Intel GPU kernel module loaded: $MODULE"
    else
        check_warn "Intel GPU kernel module (i915 or xe) not loaded"
    fi
fi

# ============================================================
# 11. INTEL COMPUTE STACK
# ============================================================
header "Intel Compute Stack"

# Check for Intel compute runtime libraries
if ldconfig -p 2>/dev/null | grep -q "libze_loader"; then
    check_pass "Intel Level Zero loader found"
else
    check_warn "Intel Level Zero loader not found (install via IntelStack scripts)"
fi

if ldconfig -p 2>/dev/null | grep -q "libigdgmm"; then
    check_pass "Intel GMMLIB found"
else
    check_warn "Intel GMMLIB not found (install via IntelStack/build_gmmlib.sh)"
fi

# Check for clinfo (OpenCL)
if command -v clinfo &>/dev/null; then
    if clinfo 2>/dev/null | grep -q "Intel"; then
        check_pass "Intel OpenCL runtime detected"
    else
        check_warn "Intel OpenCL runtime not found"
    fi
else
    check_info "clinfo not installed (optional: sudo apt install clinfo)"
fi

# ============================================================
# 12. OPTIONAL TOOLS
# ============================================================
header "Optional Tools"

# Ollama
if command -v ollama &>/dev/null; then
    VERSION=$(ollama --version 2>/dev/null || echo "installed")
    check_pass "Ollama: $VERSION (for Heretic server)"

    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags &>/dev/null; then
        MODEL_COUNT=$(ollama list 2>/dev/null | tail -n +2 | wc -l || echo "0")
        check_pass "Ollama running with $MODEL_COUNT models"
    else
        check_warn "Ollama installed but not running (start with: ollama serve)"
    fi
else
    check_info "Ollama not installed (optional, for uncensored inference)"
fi

# Docker (not used but good to check)
if command -v docker &>/dev/null; then
    VERSION=$(docker --version 2>/dev/null)
    check_info "Docker: $VERSION (not required)"
else
    check_info "Docker not installed (not required)"
fi

# ============================================================
# 13. PROJECT FILES
# ============================================================
header "Project Files"

# Check critical files
CRITICAL_FILES=(
    "requirements.txt"
    "main.py"
    "bootstrap.sh"
    "scripts/setup.sh"
    "sword_launcher.sh"
    "IntelStack/build_gmmlib.sh"
    "IntelStack/build_igc.sh"
    "IntelStack/build_compute_runtime.sh"
    "IntelStack/install_ipex.sh"
    "config/models.yaml"
    "config/hardware.yaml"
)

for file in "${CRITICAL_FILES[@]}"; do
    if [[ -f "$file" ]]; then
        check_pass "$file exists"
    else
        check_fail "$file missing"
    fi
done

# Check directories
CRITICAL_DIRS=(
    "src"
    "scripts"
    "config"
    "IntelStack"
)

for dir in "${CRITICAL_DIRS[@]}"; do
    if [[ -d "$dir" ]]; then
        check_pass "$dir/ directory exists"
    else
        check_fail "$dir/ directory missing"
    fi
done

# ============================================================
# 14. PERMISSIONS
# ============================================================
header "Permissions"

# Check if scripts are executable
SCRIPTS=(
    "bootstrap.sh"
    "scripts/setup.sh"
    "sword_launcher.sh"
    "IntelStack/build_gmmlib.sh"
    "IntelStack/build_igc.sh"
    "IntelStack/build_compute_runtime.sh"
    "IntelStack/install_ipex.sh"
)

for script in "${SCRIPTS[@]}"; do
    if [[ -x "$script" ]]; then
        check_pass "$script is executable"
    else
        check_warn "$script not executable (run: chmod +x $script)"
    fi
done

# ============================================================
# SUMMARY
# ============================================================
header "Summary"

if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
    echo -e "${GREEN}✓ All checks passed!${NC}"
    echo -e "${GREEN}System is ready for installation.${NC}"
    exit 0
elif [[ $ERRORS -eq 0 ]]; then
    echo -e "${YELLOW}⚠ $WARNINGS warnings found${NC}"
    echo -e "${YELLOW}System is mostly ready, but some optional components are missing.${NC}"
    echo -e "${YELLOW}You can proceed with installation.${NC}"
    exit 0
else
    echo -e "${RED}✗ $ERRORS errors, $WARNINGS warnings${NC}"
    echo -e "${RED}Please fix the errors before proceeding with installation.${NC}"
    exit 1
fi
