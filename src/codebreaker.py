#!/usr/bin/env python3
"""Codebreaker mode utilities.

Provides a lightweight CLI for inspecting encoded payloads and
surfacing local AI device inventory so operators can choose the right
accelerator for decoding workloads.
"""

import base64
import subprocess
from pathlib import Path
from typing import Dict, Tuple, List, Optional, Iterable

import yaml

DEFAULT_PAYLOAD = (
    "MAwMGwADN0g4ODQDP8gCJCAgNwwDMwQ0NDADyIjMwMzMwADMxIDA1IiMmYCNzMjIyMzM8wT09PDP+4jP4Pz8/gTP/8jo/PzO7sjLTMTExNiMxEycnMTJgACIiISEhcjIjMCwsIyL40SL6Ljsu81LogSkpKCKqoiK"
)
DEFAULT_HARDWARE_CONFIG = Path(__file__).resolve().parent.parent / "config" / "hardware.yaml"
SIMON_SPECK_REPO = "https://github.com/nsacyber/simon-speck-supercop"
DEFAULT_SUPERCOP_PATH = Path(__file__).resolve().parent.parent / "external" / "simon-speck-supercop"


def decode_base64_payload(encoded: str) -> Tuple[bytes, List[str]]:
    """Attempt to base64-decode the provided payload.

    Returns the decoded bytes and any warnings encountered during decoding.
    """

    warnings: List[str] = []
    cleaned = (encoded or "").strip()

    if not cleaned:
        return b"", ["No payload provided to decode."]

    try:
        return base64.b64decode(cleaned, validate=True), warnings
    except Exception as exc:  # noqa: BLE001 - intentional user feedback
        warnings.append(f"Strict base64 validation failed: {exc}")

    padded = cleaned + "=" * (-len(cleaned) % 4)
    try:
        return base64.b64decode(padded), warnings
    except Exception as exc:  # noqa: BLE001 - intentional user feedback
        warnings.append(f"Padded base64 decoding failed: {exc}")
        return b"", warnings


def ascii_preview(data: bytes, max_len: int = 96) -> str:
    """Return a printable ASCII preview of the decoded payload."""

    printable = []
    for byte in data[:max_len]:
        if 32 <= byte <= 126:
            printable.append(chr(byte))
        else:
            printable.append(".")
    suffix = "" if len(data) <= max_len else " …"
    return "".join(printable) + suffix


def hex_preview(data: bytes, max_len: int = 64) -> str:
    """Return a hex preview of the decoded payload."""

    chunk = data[:max_len]
    suffix = "" if len(data) <= max_len else " …"
    return " ".join(f"{byte:02x}" for byte in chunk) + suffix


def load_ai_devices(hardware_path: Path) -> Dict[str, Dict]:
    """Load accelerator metadata from the hardware configuration file."""

    if not hardware_path.exists():
        return {}

    with hardware_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    accelerators = config.get("accelerators", {})
    return accelerators if isinstance(accelerators, dict) else {}


def format_ai_devices(accelerators: Dict[str, Dict]) -> List[str]:
    """Format accelerator details into readable lines."""

    lines: List[str] = []
    for key, info in accelerators.items():
        if not isinstance(info, dict):
            continue

        name = info.get("name", key)
        tops = info.get("tops") or info.get("tops_total") or info.get("tops_each")
        power = info.get("power_w") or info.get("power_w_each")
        best_for = ", ".join(info.get("best_for", [])) if info.get("best_for") else "unspecified"
        quant = ", ".join(info.get("quantization", [])) if info.get("quantization") else "unspecified"
        lines.append(
            f"- {name} ({key}): {tops} TOPS, {power}W, quant: {quant}, best for {best_for}"
        )

    return lines


def compute_ai_power(accelerators: Dict[str, Dict]) -> Dict[str, Optional[float]]:
    """Compute aggregate accelerator metrics.

    Returns a mapping with total TOPS, device count, and the strongest device name.
    """

    total_tops: float = 0.0
    device_count = 0
    strongest_device: Optional[str] = None
    strongest_tops: float = -1.0

    for key, info in accelerators.items():
        if not isinstance(info, dict):
            continue

        count = info.get("count", 1) or 1
        tops = info.get("tops_total")

        if tops is None:
            tops_each = info.get("tops_each")
            tops = tops_each * count if tops_each is not None else info.get("tops")

        if tops is None:
            continue

        total_tops += float(tops)
        device_count += count

        if float(tops) > strongest_tops:
            strongest_tops = float(tops)
            strongest_device = info.get("name", key)

    return {
        "total_tops": total_tops if device_count else None,
        "device_count": device_count,
        "strongest_device": strongest_device,
    }


def guess_encryption_profile(decoded: bytes) -> Tuple[str, bool]:
    """Heuristic classification of the decoded payload.

    Returns a tuple of (encryption/encoding guess, sentence-like boolean).
    """

    if not decoded:
        return "unknown", False

    printable = sum(1 for b in decoded if 32 <= b <= 126)
    ratio = printable / len(decoded)
    sentence_like = ratio > 0.75 and any(chr(b) == " " for b in decoded)

    if ratio > 0.9:
        return "plaintext/ASCII (likely base64-encoded)", sentence_like
    if ratio > 0.6:
        return "mixed ASCII/binary (light obfuscation)", sentence_like
    return "binary/unknown cipher", sentence_like


def prepare_supercop_checkout(target_dir: Path) -> Tuple[bool, List[str]]:
    """Ensure the Simon/Speck SUPERCOP repository is available locally."""

    notes: List[str] = []
    if target_dir.exists():
        notes.append(f"Found existing SUPERCOP checkout at {target_dir}.")
        return True, notes

    target_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", SIMON_SPECK_REPO, str(target_dir)],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            notes.append(
                "git clone failed; install manually: git clone --depth 1 "
                f"{SIMON_SPECK_REPO} {target_dir}"
            )
            if result.stderr:
                notes.append(f"git stderr: {result.stderr.strip()}")
            return False, notes
        notes.append(f"Cloned SUPERCOP suite to {target_dir}.")
        return True, notes
    except FileNotFoundError:
        notes.append("git not available; cannot clone SUPERCOP.")
        return False, notes


def benchmark_simon_speck(accelerators: Dict[str, Dict], repo_dir: Path) -> Tuple[List[str], List[str]]:
    """Produce SUPERCOP benchmark notes and attempt a lightweight run."""

    log: List[str] = []
    warnings: List[str] = []

    available, prep_notes = prepare_supercop_checkout(repo_dir)
    log.extend(prep_notes)

    if not available:
        warnings.append("SUPERCOP suite unavailable; benchmark skipped.")
        return log, warnings

    build_root = repo_dir / "supercop"
    runner = build_root / "do"
    power = compute_ai_power(accelerators)
    device_names = [info.get("name", key) for key, info in accelerators.items() if isinstance(info, dict)]
    log.append(
        "Targeting SUPERCOP across all devices: "
        + (", ".join(device_names) if device_names else "none listed")
    )
    if power.get("total_tops"):
        log.append(f"Aggregate TOPS available: {power['total_tops']:.1f} (entries: {power['device_count']})")
    log.append(f"Runner path: {runner} (shell executed)")

    if not runner.exists():
        warnings.append(
            f"Runner script not found at {runner}; consult {SIMON_SPECK_REPO} docs for build steps."
        )
        return log, warnings

    for key, info in accelerators.items():
        tops = info.get("tops_total") or info.get("tops") or info.get("tops_each")
        quant = ", ".join(info.get("quantization", [])) if info.get("quantization") else "unspecified"
        log.append(
            f"Planned SUPERCOP run for {info.get('name', key)}: TOPS={tops}, quant={quant}, target={key}"
        )

    try:
        result = subprocess.run(
            ["/bin/sh", str(runner)],
            cwd=runner.parent,
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            warnings.append(
                "SUPERCOP execution returned non-zero; review output for details (run manually if needed)."
            )
        if result.stdout:
            lines = result.stdout.splitlines()
            sample = "\n".join(lines[:20])
            log.append(f"SUPERCOP output (first 20 lines):\n{sample}")
            if len(lines) > 20:
                log.append(f"… truncated, {len(lines)} total lines captured")
        if result.stderr:
            warnings.append(f"SUPERCOP stderr (truncated): {result.stderr.splitlines()[:3]}")
    except FileNotFoundError:
        warnings.append("Shell not available to execute SUPERCOP runner.")

    return log, warnings


def select_devices(
    accelerators: Dict[str, Dict], selected_keys: Optional[Iterable[str]]
) -> Tuple[Dict[str, Dict], List[str]]:
    """Filter accelerator dictionary by the provided keys.

    Returns the filtered accelerators and a list of requested keys that were missing.
    If no keys are provided, all accelerators are returned.
    Supports special tokens like "all" or "*" to explicitly request the full inventory.
    """

    if not selected_keys:
        return accelerators, []

    normalized = {k.lower(): k for k in accelerators.keys()}
    filtered: Dict[str, Dict] = {}
    missing: List[str] = []

    for key in selected_keys:
        if key is None:
            continue
        lower_key = key.lower().strip()
        if lower_key in {"all", "*"}:
            return accelerators, []
        if lower_key in normalized:
            original_key = normalized[lower_key]
            filtered[original_key] = accelerators[original_key]
        else:
            missing.append(key)

    return filtered, missing


def optimize_for_devices(accelerators: Dict[str, Dict]) -> List[str]:
    """Generate optimization guidance for the selected accelerators."""

    if not accelerators:
        return ["No accelerators available to optimize."]

    plan: List[str] = []
    total_power = 0.0
    quant_modes: set[str] = set()
    workloads: set[str] = set()

    for info in accelerators.values():
        if not isinstance(info, dict):
            continue
        power_each = info.get("power_w") or info.get("power_w_each")
        count = info.get("count", 1) or 1
        if power_each:
            total_power += float(power_each) * count
        quant_modes.update(info.get("quantization", []) or [])
        workloads.update(info.get("best_for", []) or [])

    power_stats = compute_ai_power(accelerators)
    if power_stats.get("total_tops") and total_power:
        efficiency = power_stats["total_tops"] / total_power
        plan.append(f"Efficiency: {efficiency:.2f} TOPS/W across selection")

    if power_stats.get("strongest_device"):
        plan.append(f"Lead device: {power_stats['strongest_device']}")

    if quant_modes:
        plan.append("Quantization ready: " + ", ".join(sorted(quant_modes)))

    if workloads:
        plan.append("Optimized workloads: " + ", ".join(sorted(workloads)))

    return plan


def run_codebreaker_mode(
    encoded_payload: str | None = None,
    hardware_config_path: str | None = None,
    device_keys: Optional[Iterable[str]] = None,
    benchmark_crypto: bool = False,
    supercop_path: Path | None = DEFAULT_SUPERCOP_PATH,
) -> None:
    """Execute codebreaker mode with decoding, hardware summaries, and SUPERCOP support."""

    payload = encoded_payload or DEFAULT_PAYLOAD
    hardware_path = Path(hardware_config_path) if hardware_config_path else DEFAULT_HARDWARE_CONFIG
    supercop_root = Path(supercop_path) if supercop_path else DEFAULT_SUPERCOP_PATH

    normalized_keys = [key.strip() for key in device_keys or [] if key is not None and key.strip()]
    use_all_devices = any(k.lower() in {"all", "*"} for k in normalized_keys)
    selection_label = ", ".join(normalized_keys) if normalized_keys else "all"

    decoded, warnings = decode_base64_payload(payload)
    enc_profile, sentence_like = guess_encryption_profile(decoded)

    print("Payload Analysis")
    print("-" * 60)
    print(f"Encoded length: {len(payload)} characters")
    print(f"Decoded length: {len(decoded)} bytes")
    if warnings:
        for warning in warnings:
            print(f"Warning: {warning}")

    if decoded:
        print(f"Hex preview: {hex_preview(decoded)}")
        print(f"ASCII preview: {ascii_preview(decoded)}")
    else:
        print("No decoded bytes available.")

    accelerators = load_ai_devices(hardware_path)
    print()
    print("AI Device Inventory")
    print("-" * 60)
    if not accelerators:
        print(f"No accelerators found at {hardware_path}.")
        return

    if device_keys:
        print(f"Requested devices: {selection_label}")

    scoped_accelerators, missing = select_devices(accelerators, normalized_keys if not use_all_devices else [])
    if missing:
        print(f"Missing requested devices: {', '.join(missing)}")

    if not scoped_accelerators:
        print("No accelerators match the provided selection.")
        return

    power = compute_ai_power(scoped_accelerators)
    tops_used = power.get("total_tops")
    if tops_used:
        print(
            f"Total Available: {tops_used:.1f} TOPS across {power['device_count']} device entries"
        )
    if power.get("strongest_device"):
        print(f"Strongest node: {power['strongest_device']}")

    for line in format_ai_devices(scoped_accelerators):
        print(line)

    if benchmark_crypto:
        print()
        print("Simon/Speck SUPERCOP Benchmark")
        print("-" * 60)
        bench_log, bench_warn = benchmark_simon_speck(scoped_accelerators, supercop_root)
        for entry in bench_log:
            print(f"- {entry}")
        for warn in bench_warn:
            print(f"Warning: {warn}")

    print("Optimization Plan")
    print("-" * 60)
    for line in optimize_for_devices(scoped_accelerators):
        print(f"- {line}")

    print()
    print("Final Classification")
    print("-" * 60)
    sentence_flag = "yes" if sentence_like else "no"
    tops_msg = f"{tops_used:.1f} TOPS engaged" if tops_used else "TOPS unavailable"
    print(f"Encryption type guess: {enc_profile}")
    print(f"Sentence-like payload: {sentence_flag}")
    print(f"TOPS utilization estimate: {tops_msg}")
