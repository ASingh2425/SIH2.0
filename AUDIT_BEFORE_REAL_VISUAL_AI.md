# AUDIT BEFORE REAL VISUAL AI IMPLEMENTATION (PASS #19)

**Repository:** `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0`  
**Date:** September 13, 2026  
**Audit Objective:** Document the actual pre-remediation state of visual AI, OCR packages, model execution, and benchmark metric provenance before implementing genuine local visual OCR inference.

---

## 1. PRE-REMEDIATION AUDIT FINDINGS

### A. Installed ML / OCR Packages
- **Status:** **NONE.**
- **Evidence:** `extension/package.json` contains only UI and build dependencies (`react`, `react-dom`, `lucide-react`, `vite`, `typescript`). No ML frameworks (`@xenova/transformers`, `onnxruntime-web`, `tesseract.js`) are installed.

### B. Bundled Models & Local Weights
- **Status:** **NONE.**
- **Evidence:** No `.onnx`, `.bin`, `.wasm`, or quantized model weights exist in `extension/public/`, `extension/src/`, or distribution assets.

### C. WebGPU & WASM Inference Usage
- **Status:** **NOT EXECUTED (CAPABILITY DETECTION ONLY).**
- **Evidence:** In `extension/src/privacy/visual_detector.ts`, `detectMLBackend()` checks `if ('gpu' in navigator)` and returns `{ backend: 'webgpu', modelName: 'Local-WebGPU-Spatial-OCR-Engine' }`. No WebGPU pipelines, WGSL shaders, WebGPU buffers, or WASM tensor runtimes are initialized or invoked.

### D. Visual Perception Engine Reality
- **Status:** **DOM ATTRIBUTE HEURISTICS ONLY.**
- **Evidence:** `LocalVisualDetector.performVisualPerception()` inspects DOM elements (`canvas.getAttribute('data-canvas-text')`, `img.getAttribute('alt')`, `<svg><text>`). If an element lacks text attributes, it is marked as an `UNVERIFIED_VISUAL_REGION` and masked with a solid dark rectangle `#020617`.

### E. Screenshot Pixel Pipeline
- **Status:** **NO PIXEL INFERENCE.**
- **Evidence:** `chrome.tabs.captureVisibleTab()` captures viewport pixels, which pass to `ClientCanvasRedactor` in `canvas_capture.ts` for solid-fill rectangle masking. No pixel buffer is passed to a vision model or OCR text recognition pipeline.

### F. Performance Metric Provenance
- **Status:** **SYNTHETIC CONSTANTS.**
- **Evidence:** In `benchmark/final_validation_runner.py`, metrics such as latency (22.85 ms perception, 45.71 ms OCR) and accuracy (98.0% recall, 100.0% precision) are hardcoded Python array dictionary constants.

---

## 2. REQUIRED REMEDIATION PLAN (PASS #19)

1. **Install Browser ML/OCR Inference Stack:**
   - Install `tesseract.js` / `@xenova/transformers` / `onnxruntime-web` local inference engine into `extension/package.json`.
2. **Implement Genuine Local Inference Engine:**
   - Construct `LocalVisualModelEngine` in `extension/src/privacy/visual_ocr_engine.ts`.
   - Support genuine local WASM / WebGPU OCR inference on `ImageData`, `HTMLCanvasElement`, and `ImageBitmap` pixel inputs.
   - Maintain explicit state machine (`MODEL_UNINITIALIZED`, `MODEL_LOADING`, `MODEL_READY`, `INFERENCE_RUNNING`, `INFERENCE_COMPLETE`, `INFERENCE_FAILED`) and accurate backend classification (`webgpu`, `wasm`, `cpu`, `dom_fallback`).
3. **Integrate Image Pixels into Visual Pipeline:**
   - Pass captured viewport pixels (`dataUrl` -> `ImageBitmap` / `Canvas`) directly into `LocalVisualModelEngine`.
   - Extract bounding boxes (`x`, `y`, `width`, `height`), recognized text, confidence, and backend provenance (`source: 'visual_ocr'`).
4. **Feed Visual OCR Entities into Local PII & Redaction Pipeline:**
   - Fuse detected OCR text entities with `LocalPIIDetector` to automatically locate and redact sensitive visual text on the local canvas.
   - Preserve fail-closed visual privacy state if inference fails or confidence is low.
5. **Adversarial Benchmark & Pixel Dependence:**
   - Build real visual benchmark dataset with 50 ground-truth image cases.
   - Create `test_pixel_dependent_visual_inference.py` proving visual inference differs when rendered pixels change despite identical DOM.
   - Update metrics provenance in documentation and Side Panel to display genuine runtime statistics.

---
*Audit log saved prior to Pass #19 local visual AI model implementation.*
