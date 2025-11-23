#!/bin/bash
# SWORD Coder Setup Script
# Sets up tooling WITHOUT downloading models

set -e

echo "========================================"
echo "SWORD Coder MoE Router Setup"
echo "========================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check Python
echo -e "${YELLOW}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✓ $PYTHON_VERSION${NC}"
else
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi

# Check pip
echo -e "${YELLOW}Checking pip...${NC}"
if command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✓ pip3 available${NC}"
else
    echo -e "${RED}✗ pip3 not found${NC}"
    exit 1
fi

# Create virtual environment
echo ""
echo -e "${YELLOW}Setting up virtual environment...${NC}"
cd "$(dirname "$0")/.."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate venv
source venv/bin/activate

# Install core dependencies
echo ""
echo -e "${YELLOW}Installing core dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Core dependencies installed${NC}"

# Check Intel tooling
echo ""
echo -e "${YELLOW}Checking Intel AI tooling...${NC}"

# OpenVINO
if python3 -c "import openvino" 2>/dev/null; then
    echo -e "${GREEN}✓ OpenVINO available${NC}"
else
    echo -e "${YELLOW}⚠ OpenVINO not installed (optional)${NC}"
fi

# Check hardware
echo ""
echo -e "${YELLOW}Detecting hardware...${NC}"

# NPU
if lspci 2>/dev/null | grep -qi "neural\|npu"; then
    echo -e "${GREEN}✓ NPU detected${NC}"
else
    echo -e "${YELLOW}⚠ NPU not detected${NC}"
fi

# Movidius
MOVIDIUS_COUNT=$(lspci 2>/dev/null | grep -ci "movidius\|myriad" || echo "0")
if [ -z "$MOVIDIUS_COUNT" ]; then MOVIDIUS_COUNT=0; fi
if [ "$MOVIDIUS_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Movidius VPU detected: ${MOVIDIUS_COUNT}x${NC}"
else
    echo -e "${YELLOW}⚠ Movidius VPU not detected${NC}"
fi

# Hailo
if lspci 2>/dev/null | grep -qi "hailo"; then
    echo -e "${GREEN}✓ Hailo-8 detected${NC}"
else
    echo -e "${YELLOW}⚠ Hailo-8 not detected${NC}"
fi

# Intel GPU
if lspci 2>/dev/null | grep -qi "intel.*graphics\|intel.*arc"; then
    echo -e "${GREEN}✓ Intel GPU detected${NC}"
else
    echo -e "${YELLOW}⚠ Intel GPU not detected${NC}"
fi

# Check Ollama (for Heretic)
echo ""
echo -e "${YELLOW}Checking Ollama (for Heretic)...${NC}"
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✓ Ollama installed${NC}"
    echo "  Available models:"
    ollama list 2>/dev/null | head -5 || echo "  (none or not running)"
else
    echo -e "${YELLOW}⚠ Ollama not installed${NC}"
    echo "  Install: curl -fsSL https://ollama.com/install.sh | sh"
    echo "  Required for Heretic uncensored inference"
fi

# Create directories
echo ""
echo -e "${YELLOW}Creating directories...${NC}"
mkdir -p logs cache models .cache/sword_quantization
echo -e "${GREEN}✓ Directories created${NC}"

# Verify setup
echo ""
echo -e "${YELLOW}Verifying installation...${NC}"
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from mcp_router import MCPHub
    hub = MCPHub()
    print(f'✓ MCP Hub: {len(hub.servers)} servers, {len(hub.tools)} tools')
except Exception as e:
    print(f'✗ MCP Hub failed: {e}')

try:
    from quantization_pipeline import QuantizationPipeline
    qp = QuantizationPipeline()
    print(f'✓ Quantization Pipeline ready')
except Exception as e:
    print(f'✗ Quantization Pipeline failed: {e}')
"

# Summary
echo ""
echo "========================================"
echo -e "${GREEN}Setup Complete!${NC}"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Start router:  python3 main.py"
echo "  2. Run benchmark: python3 main.py --benchmark"
echo ""
echo "For Heretic (uncensored inference):"
echo "  1. Install Ollama: curl -fsSL https://ollama.com/install.sh | sh"
echo "  2. Pull models:    ollama pull wizardlm-uncensored:13b"
echo "  3. Start Ollama:   ollama serve"
echo ""
echo "Model downloads (when ready):"
echo "  See config/models.yaml for model registry"
echo "  INT8 models: <=13B parameters"
echo "  INT4 models: >13B parameters"
echo ""
