# Final System Architecture Specification
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

---

## 1. Architectural Principles & Trust Boundaries

The fundamental security principle governing the system is:
> **"THE CLOUD CAN REASON ABOUT THE TASK, BUT THE DEVICE DECIDES WHAT IT IS ALLOWED TO SEE AND WHAT IT IS ALLOWED TO DO."**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        LOCAL PRIVACY BOUNDARY                          │
│                                                                        │
│  ┌─────────────────────────┐      ┌─────────────────────────────────┐  │
│  │ Local Visual Perception │      │ Task-Aware Minimum Disclosure   │  │
│  │  (WebGPU / WASM OCR)    │ ───► │  Engine (MDE) & Token Vault     │  │
│  └─────────────────────────┘      └─────────────────────────────────┘  │
│                                                   │                    │
│                                                   ▼                    │
│                                   ┌─────────────────────────────────┐  │
│                                   │ Independent Egress Attestation  │  │
│                                   │     (Service Worker Guard)      │  │
│                                   └─────────────────────────────────┘  │
└───────────────────────────────────────────────────┬────────────────────┘
                                                    │ Sanitized JSON + Redacted Canvas
                                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        UNTRUSTED REMOTE ZONE                           │
│                                                                        │
│                    ┌────────────────────────────────────┐              │
│                    │ Remote Reasoning Cloud VLM Server  │              │
│                    │         (Python FastAPI)           │              │
│                    └────────────────────────────────────┘              │
└───────────────────────────────────────────────────┬────────────────────┘
                                                    │ Candidate Structured Action
                                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        LOCAL PRIVACY BOUNDARY                          │
│                                                                        │
│  ┌─────────────────────────┐      ┌─────────────────────────────────┐  │
│  │ Local Action Firewall   │ ───► │ Browser Action Executor &       │  │
│  │ & Semantic Guard        │      │ Pre-Execution Token Un-Vaulting │  │
│  └─────────────────────────┘      └─────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Sub-System Breakdown

### A. Local Perception Sub-System
- **DOM Extractor** ([`dom_extractor.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/content/dom_extractor.ts)): DOM TreeWalker parsing interactive nodes, input types, ARIA roles, and bounding rectangles.
- **Local Visual Detector** ([`visual_detector.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/visual_detector.ts)): WebGPU/WASM/CPU Canvas2D spatial OCR engine for Canvas, SVG, and image elements.

### B. Local Privacy Boundary Sub-System
- **Multimodal PII Detector** ([`pii_detector.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/pii_detector.ts)): Fuses DOM attributes, regex patterns, and visual OCR entities.
- **Minimum Disclosure Engine (MDE)** ([`minimum_disclosure.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/minimum_disclosure.ts)): Decision matrix assigning `TOKENIZE`, `REMOVE`, `MASK`, `KEEP`.
- **Local Ephemeral Token Vault** ([`token_vault.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/privacy/token_vault.ts)): Scoped token mappings (`PERSON#A72F`) with 15-minute TTL.
- **Canvas Pixel Redactor** ([`canvas_capture.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/content/canvas_capture.ts)): HTML5 Canvas pixel masking with solid dark fill (`#020617`).
- **Service Worker Egress Guard** ([`service_worker.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/background/service_worker.ts)): Independent regex scanner verifying `PrivacyBoundaryReport`.

### C. Local Security & Execution Sub-System
- **Local Action Firewall** ([`action_firewall.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/firewall/action_firewall.ts)): Multi-tier firewall enforcing task ID, origin domain, permitted action types, NFKD normalization, homoglyph mapping, and scheme checks.
- **Local Semantic Action Analyzer** ([`semantic_analyzer.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/firewall/semantic_analyzer.ts)): Client-side semantic guard checking data class violations, synonym clusters, and multi-step exfiltration DAG tracking.
- **Browser Executor** ([`action_executor.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/content/action_executor.ts)): Pre-execution DOM re-evaluation and token un-vaulting in DOM memory.
