#!/usr/bin/env bash
# SWORD Coder System Dependencies Installer
# Installs ALL system-level dependencies in one go

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

header() {
    echo ""
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

# Check if running as root
if [[ $EUID -eq 0 ]] && [[ -z "${SUDO_USER:-}" ]]; then
    warn "Running as root without sudo. Consider running as regular user with sudo."
fi

header "SWORD Coder System Dependencies Installer"

# Detect package manager
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
    UPDATE_CMD="sudo apt-get update"
    INSTALL_CMD="sudo apt-get install -y"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
    UPDATE_CMD="sudo dnf check-update || true"
    INSTALL_CMD="sudo dnf install -y"
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
    UPDATE_CMD="sudo pacman -Sy"
    INSTALL_CMD="sudo pacman -S --noconfirm"
else
    error "No supported package manager found (apt, dnf, or pacman)"
    exit 1
fi

info "Detected package manager: $PKG_MGR"

# ============================================================
# 1. UPDATE PACKAGE LISTS
# ============================================================
header "Updating Package Lists"
info "Running: $UPDATE_CMD"
eval "$UPDATE_CMD"
success "Package lists updated"

# ============================================================
# 2. ESSENTIAL BUILD TOOLS
# ============================================================
header "Installing Essential Build Tools"

case $PKG_MGR in
    apt)
        $INSTALL_CMD \
            build-essential \
            git \
            cmake \
            pkg-config \
            ninja-build \
            wget \
            curl \
            lsb-release \
            gnupg \
            pciutils \
            lshw
        ;;
    dnf)
        $INSTALL_CMD \
            @development-tools \
            git \
            cmake \
            pkgconf-pkg-config \
            ninja-build \
            wget \
            curl \
            redhat-lsb-core \
            gnupg2 \
            pciutils \
            lshw
        ;;
    pacman)
        $INSTALL_CMD \
            base-devel \
            git \
            cmake \
            pkgconf \
            ninja \
            wget \
            curl \
            lsb-release \
            gnupg \
            pciutils \
            lshw
        ;;
esac

success "Essential build tools installed"

# ============================================================
# 3. GCC/G++ SPECIFIC VERSIONS
# ============================================================
header "Installing GCC/G++ Compilers"

case $PKG_MGR in
    apt)
        # Install gcc-12, g++-12 (required)
        $INSTALL_CMD gcc-12 g++-12 || warn "gcc-12/g++-12 not available"

        # Try to install gcc-13, g++-13 (preferred for IGC)
        $INSTALL_CMD gcc-13 g++-13 || warn "gcc-13/g++-13 not available (will fall back to gcc-12)"
        ;;
    dnf)
        # Fedora/RHEL typically has latest GCC
        $INSTALL_CMD gcc gcc-c++ || error "Failed to install GCC"
        ;;
    pacman)
        # Arch has rolling release GCC
        $INSTALL_CMD gcc || error "Failed to install GCC"
        ;;
esac

success "GCC compilers installed"

# ============================================================
# 4. DEVELOPMENT LIBRARIES
# ============================================================
header "Installing Development Libraries"

case $PKG_MGR in
    apt)
        $INSTALL_CMD \
            libdrm-dev \
            libpciaccess-dev \
            libelf-dev \
            zlib1g-dev \
            libssl-dev \
            libffi-dev \
            libbz2-dev \
            libreadline-dev \
            libsqlite3-dev \
            libncurses5-dev \
            libncursesw5-dev \
            xz-utils \
            tk-dev \
            liblzma-dev
        ;;
    dnf)
        $INSTALL_CMD \
            libdrm-devel \
            libpciaccess-devel \
            libelf-devel \
            zlib-devel \
            openssl-devel \
            libffi-devel \
            bzip2-devel \
            readline-devel \
            sqlite-devel \
            ncurses-devel \
            xz-devel \
            tk-devel
        ;;
    pacman)
        $INSTALL_CMD \
            libdrm \
            libpciaccess \
            libelf \
            zlib \
            openssl \
            libffi \
            bzip2 \
            readline \
            sqlite \
            ncurses \
            xz \
            tk
        ;;
esac

success "Development libraries installed"

# ============================================================
# 5. PYTHON 3
# ============================================================
header "Installing Python 3"

case $PKG_MGR in
    apt)
        $INSTALL_CMD \
            python3 \
            python3-pip \
            python3-venv \
            python3-dev
        ;;
    dnf)
        $INSTALL_CMD \
            python3 \
            python3-pip \
            python3-virtualenv \
            python3-devel
        ;;
    pacman)
        $INSTALL_CMD \
            python \
            python-pip \
            python-virtualenv
        ;;
esac

success "Python 3 installed"

# ============================================================
# 6. DOWNLOAD TOOLS
# ============================================================
header "Installing Download Tools"

case $PKG_MGR in
    apt)
        $INSTALL_CMD aria2 || warn "aria2 not available in default repos"
        ;;
    dnf)
        $INSTALL_CMD aria2 || warn "aria2 not available in default repos"
        ;;
    pacman)
        $INSTALL_CMD aria2 || warn "aria2 not available in default repos"
        ;;
esac

if command -v aria2c &>/dev/null; then
    success "aria2 installed"
else
    warn "aria2 not installed (required for fast model downloads)"
    info "You can install it later or use wget/curl instead"
fi

# ============================================================
# 7. TUI TOOLS
# ============================================================
header "Installing TUI Tools"

case $PKG_MGR in
    apt)
        $INSTALL_CMD dialog
        ;;
    dnf)
        $INSTALL_CMD dialog
        ;;
    pacman)
        $INSTALL_CMD dialog
        ;;
esac

success "TUI tools installed"

# ============================================================
# 8. LLVM 16 (OPTIONAL BUT RECOMMENDED)
# ============================================================
header "Installing LLVM 16"

if [[ "$PKG_MGR" == "apt" ]]; then
    info "Attempting to install LLVM 16 from system repos..."

    # Try direct install first
    if $INSTALL_CMD llvm-16 llvm-16-dev clang-16 lld-16 2>/dev/null; then
        success "LLVM 16 installed from system repos"
    else
        warn "LLVM 16 not available in default repos"
        info "Attempting to add LLVM apt repository..."

        # Try using the LLVM install script
        TMP_SCRIPT=$(mktemp)
        if wget -O "$TMP_SCRIPT" https://apt.llvm.org/llvm.sh 2>/dev/null; then
            chmod +x "$TMP_SCRIPT"
            if sudo "$TMP_SCRIPT" 16 2>/dev/null; then
                success "LLVM 16 installed via apt.llvm.org"
                $INSTALL_CMD llvm-16 llvm-16-dev clang-16 lld-16 || warn "Post-script install failed"
            else
                warn "LLVM install script failed"
            fi
            rm -f "$TMP_SCRIPT"
        else
            warn "Could not download LLVM install script"
        fi

        if ! command -v llvm-config-16 &>/dev/null && [[ ! -d "/usr/lib/llvm-16" ]]; then
            warn "LLVM 16 installation failed"
            info "Don't worry - the IGC build script will install LLVM 16 from source if needed"
        fi
    fi
elif [[ "$PKG_MGR" == "dnf" ]]; then
    $INSTALL_CMD llvm16.0 llvm16.0-devel clang16 lld16 || warn "LLVM 16 not available (will be built from source)"
elif [[ "$PKG_MGR" == "pacman" ]]; then
    $INSTALL_CMD llvm16 clang16 lld || warn "LLVM 16 not available (will be built from source)"
fi

if command -v llvm-config-16 &>/dev/null || [[ -d "/usr/lib/llvm-16" ]]; then
    success "LLVM 16 available"
else
    info "LLVM 16 will be built from source during IGC compilation"
fi

# ============================================================
# 9. OPENCL TOOLS (OPTIONAL)
# ============================================================
header "Installing OpenCL Tools (Optional)"

case $PKG_MGR in
    apt)
        $INSTALL_CMD clinfo ocl-icd-libopencl1 opencl-headers || warn "OpenCL tools not available"
        ;;
    dnf)
        $INSTALL_CMD clinfo ocl-icd ocl-icd-devel opencl-headers || warn "OpenCL tools not available"
        ;;
    pacman)
        $INSTALL_CMD clinfo ocl-icd opencl-headers || warn "OpenCL tools not available"
        ;;
esac

if command -v clinfo &>/dev/null; then
    success "clinfo installed (useful for debugging OpenCL)"
else
    info "clinfo not installed (optional)"
fi

# ============================================================
# 10. ADDITIONAL UTILITIES
# ============================================================
header "Installing Additional Utilities"

case $PKG_MGR in
    apt)
        $INSTALL_CMD \
            htop \
            vim \
            tree \
            jq \
            tmux \
            screen || warn "Some optional utilities not available"
        ;;
    dnf)
        $INSTALL_CMD \
            htop \
            vim-enhanced \
            tree \
            jq \
            tmux \
            screen || warn "Some optional utilities not available"
        ;;
    pacman)
        $INSTALL_CMD \
            htop \
            vim \
            tree \
            jq \
            tmux \
            screen || warn "Some optional utilities not available"
        ;;
esac

success "Additional utilities installed"

# ============================================================
# SUMMARY
# ============================================================
header "Installation Complete"

success "All system dependencies have been installed!"
echo ""
info "Next steps:"
echo "  1. Make scripts executable:"
echo "     chmod +x bootstrap.sh scripts/*.sh sword_launcher.sh IntelStack/*.sh"
echo ""
echo "  2. Run verification script:"
echo "     bash scripts/verify_installation.sh"
echo ""
echo "  3. Set up Python environment:"
echo "     bash scripts/setup.sh"
echo ""
echo "  4. Build Intel compute stack (if needed):"
echo "     bash bootstrap.sh"
echo ""
echo "  OR use the interactive launcher:"
echo "     ./sword_launcher.sh"
echo ""

info "System dependency installation completed successfully!"
