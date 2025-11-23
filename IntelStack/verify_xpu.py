#!/usr/bin/env python3
import torch
import intel_extension_for_pytorch as ipex

print("=" * 60)
print("Intel XPU Verification")
print("=" * 60)
print(f"torch version: {torch.__version__}")
print(f"ipex version:  {ipex.__version__}")

available = torch.xpu.is_available()
print(f"\nXPU available: {available}")
if available:
    print(f"device count: {torch.xpu.device_count()}")
    print(f"device name:  {torch.xpu.get_device_name(0)}")
    print(f"properties:   {torch.xpu.get_device_properties(0)}")
else:
    print("No XPU detected. Ensure xe/i915 modules are loaded, firmware present, and LD_LIBRARY_PATH includes /usr/local/lib.")

print("=" * 60)
