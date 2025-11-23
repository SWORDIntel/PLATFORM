#!/usr/bin/env bash
set -euo pipefail

# Build and install Intel Graphics Compiler (IGC) from source.

workspace="${1:-$HOME/igc_workspace}"
build_dir="${workspace}/build"
llvm_dir=""
# Default compiler (prefer gcc-13/g++-13 if installed)
if command -v gcc-13 > /dev/null; then
  cc_bin="gcc-13"
else
  cc_bin="gcc-12"
fi
if command -v g++-13 > /dev/null; then
  cxx_bin="g++-13"
else
  cxx_bin="g++-12"
fi
llvm_version="16.0.6"
llvm_tarball=""
llvm_url=""
llvm_prebuilt_release="v2025.2.0"  # awakecoding/llvm-prebuilt release tag

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
  local arch_slug="${arch}"
  if [[ "${arch}" == "x86_64" ]]; then
    arch_slug="x86_64"
  elif [[ "${arch}" == "aarch64" || "${arch}" == "arm64" ]]; then
    arch_slug="aarch64"
  fi

  # Try multiple prebuilt variants (newest first) from awakecoding/llvm-prebuilt
  local candidates=(
    "clang+llvm-${llvm_version}-${arch_slug}-ubuntu-22.04.tar.xz"
    "clang+llvm-${llvm_version}-${arch_slug}-ubuntu-24.04.tar.xz"
  )

  local dest_dir="${workspace}/llvm-16-prebuilt"

  if [[ -d "${dest_dir}" ]]; then
    llvm_dir="${dest_dir}/lib/cmake/llvm"
    return
  fi

  mkdir -p "${workspace}"
  for candidate in "${candidates[@]}"; do
    llvm_tarball="${LLVM_TARBALL_OVERRIDE:-$candidate}"
    # Try awakecoding prebuilt release first, then legacy releases site
    llvm_url="${LLVM_URL_OVERRIDE:-https://github.com/awakecoding/llvm-prebuilt/releases/download/${llvm_prebuilt_release}/${llvm_tarball}}"
    local fallback_url="https://releases.llvm.org/${llvm_version}/${llvm_tarball}"
    local checksum_url="https://github.com/awakecoding/llvm-prebuilt/releases/download/${llvm_prebuilt_release}/checksums"

    echo "Fetching prebuilt LLVM 16: ${llvm_tarball} ..."
    local target="${workspace}/${llvm_tarball}"
    rm -f "${target}"
    if command -v aria2c &>/dev/null; then
      aria2c -x 8 -s 8 -k 1M -o "$(basename "${target}")" -d "${workspace}" "${llvm_url}" || \
      aria2c -x 8 -s 8 -k 1M -o "$(basename "${target}")" -d "${workspace}" "${fallback_url}" || continue
    elif command -v curl &>/dev/null; then
      curl -L --fail --retry 3 --retry-delay 2 "${llvm_url}" -o "${target}" || curl -L --fail --retry 3 --retry-delay 2 "${fallback_url}" -o "${target}" || continue
    else
      wget --tries=3 --wait=2 -O "${target}" "${llvm_url}" || wget --tries=3 --wait=2 -O "${target}" "${fallback_url}" || continue
    fi

    # Quick sanity check on file size (>50MB)
    local size
    size=$(stat -c%s "${target}" 2>/dev/null || echo 0)
    if [[ "${size}" -lt 50000000 ]]; then
      echo "Downloaded tarball looks too small (${size} bytes); trying next candidate..."
      rm -f "${target}"
      continue
    fi

    # Download checksums file and verify sha256 if available
    local checksum_file="${workspace}/llvm-prebuilt-checksums"
    rm -f "${checksum_file}"
    if command -v aria2c &>/dev/null; then
      aria2c -x 4 -s 4 -k 1M -o "$(basename "${checksum_file}")" -d "${workspace}" "${checksum_url}" || true
    elif command -v curl &>/dev/null; then
      curl -L --fail --retry 3 --retry-delay 2 "${checksum_url}" -o "${checksum_file}" || true
    else
      wget --tries=3 --wait=2 -O "${checksum_file}" "${checksum_url}" || true
    fi

    if [[ -f "${checksum_file}" ]]; then
      local expected
      expected=$(grep "${llvm_tarball}" "${checksum_file}" | awk '{print $1}' || true)
      if [[ -n "${expected}" ]]; then
        local actual
        actual=$(sha256sum "${target}" | awk '{print $1}')
        if [[ "${expected}" != "${actual}" ]]; then
          echo "Checksum mismatch for ${llvm_tarball} (expected ${expected}, got ${actual}); trying next candidate..."
          rm -f "${target}"
          continue
        fi
      fi
    fi

    mkdir -p "${dest_dir}"
    if tar -xf "${target}" -C "${dest_dir}" --strip-components=1; then
      rm -f "${target}"
      if [[ -d "${dest_dir}/lib/cmake/llvm" ]]; then
        llvm_dir="${dest_dir}/lib/cmake/llvm"
        return
      fi
    else
      echo "Failed to extract ${llvm_tarball}; trying next candidate..."
      rm -rf "${dest_dir:?}"/*
      rm -f "${target}"
    fi
  done
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

# Ensure SPIRV-LLVM-Translator (matching LLVM 16) is available
detect_and_install_spirv_translator() {
  local translator_src="${workspace}/spirv-llvm-translator"
  local translator_build="${workspace}/spirv-llvm-translator-build"
  local translator_prefix="${workspace}/spirv-llvm-translator-install"

  if [[ -d "${translator_prefix}/lib/cmake/SPIRVLLVMTranslator" ]]; then
    return
  fi

  # Try system packages first
  if command -v apt-get &>/dev/null; then
    sudo apt-get update
    sudo apt-get install -y spirv-tools libspirv-tools-dev spirv-llvm-translator-16 || true
  elif command -v dnf &>/dev/null; then
    sudo dnf install -y spirv-tools-devel spirv-llvm-translator || true
  elif command -v pacman &>/dev/null; then
    sudo pacman -Sy --noconfirm spirv-tools || true
  fi

  # If system install provided CMake package, use it
  if pkg-config --exists SPIRV-Tools 2>/dev/null && \
     [[ -d "/usr/lib/cmake/SPIRVLLVMTranslator" || -d "/usr/lib64/cmake/SPIRVLLVMTranslator" ]]; then
    return
  fi

  # Build from source if not found
  if [[ ! -d "${translator_src}" ]]; then
    git clone --depth 1 --branch v${llvm_version} https://github.com/KhronosGroup/SPIRV-LLVM-Translator "${translator_src}"
  fi

  rm -rf "${translator_build}"
  mkdir -p "${translator_build}"

  cmake -S "${translator_src}" -B "${translator_build}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DLLVM_DIR="${llvm_dir}" \
    -DCMAKE_INSTALL_PREFIX="${translator_prefix}"
  cmake --build "${translator_build}" -j"$(nproc)"
  cmake --install "${translator_build}"
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
if [[ -z "${llvm_dir}" || ! -f "${llvm_dir}/LLVMConfig.cmake" ]]; then
  echo "LLVM 16 toolchain is required. Install llvm-16/clang-16 and retry. (Expected LLVMConfig.cmake in ${llvm_dir})" >&2
  exit 1
fi

detect_and_install_spirv_translator

rm -rf "${build_dir}"
mkdir -p "${build_dir}"
install_prereqs
# Bias CMake search paths toward the local LLVM/translator installs
export CMAKE_PREFIX_PATH="${llvm_dir}:${workspace}/spirv-llvm-translator-install:${CMAKE_PREFIX_PATH:-}"
cmake -S "${workspace}/igc" -B "${build_dir}" \
  -DCMAKE_C_COMPILER="${cc_bin}" \
  -DCMAKE_CXX_COMPILER="${cxx_bin}" \
  -DCMAKE_CXX_STANDARD=17 \
  -DSPIRV-Headers_SOURCE_DIR="${workspace}/spirv-headers" \
  -DLLVM_DIR="${llvm_dir}" \
  -DSPIRVLLVMTranslator_DIR="${workspace}/spirv-llvm-translator-install/lib/cmake/SPIRVLLVMTranslator"
cmake --build "${build_dir}" -j"$(nproc)"
sudo cmake --install "${build_dir}"
