#!/usr/bin/env bash
set -euo pipefail

# Build and install Intel Graphics Compiler (IGC) from source.

workspace="${1:-$HOME/igc_workspace}"
build_dir="${workspace}/build"

if [[ ! -d "${workspace}/igc" ]]; then
  echo "IGC source not found under ${workspace}/igc" >&2
  exit 1
fi

rm -rf "${build_dir}"
mkdir -p "${build_dir}"
cmake -S "${workspace}/igc" -B "${build_dir}" \
  -DCMAKE_C_COMPILER=gcc-12 \
  -DCMAKE_CXX_COMPILER=g++-12 \
  -DCMAKE_CXX_STANDARD=17
cmake --build "${build_dir}" -j"$(nproc)"
sudo cmake --install "${build_dir}"
