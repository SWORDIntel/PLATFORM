#!/bin/bash
#
# SWORD Launcher Script (TUI Edition)
# A master script to manage the SWORD Coder MoE Router project.
#

set -eo pipefail
PROJECT_ROOT=$(dirname "$(readlink -f "$0")")
cd "$PROJECT_ROOT"
VENV_DIR=""
SELF_TEST=0

# --- Colors and Formatting ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info() {
    echo -e "${BLUE}INFO:${NC} $1"
}

warn() {
    echo -e "${YELLOW}WARN:${NC} $1"
}

error() {
    echo -e "${RED}ERROR:${NC} $1" >&2
    exit 1
}

ensure_sys_deps() {
    # Install common system dependencies for builds and tooling.
    if command -v apt-get &>/dev/null; then
        sudo apt-get update
        sudo apt-get install -y \
            build-essential git cmake pkg-config ninja-build \
            python3 python3-venv python3-pip \
            wget curl lsb-release gnupg \
            gcc-12 g++-12 libdrm-dev libpciaccess-dev libelf-dev
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y \
            @development-tools git cmake pkgconf-pkg-config ninja-build \
            python3 python3-virtualenv python3-pip \
            wget curl redhat-lsb-core gnupg2 \
            gcc gcc-c++ libdrm-devel libpciaccess-devel libelf-devel
    elif command -v pacman &>/dev/null; then
        sudo pacman -Sy --noconfirm \
            base-devel git cmake pkgconf ninja \
            python python-virtualenv python-pip \
            wget curl lsb-release gnupg \
            gcc libdrm libpciaccess libelf
    fi
}

ensure_venv() {
    # Detect or create a virtual environment, then activate it.
    if [ -z "$VENV_DIR" ]; then
        if [ -d "venv" ]; then
            VENV_DIR="venv"
        elif [ -d ".venv" ]; then
            VENV_DIR=".venv"
        else
            info "Virtual environment not found. Running ./scripts/setup.sh..."
            if [ "$EUID" -eq 0 ] && [ -n "$SUDO_USER" ] && [ "$SUDO_USER" != "root" ]; then
                info "Detected sudo; creating venv as ${SUDO_USER} to avoid root-owned installs."
                sudo -u "$SUDO_USER" -H bash -c "cd \"$PROJECT_ROOT\" && bash scripts/setup.sh"
            else
                bash scripts/setup.sh
            fi
            VENV_DIR="venv"
        fi
    fi

    # Safety: if setup failed to create the venv, bail out.
    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment still missing after setup. Please check ./scripts/setup.sh output."
    fi

    # shellcheck source=/dev/null
    source "$VENV_DIR/bin/activate"
}

print_header() {
    echo -e "\n${YELLOW}=====================================================${NC}"
    echo -e "${YELLOW} $1${NC}"
    echo -e "${YELLOW}=====================================================${NC}"
}

# --- Prerequisite Check ---
check_dialog() {
    if ! command -v dialog &> /dev/null; then
        clear
        warn "The 'dialog' utility is not installed. Attempting automatic installation (requires sudo)..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y dialog || error "Failed to install 'dialog' via apt-get."
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y dialog || error "Failed to install 'dialog' via dnf."
        elif command -v pacman &> /dev/null; then
            sudo pacman -Sy --noconfirm dialog || error "Failed to install 'dialog' via pacman."
        else
            error "Could not determine package manager. Please install 'dialog' manually."
        fi
        clear
    fi
}

# --- Action Functions (retained from previous script) ---

self_test() {
    print_header "Launcher Self-Test (non-interactive)"
    ensure_venv

    info "Checking dialog availability..."
    if ! command -v dialog &> /dev/null; then
        error "dialog is missing even after auto-install."
    fi

    info "Checking aria2c availability..."
    if ! command -v aria2c &> /dev/null; then
        warn "aria2c still missing; downloads will fail."
    fi

    info "Running: python main.py --help"
    python main.py --help >/dev/null

    info "Running: python main.py --codebreaker --help"
    python main.py --codebreaker --help >/dev/null

    info "Running: python main.py --self-code --help"
    python main.py --self-code --help >/dev/null

    info "Running: python main.py --ide --help"
    python main.py --ide --help >/dev/null

    info "Running: python main.py --mcp-test --help"
    python main.py --mcp-test --help >/dev/null 2>&1 || true

    info "Running: python scripts/get_model_urls.py"
    python scripts/get_model_urls.py >/dev/null

    info "Running: python scripts/run_quantization.py --help"
    python scripts/run_quantization.py --help >/dev/null

    info "Checking IntelStack scripts readability..."
    for f in IntelStack/build_gmmlib.sh IntelStack/build_igc.sh IntelStack/build_compute_runtime.sh IntelStack/install_ipex.sh; do
        [ -r "$f" ] || error "Missing or unreadable: $f"
    done

    print_header "Self-Test Complete"
    exit 0
}

# Action: Bootstrap Intel Stack
do_bootstrap_intel() {
    print_header "Intel Stack Bootstrap"
    info "This will build and install the Intel compute stack from source."
    warn "Sudo privileges will be required throughout the process."

    read -p "Do you wish to continue? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Bootstrap cancelled."
        return
    fi

    local build_root="$HOME/intel-compute-runtime-build"
    info "Using build root: ${build_root}"
    mkdir -p "${build_root}"

    info "Ensuring system dependencies are installed..."
    ensure_sys_deps

    pushd IntelStack > /dev/null
    
    info "Step 1/4: Building gmmlib..."
    bash ./build_gmmlib.sh "${build_root}"
    
    info "Step 2/4: Building igc..."
    bash ./build_igc.sh "${build_root}"

    info "Step 3/4: Building compute-runtime..."
    bash ./build_compute_runtime.sh "${build_root}"

    info "Step 4/4: Installing Intel Extension for PyTorch..."
    bash ./install_ipex.sh

    popd > /dev/null
    print_header "Intel Stack Bootstrap Complete"
}

# Action: Download Models
do_download_models() {
    print_header "Model Downloader"
    ensure_venv

    if ! command -v aria2c &> /dev/null; then
        warn "aria2c is not installed. Attempting automatic installation (requires sudo)..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y aria2 || sudo apt-get install -y aria2c || error "Failed to install aria2c via apt-get."
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y aria2 || sudo dnf install -y aria2c || error "Failed to install aria2c via dnf."
        elif command -v pacman &> /dev/null; then
            sudo pacman -Sy --noconfirm aria2 || sudo pacman -Sy --noconfirm aria2c || error "Failed to install aria2c via pacman."
        elif command -v snap &> /dev/null; then
            sudo snap install aria2c || error "Failed to install aria2c via snap."
        else
            error "aria2c is required but no supported installer was found."
        fi
    fi

    local model_dir="$PROJECT_ROOT/models"
    mkdir -p "$model_dir"
    info "Models will be downloaded to: ${model_dir}"

    info "Fetching model URLs from config..."
    local urls_file=$(mktemp)
    python3 scripts/get_model_urls.py > "$urls_file"

    if [ ! -s "$urls_file" ]; then
        warn "No model URLs were found. Check 'config/models.yaml'."
    else
        info "Starting download with aria2c... (See aria-log.txt for details)"
        aria2c --input-file="$urls_file" --dir="$model_dir" --continue=true --max-concurrent-downloads=5 --max-connection-per-server=8 --split=8 --min-split-size=1M --log="aria-log.txt" --log-level=warn --summary-interval=10 --human-readable=true --auto-file-renaming=false -x 16 -s 16 -k 1M
    fi
    
    rm -f "$urls_file"
    print_header "Model Download Complete"
}

# Action: Quantize Models
do_quantize() {
    print_header "Quantization Pipeline"
    ensure_venv
    
    info "Starting quantization process..."
    python3 scripts/run_quantization.py "$1"
    
    print_header "Quantization Complete"
}

# Action: Run Router
do_run() {
    print_header "Launching SWORD Coder MoE Router"
    ensure_venv

    info "Starting application... Press Ctrl+C to stop."
    python3 main.py
}

# Action: Launch IDE
do_ide() {
    print_header "Launching Self-Coding IDE"
    ensure_venv

    # Ask for workspace path
    local workspace
    workspace=$(dialog --stdout --inputbox "Enter workspace path (default: current directory):" 8 60 "$PWD")
    if [ -z "$workspace" ]; then
        workspace="$PWD"
    fi

    info "Starting IDE with workspace: $workspace"
    info "Press Ctrl+Q to exit the IDE"
    python3 main.py --ide --workspace "$workspace"
}

# Action: Self-Coding Session
do_selfcode() {
    print_header "Interactive Self-Coding Session"
    ensure_venv

    # Ask for workspace path
    local workspace
    workspace=$(dialog --stdout --inputbox "Enter workspace path (default: current directory):" 8 60 "$PWD")
    if [ -z "$workspace" ]; then
        workspace="$PWD"
    fi

    info "Starting self-coding agent with workspace: $workspace"
    info "Type 'help' for commands, 'exit' to quit"
    python3 main.py --self-code --workspace "$workspace"
}

# Action: Codebreaker (with optional SUPERCOP benchmark)
do_codebreaker() {
    print_header "Codebreaker Mode"
    ensure_venv

    local payload devices supercop_path bench_flag="" command_args=()

    payload=$(dialog --stdout --inputbox "Enter base64 payload (leave blank to use bundled sample):" 10 70 "")
    devices=$(dialog --stdout --inputbox "Target devices (comma-separated, e.g., all or npu,movidius):" 8 70 "all")
    if dialog --stdout --yesno "Run Simon/Speck SUPERCOP benchmark across the selection?" 7 70; then
        bench_flag="--crypto-bench"
    fi
    supercop_path=$(dialog --stdout --inputbox "Custom SUPERCOP checkout path (optional):" 8 70 "")

    command_args=(python3 main.py --codebreaker)
    if [ -n "$payload" ]; then
        command_args+=(--payload "$payload")
    fi
    if [ -n "$devices" ]; then
        command_args+=(--devices "$devices")
    fi
    if [ -n "$bench_flag" ]; then
        command_args+=($bench_flag)
    fi
    if [ -n "$supercop_path" ]; then
        command_args+=(--supercop-path "$supercop_path")
    fi

    info "Running: ${command_args[*]}"
    "${command_args[@]}"
}

# Action: Codebreaker benchmark (SUPERCOP always enabled)
do_codebreaker_bench() {
    print_header "Codebreaker Benchmark"
    ensure_venv

    local payload devices supercop_path command_args=()

    payload=$(dialog --stdout --inputbox "Enter base64 payload (leave blank to use bundled sample):" 10 70 "")
    devices=$(dialog --stdout --inputbox "Target devices (comma-separated, e.g., all or npu,movidius):" 8 70 "all")
    supercop_path=$(dialog --stdout --inputbox "Custom SUPERCOP checkout path (optional):" 8 70 "")

    command_args=(python3 main.py --codebreaker --crypto-bench)
    if [ -n "$payload" ]; then
        command_args+=(--payload "$payload")
    fi
    if [ -n "$devices" ]; then
        command_args+=(--devices "$devices")
    fi
    if [ -n "$supercop_path" ]; then
        command_args+=(--supercop-path "$supercop_path")
    fi

    info "Running: ${command_args[*]}"
    "${command_args[@]}"
}

# Action: Router benchmarks
do_benchmark() {
    print_header "Router Benchmark Suite"
    ensure_venv
    info "Executing benchmark suite..."
    python3 main.py --benchmark
}

# Action: Test MCP Servers
do_test() {
    print_header "Testing MCP Servers and Tools"
    ensure_venv

    info "Running MCP server tests..."
    python3 main.py --mcp-test

    read -p "Press Enter to continue..."
}

# --- TUI Implementation ---

main_menu() {
    CHOICE=$(dialog --clear --stdout \
                    --backtitle "SWORD Launcher | Cursed AI Framework" \
                    --title "Main Menu" \
                    --menu "Select an action:" \
                    22 70 10 \
                    "Run" "Start the SWORD Coder MoE Router" \
                    "Benchmark" "Run router benchmark suite" \
                    "IDE" "Launch Self-Coding IDE (Textual TUI)" \
                    "SelfCode" "Start Interactive Self-Coding Session" \
                    "Codebreaker" "Decode payloads + SUPERCOP benchmarking" \
                    "CB Bench" "Run Codebreaker with SUPERCOP benchmark" \
                    "Download" "Download all required models" \
                    "Quantize" "Run the quantization pipeline" \
                    "Bootstrap" "Build and install the Intel compute stack" \
                    "Test" "Test MCP servers and tools" \
                    "Exit" "Exit the launcher")

    # The CHOICE variable will hold the tag of the selected menu item.
    # e.g., "Run", "Download", etc.
}

quantize_menu() {
    CHOICE=$(dialog --clear --stdout \
                    --backtitle "SWORD Launcher | Quantization" \
                    --title "Quantization Menu" \
                    --menu "Select a quantization target:" \
                    16 60 3 \
                    "All" "Quantize all models from the config file" \
                    "Specific" "Quantize a single, specific model" \
                    "Back" "Return to the Main Menu")
    
    case $CHOICE in
        "All")
            do_quantize
            ;;
        "Specific")
            local model_name
            model_name=$(dialog --stdout --inputbox "Enter the exact model name to quantize:" 8 60)
            if [ -n "$model_name" ]; then
                do_quantize "$model_name"
            else
                info "No model name entered. Returning."
            fi
            ;;
        "Back")
            return
            ;;
    esac
}

# --- Argument Parsing (non-TUI) ---
while [[ $# -gt 0 ]]; do
    case "$1" in
        --self-test)
            SELF_TEST=1
            shift
            ;;
        *)
            break
            ;;
    esac
done

if [ "$SELF_TEST" -eq 1 ]; then
    self_test
fi

# --- Main Execution Loop ---
check_dialog

while true; do
    main_menu
    case $CHOICE in
        "Run")
            do_run
            ;;
        "Benchmark")
            do_benchmark
            ;;
        "IDE")
            do_ide
            ;;
        "SelfCode")
            do_selfcode
            ;;
        "Codebreaker")
            do_codebreaker
            ;;
        "CB Bench")
            do_codebreaker_bench
            ;;
        "Download")
            do_download_models
            ;;
        "Quantize")
            quantize_menu
            ;;
        "Bootstrap")
            do_bootstrap_intel
            ;;
        "Test")
            do_test
            ;;
        "Exit" | "")
            clear
            info "Exiting SWORD Launcher."
            exit 0
            ;;
    esac
    read -p $'\nPress [Enter] to return to the main menu...'
done
