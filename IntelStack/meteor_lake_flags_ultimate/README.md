# 🚀 Intel Meteor Lake Ultimate Compiler Flags Reference
## Intel Core Ultra 7 165H - Complete Optimization Guide

### 📋 Table of Contents
1. [Quick Start](#quick-start)
2. [System Specifications](#system-specifications)
3. [Optimal Flags (Copy & Paste)](#optimal-flags-copy--paste)
4. [Kernel Compilation](#kernel-compilation)
5. [Performance Profiles](#performance-profiles)
6. [Security Hardening](#security-hardening)
7. [Advanced Techniques](#advanced-techniques)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start

### One-Line Optimal Flags
```bash
export CFLAGS_OPTIMAL="-O3 -pipe -fomit-frame-pointer -funroll-loops -fstrict-aliasing -fno-plt -fdata-sections -ffunction-sections -flto=auto -march=meteorlake -mtune=meteorlake -msse4.2 -mpopcnt -mavx -mavx2 -mfma -mf16c -mbmi -mbmi2 -mlzcnt -mmovbe -mavxvnni -maes -mvaes -mpclmul -mvpclmulqdq -msha -mgfni -madx -mclflushopt -mclwb -mcldemote -mmovdiri -mmovdir64b -mwaitpkg -mserialize -mtsxldtrk -muintr -mprefetchw -mprfchw -mrdrnd -mrdseed"
```

### Quick Test
```bash
echo 'int main(){return 0;}' | gcc -xc $CFLAGS_OPTIMAL - -o /tmp/test && echo "✓ Working!"
```

---

## System Specifications

| Component | Specification | Flags Impact |
|-----------|--------------|--------------|
| **CPU** | Intel Core Ultra 7 165H | `-march=meteorlake -mtune=meteorlake` |
| **Cores** | 16 (6P + 10E) | Hybrid aware compilation |
| **Architecture** | Meteor Lake (Family 6 Model 170) | Full AVX2 + VNNI |
| **GPU** | Intel Arc (Xe-LPG, 128 EUs) | GPU offload capable |
| **NPU** | VPU 3720 (2 NCEs) | AI acceleration ready |
| **Cache** | 24MB L3 | Cache optimization flags |

---

## Optimal Flags (Copy & Paste)

### 🎯 **COMPLETE OPTIMAL SET**
```bash
# Base optimization
CFLAGS_BASE="-O3 -pipe -fomit-frame-pointer -funroll-loops -fstrict-aliasing -fno-plt -fdata-sections -ffunction-sections -flto=auto -fuse-linker-plugin"

# Architecture 
ARCH_FLAGS="-march=meteorlake -mtune=meteorlake"

# Vector instructions
VECTOR_FLAGS="-mavx -mavx2 -mfma -mf16c -mavxvnni"

# Bit manipulation
BMI_FLAGS="-mbmi -mbmi2 -mlzcnt -mpopcnt -madx"

# Cryptography
CRYPTO_FLAGS="-maes -mvaes -mpclmul -mvpclmulqdq -msha -mgfni"

# Memory operations
MEMORY_FLAGS="-mmovbe -mmovdiri -mmovdir64b -mclflushopt -mclwb -mcldemote"

# Advanced features
ADVANCED_FLAGS="-mwaitpkg -mserialize -mtsxldtrk -muintr -mprefetchw -mprfchw"

# Security features
SECURITY_FLAGS="-mrdrnd -mrdseed -mfsgsbase -mfxsr -mxsave -mxsaveopt"

# Combined optimal
export CFLAGS_OPTIMAL="$CFLAGS_BASE $ARCH_FLAGS $VECTOR_FLAGS $BMI_FLAGS $CRYPTO_FLAGS $MEMORY_FLAGS $ADVANCED_FLAGS $SECURITY_FLAGS"

# Linker flags
export LDFLAGS_OPTIMAL="-Wl,--as-needed -Wl,--gc-sections -Wl,-O1 -Wl,--hash-style=gnu -flto=auto"
```

### 📦 **MINIMAL HIGH-PERFORMANCE SET**
```bash
# If the full set causes issues, use this minimal set
export CFLAGS_MINIMAL="-O3 -march=meteorlake -mtune=meteorlake -mavx2 -mfma -mavxvnni -maes -msha -pipe -flto=auto"
```

---

## Kernel Compilation

### 🐧 **Linux Kernel Flags**
```bash
# Kernel-specific optimizations
export KCFLAGS="-O3 -pipe -march=meteorlake -mtune=meteorlake -mavx2 -mfma -mavxvnni -maes -mvaes -mpclmul -mvpclmulqdq -msha -mgfni -falign-functions=32 -falign-jumps=32 -falign-loops=32"

export KCPPFLAGS="$KCFLAGS"

# Build kernel
make menuconfig
make -j16 KCFLAGS="$KCFLAGS" KCPPFLAGS="$KCPPFLAGS"

# Alternative with clang
make CC=clang KCFLAGS="$KCFLAGS" -j16
```

### ⚙️ **Kernel Config Recommendations**
```bash
CONFIG_MARCH_METEORLAKE=y
CONFIG_GENERIC_CPU=n
CONFIG_MNATIVE_INTEL=y
CONFIG_CC_OPTIMIZE_FOR_PERFORMANCE_O3=y
CONFIG_OPTIMIZE_INLINING=y
CONFIG_CC_OPTIMIZE_FOR_SIZE=n
```

---

## Performance Profiles

### 🚀 **Maximum Speed** (Unsafe, Fastest)
```bash
export CFLAGS_SPEED="-Ofast -march=meteorlake -mtune=meteorlake -mavx2 -mfma -mavxvnni -ffast-math -funsafe-math-optimizations -ffinite-math-only -fno-signed-zeros -fno-trapping-math -frounding-math -fsingle-precision-constant -fcx-limited-range"
```

### ⚖️ **Balanced** (Safe, Fast)
```bash
export CFLAGS_BALANCED="-O2 -march=meteorlake -mtune=meteorlake -mavx2 -mfma -mavxvnni -maes -msha -ftree-vectorize -pipe"
```

### 📏 **Size Optimized** (Smallest)
```bash
export CFLAGS_SIZE="-Os -march=meteorlake -mtune=meteorlake -fomit-frame-pointer -finline-limit=8"
```

### 🐛 **Debug** (Development)
```bash
export CFLAGS_DEBUG="-Og -g3 -ggdb -march=meteorlake -fno-omit-frame-pointer -fno-inline -fstack-protector-all -D_DEBUG"
```

---

## Security Hardening

### 🔒 **Security Hardened Flags**
```bash
# Compilation flags
export CFLAGS_SECURE="$CFLAGS_OPTIMAL \
    -D_FORTIFY_SOURCE=3 \
    -fstack-protector-strong \
    -fstack-clash-protection \
    -fcf-protection=full \
    -fpie \
    -fPIC \
    -Wformat -Wformat-security \
    -Werror=format-security \
    -mindirect-branch=thunk \
    -mfunction-return=thunk \
    -mindirect-branch-register"

# Linker flags
export LDFLAGS_SECURE="-Wl,-z,relro -Wl,-z,now -Wl,-z,noexecstack -Wl,-z,separate-code -pie"
```

---

## Advanced Techniques

### 📊 **Profile-Guided Optimization (PGO)**
```bash
# Step 1: Build with profiling
gcc $CFLAGS_OPTIMAL -fprofile-generate -o app_prof app.c
./app_prof  # Run with typical workload
            
# Step 2: Build with profile data  
gcc $CFLAGS_OPTIMAL -fprofile-use -o app app.c
```

### 🔄 **Link-Time Optimization (LTO)**
```bash
# Full LTO
export CFLAGS_LTO="$CFLAGS_OPTIMAL -flto=auto -fuse-linker-plugin"
export LDFLAGS_LTO="-flto=auto -fuse-linker-plugin -Wl,-flto"

# Thin LTO (LLVM/Clang)
export CFLAGS_THIN_LTO="$CFLAGS_OPTIMAL -flto=thin"
```

### ⚡ **Graphite Loop Optimizations**
```bash
export GRAPHITE_FLAGS="-fgraphite -fgraphite-identity -floop-nest-optimize -floop-parallelize-all"
```

### 🧵 **OpenMP Parallelization**
```bash
export OPENMP_FLAGS="-fopenmp -fopenmp-simd"
export OMP_NUM_THREADS=6  # Use P-cores only
export GOMP_CPU_AFFINITY="0-5"  # Pin to P-cores
```

---

## Build System Integration

### CMake
```cmake
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -O3 -march=meteorlake -mtune=meteorlake -mavx2 -mavxvnni")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -march=meteorlake -mtune=meteorlake -mavx2 -mavxvnni")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -flto=auto")
```

### Meson
```meson
add_project_arguments('-O3', '-march=meteorlake', '-mavxvnni', language: 'c')
add_project_link_arguments('-flto=auto', language: 'c')
```

### Autotools
```bash
./configure CFLAGS="$CFLAGS_OPTIMAL" LDFLAGS="$LDFLAGS_OPTIMAL"
```

---

## Compiler-Specific

### GCC 13+
```bash
export GCC13_FLAGS="-std=gnu2x -fharden-compares -fharden-conditional-branches -ftrivial-auto-var-init=zero -fanalyzer"
```

### Clang/LLVM 17+
```bash
export CLANG_FLAGS="-mllvm -inline-threshold=1000 -mllvm -unroll-threshold=1000 -mllvm -vectorize-loops"
```

### Intel oneAPI DPC++/ICC
```bash
export INTEL_FLAGS="-xCORE-AVX2 -qopt-zmm-usage=high -qopt-report=5"
```

---

## Performance Tips

### 1. **CPU Affinity for Hybrid Architecture**
```bash
# Use P-cores for performance critical
taskset -c 0-5 ./app

# Use E-cores for background tasks
taskset -c 6-15 ./background_app
```

### 2. **Disable E-cores for AVX-512** (If available)
```bash
for i in {6..15}; do
    echo 0 | sudo tee /sys/devices/system/cpu/cpu$i/online
done
```

### 3. **Memory Tuning**
```bash
export MALLOC_ARENA_MAX=4
export MALLOC_MMAP_THRESHOLD_=131072
echo 1024 | sudo tee /proc/sys/vm/nr_hugepages
```

---

## Troubleshooting

### ❌ **"cc1: error: bad value 'meteorlake' for '-march=' switch"**
```bash
# Use fallback:
export CFLAGS="${CFLAGS/meteorlake/alderlake}"
export CFLAGS="${CFLAGS/mtune=meteorlake/mtune=alderlake}"
```

### ❌ **"unrecognized command line option '-mavxvnni'"**
```bash
# Check GCC version (need 11+)
gcc --version

# Remove if not supported
export CFLAGS="${CFLAGS/-mavxvnni/}"
```

### ❌ **LTO Errors**
```bash
# Disable LTO
export CFLAGS="${CFLAGS/-flto=auto/}"
export LDFLAGS="${LDFLAGS/-flto=auto/}"
```

---

## Quick Function Reference

```bash
# Source the complete flags
source METEOR_LAKE_COMPLETE_FLAGS.sh

# Available functions:
show_flags()       # Display all flag sets
test_flags()       # Verify flags work
compile_optimal()  # Compile with optimal flags
compile_kernel()   # Build kernel with optimal flags
compile_pgo()      # Build with PGO
```

---

## Summary Table

| Use Case | Flags Variable | Key Options |
|----------|---------------|-------------|
| **General** | `$CFLAGS_OPTIMAL` | `-O3 -march=meteorlake -mavxvnni` |
| **Kernel** | `$KCFLAGS` | `-O3 -march=meteorlake -falign-functions=32` |
| **Security** | `$CFLAGS_SECURE` | `-D_FORTIFY_SOURCE=3 -fstack-protector-strong` |
| **Speed** | `$CFLAGS_SPEED` | `-Ofast -ffast-math` |
| **Debug** | `$CFLAGS_DEBUG` | `-Og -g3 -ggdb` |

---

## 📝 Notes

- **NPU/GPU**: Handle separately with OpenVINO/oneAPI
- **AVX-512**: Not available on Meteor Lake (P-cores limited to AVX2)
- **AMX**: May be available but requires kernel 5.18+ and BIOS support
- **Testing**: Always test with `echo 'int main(){return 0;}' | gcc -xc $FLAGS -`

---

**Version**: FINAL - November 2024  
**System**: Intel Core Ultra 7 165H (Meteor Lake)  
**Author**: KYBERLOCK Research Division
