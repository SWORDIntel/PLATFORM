#!/usr/bin/env bash
set -euo pipefail

# Build and install Intel Compute Runtime (NEO) using prebuilt IGC + GMMLIB.

root="${1:-$HOME/intel-compute-runtime-build}"
src_dir="${root}/neo"
build_dir="${root}/build"
cc_bin="gcc-12"
cxx_bin="g++-12"

install_prereqs() {
  if command -v apt-get &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y build-essential git cmake pkg-config gcc-12 g++-12 libdrm-dev libpciaccess-dev libelf-dev || true
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y @development-tools git cmake pkgconf-pkg-config gcc-c++ gcc libdrm-devel libpciaccess-devel libelf-devel || true
  elif command -v pacman &>/dev/null; then
    sudo pacman -Sy --noconfirm base-devel git cmake pkgconf gcc libdrm libpciaccess libelf || true
  fi

  if ! command -v "${cc_bin}" &>/dev/null; then
    cc_bin="gcc"
  fi
  if ! command -v "${cxx_bin}" &>/dev/null; then
    cxx_bin="g++"
  fi
}

install_prereqs

# Fetch compute-runtime if missing
if [[ ! -d "${src_dir}" ]]; then
  echo "Compute-runtime source not found under ${src_dir}. Cloning..."
  git clone --depth 1 https://github.com/intel/compute-runtime "${src_dir}"
fi

rm -rf "${build_dir}"
mkdir -p "${build_dir}"
cmake -S "${src_dir}" -B "${build_dir}" \
  -DCMAKE_C_COMPILER="${cc_bin}" \
  -DCMAKE_CXX_COMPILER="${cxx_bin}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DSKIP_UNIT_TESTS=1
cmake --build "${build_dir}" -j"$(nproc)"
sudo cmake --install "${build_dir}"
