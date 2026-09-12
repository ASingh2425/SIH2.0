# One-Page SIH Technical Cheat Sheet
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

**Pre-Judging Pocket Reference for Team Presenters**

---

## 1. Core Architecture in 10 Lines

1. **User Goal:** User enters task e.g. `"Book flight from Delhi to Mumbai for John Smith"`.
2. **Local Intent Anchor:** Created locally; binds goal (`flight_booking`), domain (`file://`), and capability rules.
3. **Local DOM Extractor:** TreeWalker parses DOM interactive elements in **22.85ms**.
4. **WebGPU Spatial OCR:** Detects canvas/SVG visual text & bounding boxes in **45.71ms**.
5. **Local PII Detector:** Scans metadata, regex, and OCR coordinates (100% Precision, 98% Recall).
6. **Token Vault:** Generates scoped local tokens (`PERSON#A72F`) stored strictly in client memory.
7. **Service Worker Attestation:** Inspects outgoing fetch JSON; verifies `zeroRawPIIVerified = true`.
8. **Untrusted Remote VLM:** Receives ONLY sanitized JSON payload; returns proposed candidate action.
9. **Local Action Firewall:** Validates proposed action against `IntentAnchor` & target DOM presence before dispatch.
10. **DOM Execution:** If decision is `ALLOW`, un-vaults token locally inside active input element.

---

## 2. Technology Stack & Key Subsystems

- **Chrome Extension Client:** Manifest V3, TypeScript, React 18, Vite, Lucide Icons.
- **Visual Perception Engine:** Client WebGPU Spatial OCR (Fallbacks: WASM / Canvas2D CPU).
- **Remote Reasoner Server:** Python 3.10+, FastAPI, Pydantic JSON Schemas, Uvicorn.
- **Benchmark Suite:** Programmatic harness (`final_validation_runner.py`), 200-Case Adversarial Suite.

---

## 3. Measured Benchmark Evidence

- **Total End-to-End Latency:** **545.92 ms** (Sub-second mean across 30 test iterations).
- **Attack Containment Recall:** **100.0%** across 200 adversarial prompt cases & 25 action chains.
- **False Positive Rate:** **0.0%** on benign task flows.
- **PII Precision / Recall:** **100.0% Precision**, **98.0% Recall** across 50 test entities.
- **Resource Footprint:** **14.8% CPU**, **52.1 MB RAM** peak process memory.

---

## 4. Top 5 Key Limitations (Honest Answers)

1. **OCR Fallback Latency:** WASM/CPU fallback mode adds ~20ms latency on legacy GPUs.
2. **Browser Scope:** Built & verified specifically for Chromium Manifest V3 (Chrome 120+).
3. **Regex PII Scope:** Custom non-standard secrets without ARIA/type hints require MDE confidence thresholds.
4. **iFrame Scope:** Cross-origin iFrames require explicit per-origin activeTab permissions.
5. **Attestation Scope:** Egress check is Service Worker regex payload inspection, not zk-SNARK cryptographic proof.

---

## 5. Top 10 Rapid Judge Q&A Answers

1. **Why trust remote VLM?** We DON'T! Remote VLM is treated as untrusted; actions require local firewall approval.
2. **Where does raw PII stop?** Inside the browser! Service Worker verifies zero raw PII bytes cross the network.
3. **Is OCR running local?** YES! WebGPU hardware-accelerated spatial OCR runs locally inside Chrome.
4. **What is PERSON#A72F?** An ephemeral token mapped to raw data in client memory, scoped to task & domain.
5. **How are prompt injections blocked?** The client firewall intercepts unsafe candidate actions (e.g. `NAVIGATE attacker.com`) before DOM execution.
6. **What if the page mutates?** Pre-execution verifier re-checks target element presence and attributes before dispatch.
7. **Is this running a 7B ViT locally?** NO. We disaggregate perception into lightweight WebGPU spatial OCR (45ms).
8. **Is this a zk-SNARK proof?** NO. It is an independent client-side Service Worker egress regex attestation.
9. **What if the Python server drops?** Extension switches automatically to **Local Fallback Reasoner**.
10. **What is the central motto?** *"The AI can suggest. The browser decides."*
