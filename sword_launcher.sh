#!/bin/bash
#
# SWORD Launcher Script (TUI Edition)
# A master script to manage the SWORD Coder MoE Router project.
#

set -eo pipefail
PROJECT_ROOT=$(dirname "$(readlink -f "$0")")
cd "$PROJECT_ROOT"

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

print_header() {
    echo -e "\n${YELLOW}=====================================================${NC}"
    echo -e "${YELLOW} $1${NC}"
    echo -e "${YELLOW}=====================================================${NC}"
}

# --- Prerequisite Check ---
check_dialog() {
    if ! command -v dialog &> /dev/null; then
        clear
        warn "The 'dialog' utility is not installed. It is required for the TUI."
        read -p "Do you want to attempt to install it now (requires sudo)? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command -v apt-get &> /dev/null; then
                sudo apt-get update && sudo apt-get install -y dialog
            elif command -v dnf &> /dev/null; then
                sudo dnf install -y dialog
            elif command -v pacman &> /dev/null; then
                sudo pacman -S --noconfirm dialog
            else
                error "Could not determine package manager. Please install 'dialog' manually."
            fi
        else
            error "'dialog' is required to continue. Aborting."
        fi
        clear
    fi
}

# --- Action Functions (retained from previous script) ---

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

    pushd IntelStack > /dev/null
    
    info "Step 1/4: Building gmmlib..."
    ./build_gmmlib.sh "${build_root}"
    
    info "Step 2/4: Building igc..."
    ./build_igc.sh "${build_root}"

    info "Step 3/4: Building compute-runtime..."
    ./build_compute_runtime.sh "${build_root}"

    info "Step 4/4: Installing Intel Extension for PyTorch..."
    ./install_ipex.sh

    popd > /dev/null
    print_header "Intel Stack Bootstrap Complete"
}

# Action: Download Models
do_download_models() {
    print_header "Model Downloader"
    if ! command -v aria2c &> /dev/null; then
        warn "aria2c is not installed. It is required for fast parallel downloads."
        read -p "Do you want to attempt to install it via snap? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if ! command -v snap &> /dev/null; then
                info "snapd not found. Attempting to install it with apt..."
                sudo apt-get update && sudo apt-get install -y snapd || error "Failed to install snapd."
            fi
            info "Installing aria2c via snap..."
            sudo snap install aria2c || error "Failed to install aria2c via snap."
            info "aria2c installed successfully."
        else
            error "aria2c is required. Aborting."
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
        aria2c --input-file="$urls_file" --dir="$model_dir" --continue=true --max-concurrent-downloads=5 --max-connection-per-server=8 --split=8 --min-split-size=1M --log="aria-log.txt" --log-level=warn --summary-interval=10 --human-readable=true --git-clone-with-full-history --auto-file-renaming=false -x 16 -s 16 -k 1M
    fi
    
    rm -f "$urls_file"
    print_header "Model Download Complete"
}

# Action: Quantize Models
do_quantize() {
    print_header "Quantization Pipeline"
    if [ ! -d "venv" ]; then
        error "Virtual environment not found. Please run ./scripts/setup.sh first."
    fi
    source venv/bin/activate
    
    info "Starting quantization process..."
    python3 scripts/run_quantization.py "$1"
    
    print_header "Quantization Complete"
}

# Action: Run Router
do_run() {
    print_header "Launching SWORD Coder MoE Router"
    if [ ! -d "venv" ]; then
        error "Virtual environment not found. Please run ./scripts/setup.sh first."
    fi
    source venv/bin/activate
    
    info "Starting application... Press Ctrl+C to stop."
    python3 main.py
}

# --- TUI Implementation ---

main_menu() {
    CHOICE=$(dialog --clear --stdout \
                    --backtitle "SWORD Launcher | Cursed AI Framework" \
                    --title "Main Menu" \
                    --menu "Select an action:" \
                    16 60 5 \
                    "Run" "Start the SWORD Coder MoE Router" \
                    "Download" "Download all required models" \
                    "Quantize" "Run the quantization pipeline" \
                    "Bootstrap" "Build and install the Intel compute stack" \
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

# --- Main Execution Loop ---
check_dialog

while true; do
    main_menu
    case $CHOICE in
        "Run")
            do_run
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
        "Exit" | "")
            clear
            info "Exiting SWORD Launcher."
            exit 0
            ;;
    esac
    read -p $'\nPress [Enter] to return to the main menu...'
done