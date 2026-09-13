# REAL-WORLD FAILURE ANALYSIS & TAXONOMY REPORT
**SIH Problem Statement 26171 — On-Device Visual Perception for Light-Weight Browser Agents**

---

## 1. Failure Taxonomy Classification

Every false negative and false positive detected during frozen baseline evaluation on the real-world UI corpus (`real_world_manifest.json`) was categorized under a 15-category failure taxonomy.

| Failure Category | Occurrences | Primary Root Cause | Proposed Remediation |
| :--- | :---: | :--- | :--- |
| **`SMALL_OBJECT`** | 14 | Sub-15px icons downscaled during $256 \times 256$ input tensor resize | Multi-scale feature pyramid or targeted crop zoom |
| **`LOW_CONTRAST`** | 8 | Frameless or borderless form inputs on light backgrounds | Edge density heuristic fusion |
| **`VISUAL_SIMILARITY`** | 5 | Text links visually resembling plain body paragraph text | OCR text link bounds fusion |
| **`DENSE_LAYOUT`** | 6 | Dense enterprise dashboard widgets exceeding NMS threshold | Adaptive NMS IoU thresholding |
| **`OVERLAPPING_ELEMENTS`** | 4 | Floating modal backdrops overlapping underlying page elements | Depth layer occlusion resolution |
| **`UNUSUAL_STYLE`** | 3 | Custom CSS glassmorphism & transparent gradient buttons | Expanded visual style dataset augmentation |
| **`RESPONSIVE_LAYOUT`** | 2 | Mobile viewport column wrapping | Multi-resolution aspect ratio training |
| **`TEXT_CONFUSION`** | 4 | Large header text blocks misclassified as button containers | OCR text occupancy filtering |
| **`ICON_CONFUSION`** | 5 | Rating star glyphs misclassified as small button pills | Dedicated SVG icon training samples |
| **`BOUNDING_BOX_ERROR`** | 7 | Partial bounding box regression jitter on elongated inputs | SmoothL1 box regression weight tuning |
| **`CLASS_CONFUSION`** | 3 | Dropdown `select` boxes misclassified as text `input` | ARIA select arrow visual feature extraction |
| **`MULTI_OBJECT_COLLISION`** | 2 | Nearby adjacent checkboxes sharing a single grid cell | $32 \times 32$ high-resolution grid head |
| **`PREDICTION_LIMIT`** | 0 | None ($320$ slots sufficient for all real-world test scenes) | N/A |
| **`PREPROCESSING_ERROR`** | 0 | None (ImageNet mean/std normalization executed cleanly) | N/A |
| **`OTHER`** | 1 | Non-standard canvas element rendering | Canvas pixel rasterizer fallback |

---

## 2. Representative Failure Case Analysis

### Case 1: Sub-15px Navigation Bar Icons (`SMALL_OBJECT`)
- **Visual Evidence**: User profile avatar icon ($16 \times 16$ px) in GitHub top navigation bar.
- **Symptom**: Model output confidence logit fell below $0.50$ threshold.
- **Diagnosis**: Spatial resolution loss during $1920 \times 1080 \to 256 \times 256$ downsampling.
- **Remediation**: OCR engine detects icon anchor text or high-resolution crop region.

### Case 2: Dark Mode Borderless Form Fields (`LOW_CONTRAST`)
- **Visual Evidence**: Search input bar on dark enterprise SaaS portal.
- **Symptom**: Bounding box coordinates offset by $>20\text{px}$.
- **Diagnosis**: Lack of explicit visual border contour.
- **Remediation**: Contrast ratio enhancement preprocessing.
