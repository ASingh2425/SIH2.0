# Official SIH Engineering Limitations Card
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

**Purpose:** Framing system boundaries as explicit engineering design choices and technical trade-offs.

---

## 1. System Limitations & Technical Boundaries

| Boundary Area | Empirical Limitation | Engineering Context & Design Rationale |
|---|---|---|
| **1. Visual OCR Latency & Fallback** | Hardware Acceleration Dependent. WebGPU runs at **45.71ms**, but WASM/CPU fallback mode increases latency to **145ms–290ms**. | Hardware WebGPU acceleration is prioritized; fallback ensures functional completeness on older GPUs at the cost of execution speed. |
| **2. Browser Scope & Platform** | Optimized specifically for **Google Chrome 120+ Manifest V3**. | Takes full advantage of Chrome MV3 `sidePanel`, `storage`, and service worker sandboxes. Multi-browser Firefox/Safari extensions are theoretical. |
| **3. PII Detection Recall (98.0%)** | 1 out of 50 entities (2.0%) missed in edge-case benchmark suite. | Occurs on highly ambiguous string literals lacking ARIA or input type hints. Handled by fail-closed Minimum Disclosure fallbacks ($<0.85$ confidence). |
| **4. Remote VLM Network Dependency** | Requires active HTTP connection to Python reasoning server (`localhost:8000`). | If offline, system switches seamlessly to local fallback reasoner (`generateDeterministicFallbackAction()`) to preserve local security testing. |
| **5. Egress Attestation Scope** | Service Worker payload regex inspection, NOT zk-SNARK cryptographic proof. | Avoids gigabytes of WASM memory overhead and multi-second compute required for Zero-Knowledge proofs inside client content scripts. |
| **6. Extension Sandbox Threat Model** | Assumes the local browser client and Chrome Extension process memory are un-compromised. | Threat model focuses on protecting user data from **untrusted cloud VLMs** and **malicious web content**, not local OS malware. |
| **7. Benchmark Dataset Scope** | Evaluated on structured 200-case dataset (`adversarial_prompt_injection_200.json`). | Demonstrates 100.0% containment on modeled attack vectors; zero-day novel vectors outside keyword & origin rules remain theoretical. |

---

## 2. Framing Strategy for Judge Presentation

> *"Judges, we are intentionally transparent about our engineering boundaries. Rather than overloading client browsers with gigabytes of local Vision Transformer models or heavy Zero-Knowledge proof circuits, we chose a disaggregated architecture: lightweight WebGPU perception and regex egress attestation locally, paired with remote cloud reasoning bounded by a local action firewall. This achieves sub-second latency (545.9ms) and 100% attack containment within realistic client resource limits."*
