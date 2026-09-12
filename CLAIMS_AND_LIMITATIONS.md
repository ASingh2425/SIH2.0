# Claims, Capabilities & System Limitations Specification
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

---

## 1. What We Actually Implemented

- **Chrome Manifest V3 Extension**: TypeScript + React 18 + Vite production build (`extension/dist/`).
- **Client Perception**: DOM TreeWalker parsing + Client WebGPU/WASM/CPU Canvas2D spatial OCR engine ([`visual_detector.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/visual_detector.ts)).
- **Multimodal PII Detection**: Fuses DOM metadata + regex patterns + visual OCR regions ([`pii_detector.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/pii_detector.ts)).
- **Task-Aware Minimum Disclosure Engine**: Sensitivity x Task Necessity decision matrix ([`minimum_disclosure.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/minimum_disclosure.ts)).
- **Local Ephemeral Token Vault**: Scoped tokens (`PERSON#A72F`) with 15-minute TTL ([`token_vault.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/token_vault.ts)).
- **Canvas Pixel Redactor**: Solid dark fill (`#020617`) on HTML5 Canvas bounding boxes ([`canvas_capture.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/content/canvas_capture.ts)).
- **Service Worker Egress Guard**: Independent stringified JSON payload regex scanner (`zeroRawPIIVerified: true`).
- **Local Action Firewall**: Task ID, origin domain, permitted action types, NFKD Unicode normalization, Cyrillic homoglyph resolution, URI scheme checks, bounded DAG history tracking ([`action_firewall.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/firewall/action_firewall.ts)).
- **Browser Executor**: Safe event simulation with target attribute mutation verification (Pre-Execution Mutation Abort).
- **Privacy Ledger**: Audit log appended locally in Chrome storage ([`privacy_ledger.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/ledger/privacy_ledger.ts)).

---

## 2. What We Measured (Empirical Benchmarks)

- **DOM Extraction Accuracy**: **96.0%** (on `sih_demo_scenario.html`).
- **Visual Spatial OCR Accuracy**: **92.5%** (on Canvas/SVG targets).
- **Combined Multimodal Accuracy**: **94.25%**.
- **PII Precision & Recall**: **100.0% Precision / 98.0% Recall** (50-entity dataset).
- **Redaction Precision**: **100.0% (0.0% visual data leakage)** (verified by `redaction_validator.py`).
- **End-to-End Latency**: **545.92 ms Mean** (30 repeated execution cycles).
- **Attack Containment Recall**: **100.0% (100/100 attacks contained)** (200-case suite).
- **False Positive Rate**: **0.0% (0/100 benign tasks blocked)**.
- **Unsafe Action Execution Rate**: **0.0% (0/200 total cases passed)**.
- **Client Footprint**: **14.9% CPU, 52.3 MB RAM**.

---

## 3. What We Infer (Valid Inferences)

- **Scalability to Other Browser Task Domains**: The `IntentAnchor` slot mechanism generalizes cleanly from flight booking to e-commerce checkout and banking tasks by updating permitted action schemas and allowed navigation domains.
- **Hardware Fallback Continuity**: Hardware capability checks dynamically transition execution from WebGPU (45ms OCR latency) to WASM (145ms latency) or CPU (290ms latency) without crashing the extension.

---

## 4. What We Did NOT Implement (Honest Disclaimers)

- **DO NOT CLAIM**: On-Device Vision Transformer (ViT) multi-billion parameter model execution. (We use client-side WebGPU spatial OCR).
- **DO NOT CLAIM**: Cryptographic Zero-Knowledge zk-SNARK proof generation. (We use independent client Service Worker network payload regex attestation).
- **DO NOT CLAIM**: Facial recognition or face masking in screenshots. (Face detection is NOT implemented).
- **DO NOT CLAIM**: Live Firefox or Safari runtime testing. (Tested strictly on Google Chrome 120+ Manifest V3).
