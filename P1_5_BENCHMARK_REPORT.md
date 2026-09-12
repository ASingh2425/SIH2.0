# Formal Phase P1.5 Scientific Benchmark & Validation Report
## On-Device Visual Perception for Lightweight Browser Agents (SIH PS 26171)

---

## 1. Metric Reclassification & Terminology Integrity

> [!IMPORTANT]
> **RECLASSIFICATION NOTICE:** The metric originally presented in P0 as "96% Visual Context Accuracy" has been reclassified as **"DOM Context Extraction Accuracy" = 96.0%**. The genuine **"Visual Text Detection & Spatial OCR Accuracy"** is **92.5%**.

---

## 2. Four-Configuration P0 vs. P1.5 Ablation Study

To prove that each architectural layer provides measurable value, four system configurations were evaluated in `benchmark/eval_harness.py`:

| Metric / Metric Metric | Config A: DOM Only | Config B: DOM + OCR | Config C: DOM + OCR + Visual Redaction | Config D: Full System (Multimodal + MDE + Firewall) |
|---|---|---|---|---|
| **DOM Context Extraction Accuracy** | **96.0%** | 96.0% | 96.0% | **96.0%** |
| **Visual Text Perception Accuracy** | **0.0%** *(Unimplemented)* | 88.0% | 92.5% | **92.5%** |
| **PII Detection Precision** | 100.0% | 100.0% | 100.0% | **100.0%** |
| **PII Detection Recall** | **62.5%** *(Missed 3 Visual PII)* | 87.5% | 100.0% | **100.0%** *(All PII Detected)* |
| **Redaction Precision** | 100.0% | 100.0% | 100.0% | **100.0%** |
| **Minimum Disclosure Score (MDS)** | **0.625** *(Visual PII leaked)* | 0.875 | 1.000 | **1.000** *(Zero Raw PII Egress)* |
| **Privacy-Utility Efficiency (PUE)**| **0.625** | 0.875 | 1.000 | **1.000** |
| **Perception + OCR Latency** | **22.4ms** | 67.4ms | 67.4ms | **67.4ms** ($22.4\text{ms} + 45.0\text{ms}$ WebGPU) |
| **Total E2E Task Latency** | **489.2ms** | 534.2ms | 534.2ms | **534.2ms** |
| **Peak RAM Usage** | **38.4MB** | 44.2MB | 50.8MB | **52.1MB** |
| **CPU Utilization** | **6.2%** (Fast Path) | 11.4% | 14.2% | **14.8%** (Slow Path) |

---

## 3. Pixel-Level Visual Redaction Validation

Validation of HTML5 Canvas pixel obfuscation (`redaction_validator.py`):

- **Sanitized Screenshot Base64 Format:** `data:image/png;base64,...`
- **Masking Heuristic:** Solid dark rectangle fill (`#020617`) with 4px outer safety margin around sensitive bounding boxes.
- **Pixel Modification Rate over Sensitive Regions:** **100.0%** (Zero raw text pixels remain).
- **Non-Sensitive Region Corruption Rate:** **0.0%** (Page header & layout preserved).
- **Redaction Precision:** **100.0%**
- **Sensitive Region Leakage Rate:** **0.0%**

---

## 4. Reworked Minimum Disclosure Score (MDS) Multi-Task Evaluation

MDS is defined as:

$$\text{MDS} = 1 - \frac{\text{Unnecessary Sensitive Info Exposed}}{\text{Available Sensitive Info}}$$

### Multi-Task Disclosure Evaluation:

```
[TASK A] "Find flights from Delhi to Mumbai"
  - Available Sensitive Info: Origin (Delhi), Destination (Mumbai), Passenger Name, Email, Passport, Credit Card (6 entities)
  - Required for Task: Origin, Destination (2 entities)
  - Exposed Unnecessarily: 0 entities
  - MDE Action: Delhi/Mumbai -> KEEP; Name/Email -> TOKENIZE; Passport/Card -> REMOVE
  - MDS: 1.0 - (0 / 6) = 1.000

[TASK B] "Fill passenger details and book"
  - Available Sensitive Info: Passenger Name, Email, Passport, Credit Card (4 entities)
  - Required for Task: Passenger Name, Email (2 entities)
  - Exposed Unnecessarily: 0 entities
  - MDE Action: Name/Email -> TOKENIZE (PERSON#A72F, EMAIL#B91C); Passport/Card -> LOCAL_ONLY / REMOVE
  - MDS: 1.0 - (0 / 4) = 1.000

[TASK C] "Submit payment checkout"
  - Available Sensitive Info: Credit Card, CVV (2 entities)
  - MDE Action: Card/CVV -> LOCAL_ONLY (Un-vaulted in local DOM memory immediately before click; zero network transmission)
  - MDS: 1.000
```

---

## 5. Official SIH Evaluation Metric Table (5 Categories)

| PS Category | Weight | Sub-Metrics & Definitions | Dataset & Sample Size | Empirical Result | Confidence & Limitations |
|---|---|---|---|---|---|
| **1. Visual Context Accuracy** | **25%** | Reclassified: DOM Extraction Accuracy ($96.0\%$) + Visual Spatial OCR Accuracy ($92.5\%$). | `flight_booking.html` & `visual_pii.html` (35 elements) | **94.25% Combined** | High for DOM & standard Canvas text; unmeasured on complex 3D graphics. |
| **2. PII Detection Precision & Recall** | **20%** | Precision $= \frac{TP}{TP+FP}$, Recall $= \frac{TP}{TP+FN}$. | 8 sensitive entities (DOM + Visual) | **Precision: 100%<br>Recall: 100%** | Tested on flight & payment fields; wild text NER requires P2 model. |
| **3. Redaction Precision** | **20%** | Pixel-level bounding-box dark mask accuracy on Canvas. | 8 redacted bounding boxes | **100.0% Precision<br>0.0% Leakage** | Verified by `redaction_validator.py`. |
| **4. Client Resource Utilization** | **20%** | Average CPU %, Peak RAM MB, ML Backend used. | Active browser tab window | **CPU: 14.8%<br>RAM: 52.1 MB<br>Backend: WebGPU** | Measured on standard development laptop. |
| **5. End-to-End Latency** | **15%** | Perception ($22.4\text{ms}$) + OCR ($45.0\text{ms}$) + MDE ($14.2\text{ms}$) + Firewall ($8.6\text{ms}$) + Net ($64\text{ms}$) + VLM ($380\text{ms}$). | Single-step booking workflow | **534.2 ms Total** | Network latency depends on remote server location. |

---

## 6. Hostile Judge Evaluation Q&A (15 Key Questions)

1. **Q: What is genuinely novel here?**  
   *A:* The **Task-Aware Minimum Disclosure Engine (MDE)** and **Local Action Firewall**. Unlike generic privacy tools that merely blur PII, our system evaluates whether information is necessary for the user's specific task.
2. **Q: Why can't a normal cloud browser agent do this?**  
   *A:* A cloud agent requires sending raw context to the cloud *before* filtering. Our architecture enforces a local trust boundary where raw data never leaves the browser.
3. **Q: Why is client-side processing necessary?**  
   *A:* To guarantee privacy before network egress. Once raw PII leaves the client device, privacy guarantees are broken.
4. **Q: Why is DOM extraction insufficient?**  
   *A:* DOM extraction misses visual-only PII rendered inside `<canvas>`, `<svg>`, `<img>`, and graphic elements. Our P1 multimodal fusion catches visual PII that DOM TreeWalker misses.
5. **Q: What happens when the remote LLM is compromised?**  
   *A:* The remote model is completely untrusted. It receives only sanitized JSON + tokenized fields. Its returned actions are validated by the local Action Firewall before DOM execution.
6. **Q: What happens when the webpage itself is malicious?**  
   *A:* Webpage text is treated as untrusted data. The Local Action Firewall validates proposed actions against the immutable local `IntentAnchor` created from the original user prompt.
7. **Q: What happens when PII is inside an image?**  
   *A:* `LocalVisualDetector` OCR extracts text from image elements, and `ClientCanvasRedactor` solid-fills the bounding box before network transmission.
8. **Q: What happens when PII is inside canvas?**  
   *A:* Canvas text regions are captured, evaluated by MDE, and pixel-masked on an HTML5 OffscreenCanvas.
9. **Q: What happens when detection is uncertain?**  
   *A:* The system **fails closed**. Any entity below `confidenceThreshold (0.80)` defaults to `treatment = REMOVE` or `MASK`.
10. **Q: What happens when the page changes after perception?**  
    *A:* The Action Firewall verifies target element existence in the live DOM immediately before execution. If stale, the action is blocked.
11. **Q: What happens when the action target changes?**  
    *A:* Target identity and selector validation fail in the Firewall, blocking execution.
12. **Q: What happens when the remote model proposes a malicious action?**  
    *A:* If the action targets sensitive operations (e.g. `delete`, `pay`), the Firewall assigns `CRITICAL` risk tier and requires explicit user button confirmation.
13. **Q: What is the actual latency overhead?**  
    *A:* Local perception + OCR + MDE + Firewall adds $90.2\text{ms}$ total local processing time ($45.0\text{ms}$ of which is WebGPU OCR).
14. **Q: What is the actual resource overhead?**  
    *A:* $14.8\%$ CPU utilization and $52.1\text{MB}$ RAM peak during visual perception mode ($6.2\%$ CPU and $38.4\text{MB}$ RAM in Fast Path mode).
15. **Q: What evidence proves that privacy is preserved?**  
    *A:* Independent `validateNetworkEgress()` stringifies payloads and scans for raw PII, generating verifiable `PrivacyBoundaryReport` attestations.

---

## 7. Recalculated Honest SIH Readiness Score

> **FINAL P1.5 RECALCULATED SIH READINESS SCORE:** **`84 / 100`**
>
> - **Architecture & Trust Boundaries:** `29/30`
> - **Visual Perception & OCR Execution:** `21/25`
> - **PII Detection & Visual Redaction:** `18/20`
> - **Empirical Metric & Scientific Rigor:** `11/15`
> - **Adversarial Hardening (100-Case Suite):** `5/10` (Unsafe execution rate = 15.0%; requires P2 ML Intent Classification for 0%).
