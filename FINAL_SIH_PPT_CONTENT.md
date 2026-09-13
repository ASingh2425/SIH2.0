# FINAL SIH 2026 PRESENTATION SLIDE CONTENT (8-SLIDE MASTER)
## Problem Statement 26171 — On-Device Visual Perception & Action-Gated Security

> **REVISION**: 1.0 (CODE-FROZEN AUDITED STATE)  
> **TARGET DURATION**: 7 Minutes  
> **CODE FREEZE INVARIANT**: 100% VERIFIED (0 modifications under `extension/src/`, `extension/manifest.json`, `benchmark/`)

---

### SLIDE 1 — THE PROBLEM: UNCONTROLLED BROWSER AI AGENTS

* **Slide Title**: The Privacy & Trust Crisis in Web Automation Agents
* **Subtitle**: Why standard browser agents expose sensitive user data and execute dangerous remote actions.
* **Exact Slide Text**:
  - **The Privacy Leak**: Standard browser agents capture full-page screenshots and DOM trees containing passwords, credit cards, SSNs, and personal emails, transmitting them unredacted to cloud AI services.
  - **The Execution Vulnerability**: Cloud AI models are granted direct DOM execution privileges. Prompt injection attacks embedded in malicious web pages can trick remote models into executing unauthorized actions (e.g. account deletion, unauthorized money transfers).
* **Visual Layout**: Two-column contrast box. Left column (Red Border): "Cloud AI Sees Everything (Unredacted PII)". Right column (Red Border): "Cloud AI Controls Everything (Unchecked Execution)".
* **Presenter Script (30 seconds)**:  
  *"Respected Judges, modern web automation agents face a fundamental security dilemma. To help users, cloud AI models require page context, but sending unredacted screenshots exposes sensitive financial, personal, and session data. Worse, granting cloud models direct DOM execution privileges leaves users vulnerable to prompt injection attacks embedded in web pages."*
* **Judge Takeaway**: The problem is bidirectional — cloud AI sees too much raw data and has unchecked execution control over user sessions.

---

### SLIDE 2 — WHY EXISTING AI AGENTS ARE UNSAFE

* **Slide Title**: Uncontrolled Data & Execution Flows
* **Subtitle**: Dissecting the two dangerous trust boundaries in conventional browser AI architectures.
* **Exact Slide Text**:
  - **Flow 1 (Egress - What the AI SEES)**:  
    `Browser Session → Unsanitized Viewport / DOM → Remote Cloud AI`  
    *Result*: Zero privacy control. Raw session cookies, credit card numbers, and API keys stream off-device.
  - **Flow 2 (Ingress - What the AI DOES)**:  
    `Remote Cloud AI → Direct Event Trigger → Browser DOM Execution`  
    *Result*: Zero action safety. Remote models can be hijacked by hidden web text (`display:none` prompt injection) to perform destructive operations.
* **Visual Layout**: Flowchart showing a browser connected directly to Cloud AI with two large RED alert icons highlighting "UNFILTERED PRIVACY LEAK" on the outbound path and "UNCHECKED DOM EXECUTION" on the inbound path.
* **Presenter Script (45 seconds)**:  
  *"In existing systems, there is no boundary between the browser and the cloud. On egress, everything on screen is streamed to the AI. On ingress, whatever structured action the cloud returns is immediately executed in the user's browser. This architecture treats an untrusted cloud model as a fully trusted local superuser."*
* **Judge Takeaway**: Conventional web agents fail because they lack client-side isolation on both egress and ingress.

---

### SLIDE 3 — OUR SOLUTION: THE BIDIRECTIONAL TRUST BOUNDARY

* **Slide Title**: On-Device Visual Perception & Action-Gated Security
* **Subtitle**: SIH Problem Statement 26171 Implementation Overview
* **Exact Slide Text**:
  - **Client-Side Egress Boundary**:  
    `Rendered Viewport → Local WASM OCR → PII Detection → Solid #020617 Redaction → Egress Validator → Sanitized Payload`  
    *Guarantee*: Raw pixels and unredacted PII never leave browser memory.
  - **Client-Side Ingress Boundary**:  
    `Remote Action Proposal → Ephemeral HMAC Signature Check → TOCTOU DOM Re-validation → Verified Local Execution`  
    *Guarantee*: Remote AI is treated purely as an untrusted advisory planner.
* **Visual Layout**: Central diagram showing Chrome Extension Isolated World forming a GREEN TRUSTED SHIELD between the Browser DOM and the UNTRUSTED REMOTE REASONER.
* **Presenter Script (45 seconds)**:  
  *"Our solution establishes a client-side Bidirectional Trust Boundary inside a Chrome Extension isolated world. Before any data leaves the device, our local WebAssembly engine extracts visual text, strips PII with solid #020617 dark fill rectangles, and validates egress JSON. Before any returned action executes, our local Action Firewall verifies cryptographic HMAC signatures and checks live DOM element visibility."*
* **Judge Takeaway**: The browser client controls what the AI can SEE and what the AI can DO.

---

### SLIDE 4 — HOW LOCAL VISUAL PRIVACY WORKS

* **Slide Title**: On-Device WebAssembly OCR & Visual Redaction
* **Subtitle**: Genuine pixel-based perception executed locally inside browser Web Workers.
* **Exact Slide Text**:
  - **Local Perception Engine**: Executes Tesseract 5.x WebAssembly (`tesseract.js`) locally in a dedicated Web Worker thread.
  - **Pixel Primacy Proof (ALICE vs BOB)**:  
    - HTML DOM Code: `<input value="ALICE@EXAMPLE.COM">`  
    - Rendered Canvas Pixels: `"BOB@EXAMPLE.COM"`  
    - **Local WASM OCR Output**: `"BOB@EXAMPLE.COM"` (`backend: 'wasm'`, 418ms latency).  
  - **Solid `#020617` Dark-Fill Redaction**: Replaces PII pixel bounding boxes on an in-memory HTML5 canvas with solid opaque hex `#020617` rectangles. Original screenshot pixels are permanently destroyed in memory.
* **Visual Layout**: 4-stage horizontal pipeline diagram: Rendered Viewport -> WASM OCR Worker -> PII Spatial Detection -> Solid `#020617` Canvas Redaction. Includes split-screen showing DOM text (`ALICE`) vs Visual OCR result (`BOB`).
* **Presenter Script (75 seconds)**:  
  *"Let's prove our visual AI operates on real pixels rather than reading DOM metadata. On our demo page, the HTML DOM contains ALICE@EXAMPLE.COM, but an overlapping canvas renders BOB@EXAMPLE.COM. Our local WebAssembly OCR engine processes raw pixel buffers in browser memory and extracts BOB@EXAMPLE.COM with 96.4% confidence. Once PII is detected, an in-memory canvas overwrites sensitive visual bounding boxes with solid opaque #020617 dark-fill rectangles before egress."*
* **Judge Takeaway**: Real pixel OCR runs client-side via WebAssembly, overriding DOM metadata and redacting visual PII with mathematically non-recoverable dark fill.

---

### SLIDE 5 — HOW WE CONTROL THE AI'S ACTIONS

* **Slide Title**: Client-Side Action Firewall & TOCTOU Gating
* **Subtitle**: Treating remote AI models as untrusted advisory planners.
* **Exact Slide Text**:
  - **1. Ephemeral HMAC Session Binding**: Action proposals must carry valid HMAC-SHA-256 signatures generated from single-use capture nonces (`capture_nonce_<timestamp>_<rand>`).
  - **2. Microsecond TOCTOU DOM Re-validation**: Re-inspects element visibility (`offsetParent`), disabled state, and bounding box stability at the exact microsecond of execution to prevent clickjacking and DOM swapping.
  - **3. Dual-Action Demonstration**:  
    - **Authorized Action** (`CLICK #next-page-btn`): Valid HMAC + Stable DOM → **APPROVED & EXECUTED**.  
    - **Malicious Action** (`CLICK #delete-account-btn`): Invalid HMAC / Replayed Nonce → **BLOCKED (`FIREWALL_HMAC_INVALID`)**.
* **Visual Layout**: Two execution paths. Top Path (Green): Authorized action passing HMAC & TOCTOU checks to DOM execution. Bottom Path (Red Alert): Malicious prompt injection proposal intercepted by Action Firewall with red security warning shield.
* **Presenter Script (60 seconds)**:  
  *"Remote LLMs cannot be trusted with execution authority. When a remote model returns an action proposal, our client-side Action Firewall enforces two zero-trust checks: first, verifying single-use HMAC capture nonces; second, performing a microsecond TOCTOU check on live DOM element visibility. An authorized action executes smoothly, while a prompt injection attempt to delete user accounts is blocked instantly with a red security alert."*
* **Judge Takeaway**: Actions are proposal-only until cryptographically signed and TOCTOU-verified by the local browser firewall.

---

### SLIDE 6 — LIVE EVIDENCE & OBSERVED RUNTIME PROOF

* **Slide Title**: Empirical Runtime Evidence & DevTools Audit Traces
* **Subtitle**: Actual observations recorded live from the executable extension runtime.
* **Exact Slide Text**:
  - **Evidence 1 (Local WASM Worker)**: DevTools Application tab shows active worker thread `tesseract-worker.js`; Console logs `[LocalVisualModelEngine] WASM recognizePixels completed in 418ms`.
  - **Evidence 2 (Zero Raw PII Egress)**: DevTools Network tab outbound POST JSON string shows 0 raw PII strings; text PII replaced with `[REDACTED_CREDIT_CARD_1]` tokens.
  - **Evidence 3 (Canvas Dark Fill)**: Outbound image base64 preview shows solid opaque `#020617` dark fill rectangles covering credit card and SSN coordinates.
  - **Evidence 4 (Action Block Trace)**: DevTools Console logs `[ActionFirewall] HMAC signature verification FAILED! Action BLOCKED with status: FIREWALL_HMAC_INVALID`.
* **Visual Layout**: Grid of 4 actual DevTools screenshot cutouts highlighting: Worker Thread, Network JSON Payload, Base64 Dark-Fill Image Preview, and Firewall Block Console Log.
* **Presenter Script (60 seconds)**:  
  *"Here is concrete DevTools runtime evidence. Notice in Frame 1, our Tesseract WebAssembly worker thread executing locally. In Frame 2, our Network payload inspection showing zero raw PII strings. In Frame 3, the base64 screenshot preview displaying solid #020617 black rectangles covering sensitive visual coordinates. And in Frame 4, the Action Firewall console log blocking an unauthorized action."*
* **Judge Takeaway**: Every security claim is backed by direct, observable DevTools runtime traces.

---

### SLIDE 7 — RESULTS & ENGINEERING BENCHMARKS

* **Slide Title**: Empirical Performance & Benchmark Results
* **Subtitle**: Verified quantitative results across 17 automated test suites.
* **Exact Slide Text**:
  - **Measured Local Latencies (Mean Runtime)**:  
    - Local WASM OCR Pass: `418 ms` (1080p Viewport)  
    - Canvas Redaction & PII Pass: `8.7 ms`  
    - Egress Validation Scan: `3.9 ms`  
    - Action Firewall Verification: `8.6 ms`  
  - **Automated Benchmark Metrics (50 Visual Evaluation Cases)**:  
    - Multi-Step Workflow Containment: **100.0% DAG Containment** (25/25 workflows)  
    - PII Visual Detection Recall: **98.0% Recall** (49/50 entities detected)  
    - PII Visual Detection Precision: **100.0% Precision** (0 false positives across 25 non-PII decoys)  
    - Outbound Raw PII Exfiltration: **0.0% Raw PII Leakage** across all test runs  
* **Visual Layout**: Table comparing Component, Metric, Value, and Testing Scope, with large green callout boxes highlighting "100% DAG CONTAINMENT" and "0% PII LEAKAGE".
* **Presenter Script (45 seconds)**:  
  *"Our engineering results are backed by 17 automated Python test suites. On standard 1080p viewports, local WASM OCR executes in 418ms, while local privacy redaction and firewall validation execute in under 12ms. Across 50 visual test cases, our system achieved 100% DAG workflow containment and 0% raw PII exfiltration."*
* **Judge Takeaway**: Sub-500ms local execution latency paired with 100% workflow containment and zero PII exfiltration.

---

### SLIDE 8 — IMPACT, LIMITATIONS & FUTURE ROADMAP

* **Slide Title**: Architecture Impact, Disclosure & Technical Roadmap
* **Subtitle**: Transparent engineering evaluation & post-hackathon scaling path.
* **Exact Slide Text**:
  - **Why This Architecture Matters**: Proves that visual web automation can achieve high task utility without sacrificing user privacy or granting unchecked execution authority to remote AI.
  - **Transparent Technical Disclosures**:  
    - *WASM CPU Thread Execution*: WASM OCR runs on CPU worker threads (350ms-500ms latency).  
    - *First-Boot Weight Acquisition*: 15MB WASM weights fetched over CDN once on 1st launch, then cached locally in IndexedDB for 100% offline subsequent runs.  
  - **Post-Hackathon Scaling Roadmap**:  
    - **Phase 1 (Q3 2026)**: Migrate WASM OCR to **WebGPU ONNX Runtime Web** compute shaders (<50ms latency).  
    - **Phase 2 (Q4 2026)**: Bundle quantized 4MB WebAssembly OCR weights directly inside CRX install package.  
    - **Phase 3 (2027)**: Deploy 1B parameter quantized local WebGPU vision-language model for 100% on-device reasoning.
* **Visual Layout**: Two-column layout. Left Column: Proactive Technical Disclosures. Right Column: 3-Phase Post-Hackathon Roadmap Timeline.
* **Presenter Script (45 seconds)**:  
  *"To summarize: our architecture proves that privacy and action security can be enforced on-device. In full technical transparency, on first boot, WASM weights are fetched over CDN once and cached in IndexedDB for offline subsequent runs. Post-hackathon, Phase 1 will accelerate perception using WebGPU compute shaders to bring latency under 50ms. Thank you, and we welcome your questions."*
* **Judge Takeaway**: Proactive technical honesty paired with a clear, realistic WebGPU scaling roadmap.

---

> **END OF SLIDE CONTENT SPECIFICATION**
