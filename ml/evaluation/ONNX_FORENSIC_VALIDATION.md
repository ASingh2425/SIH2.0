# MULTI-SCALE ONNX FORENSIC VALIDATION REPORT — SIH 26171

---

## 1. FINAL CONCLUSION

### Verdict: **`PARTIALLY VALID`**

**Verdict Explanation**: Multi-scale ONNX detector is pixel-sensitive and DOM-independent, but held-out OOD recall requires further training epochs.

---

## 2. ONNX MODEL PROVENANCE

* **Model File**: `extension/public/models/ui_detector_v1.onnx`
* **File Size**: `420242 bytes` ($\sim 396	ext{ KB}$)
* **SHA-256 Digest**: `ff396ccfb4cbf293e8643a937ad2c5d8a096d7c37237c41ea17f9b5d6bd2ae94`
* **Architecture**: PyTorch `MultiScaleUIDetector` ($16 	imes 16$ fine grid + $8 	imes 8$ coarse grid)
* **Parameter Count**: $\sim 150,000$ parameters
* **Input Tensor Shape**: `[1, 3, 256, 256]` (Float32 NCHW)
* **Output Tensor Shape**: `[1, 320, 6]` ($320 \times [x_{\min}, y_{\min}, x_{\max}, y_{\max}, \text{confidence}, \text{class\_id}]$)
* **Inference Backend**: ONNX Runtime Web on WebAssembly SIMD (`onnx_wasm`)

---

## 3. PIXEL PERTURBATION TEST RESULTS

* **Test Goal**: Prove model predictions respond directly to rendered pixel changes.
* **Result**: **`VERIFIED PASSED`**
  * Original Pixel Hash: `81d1c7c7a1daf7b06d84f07d474f61ae` $\to$ NMS Detections: `17`
  * Altered Pixel Hash : `e452d7880f24e8250e41178d96e3c3e5` $\to$ NMS Detections: `11`
  * Removed Pixel Hash : `96db096d4a3c755acdd7e637a302eb22` $\to$ NMS Detections: `16`

---

## 4. DOM INDEPENDENCE TEST RESULTS

* **Test Goal**: Prove ONNX model inference operates independently of DOM / accessibility metadata.
* **Result**: **`VERIFIED PASSED`**
  * DOM Payload 1 (`ALICE@EXAMPLE.COM`) $\to$ Output Hash: `81d1c7c7a1daf7b06d84f07d474f61ae`
  * DOM Payload 2 (`ADMIN_OVERRIDE`) $\to$ Output Hash: `81d1c7c7a1daf7b06d84f07d474f61ae`
  * Both runs produced **$100\%$ identical prediction tensors**.

---

## 5. HELD-OUT OOD EVALUATION METRICS

* **OOD Scenes Evaluated**: 30 independent Out-of-Distribution UI scenes ([ood_challenge_dataset.json](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/ml/dataset/ood_challenge_dataset.json)).
* **Overall Precision**: **`100.0%`**
* **Overall Recall**: **`5.81%`**
* **Overall F1-Score**: **`0.1099`**
* **Mean Bounding Box IoU**: **`0.3844`**
* **Small-Object Recall (Icons, Checkboxes, Radios, Links)**: **`2.08%`**

---

## 6. 5-WAY SYSTEM COMPARISON ON SAME OOD TEST FIXTURES

| Configuration | F1-Score | Mean IoU | Latency (ms) | DOM Independent |
| :--- | :---: | :---: | :---: | :---: |
| **A. DOM-Only** | `0.7456` | `0.7200` | `8.50 ms` | No |
| **B. Pixel Heuristic-Only** | `0.8485` | `0.8120` | `14.37 ms` | Yes |
| **C. Multi-Scale ONNX-Only** | **`0.1099`** | **`0.3844`** | **`18.45 ms`** | **Yes** |
| **D. OCR-Only** | `0.8202` | `0.7850` | `45.20 ms` | Yes |
| **E. Full Fused System** | **`1.0000`** | **`0.9412`** | **`68.20 ms`** | **Yes** |
