# CURRENT EVALUATION VALIDITY & FORENSIC ML PIPELINE AUDIT
**SIH Problem Statement 26171 — On-Device Visual Perception for Light-Weight Browser Agents**

---

## 1. Executive Summary

This forensic audit evaluates the validity, provenance, and real-world transferability of all evaluation benchmarks previously conducted on the on-device visual perception pipeline.

> [!WARNING]
> **Forensic Reality Check**: Previous benchmark iterations reported high quantitative scores ($85\%\text{--}100\%$ mAP/precision) on synthetic datasets and programmatically generated UI templates. While structural unit tests prove that the ONNX model is **pixel-driven** and **DOM-independent**, evaluation on programmatically generated synthetic layouts does NOT constitute proof of real-world generalization to un-encountered commercial websites.

---

## 2. Forensic Breakdown of System Components

| Pipeline Component | Implementation Detail | Genuinely Proven | Partially Proven / Unsupported |
| :--- | :--- | :--- | :--- |
| **Model Architecture** | `MultiScaleUIDetector` ($16 \times 16$ fine + $8 \times 8$ coarse grid, 320 candidate slots) | Pure pixel-first tensor decoding (`[1, 3, 256, 256]` $\to$ `[1, 320, 6]`) | Generalization to non-standard custom CSS/canvas components |
| **ONNX Runtime Web** | `extension/public/models/ui_detector_v1.onnx` ($\sim 396\text{ KB}$, WASM SIMD execution) | Browser execution readiness, input tensor normalization | Driver fallback behavior on legacy mobile browsers |
| **Pixel Perturbation** | Sensitivity testing (altered pixels change bounding box output) | Model output depends directly on pixel arrays, not static seeds | Bounding box spatial precision on complex blurred backgrounds |
| **DOM Independence** | Zero DOM metadata passed into ONNX model session | $100\%$ DOM independence during inference | N/A |
| **Dataset Provenance** | Synthetic generator (`generate_ui_dataset.py`, `generate_ood_dataset.py`) | Zero image ID overlap across splits | Synthetic visual patterns differ from real-world CSS styling |

---

## 3. Evaluation Leakage & Synthetic Artifact Analysis

### 3.1 Provenance of Previous Datasets
- **Synthetic Template Overlap**: Previous evaluation rounds relied on synthetic screen generators (`generate_ui_dataset.py`) using fixed color palettes (`CATEGORY_COLORS`), deterministic rectangle borders, and predictable layout grids (cards, inputs, buttons).
- **Geometric Regularity**: Synthetic UI elements feature clean rectangular contours with sharp edges. Real-world web pages contain complex CSS gradients, anti-aliased fonts, box shadows, rounded borders, overlapping popups, and sticky banners.

### 3.2 Distinguishing Synthetic Proof vs. Real-World Evidence
1. **Synthetic Proof**: Proves that the PyTorch architecture and ONNX WASM export pipeline function correctly end-to-end without software crashes or tensor shape mismatches.
2. **Real-World Evidence**: Proves whether the frozen ONNX weights can detect UI buttons, input fields, checkboxes, icons, and navigation controls on live commercial web pages (e.g., GitHub, Amazon, Wikipedia, Govt portals) rendered under actual browser viewports.

---

## 4. Known Pipeline Limitations

1. **Resolution Downscaling**: $1920 \times 1080$ screen captures downscaled to $256 \times 256$ input tensors undergo $\sim 7.5\times$ spatial compression. Sub-10px small icons or inline links can lose edge sharpness during bilinearly interpolated downscaling.
2. **Dense Interface Ceiling**: While 320 candidate slots significantly improve over the initial 25-slot limitation, extremely dense enterprise dashboards ($>50$ interactive elements) require non-maximum suppression (NMS) confidence tuning ($\text{conf} \ge 0.50$).
3. **Typography & Iconography Variety**: Synthetic fonts and icons use uniform SVGs/rectangles. Real-world icon sets (FontAwesome, Material Icons, Feather, Custom SVGs) exhibit diverse visual styling.

---

## 5. Non-Negotiable Baseline Directive

> [!IMPORTANT]
> The production ONNX model asset (`ui_detector_v1.onnx`, SHA-256: `31eebd79681052f9ec4b4b62d810e011d3bf2e6245531419ea99b76699787f60`) will remain **strictly frozen** during this baseline evaluation. No weights, thresholds, or architectural parameters will be modified to artificially boost scores on the real-world evaluation corpus.
