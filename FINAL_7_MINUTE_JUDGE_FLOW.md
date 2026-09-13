# FINAL 7-MINUTE JUDGE FLOW — PERFECT TIMING MASTER SCRIPT
## SIH 2026 Problem Statement 26171 (On-Device Visual Perception)

> **REVISION**: 1.0 (CODE-FROZEN AUDITED STATE)  
> **TARGET DURATION**: Exactly 7 Minutes (6m 40s speech + 20s buffer)  
> **PREREQUISITES**: Chrome Browser, DevTools pinned right, local server `localhost:8000` loaded with demo HTML fixtures.

---

### TIMED STAGE-BY-STAGE PRESENTER RUNBOOK

```
+-----------------------------------------------------------------------------------+
| 00:00 - 00:30 | PROBLEM STATEMENT & VISION                                       |
+-----------------------------------------------------------------------------------+
- Speaker: "Respected Judges, modern web apps use dynamic canvases, WebGL, and complex
  shadow DOMs. DOM-only browser agents are completely blind to visual content, while
  cloud-vision agents leak unredacted screenshots containing sensitive PII.
  Our solution satisfies SIH PS 26171: On-device WebAssembly visual perception with
  solid #020617 canvas PII redaction and a client-side HMAC Action Firewall."
- Visual Cue: Show Slide 1 Title & Problem Statement.
```

```
+-----------------------------------------------------------------------------------+
| 00:30 - 01:15 | HIGH-LEVEL ARCHITECTURE                                          |
+-----------------------------------------------------------------------------------+
- Speaker: "Look at our architecture diagram. Perception runs locally inside a Chrome
  Web Worker using Tesseract WebAssembly. Before any screenshot leaves the client,
  PII is redacted locally. Remote AI models act strictly as untrusted advisory planners;
  execution authority remains inside our local Action Firewall."
- Visual Cue: Show Architecture Diagram (Slide 2). Point to isolated world boundary.
```

```
+-----------------------------------------------------------------------------------+
| 01:15 - 02:30 | REAL LOCAL VISUAL OCR PROOF                                      |
+-----------------------------------------------------------------------------------+
- Speaker: "Let's prove our agent processes raw pixels rather than DOM metadata. On this
  page, the DOM input value is ALICE@EXAMPLE.COM, but layered on top is an HTML5 canvas
  rendering BOB@EXAMPLE.COM. Let's click 'Analyze Viewport'."
- Operator Action: Click SidePanel "Analyze Viewport".
- Visual Cue: Point to Console: `[LocalVisualModelEngine] WASM recognizePixels completed in 418ms.
  Text: "BOB@EXAMPLE.COM"`. Show `tesseract-worker.js` in DevTools Application tab.
```

```
+-----------------------------------------------------------------------------------+
| 02:30 - 03:30 | ON-DEVICE PRIVACY & REDACTION DEMO                               |
+-----------------------------------------------------------------------------------+
- Speaker: "Now observe zero-trust privacy. On this form containing a credit card and SSN,
  our local PII detector flags spatial bounding boxes and tokenizes text. An in-memory canvas
  overwrites PII pixels with solid opaque dark fill hex #020617."
- Operator Action: Click "Analyze & Prepare Egress" on `fixture_privacy_pii.html`.
- Visual Cue: Open DevTools Network tab -> POST `/api/v1/reason` -> Payload preview:
  Show base64 screenshot preview covered by solid black rectangles (`#020617`).
```

```
+-----------------------------------------------------------------------------------+
| 03:30 - 04:30 | REMOTE REASONING PAYLOAD INSPECTION                              |
+-----------------------------------------------------------------------------------+
- Speaker: "Inspect the outbound JSON string sent to the reasoner. The credit card is
  replaced with [REDACTED_CREDIT_CARD_1]. Our local EgressValidator scans the payload.
  If a single raw PII string leaks, transport fails closed instantly."
- Visual Cue: Highlight JSON payload text in DevTools Network tab. Show zero raw PII matches.
```

```
+-----------------------------------------------------------------------------------+
| 04:30 - 05:30 | ACTION FIREWALL PROMPT INJECTION DEFENSE                         |
+-----------------------------------------------------------------------------------+
- Speaker: "Remote LLMs cannot be trusted to execute actions. If a remote model is tricked
  by prompt injection into proposing DELETE_ACCOUNT, our Action Firewall checks ephemeral
  HMAC session signatures and performs microsecond TOCTOU DOM re-validation."
- Operator Action: Trigger malicious action proposal on `fixture_prompt_injection.html`.
- Visual Cue: Show red UI alert: "Action blocked by Action Firewall". Show console log:
  `FIREWALL_HMAC_INVALID`.
```

```
+-----------------------------------------------------------------------------------+
| 05:30 - 06:15 | AUDIT SECURITY LEDGER & BENCHMARK METRICS                       |
+-----------------------------------------------------------------------------------+
- Speaker: "Every perception pass and action attempt is recorded in an immutable local
  Security Ledger. Our automated benchmark suite validates 100% DAG containment and 98%
  OCR recall across 17 test suites."
- Operator Action: Click SidePanel "Ledger" tab to display append-only log table.
- Visual Cue: Point to clean ledger rows with timestamps and nonces.
```

```
+-----------------------------------------------------------------------------------+
| 06:15 - 07:00 | LIMITATIONS, ROADMAP & Q&A HANDOFF                              |
+-----------------------------------------------------------------------------------+
- Speaker: "In disclosure: Tesseract WASM weights are fetched once over CDN on initial boot
  and cached in IndexedDB for 100% offline subsequent runs. Post-hackathon, Phase 1 will
  accelerate perception using WebGPU compute shaders. We welcome your questions."
- Visual Cue: Show Slide 3 Summary & Disclosure Matrix. Hand off to viva defense.
```

---

> **END OF 7-MINUTE JUDGE FLOW**
