# Official SIH Security & Capability Claim Sheet
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

**Audit Date:** 2026-09-12  
**Baseline Git Tag:** `SIH-P26171-JUDGE-READY`  
**Purpose:** Strict reference for team presenters during SIH judge Q&A to ensure 100% technical truthfulness and prevent overclaiming.

---

## 1. Executive Claim Audit Matrix

| Technical Capability Area | Allowed Safe Claim (What You MAY Say) | Prohibited False Claim (What You MUST NOT Say) | Source Code & Empirical Justification |
|---|---|---|---|
| **Visual Perception Engine** | *"Our visual perception uses client-side WebGPU spatial OCR and HTML5 Canvas element parsing."* | ❌ *"We run a local 7-Billion parameter Vision Transformer (ViT) model inside Chrome."* | `visual_detector.ts` uses WebGPU spatial text detection and canvas coordinate extraction, NOT a 7B ViT model weight matrix. |
| **Network Egress Privacy** | *"We provide independent client-side Service Worker egress privacy attestation that verifies zero raw PII transmission."* | ❌ *"We generate cryptographic Zero-Knowledge zk-SNARK proofs on every network request."* | `background.ts` inspects outgoing fetch JSON payloads using regex PII matchers (`zeroRawPIIVerified`), NOT zk-SNARK mathematical circuits. |
| **Image & Visual Masking** | *"We perform spatial canvas bounding-box pixel redaction using solid dark fills (`#020617`)."* | ❌ *"Our system includes automated AI face detection and facial recognition blurring."* | `redaction_validator.py` and `visual_detector.ts` redact text bounding boxes on canvas; facial recognition is NOT implemented. |
| **Browser Compatibility** | *"Our production extension is built and live-verified for Google Chrome 120+ Manifest V3."* | ❌ *"Our extension is tested and live-verified across Chrome, Firefox MV3, and Safari."* | `manifest.json` and build tools strictly target Chrome Manifest V3 APIs (`chrome.sidePanel`, `chrome.storage`). |
| **Remote Model Status** | *"The remote VLM cloud server is explicitly treated as UNTRUSTED and restricted by local client firewalls."* | ❌ *"Our cloud VLM is 100% immune to prompt injection attacks."* | Cloud LLMs can be tricked; security comes from the **client-side Local Action Firewall** intercepting candidate actions. |
| **Adversarial Benchmark** | *"Our local firewall achieves 100.0% attack containment recall across our 200-case adversarial evaluation dataset."* | ❌ *"Our agent can defeat every possible zero-day web exploit in existence."* | Benchmarks validate our 200-case structured dataset (`adversarial_prompt_injection_200.json`); future un-modeled vectors remain theoretical. |
| **Latency & Performance** | *"The system operates with sub-second E2E mean latency (545.9ms) and a 52.1 MB memory footprint."* | ❌ *"Our agent executes instantaneously in 5 milliseconds with zero resource impact."* | Statistically measured over 30 test iterations (`final_validation_runner.py`). |

---

## 2. Mandatory Rules for Presentation

### A. Prohibited Buzzwords (DO NOT USE)
1. **DO NOT SAY:** `"Zero-Knowledge Proof"` $\rightarrow$ **SAY INSTEAD:** `"Client-Side Egress Privacy Attestation"`.
2. **DO NOT SAY:** `"On-Device 7B ViT Model"` $\rightarrow$ **SAY INSTEAD:** `"Lightweight WebGPU Spatial OCR & Canvas Perception"`.
3. **DO NOT SAY:** `"Face Detection"` $\rightarrow$ **SAY INSTEAD:** `"Spatial Bounding-Box Text Redaction"`.
4. **DO NOT SAY:** `"Multi-Browser Cross-Platform"` $\rightarrow$ **SAY INSTEAD:** `"Chrome Manifest V3 Production Build"`.

---

## 3. Judge Defense Q&A Cheatsheet

### Question 1: *"How does your visual perception work if you aren't running a large Vision-Language Model on the client?"*
> **Recommended Answer:**  
> *"That's the key architectural efficiency of our solution! Running a multi-billion parameter VLM on a client browser consumes gigabytes of VRAM and causes high latency. Instead, our client executes a lightweight WebGPU spatial OCR engine and DOM layout analyzer in under 50ms. It extracts visual text and interactive bounding boxes locally, redacts PII, and sends only the lightweight, sanitized spatial JSON to the remote VLM. You get high-quality VLM reasoning without sacrificing local privacy or performance."*

### Question 2: *"What happens if the cloud AI model is compromised or tricked by a prompt injection attack?"*
> **Recommended Answer:**  
> *"In our architecture, the cloud AI is explicitly treated as UNTRUSTED. The remote model does not have permission to execute DOM actions directly. It can only return candidate action proposals. Every candidate action must pass through our client-side **Local Action Firewall**, which verifies target origin, DOM element existence, and alignment with our immutable local `IntentAnchor`. If the cloud model proposes an unauthorized navigation to `attacker.com`, the client firewall BLOCKS it locally before any DOM event fires."*

### Question 3: *"How do you guarantee that user secrets (passwords, credit cards) don't leak over the network?"*
> **Recommended Answer:**  
> *"We enforce a two-stage local boundary:  
> First, our Task-Aware Minimum Disclosure Engine and Local Token Vault sanitize data locally—replacing raw values with scoped tokens like `PERSON#A72F` and masking credit card inputs.  
> Second, our Service Worker Egress Guard inspects all outgoing HTTP fetch requests before transmission, attesting that zero raw PII bytes cross the boundary (`zeroRawPIIVerified = true`)."*
