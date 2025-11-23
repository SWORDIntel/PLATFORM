#!/usr/bin/env python3
"""
DSMIL Router Benchmark Suite (Standalone)

Tests routing performance, latency, and expert selection accuracy.
No external dependencies required.
"""

import time
import statistics
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


# ============================================================
# Inline router logic (extracted from generic_router.py)
# ============================================================

class HardwareAccelerator(Enum):
    """Available hardware accelerators with TOPS and latency characteristics."""
    NPU = {"tops": 30, "latency": 10, "power": 6.5, "best_for": "realtime_inference"}
    MOVIDUS = {"tops": 4, "latency": 5, "power": 2.5, "best_for": "edge_vision"}
    MIL_NPU = {"tops": 25, "latency": 8, "power": 8.0, "best_for": "tactical_inference"}
    IGPU = {"tops": 40, "latency": 30, "power": 20, "best_for": "vision_inference"}
    AMX = {"tops": 32, "latency": 50, "power": 25, "best_for": "llm_inference"}
    AVX512 = {"tops": 10, "latency": 100, "power": 15, "best_for": "preprocessing"}
    CPU = {"tops": 5, "latency": 200, "power": 10, "best_for": "fallback"}


class ModelSize(Enum):
    """Model size categories with parameter counts and recommended hardware."""
    TINY = {"params": 100_000_000, "hardware": [HardwareAccelerator.NPU, HardwareAccelerator.AVX512]}
    SMALL = {"params": 500_000_000, "hardware": [HardwareAccelerator.IGPU, HardwareAccelerator.AMX]}
    MEDIUM = {"params": 1_000_000_000, "hardware": [HardwareAccelerator.AMX, HardwareAccelerator.IGPU]}
    LARGE = {"params": 7_000_000_000, "hardware": [HardwareAccelerator.AMX, HardwareAccelerator.CPU]}


EXPERTS = {
    # NPU-ACCELERATED (Intel NPU 3720, 30 TOPS)
    "npu_realtime": {
        "weight": 1.6, "layer": 2, "hardware": HardwareAccelerator.NPU,
        "best_for": ["realtime_inference", "streaming", "low_latency", "sensor_fusion"],
    },
    "npu_classifier": {
        "weight": 1.4, "layer": 2, "hardware": HardwareAccelerator.NPU,
        "best_for": ["classification", "anomaly_detection", "intent_recognition"],
    },
    # MOVIDUS VPU (Myriad X, 4 TOPS, 2.5W)
    "movidus_vision": {
        "weight": 1.3, "layer": 2, "hardware": HardwareAccelerator.MOVIDUS,
        "best_for": ["edge_vision", "object_detection", "thermal_imaging", "isr_processing"],
    },
    "movidus_tactical": {
        "weight": 1.4, "layer": 2, "hardware": HardwareAccelerator.MOVIDUS,
        "best_for": ["video_analytics", "target_tracking", "motion_detection"],
    },
    # MILITARY NPU (TEMPEST-compliant, 25 TOPS)
    "mil_npu_tactical": {
        "weight": 1.5, "layer": 3, "hardware": HardwareAccelerator.MIL_NPU,
        "best_for": ["tactical_inference", "iff_processing", "threat_classification", "c2_support"],
    },
    "mil_npu_sigint": {
        "weight": 1.4, "layer": 3, "hardware": HardwareAccelerator.MIL_NPU,
        "best_for": ["sigint", "comint", "elint", "signal_classification"],
    },
    # LAYER 3-9 EXPERTS
    "layer3_analytics": {
        "weight": 1.0, "layer": 3, "hardware": HardwareAccelerator.AVX512,
        "best_for": ["data_analysis", "signal_processing", "compartmented_analytics"],
    },
    "layer4_decision": {
        "weight": 1.1, "layer": 4, "hardware": HardwareAccelerator.AMX,
        "best_for": ["control_flow", "logic_synthesis", "decision_support"],
    },
    "layer5_predictive": {
        "weight": 1.2, "layer": 5, "hardware": HardwareAccelerator.IGPU,
        "best_for": ["ml_inference", "pattern_recognition", "predictive_analytics"],
    },
    "layer5_npu_predict": {
        "weight": 1.3, "layer": 5, "hardware": HardwareAccelerator.NPU,
        "best_for": ["realtime_prediction", "streaming_ml", "time_series"],
    },
    "layer6_nuclear": {
        "weight": 1.3, "layer": 6, "hardware": HardwareAccelerator.AMX,
        "best_for": ["nuclear_analysis", "strategic_intelligence", "threat_assessment"],
    },
    "layer7_llm": {
        "weight": 1.5, "layer": 7, "hardware": HardwareAccelerator.AMX,
        "best_for": ["code_generation", "nlp", "text_synthesis", "llm_inference"],
    },
    "layer8_security": {
        "weight": 1.2, "layer": 8, "hardware": HardwareAccelerator.IGPU,
        "best_for": ["security_analysis", "adversarial_defense", "threat_detection"],
    },
    "layer8_npu_anomaly": {
        "weight": 1.4, "layer": 8, "hardware": HardwareAccelerator.NPU,
        "best_for": ["realtime_anomaly", "intrusion_detection", "network_monitoring"],
    },
    "layer9_strategic": {
        "weight": 1.4, "layer": 9, "hardware": HardwareAccelerator.AMX,
        "best_for": ["strategic_synthesis", "executive_command", "high_level_analysis"],
    },
    "shared_general": {
        "weight": 0.8, "layer": 0, "hardware": HardwareAccelerator.CPU,
        "best_for": ["fallback", "general_purpose"],
    },
}


def estimate_model_size(prompt: str, metadata: Dict[str, Any]) -> ModelSize:
    """Estimate required model size based on task complexity."""
    complexity = metadata.get("complexity", "medium")
    if len(prompt) < 100 or complexity == "simple":
        return ModelSize.TINY
    elif len(prompt) < 500 or complexity == "medium":
        return ModelSize.SMALL
    elif len(prompt) < 2000:
        return ModelSize.MEDIUM
    else:
        return ModelSize.LARGE


def router_infer_device19(prompt: str, metadata: Dict[str, Any]) -> Dict[str, float]:
    """Device 19 (COMMS) routing classifier with NPU/Movidus/MIL-NPU support."""
    scores = {key: 0.0 for key in EXPERTS.keys()}
    task = metadata.get("task_type", "").lower()
    latency = metadata.get("latency", "").lower()

    # NPU/Real-time routing (Layer 2)
    if "realtime" in task or latency == "critical" or "streaming" in task:
        scores["npu_realtime"] = 0.95
        scores["npu_classifier"] = 0.85
    elif "classification" in task or "anomaly" in task:
        scores["npu_classifier"] = 0.9
        scores["layer8_npu_anomaly"] = 0.8

    # Movidus/Vision routing (Layer 2)
    elif "vision" in task or "tracking" in task or "detection" in task:
        scores["movidus_vision"] = 0.9
        scores["movidus_tactical"] = 0.85

    # Military NPU routing (Layer 3)
    elif "sigint" in task or "comint" in task or "elint" in task:
        scores["mil_npu_sigint"] = 0.95
        scores["mil_npu_tactical"] = 0.8
    elif "tactical" in task or "iff" in task or "c2" in task:
        scores["mil_npu_tactical"] = 0.9
        scores["mil_npu_sigint"] = 0.7

    # Standard routing
    elif "code" in task or "generation" in task:
        scores["layer7_llm"] = 0.9
    elif "security" in task:
        scores["layer8_security"] = 0.85
        scores["layer8_npu_anomaly"] = 0.7
    elif "strategic" in task:
        scores["layer9_strategic"] = 0.8
    elif "analytics" in task or "ml" in task or "data" in task:
        scores["layer5_predictive"] = 0.8
        scores["layer5_npu_predict"] = 0.7
    elif "decision" in task:
        scores["layer4_decision"] = 0.75
    else:
        scores["layer7_llm"] = 0.6
        scores["shared_general"] = 0.4

    return scores


def dsmil_optimized_router(prompt: str, metadata: Dict[str, Any]) -> List[tuple]:
    """Advanced routing using DSMIL layer architecture."""
    p = prompt.lower()
    lang = metadata.get("language", "").lower()

    device19_scores = router_infer_device19(p, metadata)
    domain_boosts = {}

    # Systems/kernel
    if lang in ("c", "c++", "rust", "asm") or "kernel" in p or "driver" in p or "register" in p:
        domain_boosts["layer3_analytics"] = 0.7
        domain_boosts["layer4_decision"] = 0.8
        domain_boosts["layer7_llm"] = 0.5

    # Web/frontend
    elif lang in ("js", "ts", "jsx", "tsx", "javascript", "typescript") or "react" in p or "vue" in p or "node" in p:
        domain_boosts["layer7_llm"] = 0.9
        domain_boosts["layer8_security"] = 0.6

    # ML/Data science
    elif "pytorch" in p or "tensorflow" in p or "numpy" in p or "pandas" in p or "dataset" in p:
        domain_boosts["layer5_predictive"] = 0.85
        domain_boosts["layer7_llm"] = 0.7

    # DevOps/Infrastructure
    elif "docker" in p or "kubernetes" in p or "terraform" in p or "ansible" in p or "helm" in p or "deploy" in p:
        domain_boosts["layer6_nuclear"] = 0.8
        domain_boosts["layer4_decision"] = 0.7

    # Security
    elif "security" in p or "exploit" in p or "vulnerab" in p or "threat" in p:
        domain_boosts["layer8_security"] = 0.9
        domain_boosts["layer9_strategic"] = 0.7

    else:
        domain_boosts["layer7_llm"] = 0.8
        domain_boosts["shared_general"] = 0.5

    combined_scores = {}
    for expert_key, expert_cfg in EXPERTS.items():
        base_score = device19_scores.get(expert_key, 0.0)
        domain_boost = domain_boosts.get(expert_key, 0.0)
        weight = expert_cfg.get("weight", 1.0)
        combined_scores[expert_key] = (base_score * 0.4 + domain_boost * 0.4 + weight * 0.2)

    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

    result = []
    for expert_key, score in ranked:
        if score <= 0.0:
            break
        if len(result) >= 4:
            break
        result.append((expert_key, score))

    if not any(e[0] == "shared_general" for e in result):
        result.append(("shared_general", 0.3))

    return result


# ============================================================
# Benchmark Framework
# ============================================================

@dataclass
class BenchmarkResult:
    """Single benchmark test result."""
    test_name: str
    prompt: str
    metadata: Dict[str, Any]
    expected_layer: int
    selected_experts: List[tuple]
    routing_time_us: float
    correct: bool
    notes: str = ""


@dataclass
class BenchmarkSuite:
    """Collection of benchmark results."""
    results: List[BenchmarkResult] = field(default_factory=list)
    total_time_ms: float = 0.0

    def accuracy(self) -> float:
        if not self.results:
            return 0.0
        return sum(1 for r in self.results if r.correct) / len(self.results) * 100

    def avg_routing_time_us(self) -> float:
        if not self.results:
            return 0.0
        return statistics.mean(r.routing_time_us for r in self.results)

    def p99_routing_time_us(self) -> float:
        if not self.results:
            return 0.0
        times = sorted(r.routing_time_us for r in self.results)
        idx = int(len(times) * 0.99)
        return times[min(idx, len(times) - 1)]


# ============================================================
# Test Cases
# ============================================================

TEST_CASES = [
    # NPU Real-time (expect Layer 2 - NPU)
    {"name": "realtime_stream", "prompt": "Process real-time sensor data stream with low latency inference",
     "metadata": {"task_type": "realtime", "latency": "critical"}, "expected_layer": 2},
    {"name": "npu_classify", "prompt": "Classify incoming network packets in real-time for anomaly detection",
     "metadata": {"task_type": "classification", "latency": "critical"}, "expected_layer": 2},

    # Movidus Edge Vision (expect Layer 2 - Movidus)
    {"name": "edge_vision", "prompt": "Run object detection on thermal imaging feed from edge camera",
     "metadata": {"task_type": "vision", "device": "edge"}, "expected_layer": 2},
    {"name": "target_track", "prompt": "Track moving targets in video stream with motion detection",
     "metadata": {"task_type": "tracking"}, "expected_layer": 2},

    # Military NPU (expect Layer 3 - MIL_NPU)
    {"name": "sigint_proc", "prompt": "Process SIGINT signals and classify communication patterns",
     "metadata": {"task_type": "sigint", "classification": "tactical"}, "expected_layer": 3},
    {"name": "iff_classify", "prompt": "Run IFF processing for threat classification in tactical C2",
     "metadata": {"task_type": "tactical", "domain": "c2"}, "expected_layer": 3},

    # Systems/Kernel (expect Layer 3/4)
    {"name": "kernel_driver_c", "prompt": "Write a Linux kernel driver for PCIe device with register mapping",
     "metadata": {"language": "c", "task_type": "code_generation"}, "expected_layer": 4},
    {"name": "rust_systems", "prompt": "Implement a lock-free queue in Rust with atomic operations",
     "metadata": {"language": "rust", "task_type": "code_generation"}, "expected_layer": 4},

    # Web/Frontend (expect Layer 7)
    {"name": "react_component", "prompt": "Create a React component with hooks for user authentication",
     "metadata": {"language": "typescript", "task_type": "code_generation"}, "expected_layer": 7},
    {"name": "vue_frontend", "prompt": "Build a Vue.js dashboard with real-time data updates",
     "metadata": {"language": "javascript", "task_type": "code_generation"}, "expected_layer": 7},

    # ML/Data Science (expect Layer 5)
    {"name": "pytorch_model", "prompt": "Train a PyTorch transformer model on custom dataset",
     "metadata": {"language": "python", "task_type": "ml_training"}, "expected_layer": 5},
    {"name": "pandas_analysis", "prompt": "Analyze sales dataset with pandas and numpy, create visualizations",
     "metadata": {"language": "python", "task_type": "data_analysis"}, "expected_layer": 5},

    # DevOps/Infrastructure (expect Layer 6)
    {"name": "kubernetes_deploy", "prompt": "Deploy a microservices application to Kubernetes with Helm charts",
     "metadata": {"language": "yaml", "task_type": "deployment"}, "expected_layer": 6},
    {"name": "terraform_infra", "prompt": "Create Terraform modules for AWS infrastructure with auto-scaling",
     "metadata": {"language": "hcl", "task_type": "infrastructure"}, "expected_layer": 6},

    # Security (expect Layer 8)
    {"name": "security_audit", "prompt": "Analyze this code for security vulnerabilities and exploits",
     "metadata": {"language": "python", "task_type": "security"}, "expected_layer": 8},
    {"name": "threat_analysis", "prompt": "Assess threat vectors and recommend security hardening",
     "metadata": {"task_type": "security_analysis"}, "expected_layer": 8},

    # Strategic (expect Layer 9)
    {"name": "strategic_planning", "prompt": "Develop strategic architecture for enterprise AI deployment",
     "metadata": {"task_type": "strategic"}, "expected_layer": 9},

    # General (expect Layer 7)
    {"name": "general_question", "prompt": "Explain how to optimize database queries",
     "metadata": {}, "expected_layer": 7},
    {"name": "short_prompt", "prompt": "Fix bug", "metadata": {"complexity": "simple"}, "expected_layer": 7},
]


def run_routing_benchmark(test_case: Dict) -> BenchmarkResult:
    """Run a single routing benchmark test."""
    prompt = test_case["prompt"]
    metadata = test_case.get("metadata", {})
    expected_layer = test_case["expected_layer"]

    start = time.perf_counter_ns()
    selected = dsmil_optimized_router(prompt, metadata)
    end = time.perf_counter_ns()

    routing_time_us = (end - start) / 1000.0
    selected_layers = [EXPERTS.get(e[0], {}).get("layer", 0) for e in selected]
    correct = expected_layer in selected_layers[:2]

    return BenchmarkResult(
        test_name=test_case["name"],
        prompt=prompt[:80] + "..." if len(prompt) > 80 else prompt,
        metadata=metadata,
        expected_layer=expected_layer,
        selected_experts=selected,
        routing_time_us=routing_time_us,
        correct=correct,
        notes=f"Selected layers: {selected_layers[:3]}"
    )


def run_latency_stress_test(iterations: int = 1000) -> Dict[str, float]:
    """Run stress test for routing latency."""
    prompt = "Write a function to process data efficiently"
    metadata = {"language": "python", "task_type": "code_generation"}

    times = []
    for _ in range(iterations):
        start = time.perf_counter_ns()
        dsmil_optimized_router(prompt, metadata)
        end = time.perf_counter_ns()
        times.append((end - start) / 1000.0)

    return {
        "iterations": iterations,
        "min_us": min(times),
        "max_us": max(times),
        "avg_us": statistics.mean(times),
        "median_us": statistics.median(times),
        "p95_us": sorted(times)[int(len(times) * 0.95)],
        "p99_us": sorted(times)[int(len(times) * 0.99)],
        "std_dev_us": statistics.stdev(times) if len(times) > 1 else 0,
    }


def run_model_size_benchmark() -> Dict[str, Any]:
    """Benchmark model size estimation."""
    test_prompts = [
        ("tiny", "x", {"complexity": "simple"}),
        ("small", "Write a simple function" * 10, {"complexity": "medium"}),
        ("medium", "Implement a complex system" * 100, {}),
        ("large", "Design architecture" * 500, {}),
    ]

    results = {}
    for name, prompt, metadata in test_prompts:
        size = estimate_model_size(prompt, metadata)
        results[name] = {
            "prompt_length": len(prompt),
            "estimated_size": size.name,
            "params": size.value["params"],
            "hardware": [h.name for h in size.value["hardware"]],
        }
    return results


def run_hardware_coverage_test() -> Dict[str, List[str]]:
    """Test hardware coverage."""
    hardware_usage = {h.name: [] for h in HardwareAccelerator}
    for expert_key, expert_cfg in EXPERTS.items():
        hw = expert_cfg.get("hardware", HardwareAccelerator.CPU)
        hardware_usage[hw.name].append(expert_key)
    return hardware_usage


def print_results(suite: BenchmarkSuite, latency: Dict, model_sizes: Dict, hw_coverage: Dict):
    """Print benchmark results."""
    print("=" * 80)
    print("DSMIL ROUTER BENCHMARK RESULTS")
    print("=" * 80)

    print("\n## ROUTING ACCURACY")
    print(f"Total Tests: {len(suite.results)}")
    print(f"Accuracy: {suite.accuracy():.1f}%")
    print(f"Avg Routing Time: {suite.avg_routing_time_us():.2f} us")
    print(f"P99 Routing Time: {suite.p99_routing_time_us():.2f} us")

    print("\n### Per-Test Results:")
    print(f"{'Test':<22} {'Exp':<5} {'Got':<5} {'Expert':<18} {'Time(us)':<10} {'Status'}")
    print("-" * 80)
    for r in suite.results:
        top_expert = r.selected_experts[0][0] if r.selected_experts else "none"
        top_layer = EXPERTS.get(top_expert, {}).get("layer", 0)
        status = "PASS" if r.correct else "FAIL"
        print(f"{r.test_name:<22} L{r.expected_layer:<4} L{top_layer:<4} {top_expert:<18} {r.routing_time_us:<10.2f} {status}")

    print("\n## LATENCY STRESS TEST (1000 iterations)")
    print(f"Min: {latency['min_us']:.2f} us | Max: {latency['max_us']:.2f} us | Avg: {latency['avg_us']:.2f} us")
    print(f"Median: {latency['median_us']:.2f} us | P95: {latency['p95_us']:.2f} us | P99: {latency['p99_us']:.2f} us")

    target_us = 100.0
    if latency['p99_us'] < target_us:
        print(f"PASS: P99 latency ({latency['p99_us']:.2f} us) < target ({target_us} us)")
    else:
        print(f"WARN: P99 latency ({latency['p99_us']:.2f} us) > target ({target_us} us)")

    print("\n## MODEL SIZE ESTIMATION")
    for name, data in model_sizes.items():
        print(f"  {name}: len={data['prompt_length']} -> {data['estimated_size']} ({data['params']:,} params)")

    print("\n## HARDWARE COVERAGE & TOPS")
    total_tops = 0
    for hw, experts in hw_coverage.items():
        if experts:
            hw_enum = getattr(HardwareAccelerator, hw, None)
            tops = hw_enum.value["tops"] if hw_enum else 0
            latency = hw_enum.value["latency"] if hw_enum else 0
            power = hw_enum.value["power"] if hw_enum else 0
            expert_tops = tops * len(experts)
            total_tops += expert_tops
            print(f"  {hw}: {tops} TOPS x {len(experts)} = {expert_tops} TOPS | {latency}ms lat | {power}W")
            print(f"       Experts: {experts}")
    print(f"\n  TOTAL SYSTEM TOPS: {total_tops} TOPS")

    print("\n## LAYER DISTRIBUTION")
    layer_counts = {}
    for expert_key, expert_cfg in EXPERTS.items():
        layer = expert_cfg.get("layer", 0)
        layer_counts[layer] = layer_counts.get(layer, 0) + 1
    for layer in sorted(layer_counts.keys()):
        print(f"  Layer {layer}: {layer_counts[layer]} expert(s)")

    print("\n" + "=" * 80)


def main():
    """Run all benchmarks."""
    print("Starting DSMIL Router Benchmarks...\n")

    suite = BenchmarkSuite()
    start = time.time()
    for test_case in TEST_CASES:
        result = run_routing_benchmark(test_case)
        suite.results.append(result)
    suite.total_time_ms = (time.time() - start) * 1000

    print("Running latency stress test...")
    latency = run_latency_stress_test(1000)
    model_sizes = run_model_size_benchmark()
    hw_coverage = run_hardware_coverage_test()

    print_results(suite, latency, model_sizes, hw_coverage)

    return {
        "accuracy": suite.accuracy(),
        "p99_latency_us": latency["p99_us"],
        "avg_latency_us": latency["avg_us"],
        "passed": sum(1 for r in suite.results if r.correct),
        "total": len(suite.results),
    }


if __name__ == "__main__":
    results = main()
    print(f"\nSUMMARY: {results['passed']}/{results['total']} tests passed ({results['accuracy']:.1f}%)")
    print(f"P99 Latency: {results['p99_latency_us']:.2f} us")
