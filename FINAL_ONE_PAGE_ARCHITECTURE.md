# SIH 2026 ARCHITECTURE AT A GLANCE — PROBLEM STATEMENT 26171
## On-Device Visual Perception & Action-Gated Security for Lightweight Browser Agents

> **REVISION**: 1.0 (CODE-FROZEN AUDITED STATE) | **REPOSITORY**: `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0`

---

### 1. HIGH-LEVEL ARCHITECTURE MAP

```
+---------------------------------------------------------------------------------------------------+
| CHROME EXTENSION ISOLATED WORLD (CLIENT BROWSER)                                                   |
|                                                                                                   |
|  [Rendered Webpage] ---> [chrome.tabs.captureVisibleTab] ---> [Raw Viewport Image DataURL]         |
|                                                                         |                         |
|                                                                         v                         |
|                                                     +---------------------------------------+     |
|                                                     | LOCAL WASM VISUAL OCR ENGINE          |     |
|                                                     | (Tesseract 5.x Web Worker Thread)     |     |
|                                                     +---------------------------------------+     |
|                                                                         |                         |
|                                                                         v                         |
|  [Sanitized JSON Payload] <--- [Egress Validator] <--- [Solid #020617 Canvas Redactor]             |
+----------------------------------------|----------------------------------------------------------+
                                         |
                                         v
                         +-------------------------------+
                         | UNTRUSTED REMOTE REASONER     |
                         | (Advisory Task Planner / LLM) |
                         +-------------------------------+
                                         |
                                         v Returns Unauthenticated Action Proposal
+----------------------------------------|----------------------------------------------------------+
| CLIENT-SIDE ACTION FIREWALL (ISOLATED WORLD)                                                      |
|                                                                                                   |
|  [Action Proposal] ---> [HMAC Signature Check] ---> [TOCTOU DOM Query] ---> [Execute DOM Event]   |
|                               |                           |                                       |
|                               v (Invalid)                 v (Mutated / Hidden)                    |
|                         [ABORT EXECUTION]           [ABORT EXECUTION]                             |
+---------------------------------------------------------------------------------------------------+
```

---

### 2. TRUST BOUNDARY DEFINITIONS

| LAYER | PRIVILEGE LEVEL | TRUST STATUS | SECURITY BOUNDARY & GUARANTEE |
| :--- | :--- | :--- | :--- |
| **Webpage DOM** | User Session | **UNTRUSTED (Adversarial)** | May contain prompt injection, malicious overlays, or DOM redressing. |
| **Local WASM OCR** | Extension Worker | **LOCAL TRUSTED** | Extracts text from raw pixels inside browser memory. Zero external network I/O. |
| **Canvas Redactor** | Extension Content | **LOCAL TRUSTED** | Draws solid opaque `#020617` rectangles over PII. Original screenshot destroyed. |
| **Egress Validator** | Local Gatekeeper | **HIGHLY TRUSTED** | Scans outbound JSON strings right before `fetch()`. Kills request if raw PII leaks. |
| **Remote Reasoner** | External Server | **UNTRUSTED ADVISORY** | Generates action proposals only. Has zero DOM access or execution privilege. |
| **Action Firewall** | Local Execution Gate | **HIGHLY TRUSTED** | Verifies single-use HMAC nonces & re-checks DOM element visibility before execution. |

---

### 3. CORE SYSTEM SPECIFICATIONS

* **Visual AI Backend**: Tesseract 5.x WebAssembly CPU Worker (`tesseract-worker.js`).
* **WASM Inference Latency**: ~350ms - 550ms per 1080p viewport capture pass.
* **PII Redaction Engine**: Solid opaque `#020617` dark-fill rectangles (Mathematically non-recoverable).
* **Action Authorization**: HMAC-SHA-256 session key bound to tab ID, origin, and single-use capture nonce.
* **TOCTOU Re-Validation**: Microsecond DOM query verifying element tag, visibility, disabled state, and bounding box stability.
* **Weight Persistence**: Initial 15MB fetch over CDN, cached locally in **IndexedDB** for 100% offline subsequent runs.

---

### 4. SOURCE FILE TRACEABILITY MATRIX

* Capture Orchestration: [content_script.ts](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/content/content_script.ts)
* Secure Service Worker: [service_worker.ts](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/background/service_worker.ts)
* WASM OCR Engine: [visual_ocr_engine.ts](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/visual_ocr_engine.ts)
* PII & Canvas Redactor: [pii_detector.ts](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/pii_detector.ts)
* Egress Boundary Control: [egress_validator.ts](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/egress_validator.ts)
* Action Firewall Gate: [action_firewall.ts](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/firewall/action_firewall.ts)

---

> **END OF ONE-PAGE ARCHITECTURE SPEC**
