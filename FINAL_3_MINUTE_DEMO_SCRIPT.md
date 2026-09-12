# Official 3-Minute SIH Grand Finale Judge Demo Script
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

**Execution Time:** Exactly 3 Minutes (Max 3m 30s)  
**Presenter Setup:**  
1. Google Chrome window open with `file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/benchmark/test_pages/sih_demo_scenario.html`.
2. Chrome Side Panel open on right half displaying **PRIVACY GUARD CONTROL PLANE** (`SIH PS 26171`).
3. Terminal tab running Python FastAPI server on `http://localhost:8000`.

---

## Cue Sheet & Visual Action Timeline

| Timeline | Phase | Presenter Action | Visual Target to Point At | Spoken Script |
|---|---|---|---|---|
| **0:00 – 0:30** | **Problem & Paradigm** | Open Chrome window with webpage and side panel. | Point at top header tagline: *"The AI can suggest. The browser decides."* | *"Respected Judges, commercial browser agents today stream raw DOMs, screenshots, and user secrets directly to cloud AI models. If a webpage contains credit cards or prompt injections, your data is exposed. Our solution for **SIH PS 26171** establishes an on-device privacy control plane: **The cloud may reason, but the local browser decides what it can see and do.**"* |
| **0:30 – 1:15** | **Safe Flow & PII Redaction** | 1. Enter task: `"Book flight from Delhi to Mumbai for John Smith"`.<br>2. Click **RUN AGENT**.<br>3. Switch to **PRIVACY** tab. | 1. Point at Green Shield: `ZERO RAW PII VERIFIED`.<br>2. Point at Mapping: `John Smith` $\rightarrow$ `PERSON#A72F`, Card $\rightarrow$ `[REDACTED]`.<br>3. Point at Egress Inspector. | *"Watch our local perception engine in action. DOM TreeWalker and WebGPU spatial OCR parse page elements locally. Our Local Token Vault replaces `John Smith` with `PERSON#A72F` and masks credit cards (`[REDACTED]`). Look at our live Network Egress Inspector: **ZERO raw PII bytes leave your device**, attested by our Service Worker Egress Guard."* |
| **1:15 – 2:00** | **Firewall Action Approval** | Switch to **AGENT** tab. | 1. Point at `Immutable Intent Anchor`.<br>2. Point at candidate action `TYPE #passenger_name PERSON#A72F`.<br>3. Point at `FIREWALL: ALLOW`. | *"The cloud VLM receives ONLY this sanitized JSON payload. It returns a candidate action: `TYPE #passenger_name PERSON#A72F`. Before any DOM event fires, our **Local Action Firewall** validates the node ID and target origin against our Intent Anchor, returning an **ALLOW** decision."* |
| **2:00 – 2:35** | **Attack Containment** | On webpage, click red button: **TRIGGER ATTACK DEMO**. | 1. Point at flashing red banner: `FIREWALL: BLOCK`.<br>2. Point at Attack Flow: `NAVIGATE attacker.com` blocked.<br>3. Point at Rule: `Unauthorized Domain`. | *"Now let's test security. This malicious webpage injects a hidden prompt attack trying to force navigation to an attacker's domain (`attacker.com`). The untrusted cloud model proposes a `NAVIGATE` action. But our **Local Action Firewall** flags an origin mismatch and **BLOCKS** the action instantly! The attack is contained locally."* |
| **2:35 – 3:00** | **Metrics & Conclusion** | 1. Click **METRICS** tab.<br>2. Click **AUDIT** tab. | 1. Point at Live E2E Latency: `545.92 ms`.<br>2. Point at RAM footprint: `52.1 MB`.<br>3. Point at Privacy Ledger. | *"Our solution is benchmarked across 200 adversarial cases with **100.0% attack containment recall**. E2E latency is a sub-second **545.9ms** with a lightweight **52.1 MB RAM** footprint. Every event is logged in our local Privacy Ledger. Thank you, Judges—we welcome your questions!"* |

---

## Failure Point Mitigation Playbook

| Potential Demo Glitch | Cause | Immediate 5-Second Presenter Fix |
|---|---|---|
| **Python Server Unreachable** | Backend process dropped. | The extension automatically activates **`LOCAL FALLBACK REASONER`**. Continue demo smoothly without stopping! |
| **Side Panel Unresponsive** | Chrome Service Worker idle. | Click Extension Reload (🔄) in `chrome://extensions/` and press `Ctrl + F5` on demo page. |
| **WebGPU Hardware Warning** | GPU flag disabled in Chrome. | System automatically runs in **`WASM / CPU Mode`** (~20ms latency addition). Functionality is identical. |
