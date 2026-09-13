# FINAL LIVE DEMO RISK REGISTER — OPERATIONAL MITIGATION PLAN
## Risk Assessment & Contingency Protocol for Live SIH Judging (PS 26171)

> **REVISION**: 1.0 (POST-REHEARSAL AUDITED STATE)  
> **PURPOSE**: Operational risk register ranking all potential demo friction points from P0 (Critical) to P3 (Cosmetic) with explicit detection signals, mitigations, and backup protocols.

---

### SECTION 1: RISK RANKING & CONTINGENCY MATRIX

| RISK ID | SEVERITY | RISK DESCRIPTION | PROBABILITY | IMPACT | DETECTION SIGNAL | PREVENTATIVE MITIGATION | EMERGENCY BACKUP PROTOCOL |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **R01** | **P0** | Service worker drops context / becomes inactive. | Low | High | Extension UI shows "Extension disconnected" or no console log on click. | Keep Service Worker DevTools window open (prevents Chrome worker idle timeout). | Click "Service Worker (Inactive)" link in `chrome://extensions` to re-wake instantly. |
| **R02** | **P1** | First-time Tesseract WASM CDN download delay on clean machine. | Medium | Medium | Perception step takes >3s on initial launch. | Run warmup perception pass T-5 minutes before presentation to populate IndexedDB cache. | Show IndexedDB cache entry in DevTools; explain one-time CDN acquisition architecture. |
| **R03** | **P1** | Active tab focus lost during `captureVisibleTab`. | Low | Medium | Chrome runtime error: `activeTab permission requires focused window`. | Keep browser window maximized and click active tab body once before triggering perception pass. | Click tab body to regain window focus and re-trigger SidePanel action button. |
| **R04** | **P2** | Local Python HTTP server (`localhost:8000`) not listening. | Low | Low | Network error `ERR_CONNECTION_REFUSED` on demo fixtures. | Launch `python -m http.server 8000` during T-10 minutes pre-flight setup. | Restart server via command line `python -m http.server 8000` (takes 1 second). |
| **R05** | **P2** | Network tab payload preview base64 image too long to display. | Low | Low | DevTools truncates payload string preview. | Pre-configure DevTools payload view or use `copy(payload.screenshot)` in console. | Render base64 image via in-console `console.log('%c ', 'font-size:100px; background:url(...)')`. |
| **R06** | **P3** | SidePanel font size small on projector resolution. | Low | Low | Judge asks to see UI text clearly. | Set Chrome UI zoom to 125% during pre-flight setup. | Zoom browser window (`Ctrl + +`) during presentation. |

---

### SECTION 2: SEVERITY DEFINITIONS

* **P0 (Critical)**: Operational failure that completely halts the demo (0 instances remaining post-mitigation).
* **P1 (Significant Interruption)**: Delay > 3 seconds or user flow disruption requiring quick intervention.
* **P2 (Minor Inconvenience)**: Cosmetic layout issue or minor DevTools navigation delay.
* **P3 (Cosmetic)**: Low-impact visual or font size adjustment.

---

### SECTION 3: EMERGENCY RECOVERY RUNBOOK FOR OPERATOR

1. **If Anything Freezes**: Press `F5` on the active webpage tab -> Re-open SidePanel -> Trigger task pass.
2. **If Console Logs Disappear**: Click the DevTools Console filter clear button, then re-trigger task pass.
3. **If Judge Asks for Code Verification**: Open VS Code or GitHub repo directly at [content_script.ts](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/content/content_script.ts#L105-L160).

---

> **END OF LIVE DEMO RISK REGISTER**
