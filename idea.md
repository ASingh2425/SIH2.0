# SIH Problem Statement 26171 — Concept & Architecture Specification

## 1. Executive Summary

**Core Architecture**:
> **Lightweight on-device visual perception for browser agents with a local privacy boundary and locally validated actions.**

The cloud VLM/LLM reasoner receives rich, task-relevant visual and semantic context, except information identified locally as private.

```
┌─────────────────────────────────────────────────────────────────┐
│                    LOCAL BROWSER EXTENSION                      │
│                        TRUSTED ZONE                             │
│                                                                 │
│   ┌──────────────┐    ┌──────────────────────────────────────┐  │
│   │ Rendered UI  │───▶│ Local Perception                     │  │
│   │ Viewport     │    │ (ONNX WASM SIMD + Tesseract OCR +    │  │
│   └──────────────┘    │  DOM Semantic Tree)                  │  │
│                       └──────────────────┬───────────────────┘  │
│                                          │                      │
│                                          ▼                      │
│                       ┌──────────────────────────────────────┐  │
│                       │ Binary Local Privacy Filter          │  │
│                       │ PRIVATE     -> Privacy Transformation│  │
│                       │ NON-PRIVATE -> Preserve Rich Context │  │
│                       └──────────────────┬───────────────────┘  │
│                                          │                      │
│                                          ▼                      │
│                       ┌──────────────────────────────────────┐  │
│                       │ Sanitized Context & 2px Redaction    │  │
│                       └──────────────────┬───────────────────┘  │
└──────────────────────────────────────────┼──────────────────────┘
                                           │
                                           │ SANITIZED DATA DISPATCH
                                           ▼
                                 ┌──────────────────┐
                                 │ Remote VLM / LLM │
                                 │ Reasoner         │
                                 └─────────┬────────┘
                                           │ Proposed Action
                                           ▼
┌──────────────────────────────────────────┴──────────────────────┐
│                    LOCAL TRUSTED ZONE                           │
│                                                                 │
│                       ┌──────────────────────────────────────┐  │
│                       │ Local Action Validation / Firewall   │  │
│                       │ (Target existence, BBox grounding,   │  │
│                       │  TOCTOU DOM revalidation, HMAC)      │  │
│                       └──────────────────┬───────────────────┘  │
│                                          │ Validated Action     │
│                                          ▼                      │
│                       ┌──────────────────────────────────────┐  │
│                       │ Real Browser DOM Action Execution    │  │
│                       └──────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Operational Principles

1. **Binary Privacy Filtering**:
   - `PRIVATE`: Undergoes 2px tight padded canvas redaction and local tokenization.
   - `NON-PRIVATE`: Preserved with maximum visual and structural detail for remote reasoning.

2. **Rich Task Context Transmission**:
   - Rather than data minimization, the remote reasoner receives complete visual layout structure and OCR text regions, stripping only identified PII entities.

3. **Local Action Validation / Trust Boundary**:
   - The remote model acts as an *untrusted action proposer*. The local browser agent validates target existence, visual grounding, bounding box consistency, visibility, enabled state, coordinate drift, and capture freshness before DOM execution. Prompt injection is evaluated as an adversarial threat model against this boundary.

---

## 3. Implementation Status Matrix

### [IMPLEMENTED NOW]
- **Local Neural Vision Engine**: ONNX Runtime Web on WASM SIMD running SqueezeNet v1.0 ONNX model weights (`squeezenet1.0-12.onnx`, 4.95 MB).
- **Formal Visual Perception Interface**: `VisualPerceptionModel` interface with `predict()`, `getModelInfo()`, `getBackendInfo()`.
- **2px Tight Padded Redaction**: Solid fill canvas masking with safety margins and clipped labels (`ctx.clip()`).
- **Local Action Validation Firewall**: Semantic compatibility matrix, HMAC action signing, TOCTOU DOM revalidation.
- **Empirical Evaluation Suites**: 45-test suite covering 100-cycle memory leak verification, statistical latency distributions, held-out generalization, and baseline ablation studies.

### [TRAINING / DEPLOYMENT TARGET]
- **Custom UI Element Detector**: PyTorch MobileNetV3-Small training pipeline (`ml/training/train_ui_detector.py`) exported to INT8 ONNX (`ml/export/export_onnx.py`).
- **WebGPU Acceleration**: Direct WebGPU execution provider fallback to WASM SIMD when hardware acceleration is available.

### [FUTURE ROADMAP]
- **Polygonal Clipping Masks**: Non-axis-aligned rotated text polygon masking.
- **Multi-Modal Vision-Language Adapters**: In-browser zero-shot UI element classification.

---

## 4. Machine Learning Training Specification

- **Architecture**: MobileNetV3-Small / SqueezeNet backbone with custom object detection head.
- **Dataset**: COCO-formatted UI bounding box dataset (`ml/dataset/dev_ui_samples.json` & `heldout_ui_samples.json`).
- **Annotations**: 12 target UI element classes (`BUTTON`, `INPUT`, `CHECKBOX`, `RADIO`, `DROPDOWN`, `TAB`, `NAVIGATION`, `CARD`, `DIALOG`, `TABLE`, `IMAGE`, `ICON`).
- **Split**: 60% Train, 20% Validation, 20% Held-out Test (Zero template overlap).
- **Quantization & Export**: INT8 dynamic quantization via ONNX Runtime Web export pipeline.
