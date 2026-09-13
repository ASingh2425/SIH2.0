# SIH 2026 JUDGE POSITIONING MASTER — PROBLEM STATEMENT 26171
## On-Device Visual Perception & Action-Gated Security for Lightweight Browser Agents

> **REVISION**: 1.0 (POST-AUDIT CODE-FROZEN VERIFIED STATE)  
> **PURPOSE**: Master positioning document equipping the team with exact one-liners, pitch scripts, differentiators, disclosures, and presentation boundaries for SIH judging.

---

### SECTION 1: CORE POSITIONING STATEMENTS

#### 1. One-Sentence Problem Statement
> *"Existing browser automation agents leak sensitive user screenshots to remote cloud VLMs and execute unverified remote actions directly on active web sessions, making them vulnerable to privacy exfiltration and prompt injection attacks."*

#### 2. One-Sentence Solution
> *"Our system enforces a client-side zero-trust security architecture using on-device WebAssembly visual OCR to strip PII with solid `#020617` canvas dark fill before remote transmission, while gating all returned action proposals through a local HMAC Action Firewall with microsecond TOCTOU DOM re-validation."*

#### 3. 30-Second Elevator Pitch
> *"Respected Judges, we have built a privacy-preserving lightweight browser agent extension that solves SIH Problem Statement 26171. Instead of sending raw screenshots to the cloud, our browser extension performs local visual perception inside a WebAssembly Web Worker. It extracts rendered text directly from pixels, masks sensitive PII on an in-memory canvas using solid `#020617` dark fill rectangles, and sanitizes outbound text payloads. When the remote AI returns action proposals, our local Action Firewall verifies single-use HMAC nonces and checks live DOM element visibility before any click executes, protecting the user from prompt injection and exfiltration attacks."*

#### 4. 60-Second Technical Deep-Dive
> *"Architecturally, our system establishes two strict local trust boundaries inside the Chrome extension isolated world. First, on the egress boundary, `content_script.ts` triggers active tab capture, passing raw viewport pixel buffers into a dedicated Web Worker thread running Tesseract WebAssembly (`tesseract-worker.js`). Local visual OCR output is fused with DOM tree nodes. When PII patterns are matched, an in-memory HTML5 canvas overwrites the exact bounding box pixels with solid opaque `#020617` dark fill rectangles, while DOM strings are tokenized into temporary tokens. The local `EgressValidator` performs a fail-closed string scan on the JSON payload before `fetch()` transport. Second, on the ingress boundary, returned action proposals are intercepted by `action_firewall.ts`. The firewall verifies ephemeral session HMAC-SHA-256 signatures, validates single-use capture nonces, and performs a microsecond TOCTOU check on live DOM node visibility and position before dispatching synthetic DOM events."*

---

### SECTION 2: THE 3 STRONGEST DIFFERENTIATORS

1. **True On-Device Pixel AI (WASM OCR)**: Unlike DOM-only agents that break on canvas/WebGL UIs or cloud-vision agents that stream raw screenshots, our extension executes neural WebAssembly OCR locally on raw pixel buffers.
2. **Solid `#020617` Canvas Redaction & Fail-Closed Egress**: Replaces sensitive visual regions with mathematically non-recoverable solid dark-fill hex `#020617` rectangles, backed by a fail-closed validator that kills network requests if raw PII is detected.
3. **Client-Side HMAC Action Firewall with TOCTOU Protection**: Remote AI models act strictly as advisory planners. Actions cannot execute unless signed with ephemeral session HMAC keys and verified against live DOM visibility at the exact microsecond of execution.

---

### SECTION 3: THE 3 STRONGEST PIECES OF EMPIRICAL EVIDENCE

1. **Visual Primacy Evidence (`BOB@EXAMPLE.COM`)**: On a test page where DOM code contains `ALICE@EXAMPLE.COM` but canvas pixels display `BOB@EXAMPLE.COM`, our local WASM engine extracts `BOB@EXAMPLE.COM` from pixels (`backend: 'wasm'`, 418ms latency).
2. **Zero-Leakage Network Inspection**: Outbound POST payloads to `/api/v1/reason` show 0 raw PII strings (`[REDACTED_*]` tokenization) and base64 screenshots covered by solid black `#020617` rectangles.
3. **100% Benchmark Containment**: 17 automated Python test suites pass with 100% DAG containment and 98% PII recall across 50 visual test cases.

---

### SECTION 4: THE 3 PROACTIVE DISCLOSURES

1. **Disclosure 1 (First-Boot CDN Acquisition)**:  
   *"Model weights (`tesseract-core.wasm` & `eng.traineddata.gz`, ~15MB) are fetched over HTTPS CDN on initial launch, then stored in browser **IndexedDB** (`tesseract_cache`) for 100% offline subsequent runs."*
2. **Disclosure 2 (WASM CPU Thread Execution)**:  
   *"The current audited production version executes WASM OCR on Web Worker CPU threads (~350-500ms latency). WebGPU compute shaders represent Phase 1 of our post-hackathon roadmap."*
3. **Disclosure 3 (Remote Advisory Reasoner)**:  
   *"While perception, privacy redaction, and action gating run 100% locally on-device, high-level task planning communicates with an advisory remote LLM over HTTPS."*

---

### SECTION 5: 5 CLAIMS WE ABSOLUTELY MUST NOT MAKE

1. ❌ **DO NOT CLAIM**: *"We run WebGPU neural shaders in the browser."* (We run WebAssembly CPU worker threads).
2. ❌ **DO NOT CLAIM**: *"Zero network downloads occur on first extension launch."* (First launch fetches ~15MB WASM weights over CDN).
3. ❌ **DO NOT CLAIM**: *"We use Gaussian blur or AI de-noising for privacy."* (We use solid opaque `#020617` dark fill).
4. ❌ **DO NOT CLAIM**: *"We run a custom-trained PyTorch WEBREDACT model."* (We use Tesseract WASM + regex spatial heuristics).
5. ❌ **DO NOT CLAIM**: *"Our system has 100% global security immunity."* (We enforce local zero-trust controls; claiming global immunity is unscientific).

---

> **END OF JUDGE POSITIONING MASTER**
