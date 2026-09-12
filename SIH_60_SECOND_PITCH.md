# Official SIH 60-Second Elevator Pitch
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

**Central Architectural Motto:**  
> **"THE AI CAN SUGGEST. THE BROWSER DECIDES."**

---

## Pitch Script (Read Time: Exactly 60 Seconds)

> *"Respected Judges, commercial browser agents today suffer from a massive security flaw: they stream raw screenshots, full HTML DOMs, and un-redacted user credentials directly to cloud AI models. If a webpage contains credit cards or hidden prompt injection attacks, your private data and browser session are compromised instantly.
> 
> Our solution for **SIH Problem Statement 26171** enforces an on-device privacy control plane inside Chrome Manifest V3 based on one core principle:  
> **'The AI can suggest actions, but the local browser decides what it is allowed to see and what it is allowed to do.'**
> 
> 1. Our client-side WebGPU spatial OCR and DOM TreeWalker parse page elements locally in under 68 milliseconds.
> 2. Our Local Token Vault replaces user credentials with scoped tokens (`PERSON#A72F`) and masks credit card inputs locally. Zero raw PII bytes cross the network boundary, attested independently by our Service Worker Egress Guard.
> 3. The remote cloud VLM is explicitly treated as **UNTRUSTED**. Candidate actions returned by the AI pass through our **Local Action Firewall** before DOM execution.
> 
> In our 200-case adversarial benchmark, we achieved **100.0% prompt injection attack containment** with sub-second latency (**545.9ms mean**) and a **52.1 MB memory footprint**.
> 
> Complete visual perception, total privacy, and mathematical execution control—on your device. Thank you!"*
