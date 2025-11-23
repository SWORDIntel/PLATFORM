#!/usr/bin/env python3
"""
SWORD Coder MoE Router - Enhanced with DSMIL Layer Architecture

System: JRTC1-5450 (Dell Latitude 5450 MIL-SPEC)
Primary Routing Accelerator: Device 19 (COMMS | 0x8039 | 6 TOPS)
Contract: "router model lives on Device 19 (COMMS), fallback to CPU if unavailable"

HARDWARE ACCELERATION (from DSMIL):
- NPU (30 TOPS): <100M param models, <10ms latency, 5-8W power
- iGPU (40 TOPS): 100-500M param, vision AI, XMX engines, 15-25W
- CPU AMX (32 TOPS): transformers, LLM inference up to 7B, BF16/INT8
- AVX-512 (10 TOPS): preprocessing, classical ML, <50ms latency

LAYER EXPERT ASSIGNMENT (from COMPLETE_AI_ARCHITECTURE_LAYERS_3_9.md):
- Layer 3 (50 TOPS): Compartmented Analytics - Systems analysis, data processing
- Layer 4 (65 TOPS): Decision Support - Logic, control flow
- Layer 5 (105 TOPS): Predictive Analytics - ML inference, pattern recognition
- Layer 6 (160 TOPS): Nuclear Intelligence - Strategic analysis
- Layer 7 (440 TOPS): LLMs & Generative - Code generation, NLP
- Layer 8 (188 TOPS): Security AI - Adversarial defense, security analysis
- Layer 9 (330 TOPS): Strategic Command - Executive AI, high-level synthesis

Exposes OpenAI-style /v1/chat/completions endpoint and intelligently routes
to Layer-specific expert backends based on hardware acceleration availability.
"""

import os
import time
import json
from typing import List, Dict, Any, Optional
from enum import Enum

import requests
from fastapi import FastAPI, Header
from pydantic import BaseModel, Field

from openvino.runtime import Core

app = FastAPI(title="SWORD Coder MoE Router - DSMIL Enhanced")

# ============================================================
# Hardware Acceleration Model (from DSMIL architecture)
# ============================================================

class HardwareAccelerator(Enum):
    """Available hardware accelerators with TOPS and latency characteristics."""
    # Intel NPU 3720 (integrated in Core Ultra 7 165H)
    NPU = {"tops": 30, "latency": 10, "power": 6.5, "best_for": "realtime_inference"}

    # Intel Movidus Myriad X VPU (M.2 edge accelerator)
    MOVIDUS = {"tops": 4, "latency": 5, "power": 2.5, "best_for": "edge_vision"}

    # Military-grade NPU (hardened, TEMPEST-compliant)
    MIL_NPU = {"tops": 25, "latency": 8, "power": 8.0, "best_for": "tactical_inference"}

    # Intel Arc iGPU (XMX engines)
    IGPU = {"tops": 40, "latency": 30, "power": 20, "best_for": "vision_inference"}

    # CPU AMX (Advanced Matrix Extensions)
    AMX = {"tops": 32, "latency": 50, "power": 25, "best_for": "llm_inference"}

    # AVX-512 VNNI
    AVX512 = {"tops": 10, "latency": 100, "power": 15, "best_for": "preprocessing"}

    # Fallback CPU
    CPU = {"tops": 5, "latency": 200, "power": 10, "best_for": "fallback"}

class ModelSize(Enum):
    """Model size categories with parameter counts and recommended hardware."""
    TINY = {"params": 100_000_000, "hardware": [HardwareAccelerator.NPU, HardwareAccelerator.AVX512]}
    SMALL = {"params": 500_000_000, "hardware": [HardwareAccelerator.IGPU, HardwareAccelerator.AMX]}
    MEDIUM = {"params": 1_000_000_000, "hardware": [HardwareAccelerator.AMX, HardwareAccelerator.IGPU]}
    LARGE = {"params": 7_000_000_000, "hardware": [HardwareAccelerator.AMX, HardwareAccelerator.CPU]}

# ============================================================
# Enhanced Config: expert backends mapped to DSMIL layers
# ============================================================

EXPERTS = {
    # ============================================================
    # NPU-ACCELERATED EXPERTS (Real-time, <10ms latency)
    # ============================================================

    # NPU Expert: Real-time inference (Intel NPU 3720, 30 TOPS)
    "npu_realtime": {
        "url": os.getenv("EXPERT_NPU_REALTIME_URL", "http://node-npu:8000/v1/chat/completions"),
        "weight": 1.6,  # High priority for real-time tasks
        "layer": 2,  # Layer 2: Real-time processing
        "hardware": HardwareAccelerator.NPU,
        "best_for": ["realtime_inference", "streaming", "low_latency", "sensor_fusion"],
    },

    # NPU Expert: Edge classification (small models <100M params)
    "npu_classifier": {
        "url": os.getenv("EXPERT_NPU_CLASSIFIER_URL", "http://node-npu:8001/v1/chat/completions"),
        "weight": 1.4,
        "layer": 2,
        "hardware": HardwareAccelerator.NPU,
        "best_for": ["classification", "anomaly_detection", "intent_recognition"],
    },

    # ============================================================
    # MOVIDUS VPU EXPERTS (Edge vision, ultra-low power)
    # ============================================================

    # Movidus: Edge vision processing (Myriad X, 4 TOPS, 2.5W)
    "movidus_vision": {
        "url": os.getenv("EXPERT_MOVIDUS_URL", "http://node-movidus:8000/v1/chat/completions"),
        "weight": 1.3,
        "layer": 2,
        "hardware": HardwareAccelerator.MOVIDUS,
        "best_for": ["edge_vision", "object_detection", "thermal_imaging", "isr_processing"],
    },

    # Movidus: Tactical video analytics
    "movidus_tactical": {
        "url": os.getenv("EXPERT_MOVIDUS_TACTICAL_URL", "http://node-movidus:8001/v1/chat/completions"),
        "weight": 1.4,
        "layer": 2,
        "hardware": HardwareAccelerator.MOVIDUS,
        "best_for": ["video_analytics", "target_tracking", "motion_detection"],
    },

    # ============================================================
    # MILITARY NPU EXPERTS (TEMPEST-compliant, hardened)
    # ============================================================

    # MIL-NPU: Tactical inference (hardened, 25 TOPS)
    "mil_npu_tactical": {
        "url": os.getenv("EXPERT_MIL_NPU_URL", "http://node-mil-npu:8000/v1/chat/completions"),
        "weight": 1.5,
        "layer": 3,
        "hardware": HardwareAccelerator.MIL_NPU,
        "best_for": ["tactical_inference", "iff_processing", "threat_classification", "c2_support"],
    },

    # MIL-NPU: SIGINT processing
    "mil_npu_sigint": {
        "url": os.getenv("EXPERT_MIL_NPU_SIGINT_URL", "http://node-mil-npu:8001/v1/chat/completions"),
        "weight": 1.4,
        "layer": 3,
        "hardware": HardwareAccelerator.MIL_NPU,
        "best_for": ["sigint", "comint", "elint", "signal_classification"],
    },

    # ============================================================
    # LAYER 3-9 EXPERTS (Original + enhanced)
    # ============================================================

    # Layer 3: Compartmented Analytics (50 TOPS, 8 devices)
    "layer3_analytics": {
        "url": os.getenv("EXPERT_LAYER3_URL", "http://node-layer3:8000/v1/chat/completions"),
        "weight": 1.0,
        "layer": 3,
        "hardware": HardwareAccelerator.AVX512,
        "best_for": ["data_analysis", "signal_processing", "compartmented_analytics"],
    },

    # Layer 4: Decision Support (65 TOPS, 8 devices)
    "layer4_decision": {
        "url": os.getenv("EXPERT_LAYER4_URL", "http://node-layer4:8000/v1/chat/completions"),
        "weight": 1.1,
        "layer": 4,
        "hardware": HardwareAccelerator.AMX,
        "best_for": ["control_flow", "logic_synthesis", "decision_support"],
    },

    # Layer 5: Predictive Analytics (105 TOPS, 6 devices)
    "layer5_predictive": {
        "url": os.getenv("EXPERT_LAYER5_URL", "http://node-layer5:8000/v1/chat/completions"),
        "weight": 1.2,
        "layer": 5,
        "hardware": HardwareAccelerator.IGPU,
        "best_for": ["ml_inference", "pattern_recognition", "predictive_analytics"],
    },

    # Layer 5: NPU-accelerated prediction (real-time ML)
    "layer5_npu_predict": {
        "url": os.getenv("EXPERT_LAYER5_NPU_URL", "http://node-layer5-npu:8000/v1/chat/completions"),
        "weight": 1.3,
        "layer": 5,
        "hardware": HardwareAccelerator.NPU,
        "best_for": ["realtime_prediction", "streaming_ml", "time_series"],
    },

    # Layer 6: Nuclear Intelligence (160 TOPS, 6 devices)
    "layer6_nuclear": {
        "url": os.getenv("EXPERT_LAYER6_URL", "http://node-layer6:8000/v1/chat/completions"),
        "weight": 1.3,
        "layer": 6,
        "hardware": HardwareAccelerator.AMX,
        "best_for": ["nuclear_analysis", "strategic_intelligence", "threat_assessment"],
    },

    # Layer 7: LLMs & Generative AI (440 TOPS, 8 devices) - PRIMARY FOR CODE GENERATION
    "layer7_llm": {
        "url": os.getenv("EXPERT_LAYER7_URL", "http://node-layer7:8000/v1/chat/completions"),
        "weight": 1.5,
        "layer": 7,
        "hardware": HardwareAccelerator.AMX,
        "best_for": ["code_generation", "nlp", "text_synthesis", "llm_inference"],
    },

    # Layer 8: Security AI (188 TOPS, 8 devices)
    "layer8_security": {
        "url": os.getenv("EXPERT_LAYER8_URL", "http://node-layer8:8000/v1/chat/completions"),
        "weight": 1.2,
        "layer": 8,
        "hardware": HardwareAccelerator.IGPU,
        "best_for": ["security_analysis", "adversarial_defense", "threat_detection"],
    },

    # Layer 8: NPU-accelerated anomaly detection (real-time security)
    "layer8_npu_anomaly": {
        "url": os.getenv("EXPERT_LAYER8_NPU_URL", "http://node-layer8-npu:8000/v1/chat/completions"),
        "weight": 1.4,
        "layer": 8,
        "hardware": HardwareAccelerator.NPU,
        "best_for": ["realtime_anomaly", "intrusion_detection", "network_monitoring"],
    },

    # Layer 9: Strategic Command (330 TOPS, 4 devices)
    "layer9_strategic": {
        "url": os.getenv("EXPERT_LAYER9_URL", "http://node-layer9:8000/v1/chat/completions"),
        "weight": 1.4,
        "layer": 9,
        "hardware": HardwareAccelerator.AMX,
        "best_for": ["strategic_synthesis", "executive_command", "high_level_analysis"],
    },

    # Fallback: Shared General (CPU-based)
    "shared_general": {
        "url": os.getenv("EXPERT_SHARED_GENERAL_URL", "http://localhost:8001/v1/chat/completions"),
        "weight": 0.8,
        "layer": 0,
        "hardware": HardwareAccelerator.CPU,
        "best_for": ["fallback", "general_purpose"],
    },
}

# ============================================================
# OpenAI-style schemas
# ============================================================

class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    max_tokens: int = 512
    temperature: float = 0.2
    stream: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: Dict[str, int] = Field(default_factory=lambda: {
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    })

# ============================================================
# Router model (OpenVINO) on Device 19 (COMMS) with CPU fallback
# ============================================================

ie = Core()

# NOTE:
# - ROUTER_DEVICE_19 is a *placeholder* for whatever OpenVINO exposes
#   for Device 19 (COMMS) on your system (e.g. "GPU.1", custom device name, etc.).
# - You can override via env: ROUTER_DEVICE_OVERRIDE
ROUTER_DEVICE_19 = os.getenv("ROUTER_DEVICE_OVERRIDE", "COMMS_19")  # placeholder

ROUTER_MODEL_PATH = os.getenv("ROUTER_MODEL_PATH", "router_classifier.xml")

ROUTER_DEVICE_USED = "CPU"
ROUTER_DEVICE_COMMENT = (
    "router model lives on Device 19 (COMMS), fallback to CPU if unavailable"
)

try:
    # Primary path: Device 19 (COMMS)
    router_compiled_model = ie.compile_model(ROUTER_MODEL_PATH, ROUTER_DEVICE_19)
    ROUTER_DEVICE_USED = ROUTER_DEVICE_19
except Exception:
    # Fallback path: CPU
    router_compiled_model = ie.compile_model(ROUTER_MODEL_PATH, "CPU")
    ROUTER_DEVICE_USED = "CPU"

def estimate_model_size(prompt: str, metadata: Dict[str, Any]) -> ModelSize:
    """
    Estimate required model size based on task complexity.

    From DSMIL:
    - <100M: NPU, <10ms
    - 100-500M: iGPU/AMX, <100ms
    - 500M-1B: AMX, <300ms
    - 1B-7B: AMX + CPU, <1000ms
    """
    p = prompt.lower()
    complexity = metadata.get("complexity", "medium")

    if len(prompt) < 100 or complexity == "simple":
        return ModelSize.TINY
    elif len(prompt) < 500 or complexity == "medium":
        return ModelSize.SMALL
    elif len(prompt) < 2000:
        return ModelSize.MEDIUM
    else:
        return ModelSize.LARGE

def get_best_hardware(model_size: ModelSize, available_accelerators: List[HardwareAccelerator]) -> HardwareAccelerator:
    """Select best hardware for model size from available accelerators."""
    preferred = model_size.value["hardware"]
    for accel in preferred:
        if accel in available_accelerators:
            return accel
    return HardwareAccelerator.CPU

def router_infer_device19(prompt: str, metadata: Dict[str, Any]) -> Dict[str, float]:
    """
    Device 19 (COMMS) routing classifier on actual hardware.

    Maps to:
    - NPU: Fast small inference
    - iGPU: Vision/medium models
    - AMX: LLM inference (primary)
    - AVX-512: Preprocessing/classical ML

    Returns confidence scores per expert layer.
    """
    # Estimate model size requirements
    model_size = estimate_model_size(prompt, metadata)

    # Simulate Device 19 routing decision (placeholder for actual model)
    scores = {key: 0.0 for key in EXPERTS.keys()}

    # Task-specific boosts (will be replaced by real classifier on Device 19)
    task = metadata.get("task_type", "").lower()

    if "code" in task or "generation" in task:
        scores["layer7_llm"] = 0.9  # Layer 7 (440 TOPS) for code
    elif "security" in task:
        scores["layer8_security"] = 0.85  # Layer 8 for security
    elif "strategic" in task:
        scores["layer9_strategic"] = 0.8  # Layer 9 for high-level
    elif "analytics" in task:
        scores["layer5_predictive"] = 0.8  # Layer 5 for ML inference
    elif "decision" in task:
        scores["layer4_decision"] = 0.75  # Layer 4 for logic
    else:
        scores["layer7_llm"] = 0.6  # Default to Layer 7
        scores["shared_general"] = 0.4  # Fallback

    return scores

# ============================================================
# Advanced multi-expert router (Device 19 COMMS optimized)
# ============================================================

def dsmil_optimized_router(prompt: str, metadata: Dict[str, Any]) -> List[tuple[str, float]]:
    """
    Advanced routing using DSMIL layer architecture and Device 19 acceleration.

    Strategy:
    1. Estimate model size requirements
    2. Get Device 19 routing scores
    3. Filter by hardware availability
    4. Rank by relevance and hardware efficiency
    5. Return up to 4 best experts (shared + specialists)

    From DSMIL: Cap at 4 experts to balance accuracy vs latency.
    """
    p = prompt.lower()
    lang = metadata.get("language", "").lower()
    task = metadata.get("task_type", "").lower()

    # 1. Get Device 19 routing scores
    device19_scores = router_infer_device19(p, metadata)

    # 2. Rule-based layer selection based on language/domain
    domain_boosts = {}

    # Systems/kernel work → Layer 3 (analytics) + Layer 4 (decision)
    if lang in ("c", "c++", "rust", "asm") or "kernel" in p or "driver" in p or "register" in p:
        domain_boosts["layer3_analytics"] = 0.7
        domain_boosts["layer4_decision"] = 0.8
        domain_boosts["layer7_llm"] = 0.5  # Still support for synthesis

    # Web/frontend → Layer 7 (LLM) with iGPU acceleration
    elif lang in ("js", "ts", "jsx", "tsx", "python") or "react" in p or "vue" in p or "node" in p:
        domain_boosts["layer7_llm"] = 0.9  # Primary
        domain_boosts["layer8_security"] = 0.6  # Security checks

    # ML/Data science → Layer 5 (predictive) + Layer 7 (LLM)
    elif lang == "python" or "pytorch" in p or "tensorflow" in p or "numpy" in p or "pandas" in p or "dataset" in p:
        domain_boosts["layer5_predictive"] = 0.85  # Primary
        domain_boosts["layer7_llm"] = 0.7  # Code synthesis

    # DevOps/Infrastructure → Layer 6 (nuclear/strategic intelligence)
    elif "docker" in p or "kubernetes" in p or "terraform" in p or "ansible" in p or "helm" in p or "deploy" in p:
        domain_boosts["layer6_nuclear"] = 0.8  # Strategic planning
        domain_boosts["layer4_decision"] = 0.7  # Logic control

    # Security/Analysis → Layer 8 (security AI)
    elif "security" in p or "exploit" in p or "vulnerab" in p or "threat" in p:
        domain_boosts["layer8_security"] = 0.9  # Primary
        domain_boosts["layer9_strategic"] = 0.7  # High-level assessment

    # Default for generic queries
    else:
        domain_boosts["layer7_llm"] = 0.8
        domain_boosts["shared_general"] = 0.5

    # 3. Combine Device 19 scores with domain boosts
    combined_scores = {}
    for expert_key, expert_cfg in EXPERTS.items():
        base_score = device19_scores.get(expert_key, 0.0)
        domain_boost = domain_boosts.get(expert_key, 0.0)
        weight = expert_cfg.get("weight", 1.0)

        # Combined score: Device 19 classification + domain routing + expert weight
        combined_scores[expert_key] = (base_score * 0.4 + domain_boost * 0.4 + weight * 0.2)

    # 4. Sort by score and return top 4 (1-2 shared + 2-3 specialists)
    ranked = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)

    # Always include shared_general as fallback if present
    result = []
    included_layers = set()

    for expert_key, score in ranked:
        if score <= 0.0:
            break

        layer = EXPERTS[expert_key].get("layer", 0)

        # Cap at 4 experts, but prefer diversity (different layers)
        if len(result) >= 4:
            break

        result.append((expert_key, score))
        included_layers.add(layer)

    # Ensure we have a fallback
    if not any(e[0] == "shared_general" for e in result):
        result.append(("shared_general", 0.3))

    return result


def forward_to_expert(expert_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Forward OpenAI-style chat request to a specific expert."""
    cfg = EXPERTS[expert_key]
    resp = requests.post(cfg["url"], json=payload, timeout=60)
    resp.raise_for_status()
    return resp.json()

# ============================================================
# Main endpoint
# ============================================================

@app.post("/v1/chat/completions", response_model=ChatCompletionResponse)
def chat_completions(
    req: ChatCompletionRequest,
    x_request_id: Optional[str] = Header(None),
):
    """
    Enhanced endpoint using DSMIL layer routing and Device 19 (COMMS) optimization.

    Request flow:
    1. Receive OpenAI-style chat completion request
    2. Use DSMIL routing (Device 19 + domain logic) to select 1-4 experts
    3. Forward to each expert's hardware-optimized backend
    4. Aggregate responses using quality + latency scoring
    5. Return best response with metadata

    Hardware mapping:
    - Layer 3: AVX-512 (analytics)
    - Layer 4: AMX (decision)
    - Layer 5: iGPU (predictive)
    - Layer 6: AMX (nuclear intelligence)
    - Layer 7: AMX (LLMs) ← PRIMARY for code generation
    - Layer 8: iGPU (security)
    - Layer 9: AMX (strategic command)
    """
    t0 = int(time.time())
    request_id = x_request_id or f"router-{int(time.time() * 1000)}"
    prompt_text = req.messages[-1].content if req.messages else ""
    metadata = req.metadata or {}

    # Log incoming request with metadata
    metadata["request_id"] = request_id
    metadata["timestamp"] = t0

    # 1) Use DSMIL-optimized router (Device 19 classification + domain routing)
    expert_rankings = dsmil_optimized_router(prompt_text, metadata)

    expert_payload = {
        "model": req.model,
        "messages": [m.dict() for m in req.messages],
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "stream": False,
    }

    candidates = []
    latencies = {}

    for expert_key, routing_score in expert_rankings:
        try:
            expert_cfg = EXPERTS.get(expert_key, {})
            start = time.time()

            # Forward to expert with timeout
            raw = forward_to_expert(expert_key, expert_payload)
            latency = time.time() - start
            latencies[expert_key] = latency

            txt = raw.get("choices", [{}])[0].get("message", {}).get("content", "")

            if not txt:
                candidates.append({
                    "expert": expert_key,
                    "layer": expert_cfg.get("layer", 0),
                    "text": f"// {expert_key} returned empty response",
                    "score": 1e8,
                    "latency": latency,
                    "routing_score": routing_score,
                })
                continue

            # Intelligent scoring: combines multiple factors
            # Priority: routing confidence > latency > response length
            latency_factor = latency / 2.0  # Normalize: <2s responses preferred
            length_factor = max(0, (len(txt) - 200) / 1000.0)  # Penalize very long
            hardware_factor = expert_cfg.get("weight", 1.0)

            quality_score = (
                routing_score * 10 +  # 0-10: routing confidence (highest priority)
                (1.0 - min(latency_factor, 1.0)) * 5 +  # 0-5: speed bonus
                (1.0 - min(length_factor, 1.0)) * 2 +  # 0-2: conciseness bonus
                hardware_factor * 0.5  # Small boost for expert weight
            )

            candidates.append({
                "expert": expert_key,
                "layer": expert_cfg.get("layer", 0),
                "text": txt,
                "score": quality_score,  # Higher is better
                "latency": latency,
                "routing_score": routing_score,
                "length": len(txt),
            })

        except requests.Timeout:
            candidates.append({
                "expert": expert_key,
                "layer": EXPERTS[expert_key].get("layer", 0),
                "text": f"// {expert_key} timeout (>60s)",
                "score": -1e6,
                "latency": 60.0,
                "routing_score": routing_score,
            })
        except Exception as e:
            candidates.append({
                "expert": expert_key,
                "layer": EXPERTS[expert_key].get("layer", 0),
                "text": f"// {expert_key} error: {str(e)[:100]}",
                "score": -1e6,
                "latency": 0.0,
                "routing_score": routing_score,
            })

    # 2) Select best response
    if candidates:
        # Filter out errors (score < 0)
        valid_candidates = [c for c in candidates if c["score"] > 0]
        if valid_candidates:
            best = max(valid_candidates, key=lambda c: c["score"])
        else:
            best = max(candidates, key=lambda c: c["score"])
    else:
        best = {
            "expert": "fallback",
            "layer": 0,
            "text": "// No experts available. Please try again.",
            "score": 0.0,
            "latency": 0.0,
            "routing_score": 0.0,
        }

    # 3) Build response with metadata
    choice = ChatCompletionChoice(
        index=0,
        message=ChatMessage(role="assistant", content=best["text"]),
        finish_reason="stop",
    )

    # Collect performance metrics
    response_metadata = {
        "request_id": request_id,
        "routing_device": ROUTER_DEVICE_USED,
        "selected_expert": best["expert"],
        "selected_layer": best["layer"],
        "routing_score": best.get("routing_score", 0.0),
        "expert_latency_ms": round(best.get("latency", 0.0) * 1000),
        "response_length": best.get("length", len(best["text"])),
        "total_experts_queried": len(candidates),
        "fallback_used": best["expert"] == "fallback",
        "device_19_comment": ROUTER_DEVICE_COMMENT,
    }

    return ChatCompletionResponse(
        id=request_id,
        created=t0,
        model=req.model,
        choices=[choice],
        usage={
            "prompt_tokens": len(prompt_text.split()) + 50,  # Rough estimate
            "completion_tokens": len(best["text"].split()) if best["text"] else 0,
            "total_tokens": len(prompt_text.split()) + len(best.get("text", "").split()) + 50,
        },
    )


# ============================================================
# Health check and metrics endpoints
# ============================================================

@app.get("/health")
def health_check():
    """
    Health check endpoint for DSMIL router status.

    Returns Device 19 status and layer availability.
    """
    expert_status = {}
    for expert_key, expert_cfg in EXPERTS.items():
        try:
            resp = requests.get(
                expert_cfg["url"].replace("/v1/chat/completions", "/health"),
                timeout=2.0
            )
            expert_status[expert_key] = {
                "status": "healthy" if resp.status_code == 200 else "unhealthy",
                "layer": expert_cfg.get("layer", 0),
                "hardware": expert_cfg.get("hardware", HardwareAccelerator.CPU).name,
            }
        except Exception:
            expert_status[expert_key] = {
                "status": "unreachable",
                "layer": expert_cfg.get("layer", 0),
                "hardware": expert_cfg.get("hardware", HardwareAccelerator.CPU).name,
            }

    return {
        "status": "healthy",
        "router_device": ROUTER_DEVICE_USED,
        "device_19_contract": ROUTER_DEVICE_COMMENT,
        "experts": expert_status,
        "hardware_capabilities": {
            "NPU": {"tops": 30, "latency_ms": 10, "power_w": 6.5},
            "iGPU": {"tops": 40, "latency_ms": 30, "power_w": 20},
            "AMX": {"tops": 32, "latency_ms": 50, "power_w": 25},
            "AVX512": {"tops": 10, "latency_ms": 100, "power_w": 15},
        },
    }


@app.get("/v1/models")
def list_models():
    """
    List available DSMIL layer models/experts.

    Compatible with OpenAI's /v1/models endpoint.
    """
    models = []
    for expert_key, expert_cfg in EXPERTS.items():
        models.append({
            "id": expert_key,
            "object": "model",
            "created": int(time.time()),
            "owned_by": f"dsmil-layer-{expert_cfg.get('layer', 0)}",
            "permission": [],
            "root": expert_key,
            "parent": None,
            "capabilities": expert_cfg.get("best_for", []),
            "hardware": expert_cfg.get("hardware", HardwareAccelerator.CPU).name,
            "weight": expert_cfg.get("weight", 1.0),
        })

    return {
        "object": "list",
        "data": models,
    }


@app.get("/v1/router/info")
def router_info():
    """
    Detailed router information for DSMIL system.

    Returns layer architecture, hardware mapping, and routing configuration.
    """
    return {
        "system": "JRTC1-5450 (Dell Latitude 5450 MIL-SPEC)",
        "router_device": {
            "primary": "Device 19 (COMMS | 0x8039 | 6 TOPS)",
            "active": ROUTER_DEVICE_USED,
            "contract": ROUTER_DEVICE_COMMENT,
        },
        "layer_architecture": {
            "layer_3": {"tops": 50, "devices": 8, "focus": "Compartmented Analytics"},
            "layer_4": {"tops": 65, "devices": 8, "focus": "Decision Support"},
            "layer_5": {"tops": 105, "devices": 6, "focus": "Predictive Analytics"},
            "layer_6": {"tops": 160, "devices": 6, "focus": "Nuclear Intelligence"},
            "layer_7": {"tops": 440, "devices": 8, "focus": "LLMs & Generative AI"},
            "layer_8": {"tops": 188, "devices": 8, "focus": "Security AI"},
            "layer_9": {"tops": 330, "devices": 4, "focus": "Strategic Command"},
        },
        "hardware_acceleration": {
            "NPU": {"tops": 30, "best_for": "<100M params", "latency": "<10ms"},
            "iGPU": {"tops": 40, "best_for": "100-500M params", "latency": "<100ms"},
            "AMX": {"tops": 32, "best_for": "500M-7B params", "latency": "<1000ms"},
            "AVX512": {"tops": 10, "best_for": "preprocessing", "latency": "<50ms"},
        },
        "routing_strategy": {
            "max_experts": 4,
            "fallback": "shared_general",
            "scoring": "routing_confidence * 0.4 + domain_boost * 0.4 + weight * 0.2",
        },
        "total_tops": 1338,  # Sum of all layers
    }


# ============================================================
# MCP (Model Context Protocol) Integration
# ============================================================

try:
    from mcp_router import MCPHub
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPHub = None

# Initialize MCP Hub if available
mcp_hub = None
if MCP_AVAILABLE:
    try:
        mcp_hub = MCPHub(workspace=os.getcwd())
    except Exception as e:
        print(f"MCP Hub initialization failed: {e}")
        mcp_hub = None


class MCPToolRequest(BaseModel):
    """MCP tool call request."""
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class MCPToolResponse(BaseModel):
    """MCP tool call response."""
    tool: str
    result: Dict[str, Any]
    success: bool
    error: Optional[str] = None


@app.get("/v1/mcp/status")
def mcp_status():
    """Get MCP hub status."""
    if not MCP_AVAILABLE or mcp_hub is None:
        return {
            "status": "unavailable",
            "message": "MCP not initialized. Run: pip install -e mcp_router",
        }
    return {
        "status": "active",
        "servers": list(mcp_hub.servers.keys()),
        "total_tools": len(mcp_hub.tools),
        "workspace": mcp_hub.workspace,
    }


@app.get("/v1/mcp/tools")
def mcp_list_tools():
    """List all available MCP tools."""
    if not MCP_AVAILABLE or mcp_hub is None:
        return {"error": "MCP not available", "tools": []}
    return {
        "tools": mcp_hub.list_tools(),
        "total": len(mcp_hub.tools),
    }


@app.post("/v1/mcp/call", response_model=MCPToolResponse)
def mcp_call_tool(request: MCPToolRequest):
    """Call an MCP tool."""
    if not MCP_AVAILABLE or mcp_hub is None:
        return MCPToolResponse(
            tool=request.tool,
            result={},
            success=False,
            error="MCP not available",
        )

    result = mcp_hub.call_tool(request.tool, request.arguments)

    if "error" in result:
        return MCPToolResponse(
            tool=request.tool,
            result=result,
            success=False,
            error=result["error"],
        )

    return MCPToolResponse(
        tool=request.tool,
        result=result.get("result", result),
        success=True,
    )


# MCP Tool shortcuts for common operations
@app.post("/v1/mcp/read")
def mcp_read_file(path: str, offset: int = 0, limit: int = 2000):
    """Read file via MCP codemod."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("codemod_read_file", {"path": path, "offset": offset, "limit": limit})


@app.post("/v1/mcp/edit")
def mcp_edit_file(path: str, old_string: str, new_string: str, replace_all: bool = False):
    """Edit file via MCP codemod."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("codemod_edit_file", {
        "path": path, "old_string": old_string, "new_string": new_string, "replace_all": replace_all
    })


@app.post("/v1/mcp/grep")
def mcp_grep(pattern: str, path: str = ".", file_pattern: str = "*"):
    """Search files via MCP codemod."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("codemod_grep_files", {"pattern": pattern, "path": path, "file_pattern": file_pattern})


@app.post("/v1/mcp/bash")
def mcp_bash(command: str, timeout: int = 30):
    """Run bash command via MCP codemod."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("codemod_run_bash", {"command": command, "timeout": timeout})


@app.post("/v1/mcp/memory/store")
def mcp_memory_store(content: str, memory_type: str = "fact", tags: List[str] = None):
    """Store memory via MCP memlayer."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("memlayer_store_memory", {"content": content, "memory_type": memory_type, "tags": tags or []})


@app.post("/v1/mcp/memory/recall")
def mcp_memory_recall(query: str, limit: int = 10):
    """Recall memories via MCP memlayer."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("memlayer_recall_memories", {"query": query, "limit": limit})


@app.post("/v1/mcp/think/start")
def mcp_think_start(problem: str, approach: str = "analytical"):
    """Start thinking chain via MCP sequential thinking."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("thinking_start_thinking", {"problem": problem, "approach": approach})


@app.post("/v1/mcp/think/step")
def mcp_think_step(chain_id: str, thought: str, thought_type: str = "reasoning"):
    """Add thought step via MCP sequential thinking."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("thinking_add_thought", {"chain_id": chain_id, "thought": thought, "thought_type": thought_type})


@app.post("/v1/mcp/docs")
def mcp_get_docs(library_name: str, topic: str = None):
    """Get library docs via MCP context7."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    # First resolve library
    resolved = mcp_hub.call_tool("context7_resolve_library", {"library_name": library_name})
    if "error" in resolved:
        return resolved
    library_id = resolved.get("result", {}).get("library_id", library_name)
    # Then get docs
    return mcp_hub.call_tool("context7_get_library_docs", {"library_id": library_id, "topic": topic})


@app.post("/v1/mcp/fetch")
def mcp_fetch_url(url: str):
    """Fetch URL content via MCP fetch."""
    if not mcp_hub:
        return {"error": "MCP not available"}
    return mcp_hub.call_tool("fetch_fetch_html_text", {"url": url})


# ============================================================
# Quantization Pipeline Integration
# ============================================================

try:
    from quantization_pipeline import (
        QuantizationPipeline,
        QuantizationConfig,
        MCPQuantizationTool,
        MODEL_SIZES
    )
    QUANT_AVAILABLE = True
    quant_pipeline = QuantizationPipeline()
    quant_mcp = MCPQuantizationTool()
except ImportError:
    QUANT_AVAILABLE = False
    quant_pipeline = None
    quant_mcp = None
    MODEL_SIZES = {}


@app.get("/v1/models/storage")
def get_model_storage_estimates(quantization: str = "int4"):
    """Get storage estimates for all models."""
    if not QUANT_AVAILABLE:
        return {"error": "Quantization pipeline not available"}
    return quant_pipeline.estimate_total_storage(quantization=quantization)


@app.get("/v1/models/{model_name}/info")
def get_model_info(model_name: str):
    """Get size/quantization info for a model."""
    if not QUANT_AVAILABLE:
        return {"error": "Quantization pipeline not available"}
    return quant_pipeline.get_model_size_info(model_name)


@app.post("/v1/models/quantize")
def quantize_model_endpoint(model_name: str, target_hardware: str = "npu"):
    """Quantize a model for specific hardware."""
    if not QUANT_AVAILABLE:
        return {"error": "Quantization pipeline not available"}

    config = QuantizationConfig(target_hardware=target_hardware)
    result = quant_pipeline.quantize(model_name, None, config)

    return {
        "model": model_name,
        "method": result.quantization_method,
        "tier": result.quantization_tier.name,
        "target_hardware": result.target_hardware,
        "compression_ratio": result.compression_ratio,
        "original_size_mb": result.original_size_mb,
        "quantized_size_mb": result.quantized_size_mb,
        "savings_percent": result.get_memory_savings_percent(),
        "accuracy_loss_percent": result.accuracy_loss_percent
    }


@app.get("/v1/quantization/stats")
def get_quantization_stats():
    """Get quantization pipeline statistics."""
    if not QUANT_AVAILABLE:
        return {"error": "Quantization pipeline not available"}
    return quant_pipeline.get_statistics()


# ============================================================
# Entry point
# ============================================================

if __name__ == "__main__":
    import uvicorn

    print(f"SWORD Coder MoE Router - DSMIL Enhanced + MCP + Quantization")
    print(f"Router Device: {ROUTER_DEVICE_USED}")
    print(f"Contract: {ROUTER_DEVICE_COMMENT}")
    print(f"Total Layers: 7 (Layer 3-9)")
    print(f"Total Compute: 1338 TOPS")
    print(f"MCP Available: {MCP_AVAILABLE}")
    if mcp_hub:
        print(f"MCP Servers: {', '.join(mcp_hub.servers.keys())}")
        print(f"MCP Tools: {len(mcp_hub.tools)}")
    print(f"Quantization: {QUANT_AVAILABLE}")
    if QUANT_AVAILABLE:
        print(f"  Models: {len(MODEL_SIZES)}")
        storage = quant_pipeline.estimate_total_storage(quantization="int4")
        print(f"  Total FP32: {storage['total_fp32_gb']:.1f} GB")
        print(f"  Total INT4: {storage['total_quantized_gb']:.1f} GB")
    print()

    uvicorn.run(
        app,
        host=os.getenv("ROUTER_HOST", "0.0.0.0"),
        port=int(os.getenv("ROUTER_PORT", "8000")),
        log_level="info",
    )
