# Pre-Demonstration Setup & Verification Checklist
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

---

## 1. Pre-Demo Setup Tasks (Execute 10 minutes before presentation)

- [x] **Chrome Extension Build**: Run `cd extension && npm run build` (Verify `extension/dist/` is generated).
- [x] **Chrome Browser Setup**: Open Google Chrome (`chrome://extensions/`), enable **Developer mode**, and click **Load unpacked** $\rightarrow$ select `extension/dist/`.
- [x] **Remote Server Startup**: Open terminal, run `python server/main.py` (Verify server running on `http://localhost:8000`).
- [x] **API Health Verification**: Open `http://localhost:8000/health` in browser (Verify `{"status": "healthy"}`).
- [x] **Demo Scenario Page**: Open `benchmark/test_pages/sih_demo_scenario.html` in Chrome tab.
- [x] **Extension Panel**: Open Chrome Side Panel and select **Privacy Guard Agent**.

---

## 2. Live Demonstration Flow Steps

| Step | Presenter Action | System Verification Target | Expected Result |
|---|---|---|---|
| **1** | Open `sih_demo_scenario.html` | Content script initialization | Side Panel shows active tab connected |
| **2** | Enter prompt `"Book flight from Delhi to Mumbai"` | Intent Anchor creation | `IntentAnchor` initialized with domain & goal |
| **3** | Click **START SAFE DEMO TASK** | Local Perception + MDE + Token Vault | Raw name/email tokenized; card/CVV redacted |
| **4** | Inspect **PRIVACY** tab | Network Payload Inspector | Egress JSON contains `PERSON#A72F`, zero raw PII |
| **5** | Click **TRIGGER ATTACK DEMO** | Local Action Firewall + Semantic Guard | Unsafe action `NAVIGATE attacker.com` blocked |
| **6** | Inspect **SECURITY** tab | Firewall decision log | Block reason: `Unauthorized Navigation Domain` |
| **7** | Inspect **PERFORMANCE** tab | Benchmark & Runtime Latency | Sub-second latency breakdown (545.9ms mean) |
| **8** | Inspect **AUDIT** tab | Privacy Ledger | Full audit log appended in Chrome storage |
