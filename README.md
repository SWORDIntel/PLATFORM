# SWORD Coder MoE Router + Self-Coding Agent

AI inference router with autonomous coding capabilities.

## Installation

📦 **First time setup?** See the [Complete Installation Guide](INSTALL.md)

**Quick install:**
```bash
# Install all system dependencies
bash scripts/install_system_deps.sh

# Verify prerequisites
bash scripts/verify_installation.sh

# Run full bootstrap
bash bootstrap.sh
```

## Quick Start

### Launch Self-Coding IDE
```bash
./sword_launcher.sh
# Select "IDE" from menu
```

### Launch Router
```bash
python main.py
```

### Self-Code Interactively
```bash
python main.py --self-code
```

### Run Codebreaker Mode
```bash
python main.py --codebreaker --payload "<encoded_payload>"
# payload defaults to a bundled sample if omitted
# optionally scope to accelerators: --devices npu,movidius (use "--devices all" to force the full list)
# enable Simon/Speck SUPERCOP crypto benchmarks across all devices: --crypto-bench
```

Inside the IDE TUI, press `F6` or run `codebreaker` in the command box (optionally with `devices=npu,movidius benchmark`) to launch the same analysis with live progress, AI device inventory, SUPERCOP benchmarking, and per-selection optimization. The modal now closes with an encryption-type guess, a sentence-likeness flag, and TOPS utilization.

## Features
- 🤖 **Autonomous Coding Agent** - Claude-like self-coding with planning
- 💻 **IDE Interface** - Full-featured TUI with file browser and terminal
- 🔌 **MCP Integration** - context7, memlayer, filesystem, heretic servers
- 🎯 **MoE Router** - Intelligent model routing across Intel hardware
- ⚡ **Hardware Acceleration** - NPU, iGPU, Movidius VPU support
- 🔍 **Codebreaker Mode** - Inspect encoded payloads and list available AI devices

## Documentation
- **Installation Guide**: [INSTALL.md](INSTALL.md) - Complete setup instructions
- **Self-Coding Guide**: [SELF_CODING.md](SELF_CODING.md) - Autonomous agent usage
- **Full Documentation**: [GEMINI.md](GEMINI.md) - Comprehensive platform docs
- **Agent Architecture**: [AGENTS.md](AGENTS.md) - Multi-agent system design

---

AI Platform for rapid use
