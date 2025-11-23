# Gemini Context: SWORD Coder MoE Router

## Project Overview

This project, "SWORD Coder MoE Router," is a sophisticated Mixture-of-Experts (MoE) routing system for AI model inference. It runs on specific Intel-based hardware, including Core Ultra processors ("Meteor Lake") with integrated NPUs, iGPUs, and AMX accelerators, as well as discrete Movidius VPUs.

The core of the project is a FastAPI server that exposes an OpenAI-compatible API. It intelligently routes incoming requests to a pool of "expert" models based on the prompt's content, metadata, and a detailed hardware configuration. The system is designed to maximize performance and efficiency by leveraging the best-suited hardware component for a given task (e.g., NPU for real-time tasks, iGPU for vision, AMX for large language models).

A key feature is the "DSMIL Layer Architecture," which organizes models into functional layers (e.g., code generation, security analysis, strategic command). The project also includes a comprehensive quantization pipeline to run very large models (70B+ parameters) in a memory-constrained environment using INT8 and INT4 precision.

**Key Technologies:**
*   Python
*   FastAPI
*   PyTorch
*   Intel Extension for PyTorch (IPEX)
*   OpenVINO
*   YAML for configuration

## Building and Running

### 1. Environment Setup

The primary setup is managed by `scripts/setup.sh`. This script creates a Python virtual environment, installs dependencies from `requirements.txt`, and checks for available hardware accelerators.

```bash
# Run the setup script
bash scripts/setup.sh
```

### 2. Building the Intel Compute Stack (If Required)

For bare-metal or custom installations, the project includes scripts to build the necessary Intel drivers and libraries from source. These must be run in order.

```bash
# WARNING: These scripts build and install system-level drivers.
# Execute with caution.

# 1. Build GMMLIB
bash IntelStack/build_gmmlib.sh

# 2. Build IGC
bash IntelStack/build_igc.sh

# 3. Build Compute Runtime (NEO)
bash IntelStack/build_compute_runtime.sh

# 4. Install Intel Extension for PyTorch (IPEX)
bash IntelStack/install_ipex.sh
```

For "ultimate performance" on Meteor Lake hardware, custom flags can be installed:
```bash
bash IntelStack/meteor_lake_flags_ultimate/install.sh
```

### 3. Running the Router

The main application can be started via the `main.py` entrypoint.

```bash
# Activate the virtual environment
source venv/bin/activate

# Start the main router server
python main.py

# The server will be available at http://0.0.0.0:8000
```

### 4. Other Operations

The `main.py` script provides several modes of operation:

```bash
# Run the benchmark suite
python main.py --benchmark

# Show model storage estimates after quantization
python main.py --storage
```

## Development Conventions

*   **Configuration:** All hardware and model definitions are managed in YAML files within the `config/` directory. `hardware.yaml` details the system's accelerators, while `models.yaml` serves as a registry for all available models, their parameters, and quantization targets.
*   **Routing Logic:** The core routing intelligence is in `src/generic_router.py`. The logic is heavily documented, referencing a "DSMIL Layer Architecture" and a hardware-based classifier ("Device 19") to make decisions.
*   **Quantization:** The `src/quantization_pipeline.py` file contains the logic for model quantization, including size estimation and applying different precision levels (INT8, INT4).
*   **Dependencies:** Python package dependencies are strictly managed in `requirements.txt`.
*   **Entrypoint:** `main.py` is the main user-facing entrypoint that parses command-line arguments and launches the appropriate sub-system (router, benchmark, etc.).
