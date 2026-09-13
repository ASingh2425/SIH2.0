# REAL-WORLD VISUAL GENERALIZATION EVALUATION PROTOCOL
**SIH Problem Statement 26171 — On-Device Visual Perception for Light-Weight Browser Agents**

---

## 1. Evaluation Objective

To establish a strict, reproducible, empirical evaluation methodology measuring the performance of the frozen browser-side ONNX visual UI object detector (`extension/public/models/ui_detector_v1.onnx`) on genuinely external real-world web page interfaces.

---

## 2. Real-World Corpus Criteria & Sampling Categories

The evaluation corpus must consist exclusively of actual rendered web page screenshots captured from real public websites. Synthetic HTML/SVG templates, local demo generators, and programmatic test scenes are strictly excluded.

### Target Interface Categories (Categories A–F)

1. **Category A — Forms & Authentication**:
   - Registration, login, contact, search, checkout, and settings forms.
   - Target Elements: `input` (text/password), `button` (submit/cancel), `checkbox`, `radio`, `select` (dropdown).
2. **Category B — Enterprise & SaaS Dashboards**:
   - Analytics, admin panels, cloud monitoring, project management, and financial portals.
   - Target Elements: `card`, `navigation`, `button`, `icon`, `text_block`, `select`.
3. **Category C — E-Commerce & Retail**:
   - Product detail pages, category listings, cart drawers, and checkout flows.
   - Target Elements: `image`, `button` (Add to Cart), `card`, `text_block` (price/title), `icon` (rating stars).
4. **Category D — Technical Documentation & Content**:
   - Developer documentation, tech blogs, knowledge bases, and news articles.
   - Target Elements: `navigation`, `link`, `text_block`, `image`, `card`.
5. **Category E — Government & Public Service Portals**:
   - High-density public forms, citizen portals, tax/filing interfaces, and municipal tables.
   - Target Elements: `input`, `button`, `checkbox`, `select`, `navigation`, `text_block`.
6. **Category F — Responsive & Layout Variations**:
   - Viewport scaling across Desktop ($1920 \times 1080$, $1440 \times 900$, $1366 \times 768$), Laptop ($1280 \times 720$), and Mobile ($390 \times 844$).

---

## 3. Strict Anti-Leakage & Data Integrity Rules

1. **Frozen Test Set**: Real-world evaluation screenshots and annotations must be frozen prior to model inference.
2. **No DOM Leakage**: Bounding box ground truth must be annotated manually from visual pixel appearance. DOM/Accessibility trees must NOT be used to generate target annotations.
3. **Fixed Thresholds**: Confidence threshold ($\text{conf} \ge 0.50$), NMS IoU threshold ($0.45$), and preprocessing normalization ($\text{ImageNet mean/std}$) must remain fixed.

---

## 4. Required Evaluation Metrics

- **Overall Accuracy**: Precision, Recall, F1-Score, mAP@0.50, mAP@0.50:0.95, Mean IoU, Median IoU, P95 IoU.
- **Per-Class Metrics**: Individual evaluation across all 11 classes (`button`, `input`, `checkbox`, `radio`, `select`, `link`, `navigation`, `card`, `image`, `icon`, `text_block`).
- **Scale Breakdown**: Tiny ($<32\times32$), Small ($32\times32\text{--}64\times64$), Medium ($64\times64\text{--}128\times128$), Large ($>128\times128$).
- **Density Breakdown**: Low ($<10$), Medium ($10\text{--}25$), High ($26\text{--}50$), Very High ($>50$ objects).
- **5-Way System Ablation**: DOM-Only vs OCR-Only vs Pixel Detector-Only vs Pixel+OCR vs Full Fused System.
