#!/usr/bin/env bash
set -euo pipefail

# Build and install Intel Compute Runtime (NEO) using prebuilt IGC + GMMLIB.

root="${1:-$HOME/intel-compute-runtime-build}"
src_dir="${root}/neo"
build_dir="${root}/build"

if [[ ! -d "${src_dir}" ]]; then
  echo "Compute-runtime source not found under ${src_dir}" >&2
  exit 1
fi

rm -rf "${build_dir}"
mkdir -p "${build_dir}"
cmake -S "${src_dir}" -B "${build_dir}" \
  -DCMAKE_C_COMPILER=gcc-12 \
  -DCMAKE_CXX_COMPILER=g++-12 \
  -DCMAKE_BUILD_TYPE=Release \
  -DSKIP_UNIT_TESTS=1
cmake --build "${build_dir}" -j"$(nproc)"
sudo cmake --install "${build_dir}"
