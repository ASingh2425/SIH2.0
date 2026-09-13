# FINAL SIH DEMO CHECKLIST — PRE-PRESENTATION VERIFICATION
## Live Demo Operational Checklist (SIH PS 26171)

> **REVISION**: 1.0 (CODE-FROZEN AUDITED STATE)  
> **PURPOSE**: Operational pre-flight checklist to ensure 100% flawless execution during SIH live demo and judging evaluation.

---

### STAGE 1: SYSTEM & BUILD VERIFICATION (T-30 MINUTES)

- [ ] **Verify Production Code Freeze**:
  - Run `git status` to confirm zero uncommitted edits in production source code (`extension/src`, `extension/manifest.json`).
- [ ] **Verify Chrome Extension Build**:
  - Open terminal at `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0\extension`.
  - Run `npm run build`.
  - Confirm build completes with **0 errors** and generates `dist/background.js`, `dist/content.js`, `dist/index.html`.
- [ ] **Verify Benchmark Test Suite**:
  - Open terminal at `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0`.
  - Run `python benchmark/final_validation_runner.py`.
  - Confirm output: **100% DAG containment, 98% recall, 17/17 test suites OK**.

---

### STAGE 2: BROWSER ENVIRONMENT CONFIGURATION (T-15 MINUTES)

- [ ] **Chrome Browser Launch**:
  - Launch Google Chrome with developer mode enabled:
    `chrome.exe --enable-logging --v=1 --allow-insecure-localhost`
- [ ] **Load Unpackaged Extension**:
  - Navigate to `chrome://extensions`.
  - Enable **Developer mode** toggle (top right).
  - Click **Load unpacked** -> Select directory `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0\extension\dist`.
  - Confirm Extension Name: *"SIH Lightweight Visual Browser Agent Extension"*.
  - Confirm Extension ID generated.
- [ ] **Configure Chrome DevTools Layout**:
  - Open DevTools (`F12`) pinned to the right dock.
  - Set **Console** tab logging level to `Info`, `Warnings`, `Errors`.
  - Set **Network** tab filter to `Fetch/XHR`.
  - Click **Inspect Background Page** in `chrome://extensions` to open Service Worker DevTools in a separate window.

---

### STAGE 3: TEST FIXTURE HTTP SERVER LAUNCH (T-10 MINUTES)

- [ ] **Start Local Server for Demo Fixtures**:
  - Open terminal at `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0\benchmark`.
  - Launch local server: `python -m http.server 8000`.
- [ ] **Verify Demo URLs Load Cleanly**:
  - Tab 1: `http://localhost:8000/fixture_pixel_text.html` (Canvas `BOB@EXAMPLE.COM` vs DOM `ALICE@EXAMPLE.COM`)
  - Tab 2: `http://localhost:8000/fixture_privacy_pii.html` (Form with Credit Card & SSN)
  - Tab 3: `http://localhost:8000/fixture_prompt_injection.html` (Prompt injection attack page)

---

### STAGE 4: HARDWARE & DISPLAY CHECKLIST (T-5 MINUTES)

- [ ] **Screen Resolution**: Set display scaling to 100% at 1920x1080 resolution.
- [ ] **Font Zoom**: Set Chrome default page zoom to 100%.
- [ ] **SidePanel Docking**: Click Extension icon in Chrome toolbar -> Pin SidePanel to right side of browser window.
- [ ] **Network Connection**: Ensure Wi-Fi/Ethernet is connected (or local IndexedDB WASM weights pre-cached).

---

### STAGE 5: LIVE DEMO EXECUTION RUNBOOK (DURING PRESENTATION)

| TIMING | STEP | ACTION | EXPECTED VERIFICATION |
| :--- | :--- | :--- | :--- |
| **0:00 - 1:00** | Introduction | Show Slide 1 Architecture | Introduce problem statement & on-device WASM solution. |
| **1:00 - 2:30** | Visual OCR Demo | Open Tab 1 (`fixture_pixel_text.html`) -> Click SidePanel "Analyze Viewport" | DevTools Console shows `BOB@EXAMPLE.COM` extracted via WASM OCR. |
| **2:30 - 4:00** | Privacy Redaction | Open Tab 2 (`fixture_privacy_pii.html`) -> Click "Run Privacy Pass" | Network payload preview shows `#020617` dark-fill rectangles. |
| **4:00 - 5:30** | Action Firewall | Open Tab 3 (`fixture_prompt_injection.html`) -> Trigger Action | DevTools Console shows `FIREWALL_HMAC_INVALID` / Red UI Warning. |
| **5:30 - 6:30** | Benchmarks | Show Benchmark Results Slide | Highlight 17/17 test suites OK & 100% DAG containment. |
| **6:30 - 7:00** | Conclusion | Open Q&A Handoff | Invite judge questions & hand off to Safe Claims Card. |

---

### EMERGENCY CONTINGENCY PROTOCOL

| CONTINGENCY | INSTANT ACTION |
| :--- | :--- |
| **Service Worker becomes inactive** | Click `Service Worker (Inactive)` link on `chrome://extensions` page to wake it up immediately. |
| **DevTools Console clear button clicked by accident** | Re-run task step in SidePanel; console logs will re-populate instantly. |
| **Judge asks to run Python tests live** | Run `python benchmark/final_validation_runner.py` in terminal; takes <3 seconds to execute all 17 suites. |

---

> **END OF DEMO CHECKLIST**
