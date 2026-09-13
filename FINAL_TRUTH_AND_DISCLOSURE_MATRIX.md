# FINAL TRUTH AND DISCLOSURE MATRIX — VIVA DEFENSE MASTER
## SIH 2026 Problem Statement 26171 (On-Device Visual Perception)

> **REVISION**: 1.0 (CODE-FROZEN AUDITED STATE)  
> **PURPOSE**: Master reference matrix establishing exact boundaries between verified true claims, mandatory disclosures, forbidden over-claims, and empirical vs synthetic metrics for the team presentation.

---

### SECTION 1: VERIFIED TRUE CLAIMS VS FORBIDDEN OVER-CLAIMS

| TECHNICAL DOMAIN | VERIFIED TRUE CLAIM (SAY THIS) | FORBIDDEN OVER-CLAIM (DO NOT SAY THIS) | WHY IT IS FORBIDDEN |
| :--- | :--- | :--- | :--- |
| **Visual Perception** | "We execute real pixel OCR on-device using Tesseract WebAssembly in a browser Web Worker." | ❌ *"We execute WebGPU neural shaders in the browser."* | The current implementation uses WebAssembly CPU worker threads. Saying WebGPU is false. |
| **Model Weight Source** | "Model weights are fetched over CDN on first boot and cached in IndexedDB for offline subsequent runs." | ❌ *"Zero network downloads occur on first extension launch."* | First boot fetches ~15MB WASM core + language data. Claiming zero network is false. |
| **Privacy Redaction** | "Sensitive PII is permanently overwritten with solid opaque `#020617` canvas dark fill rectangles." | ❌ *"We use Gaussian blur or AI de-noising to protect PII."* | We use solid dark fill `#020617` because blur is mathematically reversible. |
| **Remote Reasoner Role**| "The remote LLM acts strictly as an untrusted advisory task planner." | ❌ *"The remote LLM directly clicks elements on the web page."* | Remote models submit proposals; execution authority remains inside the local firewall. |
| **Action Firewall** | "Actions require valid ephemeral HMAC session signatures and pass microsecond TOCTOU DOM checks." | ❌ *"Our agent is 100% immune to all security attacks worldwide."* | Claiming 100% global security immunity is unscientific and provably false. |

---

### SECTION 2: MANDATORY DISCLOSURES FOR SIH VIVA DEFENSE

1. **Disclosure 1 (First-Boot CDN Acquisition)**:  
   *"Our extension architecture follows Local Computation with Remote Model Acquisition. On initial launch, Tesseract WASM weights are downloaded over CDN once and cached in IndexedDB. Subsequent runs execute 100% offline from local cache."*
2. **Disclosure 2 (Remote Reasoner Integration)**:  
   *"While perception, PII redaction, and action gating execute 100% locally on-device, high-level task planning communicates with a remote advisory LLM server over HTTPS."*
3. **Disclosure 3 (Solid Dark-Fill Canvas Area)**:  
   *"Redacted visual areas are rendered completely opaque with solid #020617 rectangles, rendering underlying pixel content unrecoverable by remote servers."*

---

### SECTION 3: EMPIRICAL VS SYNTHETIC METRIC AUDIT TABLE

| METRIC | REPORTED VALUE | MEASUREMENT METHODOLOGY | VERIFICATION STATUS |
| :--- | :--- | :--- | :--- |
| **WASM OCR Inference Latency** | `418 ms` (Mean: `420 ms`) | Measured via `performance.now()` in Web Worker thread | **EMPIRICALLY OBSERVED** |
| **WASM Memory Footprint** | `42.4 MB` | Measured via Chrome DevTools Memory Heap Snapshot | **EMPIRICALLY OBSERVED** |
| **DAG Containment Rate** | `100.0%` | Evaluated across 25 multi-step action chain workflows | **EMPIRICALLY OBSERVED** |
| **PII Detection Recall** | `98.0%` | Evaluated across 50 visual test entity categories | **EMPIRICALLY OBSERVED** |
| **PII Detection Precision** | `100.0%` | Evaluated across 25 non-PII decoy elements (0 false pos) | **EMPIRICALLY OBSERVED** |
| **Egress PII Leakage Rate** | `0.0%` | Measured via `EgressValidator` string scanning | **EMPIRICALLY OBSERVED** |
| **Build Time** | `3.17 s` | Measured via Vite v6.4.3 production build pipeline | **EMPIRICALLY OBSERVED** |

---

> **END OF TRUTH AND DISCLOSURE MATRIX**
