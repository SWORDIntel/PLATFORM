#!/usr/bin/env bash

# Bootstrap script for SWORD Coder MoE Router
# -------------------------------------------------
# This script performs the full setup required to build and run the
# router on a fresh machine. It:
#   1. Runs the Python environment setup (scripts/setup.sh)
#   2. Installs the Intel compute stack (GMMLIB, IGC, IPEX)
#   3. Ensures LLVM‑16 toolchain is available (handled by IGC script)
#   4. Optionally installs Meteor Lake optimal flags
#   5. Starts the FastAPI router.
# -------------------------------------------------

set -euo pipefail

# Helper for colored output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}=== Bootstrap starting ===${NC}"

# 1️⃣ Run the Python environment setup
if [[ -f "scripts/setup.sh" ]]; then
  echo -e "${YELLOW}Running scripts/setup.sh...${NC}"
  bash scripts/setup.sh
else
  echo -e "${RED}Error:${NC} scripts/setup.sh not found"
  exit 1
fi

# Activate virtual environment
if [[ -d "venv" ]]; then
  echo -e "${YELLOW}Activating virtual environment...${NC}"
  source venv/bin/activate

  # Export optimisation flags for Alder Lake (used by all subsequent C/C++ builds)
  export CFLAGS="-march=alderlake -O2"
  export CXXFLAGS="-march=alderlake -O2 $CXXFLAGS"

  # Install GCC 13 (required for LLVM 16 source builds)
  if command -v apt-get > /dev/null; then
    sudo apt-get update
    sudo apt-get install -y gcc-13 g++-13 || true
  elif command -v dnf > /dev/null; then
    sudo dnf install -y gcc gcc-c++ || true
  elif command -v pacman > /dev/null; then
    sudo pacman -Sy --noconfirm gcc || true
  fi
else
  echo -e "${RED}Error:${NC} venv directory missing after setup"
  exit 1
fi

# 2️⃣ Build Intel compute stack components
pushd IntelStack > /dev/null

# GMMLIB
if [[ -x "./build_gmmlib.sh" ]]; then
  echo -e "${YELLOW}Building GMMLIB...${NC}"
  ./build_gmmlib.sh
else
  echo -e "${RED}Error:${NC} build_gmmlib.sh not executable"
  exit 1
fi

# IGC (includes LLVM‑16 detection/installation)
if [[ -x "./build_igc.sh" ]]; then
  echo -e "${YELLOW}Building Intel Graphics Compiler (IGC)...${NC}"
  ./build_igc.sh
else
  echo -e "${RED}Error:${NC} build_igc.sh not executable"
  exit 1
fi

# IPEX
if [[ -x "./install_ipex.sh" ]]; then
  echo -e "${YELLOW}Installing Intel Extension for PyTorch (IPEX)...${NC}"
  ./install_ipex.sh
else
  echo -e "${RED}Error:${NC} install_ipex.sh not executable"
  exit 1
fi

popd > /dev/null

# 3️⃣ Optional: install Meteor Lake ultimate flags if present
if [[ -d "IntelStack/meteor_lake_flags_ultimate" && -x "IntelStack/meteor_lake_flags_ultimate/install.sh" ]]; then
  echo -e "${YELLOW}Installing Meteor Lake ultimate flags...${NC}"
  bash IntelStack/meteor_lake_flags_ultimate/install.sh
fi

# 4️⃣ Verify LLVM‑16 is available (quick sanity check)
if [[ -d "/usr/lib/llvm-16/cmake" ]]; then
  echo -e "${GREEN}LLVM‑16 toolchain detected${NC}"
else
  echo -e "${RED}Warning:${NC} LLVM‑16 not found after IGC build – you may need to install it manually"
fi

# 5️⃣ Start the router (default host/port from main.py)
echo -e "${YELLOW}Starting SWORD Coder MoE Router...${NC}"
python main.py &
ROUTER_PID=$!

# Give the server a moment to start
sleep 3

# Simple health check – try to hit the OpenAPI docs endpoint
if curl -s http://127.0.0.1:8000/docs > /dev/null; then
  echo -e "${GREEN}Router is up and running at http://127.0.0.1:8000${NC}"
else
  echo -e "${RED}Router failed to start. Check logs above for details.${NC}"
  kill $ROUTER_PID || true
  exit 1
fi

# Keep the script alive while the router is running
wait $ROUTER_PID

# End of bootstrap
echo -e "${YELLOW}=== Bootstrap completed ===${NC}"
