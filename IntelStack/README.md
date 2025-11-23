Intel GPU Stack Helpers
=======================

This folder contains small scripts to rebuild the Intel GPU software stack from source and verify PyTorch XPU support.

- `build_igc.sh [workspace]` – builds/installs IGC from `~/igc_workspace` (or given path).
- `build_gmmlib.sh [root]` – builds/installs GMMLIB under `~/intel-compute-runtime-build` (or given path), cloning if missing.
- `build_compute_runtime.sh [root]` – builds/installs the compute runtime from `~/intel-compute-runtime-build/neo` (or given path); unit tests are skipped.
- `install_ipex.sh` – installs PyTorch 2.8.0 and IPEX 2.8.0 with `--break-system-packages`.
- `verify_xpu.py` – prints torch/ipex versions and XPU availability.
- `opt_flags.env` – exports `CFLAGS_OPTIMAL` and `LDFLAGS_OPTIMAL` tuned for Meteor Lake.
- `run_with_opt_flags.sh` – wraps any command to inject those optimal flags (uses `opt_flags.env` if present).

Notes
-----
- Ensure `LD_LIBRARY_PATH` includes `/usr/local/lib` (already set in `.bashrc`).
- Kernel modules `xe` or `i915` must be loaded for the Arc GPU.
- Run scripts with `bash script.sh` (they use gcc-12/g++-12 and `cmake --install`, so sudo may be required).
