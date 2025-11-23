#!/usr/bin/env bash
set -euo pipefail

# Build and install Intel Graphics Compiler (IGC) from source.

workspace="${1:-$HOME/igc_workspace}"
build_dir="${workspace}/build"
llvm_dir=""
cc_bin="gcc-12"
cxx_bin="g++-12"
llvm_version="16.0.6"
llvm_tarball=""
llvm_url=""

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

build_llvm16_from_source() {
  local llvm_src="${workspace}/llvm-project"
  local llvm_build="${workspace}/llvm-build"
  local llvm_prefix="${workspace}/llvm-16"
  local generator="Unix Makefiles"

  if command -v ninja &>/dev/null; then
    generator="Ninja"
  fi

  if [[ ! -d "${llvm_src}" ]]; then
    echo "Cloning llvm-project (v16.0.6)..."
    git clone --depth 1 --branch llvmorg-16.0.6 https://github.com/llvm/llvm-project "${llvm_src}"
  fi

  rm -rf "${llvm_build}"
  mkdir -p "${llvm_build}"

  echo "Building LLVM 16 from source (this may take a while)..."
  cmake -G "${generator}" -S "${llvm_src}/llvm" -B "${llvm_build}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_ENABLE_PROJECTS="clang;lld" \
    -DLLVM_TARGETS_TO_BUILD="X86" \
    -DCMAKE_INSTALL_PREFIX="${llvm_prefix}"

  cmake --build "${llvm_build}" -j"$(nproc)"
  cmake --install "${llvm_build}"

  if [[ -d "${llvm_prefix}/lib/cmake/llvm" ]]; then
    llvm_dir="${llvm_prefix}/lib/cmake/llvm"
  fi
}

install_prebuilt_llvm16() {
  local arch="$(uname -m)"
  llvm_tarball="${LLVM_TARBALL_OVERRIDE:-clang+llvm-${llvm_version}-${arch}-linux-gnu-ubuntu-22.04.tar.xz}"
  llvm_url="${LLVM_URL_OVERRIDE:-https://github.com/llvm/llvm-project/releases/download/llvmorg-${llvm_version}/${llvm_tarball}}"
  local dest_dir="${workspace}/llvm-16-prebuilt"

  if [[ -d "${dest_dir}" ]]; then
    llvm_dir="${dest_dir}/lib/cmake/llvm"
    return
  fi

  echo "Fetching prebuilt LLVM 16 (Ubuntu 22.04 tarball)..."
  mkdir -p "${workspace}"
  if command -v curl &>/dev/null; then
    curl -L "${llvm_url}" -o "${workspace}/${llvm_tarball}"
  else
    wget -O "${workspace}/${llvm_tarball}" "${llvm_url}"
  fi

  mkdir -p "${dest_dir}"
  tar -xf "${workspace}/${llvm_tarball}" -C "${dest_dir}" --strip-components=1
  rm -f "${workspace}/${llvm_tarball}"

  if [[ -d "${dest_dir}/lib/cmake/llvm" ]]; then
    llvm_dir="${dest_dir}/lib/cmake/llvm"
  fi
}

# Ensure LLVM 16 toolchain is available (IGC requires LLVM 16.x)
detect_and_install_llvm16() {
  if [[ -d "/usr/lib/llvm-16/cmake" ]]; then
    llvm_dir="/usr/lib/llvm-16/cmake"
    return
  fi

  echo "LLVM 16 not found; attempting installation (requires sudo)..."
  if command -v apt-get &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y wget lsb-release gnupg || true
    sudo apt-get install -y llvm-16 llvm-16-dev clang-16 lld-16 || true
    if [[ ! -d "/usr/lib/llvm-16/cmake" ]]; then
      echo "Attempting LLVM 16 install via apt.llvm.org helper script..."
      tmp_script="$(mktemp)"
      wget -O "${tmp_script}" https://apt.llvm.org/llvm.sh || true
      if [[ -s "${tmp_script}" ]]; then
        chmod +x "${tmp_script}"
        sudo "${tmp_script}" 16 || true
      fi
      rm -f "${tmp_script}"
      sudo apt-get update || true
      sudo apt-get install -y llvm-16 llvm-16-dev clang-16 lld-16 || true
    fi
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y llvm16.0 llvm16.0-devel clang16 lld16 || true
  elif command -v pacman &>/dev/null; then
    sudo pacman -Sy --noconfirm llvm16 clang16 lld || true
  else
    echo "No supported package manager found to install LLVM 16." >&2
  fi

  if [[ -d "/usr/lib/llvm-16/cmake" ]]; then
    llvm_dir="/usr/lib/llvm-16/cmake"
    return
  fi

  # Try prebuilt binaries before building from source
  install_prebuilt_llvm16
  if [[ -n "${llvm_dir}" ]]; then
    return
  fi

  # Fall back to building from source
  build_llvm16_from_source
}

# Fetch IGC if missing
if [[ ! -d "${workspace}/igc" ]]; then
  echo "IGC source not found under ${workspace}/igc. Cloning..."
  git clone --depth 1 https://github.com/intel/intel-graphics-compiler "${workspace}/igc"
fi

# IGC depends on SPIRV headers; fetch if missing
if [[ ! -d "${workspace}/spirv-headers" ]]; then
  echo "SPIRV-Headers not found. Cloning..."
  git clone --depth 1 https://github.com/KhronosGroup/SPIRV-Headers "${workspace}/spirv-headers"
fi

detect_and_install_llvm16
if [[ -z "${llvm_dir}" ]]; then
  echo "LLVM 16 toolchain is required. Install llvm-16/clang-16 and retry." >&2
  exit 1
fi

rm -rf "${build_dir}"
mkdir -p "${build_dir}"
install_prereqs
cmake -S "${workspace}/igc" -B "${build_dir}" \
  -DCMAKE_C_COMPILER="${cc_bin}" \
  -DCMAKE_CXX_COMPILER="${cxx_bin}" \
  -DCMAKE_CXX_STANDARD=17 \
  -DSPIRV-Headers_SOURCE_DIR="${workspace}/spirv-headers" \
  -DLLVM_DIR="${llvm_dir}"
cmake --build "${build_dir}" -j"$(nproc)"
sudo cmake --install "${build_dir}"
