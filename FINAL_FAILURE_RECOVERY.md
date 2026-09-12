# Emergency Live Demo Recovery Playbook
## SIH Problem Statement 26171: On-device Visual Perception for Lightweight Browser Agents

**Purpose:** Emergency recovery steps for team presenters if technical glitches (server drops, browser freezes, extension crashes) occur during the live judge presentation.

---

## 1. Fast-Action Decision Matrix

| Failure Symptom | Immediate Cause | 10-Second Presenter Recovery Action |
|---|---|---|
| **Python Server Fails to Start** | Port 8000 already in use by background process. | Run: `Stop-Process -Name python -Force` then `python server/main.py`. |
| **Side Panel Shows "DISCONNECTED"** | Chrome extension lost Service Worker connection. | Click refresh 🔄 icon on extension card in `chrome://extensions/` and press `Ctrl + R` on demo tab. |
| **Server Offline / Network Dropped** | Python backend process terminated. | The extension automatically switches to **`LOCAL FALLBACK REASONER`**. The demo continues without interruption! |
| **WebGPU Unavailable Warning** | Chrome GPU acceleration disabled. | System automatically falls back to **`WASM / CPU Mode`**. Functionality is identical (~20ms latency increase). |
| **Demo Tab Inputs Not Updating** | Content script detached. | Click Chrome refresh on `sih_demo_scenario.html` tab. |

---

## 2. Step-by-Step Recovery Operating Procedures

### Scenario A: FastAPI Server Port Conflict (Port 8000 Busy)

**Symptom:** Terminal error `OSError: [Errno 10048] address already in use`.

**Recovery Procedure:**
1. Open PowerShell terminal.
2. Force kill existing Python processes:
   ```powershell
   Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force
   ```
3. Restart FastAPI server:
   ```powershell
   cd c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0
   python server/main.py
   ```
4. Verify server health in Chrome: Navigate to `http://localhost:8000/health`.

---

### Scenario B: Chrome Extension Side Panel Blank or Unresponsive

**Symptom:** Side Panel displays blank white screen or does not respond to button clicks.

**Recovery Procedure:**
1. Open a new Chrome tab and go to `chrome://extensions/`.
2. Locate **Privacy Guard Agent (SIH PS 26171)**.
3. Click the **Reload (🔄)** icon on the extension card.
4. Return to `file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/benchmark/test_pages/sih_demo_scenario.html`.
5. Press `Ctrl + F5` (Hard Reload).
6. Re-open Side Panel from the Chrome toolbar icon.

---

### Scenario C: Backend Outage / Emergency Standalone Fallback Demo

**Symptom:** Server crashes mid-demonstration or laptop network disconnects.

**Recovery Procedure:**
> **Do NOT panic! The extension has built-in offline insurance.**
1. In the Side Panel **AGENT** tab, click **START SAFE DEMO TASK**.
2. If `http://localhost:8000` is unreachable, `background.ts` intercepts the request and switches to **`MODE: LOCAL FALLBACK REASONER`**.
3. Point out to judges:
   > *"Notice our fail-safe resilience: even if the cloud server goes offline, our client-side Local Reasoner continues tokenizing PII locally and enforcing action firewall rules without losing protection."*
4. All UI features (Token Vault, Redaction Inspector, Action Firewall BLOCK on prompt injection) will execute seamlessly from client memory.

---

## 3. Pre-Demo Checklist (2 Minutes Before Demo)

- [ ] Run `python server/main.py` in Terminal 1.
- [ ] Confirm `http://localhost:8000/health` returns `200 OK`.
- [ ] Open `sih_demo_scenario.html` in Google Chrome.
- [ ] Open **Privacy Guard Agent** Side Panel.
- [ ] Confirm status reads: `SIH PS 26171 | JUDGE-READY DEMO MODE`.
