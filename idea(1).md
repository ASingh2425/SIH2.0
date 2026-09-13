# Privacy Agent — SIH Problem Statement 26171 Architecture

## 1. Project Overview

**Privacy Agent** is an on-device visual browser agent built for privacy-preserving web automation.

> **The cloud can reason about the task, but the user's device decides what the AI is allowed to see and what it is allowed to do.**

Modern browser agents automate web workflows, but sending raw screenshots and unredacted DOM metadata to remote cloud systems exposes personal data, credentials, and financial details.

Privacy Agent introduces a **local privacy boundary** between the browser and remote AI. The browser performs local visual perception and binary privacy filtering first. Only sanitized, rich context is transmitted to the remote reasoner. A second local security boundary—the **Local Action Firewall**—validates proposed actions before execution in the browser.

---

## 2. Architecture & Data Flow

```text
USER DEVICE (TRUSTED ZONE)
Browser Viewport
  ↓
Local Perception
(ONNX WASM SIMD Neural Vision + Tesseract Scene OCR + DOM Tree)
  ↓
Binary Privacy Filter
(PRIVATE -> 2px Padded Redaction, NON-PRIVATE -> Preserve Rich Context)
  ↓
Sanitized Visual & Semantic Context
  ↓
========== TRUST BOUNDARY ==========
  ↓
Remote LLM / VLM Reasoner
  ↓
Structured Proposed Action
  ↓
========== TRUST BOUNDARY ==========
  ↓
Local Action Validation Firewall
(Target existence, Visual Grounding, TOCTOU DOM Revalidation, HMAC)
  ↓
Real Browser DOM Execution
```

---

## 3. Core Architectural Principles

1. **Rich Context Preservation**:
   The remote reasoner receives the richest possible visual and structural context required for high-accuracy reasoning, excluding only locally identified private data.

2. **Binary Local Privacy Policy**:
   - `PRIVATE`: Undergoes tight 2px padded canvas masking and token vault abstraction.
   - `NON-PRIVATE`: Preserved with intact layout geometry and attributes.

3. **Local Action Validation Boundary**:
   The remote model is treated as an *untrusted action proposer*. All proposed actions undergo local target existence validation, visual grounding, TOCTOU DOM revalidation, and HMAC integrity verification before execution. Prompt injection is treated as an adversarial threat model evaluated against this boundary.

---

## 4. Implementation Status Matrix

| Subsystem | Implemented Now | Training / Deployment Target | Future Roadmap |
| :--- | :---: | :---: | :---: |
| **Local Perception** | ONNX WASM SIMD + SqueezeNet v1.0 | PyTorch MobileNetV3 UI Detector | WebGPU Native Pipeline |
| **Contract Abstraction** | `VisualPerceptionModel` interface | Multi-class UI Tensor Output | Zero-Shot UI Segmentation |
| **Privacy Transformation** | 2px Padded Canvas Redaction | Adaptive Padding Engine | SVG Polygon Clipping Masks |
| **Action Validation** | Visual Action Firewall & HMAC | TOCTOU Revalidation | Multi-Step DAG Tracker |

---

## 5. Machine Learning Training Specification

- **Dataset**: COCO-formatted UI element detection dataset (`ml/dataset/dev_ui_samples.json` & `heldout_ui_samples.json`).
- **Target Classes**: `BUTTON`, `INPUT`, `CHECKBOX`, `RADIO`, `DROPDOWN`, `TAB`, `NAVIGATION`, `CARD`, `DIALOG`, `TABLE`, `IMAGE`, `ICON`.
- **Training Pipeline**: PyTorch training script (`ml/training/train_ui_detector.py`) exporting weights to INT8 ONNX (`ml/export/export_onnx.py`).
- **Evaluation**: Quantitative evaluation script (`ml/evaluation/evaluate_model.py`) measuring Precision, Recall, F1, and mean Bounding Box IoU on unseen website templates.
