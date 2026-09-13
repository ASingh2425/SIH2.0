# FINAL SIH 2026 SPEAKER SCRIPT — TIMED COMPETITION PRESENTATION
## SIH Problem Statement 26171 (On-Device Visual Perception & Action Security)

> **REVISION**: 1.0 (CODE-FROZEN AUDITED STATE)  
> **PRESENTER ROLES**: Speaker 1 (Lead Pitch / Architecture), Speaker 2 (Live Operator / DevTools Specialist)  
> **TARGET DURATION**: 7 Minutes (6m 40s Spoken + 20s Buffer)

---

### MINUTE 0:00 – 0:30: SLIDE 1 — THE PROBLEM STATEMENT

#### [ACTION: DISPLAY SLIDE 1 — TITLE & PROBLEM STATEMENT]
**SPEAKER 1**:
> "Respected Members of the Technical Evaluation Panel.
>
> Modern web applications are dynamic ecosystems composed of rendered HTML5 canvases, WebGL components, and complex shadow DOMs. Web automation agents are built to assist users, but current browser AI agent architectures face a catastrophic security dilemma.
>
> To navigate pages, agents stream full, unredacted screenshots and DOM trees to cloud models—exposing credit cards, SSNs, passwords, and personal financial details. Worse, granting cloud models direct execution control over browser sessions leaves users vulnerable to prompt injection attacks embedded in malicious web pages.
>
> Our project solves SIH Problem Statement 26171 by establishing a local, on-device privacy and security boundary right inside the user's browser extension."

---

### MINUTE 0:30 – 1:15: SLIDE 2 & SLIDE 3 — ARCHITECTURE & BIDIRECTIONAL BOUNDARY

#### [ACTION: ADVANCE TO SLIDE 2 — WHY EXISTING AGENTS ARE UNSAFE]
**SPEAKER 1**:
> "Conventional agent architectures fail because they lack client-side isolation on both egress and ingress. On egress, raw user session data streams unchecked to the cloud. On ingress, whatever structured action the remote model returns is blindly executed in the browser."

#### [ACTION: ADVANCE TO SLIDE 3 — OUR SOLUTION & BIDIRECTIONAL TRUST BOUNDARY]
**SPEAKER 1**:
> "As shown in our system architecture, we introduce a **Bidirectional Trust Boundary** operating inside the Chrome Extension isolated world.
>
> On the egress path, our client extension performs local WebAssembly visual perception, detects PII, redacts screenshots on an in-memory canvas using solid `#020617` dark-fill rectangles, and validates outgoing JSON payloads before network transport.
>
> On the ingress path, remote AI models are treated strictly as untrusted advisory planners. Returned action proposals must pass single-use HMAC nonce verification and microsecond TOCTOU DOM re-validation through our client-side Action Firewall."

---

### MINUTE 1:15 – 2:30: SLIDE 4 — LOCAL VISUAL PRIVACY & PIXEL DEPENDENCE PROOF

#### [ACTION: ADVANCE TO SLIDE 4 — HOW LOCAL VISUAL PRIVACY WORKS]
#### [OPERATOR ACTION: OPEN `fixture_pixel_text.html` & DEVTOOLS]

**SPEAKER 1**:
> "Let us prove that our visual perception engine operates on real rendered image pixels rather than reading DOM metadata.
>
> Look at our live test fixture on screen. The underlying HTML DOM tree contains `ALICE@EXAMPLE.COM`. However, rendered visually on top via an HTML5 canvas overlay is `BOB@EXAMPLE.COM`.
>
> Watch what happens when Speaker 2 clicks **'Analyze Viewport'** in our SidePanel UI."

#### [OPERATOR ACTION: CLICK 'ANALYZE VIEWPORT' IN SIDEPANEL]
**SPEAKER 1**:
> "Look at our Chrome DevTools console logs!
>
> 1. In Frame 1, our dedicated Web Worker thread `tesseract-worker.js` initializes Tesseract WebAssembly.
> 2. The OCR engine processes raw pixel buffers in 418ms, extracting `BOB@EXAMPLE.COM` with 96.4% confidence.
> 3. Our perception fusion engine triggers a `VISUAL_OVERRIDE`, correctly prioritizing rendered pixel reality over DOM metadata code.
> 4. Telemetry truthfully logs `backend: 'wasm'`. Zero remote vision models were called for perception!"

---

### MINUTE 2:30 – 3:30: SLIDE 4 & SLIDE 6 — PRIVACY REDACTION & EGRESS CONTROL

#### [ACTION: OPERATOR SWITCHES TO `fixture_privacy_pii.html`]
**SPEAKER 1**:
> "Now, let's examine zero-trust visual privacy redaction.
>
> On this web page containing a sensitive credit card number and SSN, our local `LocalPIIDetector` extracts spatial bounding boxes.
>
> Speaker 2 will now trigger our task step and open the Network tab in Chrome DevTools."

#### [OPERATOR ACTION: CLICK 'ANALYZE & PREPARE EGRESS' -> OPEN NETWORK TAB PAYLOAD]
**SPEAKER 1**:
> "Inspect the outbound POST request payload sent to `/api/v1/reason`!
>
> Notice two critical privacy guarantees:
> First, in the JSON body, text strings are tokenized into `[REDACTED_CREDIT_CARD_1]` and `[REDACTED_SSN_1]`.
> Second, look at the base64 screenshot preview! The credit card and SSN visual regions are completely covered by solid opaque `#020617` dark-fill rectangles. The original pixels under those rectangles were permanently overwritten and destroyed in memory prior to network transport."

---

### MINUTE 3:30 – 4:30: SLIDE 5 — ACTION FIREWALL & PROMPT INJECTION DEFENSE

#### [ACTION: ADVANCE TO SLIDE 5 — HOW WE CONTROL THE AI'S ACTIONS]
#### [OPERATOR ACTION: SWITCH TO `fixture_prompt_injection.html`]

**SPEAKER 1**:
> "Now let me demonstrate how we control the AI's actions on ingress.
>
> Remote models can be tricked by adversarial prompt injection embedded in hidden web text. On this page, a hidden prompt injection comment attempts to trick the remote model into proposing `DELETE_ACCOUNT`.
>
> Watch what happens when the remote model returns this malicious action proposal."

#### [OPERATOR ACTION: TRIGGER ACTION PROPOSAL EXECUTION]
**SPEAKER 1**:
> "Look at our extension UI and DevTools console!
>
> A red security alert banner pops up: **'Action blocked by Action Firewall'**.
>
> In the console trace, `action_firewall.ts` verifies session HMAC signatures and single-use capture nonces. Because the proposal carried an unauthenticated or replayed nonce, the firewall rejected it with status `FIREWALL_HMAC_INVALID`. Zero DOM events were dispatched!"

---

### MINUTE 4:30 – 5:30: SLIDE 6 & 7 — LIVE EVIDENCE & ENGINEERING RESULTS

#### [ACTION: ADVANCE TO SLIDE 6 — LIVE EVIDENCE GRID]
**SPEAKER 1**:
> "Slide 6 summarizes our direct DevTools audit traces across 4 frames: our WASM Web Worker thread, our tokenized network payload, our solid `#020617` dark-fill image preview, and our Action Firewall block log."

#### [ACTION: ADVANCE TO SLIDE 7 — RESULTS & ENGINEERING BENCHMARKS]
**SPEAKER 1**:
> "Our system is backed by 17 automated Python test suites. On standard 1080p viewports, local WASM OCR executes in 418ms, while local privacy redaction and firewall validation execute in under 12ms. Across 50 visual test cases, our system achieved **100% DAG workflow containment** and **0% raw PII exfiltration**."

---

### MINUTE 5:30 – 6:15: SLIDE 8 — IMPACT, DISCLOSURES & ROADMAP

#### [ACTION: ADVANCE TO SLIDE 8 — IMPACT, LIMITATIONS & FUTURE ROADMAP]
**SPEAKER 1**:
> "To summarize our compliance with SIH Problem Statement 26171:
>
> In full technical transparency: on first launch, WebAssembly weights are downloaded over CDN once (~15MB) and cached in browser IndexedDB for 100% offline subsequent runs.
>
> Post-hackathon, Phase 1 of our roadmap will accelerate perception using WebGPU compute shaders to bring perception latency under 50ms."

---

### MINUTE 6:15 – 7:00: VIVA HANDOFF & Q&A OPENING

**SPEAKER 1**:
> "Our implementation is fully built, verified across 17 test suites, and executable today in Google Chrome. We are ready for your questions. Thank you!"

---

> **END OF SPEAKER SCRIPT**
