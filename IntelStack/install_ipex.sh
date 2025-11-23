#!/usr/bin/env bash
set -euo pipefail

# Install PyTorch 2.8.0 and Intel Extension for PyTorch 2.8.0.
# Uses --break-system-packages to allow user-site install on Debian/Ubuntu.

pip install --user --break-system-packages "torch==2.8.0" "intel-extension-for-pytorch==2.8.0"
