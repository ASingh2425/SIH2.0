# FINAL SAFE CLAIMS CARD — TEAM VIVA DEFENSE MATRIX
## SIH 2026 Problem Statement 26171 (On-Device Visual Perception)

> **REVISION**: 1.0 (CODE-FROZEN VERIFIED STATE)  
> **PURPOSE**: Quick-reference guide for all team members to guarantee 100% accurate, defensible, and judge-proof claims during SIH judging and Q&A.

---

### THREE-COLUMN TEAM CLAIMS MATRIX

| SAFE TO SAY (100% VERIFIED FACT) | SAY WITH DISCLOSURE (REQUIRES QUALIFIER) | DO NOT SAY (STRICTLY FORBIDDEN / FALSE) |
| :--- | :--- | :--- |
| **"We execute real pixel OCR on-device inside the browser."** | **"The visual OCR engine runs locally after fetching WASM weights on first boot."** | ❌ *"We run WebGPU neural shaders in the browser."* |
| **"Our system uses Tesseract WebAssembly (`tesseract.js`) in a Web Worker."** | **"Model weights are fetched over CDN once, then stored in local IndexedDB cache."** | ❌ *"Zero network downloads occur on first launch."* |
| **"Visual perception processes raw viewport screenshots via `captureVisibleTab`."** | **"Visual perception runs locally before any remote reasoner call is initiated."** | ❌ *"We run a 7 billion parameter VLM inside the browser extension."* |
| **"PII is redacted on-device using solid `#020617` opaque fill rectangles."** | **"Redaction covers both detected DOM text and visual OCR bounding boxes."** | ❌ *"We use reversible Gaussian blur for privacy."* |
| **"Egress validation is fail-closed and scans outbound payloads."** | **"If any unredacted PII matches regex rules, payload transmission is aborted."** | ❌ *"The remote server redacts the privacy sensitive information."* |
| **"Action proposals are validated by a local Action Firewall."** | **"Proposals must carry valid HMAC signatures and pass microsecond TOCTOU DOM checks."** | ❌ *"The remote LLM directly clicks buttons on the webpage."* |
| **"The system achieves 100% DAG containment on canvas benchmarks."** | **"Evaluated across 17 automated Python test suites and real canvas fixtures."** | ❌ *"Our agent has 100% accuracy on all web tasks globally."* |

---

### DETAILED CLAIM EXPLANATIONS FOR TEAM MEMBERS

#### 1. Visual AI & OCR Engine
* **SAFE**: "Our client-side visual engine parses raw viewport image pixels using WebAssembly Tesseract OCR."
* **DISCLOSURE**: "First-time execution fetches WASM binaries, which are then cached locally in IndexedDB for subsequent offline runs."
* **WHY NOT SAY WEBGPU**: The current audited implementation uses WASM CPU worker threads. Saying "WebGPU" will get called out immediately if a judge inspects devtools or source code.

#### 2. Egress Privacy & Redaction
* **SAFE**: "Screenshots are sanitized locally on an HTML5 canvas using solid `#020617` dark-fill rectangles over detected PII coordinates."
* **DISCLOSURE**: "Unredacted raw screenshots never leave the client browser."
* **WHY NOT SAY GAUSSIAN BLUR**: Gaussian blur is security-vulnerable and reversible. We use solid dark fill `#020617` which overwrites pixel data permanently.

#### 3. Action Firewall & Execution
* **SAFE**: "Remote AI models have zero direct DOM access. All actions are proposal-only and gated by our local firewall."
* **DISCLOSURE**: "The firewall validates single-use capture nonces, HMAC signatures, and live DOM element visibility."
* **WHY NOT SAY THE LLM EXECUTED IT**: The LLM is an untrusted planner. Execution authority remains strictly inside the local extension content script.

---

### EMERGENCIES & CORRECTION PROTOCOL DURING JUDGING

If a teammate accidentally makes an inaccurate claim during viva (e.g., *"We run local WebGPU shaders"*):

> **CORRECTION PROTOCOL (Speaker 1 Step-In)**:  
> *"To clarify technically: our current production implementation achieves local visual perception via **Tesseract WebAssembly CPU workers**, which ensures universal compatibility across all client machines without requiring dedicated WebGPU hardware. WebGPU compute shaders represent Phase 1 of our post-hackathon roadmap."*

---

> **END OF SAFE CLAIMS CARD**
