#!/usr/bin/env bash
set -euo pipefail

# Build and install Intel GMMLIB (prereq for compute-runtime).

root="${1:-$HOME/intel-compute-runtime-build}"
src_dir="${root}/gmmlib"
build_dir="${src_dir}/build"

if [[ ! -d "${src_dir}" ]]; then
  git clone https://github.com/intel/gmmlib "${src_dir}"
fi

rm -rf "${build_dir}"
mkdir -p "${build_dir}"
cmake -S "${src_dir}" -B "${build_dir}" \
  -DCMAKE_C_COMPILER=gcc-12 \
  -DCMAKE_CXX_COMPILER=g++-12 \
  -DCMAKE_BUILD_TYPE=Release
cmake --build "${build_dir}" -j"$(nproc)"
sudo cmake --install "${build_dir}"
