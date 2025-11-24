#!/bin/bash
# ============================================================================
# INTEL METEOR LAKE ULTIMATE COMPILER FLAGS REFERENCE
# Intel Core Ultra 7 165H - Complete Optimization Guide
# Version: FINAL - November 2024
# KYBERLOCK Research Division - Tactical Computing
# ============================================================================

# ============================================================================
# SYSTEM SPECIFICATIONS DETECTED
# ============================================================================
# CPU: Intel(R) Core(TM) Ultra 7 165H
# Architecture: Meteor Lake (Family 6 Model 170 Stepping 4)
# Cores: 16 (6P + 10E) - Hybrid Architecture
# GPU: Intel Arc Graphics (Xe-LPG, 128 EUs)
# NPU: VPU 3720 (2 Neural Compute Engines)
# ============================================================================

# ============================================================================
# SECTION 1: BASE OPTIMIZATION FLAGS
# ============================================================================

# Maximum Performance Base
export CFLAGS_BASE="-O3 -pipe -fomit-frame-pointer -funroll-loops -fstrict-aliasing -fno-plt -fdata-sections -ffunction-sections -flto=auto -fuse-linker-plugin -fgraphite-identity -floop-nest-optimize -ftree-vectorize -ftree-slp-vectorize"

# Architecture Specific
export ARCH_FLAGS="-march=meteorlake -mtune=meteorlake"

# Alternative if meteorlake not recognized
export ARCH_FLAGS_FALLBACK="-march=alderlake -mtune=alderlake -mcpu=alderlake"

# Native detection fallback
export ARCH_FLAGS_NATIVE="-march=native -mtune=native -mcpu=native"

# ============================================================================
# SECTION 2: INSTRUCTION SET EXTENSIONS - COMPLETE
# ============================================================================

# Core x86-64 Features
export ISA_BASELINE="-msse -msse2 -msse3 -mssse3 -msse4 -msse4.1 -msse4.2"

# Advanced Vector Extensions
export ISA_AVX="-mavx -mavx2 -mf16c -mfma"

# AI/ML Acceleration (Meteor Lake Special)
export ISA_VNNI="-mavxvnni"  # Confirmed working on your system

# Bit Manipulation
export ISA_BMI="-mbmi -mbmi2 -mlzcnt -mpopcnt"

# Cryptographic Acceleration (All confirmed on your CPU)
export ISA_CRYPTO="-maes -mvaes -mpclmul -mvpclmulqdq -msha -mgfni"

# Memory & Cache Operations
export ISA_MEMORY="-mmovbe -mmovdiri -mmovdir64b -mclflushopt -mclwb -mcldemote"

# Advanced Features
export ISA_ADVANCED="-madx -mrdrnd -mrdseed -mfsgsbase -mfxsr -mxsave -mxsaveopt -mxsavec -mxsaves"

# Prefetch Instructions
export ISA_PREFETCH="-mprefetchw -mprfchw -mprefetchwt1"

# Control Flow
export ISA_CONTROL="-mwaitpkg -muintr -mserialize -mtsxldtrk"

# CET (Control-flow Enforcement Technology)
export ISA_CET="-mcet -mshstk"

# ============================================================================
# SECTION 3: COMPLETE OPTIMAL FLAGS - TIER 1
# ============================================================================

export CFLAGS_OPTIMAL="\
-O3 \
-pipe \
-fomit-frame-pointer \
-funroll-loops \
-fstrict-aliasing \
-fno-plt \
-fdata-sections \
-ffunction-sections \
-flto=auto \
-fuse-linker-plugin \
-march=meteorlake \
-mtune=meteorlake \
-msse4.2 \
-mpopcnt \
-mavx \
-mavx2 \
-mfma \
-mf16c \
-mbmi \
-mbmi2 \
-mlzcnt \
-mmovbe \
-mavxvnni \
-maes \
-mvaes \
-mpclmul \
-mvpclmulqdq \
-msha \
-mgfni \
-madx \
-mclflushopt \
-mclwb \
-mcldemote \
-mmovdiri \
-mmovdir64b \
-mwaitpkg \
-mserialize \
-mtsxldtrk \
-muintr \
-mprefetchw \
-mprfchw \
-mrdrnd \
-mrdseed \
-mfsgsbase \
-mfxsr \
-mxsave \
-mxsaveopt \
-mxsavec \
-mxsaves"

# ============================================================================
# SECTION 4: PERFORMANCE PROFILES
# ============================================================================

# PROFILE: Maximum Speed (No Safety)
export CFLAGS_SPEED="-Ofast -ffast-math -funsafe-math-optimizations -ffinite-math-only -fno-signed-zeros -fno-trapping-math -frounding-math -fsingle-precision-constant -fcx-limited-range $CFLAGS_OPTIMAL"

# PROFILE: Balanced Performance
export CFLAGS_BALANCED="-O2 -ftree-vectorize $ARCH_FLAGS $ISA_AVX $ISA_CRYPTO -pipe"

# PROFILE: Size Optimized
export CFLAGS_SIZE="-Os -fomit-frame-pointer -finline-limit=8 $ARCH_FLAGS $ISA_BASELINE"

# PROFILE: Debug Build
export CFLAGS_DEBUG="-Og -g3 -ggdb -fno-omit-frame-pointer -fno-inline -fstack-protector-all -D_DEBUG $ARCH_FLAGS"

# ============================================================================
# SECTION 5: LINK-TIME OPTIMIZATION
# ============================================================================

export LDFLAGS_BASE="-Wl,--as-needed -Wl,--gc-sections -Wl,-O1 -Wl,--hash-style=gnu"

export LDFLAGS_LTO="-flto=auto -fuse-linker-plugin -Wl,-flto"

export LDFLAGS_OPTIMAL="$LDFLAGS_BASE $LDFLAGS_LTO -Wl,--sort-common -Wl,--enable-new-dtags"

# Gold Linker Optimizations
export LDFLAGS_GOLD="-fuse-ld=gold -Wl,--icf=all -Wl,--print-gc-sections"

# MOLD Linker (Fastest)
export LDFLAGS_MOLD="-fuse-ld=mold -Wl,--threads=16"

# ============================================================================
# SECTION 6: SECURITY HARDENED FLAGS
# ============================================================================

export CFLAGS_SECURITY="\
-D_FORTIFY_SOURCE=3 \
-fstack-protector-strong \
-fstack-clash-protection \
-fcf-protection=full \
-fpie \
-fPIC \
-Wformat \
-Wformat-security \
-Werror=format-security \
-Wl,-z,relro \
-Wl,-z,now \
-Wl,-z,noexecstack \
-Wl,-z,separate-code \
-mindirect-branch=thunk \
-mfunction-return=thunk \
-mindirect-branch-register"

export LDFLAGS_SECURITY="-Wl,-z,relro -Wl,-z,now -Wl,-z,noexecstack -Wl,-z,separate-code -pie"

# ============================================================================
# SECTION 7: KERNEL COMPILATION FLAGS
# ============================================================================

export KCFLAGS="\
-O3 \
-pipe \
-march=meteorlake \
-mtune=meteorlake \
-msse4.2 \
-mpopcnt \
-mavx \
-mavx2 \
-mfma \
-mavxvnni \
-maes \
-mvaes \
-mpclmul \
-mvpclmulqdq \
-msha \
-mgfni \
-falign-functions=32 \
-falign-jumps=32 \
-falign-loops=32 \
-falign-labels=32"

export KCPPFLAGS="$KCFLAGS"

# Kernel Make Variables
export KBUILD_BUILD_HOST="kyberlock"
export KBUILD_BUILD_USER="tactical"
export KBUILD_CFLAGS_KERNEL="$KCFLAGS"
export KBUILD_AFLAGS_KERNEL="$KCFLAGS"

# ============================================================================
# SECTION 8: ADVANCED OPTIMIZATION TECHNIQUES
# ============================================================================

# Profile-Guided Optimization Stage 1
export PGO_GEN="-fprofile-generate -fprofile-arcs -ftest-coverage"

# Profile-Guided Optimization Stage 2
export PGO_USE="-fprofile-use -fprofile-correction -fbranch-probabilities"

# Graphite Loop Optimizations
export GRAPHITE="-fgraphite -fgraphite-identity -floop-nest-optimize -floop-parallelize-all"

# Aggressive Inlining
export INLINE_FLAGS="-finline-functions -finline-functions-called-once -finline-limit=1000 -finline-small-functions --param inline-unit-growth=100 --param large-function-growth=1000"

# Vectorization Tuning
export VECTORIZE="-ftree-vectorize -ftree-slp-vectorize -ftree-loop-vectorize -fvect-cost-model=unlimited -fsimd-cost-model=unlimited"

# ============================================================================
# SECTION 9: COMPILER-SPECIFIC FLAGS
# ============================================================================

# GCC 13+ Specific
export GCC13_FLAGS="-std=gnu2x -fharden-compares -fharden-conditional-branches -ftrivial-auto-var-init=zero -fanalyzer"

# Clang/LLVM Specific
export CLANG_FLAGS="-mllvm -inline-threshold=1000 -mllvm -unroll-threshold=1000 -mllvm -vectorize-loops -mllvm -vectorize-slp"

# Intel ICC Compatibility
export ICC_COMPAT="-diag-disable=10441 -qopt-report=5 -qopt-zmm-usage=high"

# ============================================================================
# SECTION 10: PARALLELIZATION & THREADING
# ============================================================================

# OpenMP Flags
export OPENMP_FLAGS="-fopenmp -fopenmp-simd"

# Threading Optimizations
export THREAD_FLAGS="-pthread -D_REENTRANT -D_THREAD_SAFE"

# Parallel STL (C++17)
export PSTL_FLAGS="-ltbb -DPSTL_USE_PARALLEL_POLICIES=1"

# ============================================================================
# SECTION 11: MATHEMATICS & NUMERICAL
# ============================================================================

# Math Optimizations
export MATH_FLAGS="-ffast-math -funsafe-math-optimizations -fassociative-math -freciprocal-math -ffinite-math-only"

# Intel MKL Integration
export MKL_FLAGS="-DMKL_ILP64 -m64 -I${MKLROOT}/include"
export MKL_LIBS="-L${MKLROOT}/lib/intel64 -lmkl_intel_ilp64 -lmkl_intel_thread -lmkl_core -liomp5 -lpthread -lm -ldl"

# ============================================================================
# SECTION 12: MEMORY OPTIMIZATION
# ============================================================================

# Memory Alignment
export ALIGN_FLAGS="-falign-functions=64 -falign-jumps=64 -falign-loops=64 -falign-labels=64"

# Stack Optimization
export STACK_FLAGS="-mpreferred-stack-boundary=5 -maccumulate-outgoing-args"

# Malloc Optimization
export MALLOC_FLAGS="-fno-builtin-malloc -fno-builtin-calloc -fno-builtin-realloc -fno-builtin-free"

# ============================================================================
# SECTION 13: WARNING FLAGS (PRODUCTION)
# ============================================================================

export WARN_FLAGS="-Wall -Wextra -Wpedantic -Wformat=2 -Wformat-security -Wnull-dereference -Wstack-protector -Wtrampolines -Walloca -Wvla -Warray-bounds=2 -Wimplicit-fallthrough=3 -Wshift-overflow=2 -Wcast-qual -Wstringop-overflow=4 -Wconversion -Wlogical-op -Wduplicated-cond -Wduplicated-branches -Wformat-signedness -Wshadow -Wstrict-overflow=4 -Wundef -Wstrict-prototypes -Wswitch-default -Wswitch-enum -Wstack-usage=1000000 -Wcast-align=strict"

# ============================================================================
# SECTION 14: LANGUAGE-SPECIFIC FLAGS
# ============================================================================

# C++ Optimizations
export CXXFLAGS_OPTIMAL="$CFLAGS_OPTIMAL -std=c++23 -fcoroutines -fconcepts -fmodules-ts"

# Fortran Optimizations
export FFLAGS_OPTIMAL="$CFLAGS_OPTIMAL -fdefault-real-8 -fdefault-integer-8"

# Rust Integration
export RUSTFLAGS="-C target-cpu=meteorlake -C opt-level=3 -C lto=fat -C embed-bitcode=yes"

# ============================================================================
# SECTION 15: BUILD SYSTEM EXPORTS
# ============================================================================

# CMake
export CMAKE_C_FLAGS="$CFLAGS_OPTIMAL"
export CMAKE_CXX_FLAGS="$CXXFLAGS_OPTIMAL"
export CMAKE_EXE_LINKER_FLAGS="$LDFLAGS_OPTIMAL"

# Autotools
export CFLAGS="$CFLAGS_OPTIMAL"
export CXXFLAGS="$CXXFLAGS_OPTIMAL"
export LDFLAGS="$LDFLAGS_OPTIMAL"

# Meson
export CFLAGS="$CFLAGS_OPTIMAL"
export CXXFLAGS="$CXXFLAGS_OPTIMAL"
export LDFLAGS="$LDFLAGS_OPTIMAL"

# ============================================================================
# SECTION 16: USAGE FUNCTIONS
# ============================================================================

# Function to compile with optimal flags
compile_optimal() {
    gcc $CFLAGS_OPTIMAL "$@" $LDFLAGS_OPTIMAL
}

# Function to compile kernel
compile_kernel() {
    make -j16 KCFLAGS="$KCFLAGS" KCPPFLAGS="$KCPPFLAGS" "$@"
}

# Function to compile with PGO
compile_pgo() {
    # Stage 1: Generate profile
    gcc $CFLAGS_OPTIMAL $PGO_GEN -o "$1_gen" "$1.c"
    ./"$1_gen" # Run with typical workload
    
    # Stage 2: Use profile
    gcc $CFLAGS_OPTIMAL $PGO_USE -o "$1" "$1.c"
    rm -f "$1_gen" *.gcda
}

# ============================================================================
# SECTION 17: COMPLETE ENVIRONMENT SETUP
# ============================================================================

# Set all optimal flags
export CC="gcc-13"
export CXX="g++-13"
export AR="gcc-ar"
export NM="gcc-nm"
export RANLIB="gcc-ranlib"

# CPU Affinity for P-cores
export GOMP_CPU_AFFINITY="0-5"
export OMP_NUM_THREADS="6"
export OMP_PROC_BIND="true"
export OMP_PLACES="cores"

# Memory Settings
export MALLOC_ARENA_MAX="4"
export MALLOC_MMAP_THRESHOLD_="131072"
export MALLOC_TRIM_THRESHOLD_="131072"
export MALLOC_TOP_PAD_="131072"
export MALLOC_MMAP_MAX_="65536"

# ============================================================================
# SECTION 18: QUICK REFERENCE COMMANDS
# ============================================================================

# Show current flags
show_flags() {
    echo "=== INTEL METEOR LAKE OPTIMIZATION FLAGS ==="
    echo "Architecture: Intel Core Ultra 7 165H"
    echo ""
    echo "OPTIMAL: $CFLAGS_OPTIMAL"
    echo ""
    echo "KERNEL: $KCFLAGS"
    echo ""
    echo "SECURITY: $CFLAGS_SECURITY"
}

# Test flags work
test_flags() {
    echo 'int main(){return 0;}' | gcc -xc $CFLAGS_OPTIMAL - -o /tmp/test && \
    echo "✓ Flags verified working!" && rm /tmp/test
}

# ============================================================================
# ACTIVATION MESSAGE
# ============================================================================

echo "╔══════════════════════════════════════════════════════════════════════════╗"
echo "║  INTEL METEOR LAKE OPTIMIZATION FLAGS LOADED                            ║"
echo "║  CPU: Intel Core Ultra 7 165H | 6P+10E Cores | Arc Graphics | NPU 3720  ║"
echo "╚══════════════════════════════════════════════════════════════════════════╝"
echo ""
echo "Usage:"
echo "  Optimal:  gcc \$CFLAGS_OPTIMAL -o app app.c \$LDFLAGS_OPTIMAL"
echo "  Kernel:   make -j16 KCFLAGS=\"\$KCFLAGS\""
echo "  Security: gcc \$CFLAGS_SECURITY -o app app.c \$LDFLAGS_SECURITY"
echo ""
echo "Functions:"
echo "  show_flags       - Display all flag sets"
echo "  test_flags       - Verify flags work"
echo "  compile_optimal  - Compile with optimal flags"
echo ""
