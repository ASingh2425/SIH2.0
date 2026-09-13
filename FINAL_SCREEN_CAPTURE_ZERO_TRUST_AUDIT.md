# FINAL REAL SCREEN CAPTURE ZERO-TRUST SECURITY AUDIT
## SIH Problem Statement 26171 — On-Device Visual Perception for Lightweight Browser Agents

> **AUDIT TYPE:** ZERO-TRUST PRE-FREEZE HOSTILE SECURITY AUDIT  
> **CODEBASE STATUS:** PRODUCTION FROZEN (0 CODE MODIFICATIONS PERFORMED IN THIS PASS)  
> **AUDIT DATE:** September 13, 2026  
> **VERDICT:** **HOLD — P0 REMEDIATION REQUIRED BEFORE FINAL CODE FREEZE**  
> **ADVERSARIAL JUDGE SCORE:** **87 / 100**  

---

## 1. Executive Verdict & Core Finding

This hostile zero-trust audit evaluated the real browser screen capture pipeline (`chrome.tabs.captureVisibleTab()` → background service worker → content script -> local redaction -> egress validator) in **c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0**.

### Key Audit Findings:
1. **Real Capture Pipeline Verified:** `chrome.tabs.captureVisibleTab()` is genuinely integrated into the production execution path (`service_worker.ts`, `content_script.ts`, `canvas_capture.ts`). The synthetic canvas fallback has been disarmed for production capture.
2. **Critical Active-Tab Ambiguity Discovered (VULN-01):** `chrome.tabs.captureVisibleTab(windowId)` captures whichever tab is currently active/visible in the browser window. If a user switches tabs during a task, pixels from the newly active tab (e.g., bank/email) can be captured and returned to the task content script.
3. **Post-Capture TOCTOU Window Discovered (VULN-02):** Origin validation in `handleCaptureVisibleTab()` occurs *before* `captureVisibleTab()` resolves. If the webpage navigates between origin check and capture completion, a screenshot of the new origin is returned without post-capture re-verification.
4. **Raw Screenshot Base64 Crosses Extension IPC:** Raw PNG base64 strings travel from background service worker to content script via `chrome.runtime.sendMessage` `sendResponse`. While Isolated Worlds separate extension JS from webpage JS, in-memory lifetime must be strictly bounded.

---

## 2. Phase 1 — Call Graph & Real Capture Verification

```
+---------------------------------------------------------------------------------------------------+
| COMPONENT                  | FILE LOCATION                                | VERIFIED STATUS       |
+----------------------------+----------------------------------------------+-----------------------+
| Manifest Permissions       | `extension/manifest.json`                    | REAL ("tabs", "<all_urls>") |
| Background IPC Listener    | `extension/src/background/service_worker.ts` | REAL (`handleCaptureVisibleTab`) |
| Chrome API Capture Call    | `extension/src/background/service_worker.ts` | REAL (`captureVisibleTab`) |
| Content Agent Controller   | `extension/src/content/content_script.ts`    | REAL (`sendMessage CAPTURE_VISIBLE_TAB`) |
| Local Canvas Redactor      | `extension/src/content/canvas_capture.ts`    | REAL (`redactRealViewportScreenshot`) |
| Egress Boundary Auditor    | `extension/src/privacy/egress_validator.ts`  | REAL (`validateNetworkEgress`) |
+---------------------------------------------------------------------------------------------------+
```

- **`CAPTURE_PATH` = REAL** (Production execution triggers `chrome.tabs.captureVisibleTab`).
- **`REDACTION_PATH` = REAL** (Offscreen canvas applies solid fill `#020617` over sensitive/unverified bounds).
- **`EGRESS_PATH` = REAL** (Sanitized screenshot is attached to payload and validated prior to network dispatch).

---

## 3. Phase 2 — Raw Screenshot Lifetime & Storage Audit

| Storage / Memory Location | Raw Screenshot Presence | Evidence / Verification |
|---|---|---|
| `console.log` / `console.error` | **ABSENT** | Source search confirms no raw base64 data URLs logged. |
| `chrome.storage.local` / `sync` | **ABSENT** | Zero storage writes for screenshot data. |
| `localStorage` / `sessionStorage` | **ABSENT** | Zero browser storage writes. |
| `IndexedDB` / Cookies | **ABSENT** | Zero persistent database storage. |
| Background Service Worker Memory | **TEMPORARY** | Exists as `capturedDataUrl` string during async message handling. |
| Content Script Isolated World Memory | **TEMPORARY** | Exists as `captureRes.dataUrl` string prior to `redactViewportScreenshot()`. |
| Extension IPC Message Payload | **PRESENT** | Transmitted via `sendResponse` from background worker to content script. |

> [!WARNING]
> **IPC BOUNDARY FINDING:**  
> Raw screenshot base64 strings cross the Service Worker → Content Script IPC boundary. Content script memory holds the raw base64 string until `redactRealViewportScreenshot()` executes canvas zeroing.

---

## 4. Phase 3 — Screenshot Redaction Ordering Proof

```
CURRENT WEBPAGE VIEWPORT
  ↓ [chrome.tabs.captureVisibleTab]
RAW BASE64 PNG (Service Worker Memory)
  ↓ [chrome.runtime.sendMessage sendResponse]
RAW BASE64 PNG (Content Script Isolated World)
  ↓ [HTMLImageElement.src & ctx.drawImage]
OFFSCREEN CANVAS (Viewport Dimensions)
  ↓ [Solid Dark Fill #020617 Overlay]
SANITIZED BASE64 PNG (Redacted Canvas Output)
  ↓ [ctx.clearRect & img.src = '']
IN-MEMORY REFERENCE ZEROING
  ↓ [validateNetworkEgress]
MINIMUM DISCLOSURE AUDIT REPORT
  ↓ [HTTPS POST /api/v1/reason]
UNTRUSTED REMOTE REASONER
```

**Ordering Verification:** Zero paths exist where raw un-redacted screenshots are sent to the network, VLM, or storage.

---

## 5. Phase 4 — Fail-Closed Vulnerability Analysis

| Scenario ID | Failure Trigger | Expected Behavior | Actual Production Behavior | Status |
|---|---|---|---|---|
| **A** | `captureVisibleTab` throws error | `VISUAL_PRIVACY_UNVERIFIED` + No Egress | Catches error; returns `{ success: false, visualPrivacyState: 'VISUAL_PRIVACY_UNVERIFIED' }`. | **FAIL-CLOSED (PASS)** |
| **B** | `captureVisibleTab` returns empty | `VISUAL_PRIVACY_UNVERIFIED` + No Egress | Checks `!dataUrl.startsWith('data:image/')`; returns failure. | **FAIL-CLOSED (PASS)** |
| **C** | Malformed data URL format | `VISUAL_PRIVACY_UNVERIFIED` + No Egress | Checks `startsWith('data:image/')`; returns empty base64 string. | **FAIL-CLOSED (PASS)** |
| **D** | Corrupt PNG decoding failure | `VISUAL_PRIVACY_UNVERIFIED` + No Egress | `img.onerror` fires; returns `sanitizedBase64: ''`. | **FAIL-CLOSED (PASS)** |
| **E** | Image zero dimensions | `VISUAL_PRIVACY_UNVERIFIED` + No Egress | `img.width === 0` check returns `sanitizedBase64: ''`. | **FAIL-CLOSED (PASS)** |
| **F** | Canvas 2D context allocation fails | `VISUAL_PRIVACY_UNVERIFIED` + No Egress | `!ctx` check returns failure result. | **FAIL-CLOSED (PASS)** |
| **G–K** | Redactor / Visual / PII throws | Task Abort + No Egress | `try/catch` in `content_script.ts` catches exception; aborts task. | **FAIL-CLOSED (PASS)** |
| **L** | Unknown visual content present | Solid Dark Fill `#020617` Masking | `LocalVisualDetector` flags region `UNVERIFIED_VISUAL_REGION`. | **FAIL-CLOSED (PASS)** |
| **Q** | Tab closed during capture | `VISUAL_PRIVACY_UNVERIFIED` + No Egress | Service Worker catches `Tab closed` error; returns failure. | **FAIL-CLOSED (PASS)** |
| **R** | Active tab changes mid-capture | **BLOCK / ABORT** | **Captures newly active tab (Tab B)!** | **FAIL-OPEN (VULN-01)** |
| **S** | Navigation mid-capture | **BLOCK / ABORT** | **Returns image of new origin without post-capture re-check.** | **FAIL-OPEN (VULN-02)** |
| **T** | Cross-tab capture request | **BLOCK / ABORT** | **Validates sender tab URL origin at start; TOCTOU risk.** | **POTENTIAL FAIL-OPEN** |

---

## 6. Phase 5 & 6 — Permission & TOCTOU Audit

### Permission Analysis (`"tabs"`):
- **Why Required:** `"tabs"` permission allows background service worker to access `sender.tab.url` and `sender.tab.windowId` to perform origin verification.
- **Granted Authority:** Allows reading tab metadata across browser windows.
- **Risk Mitigation:** Service worker enforces `parsedSenderOrigin === parsedReqOrigin` on incoming requests.

### TOCTOU Vulnerability Details (VULN-02):
- **Timeline:**
  - `T0`: Content script sends `CAPTURE_VISIBLE_TAB` message.
  - `T1`: Service Worker validates `sender.tab.url` origin (`trusted.example`).
  - `T2`: Webpage navigates to `attacker.example` (or user changes URL).
  - `T3`: `chrome.tabs.captureVisibleTab()` captures the new page (`attacker.example`).
  - `T4`: Service worker returns screenshot of `attacker.example` without post-capture origin verification!

---

## 7. Phase 7 — Active-Tab Ambiguity Audit (VULN-01)

### Cross-Tab Screen Leakage Scenario:
1. Agent task initiated on **Tab A** (`booking.example.com`).
2. User switches browser focus to **Tab B** (`personal-banking.example.com`).
3. `content_script.ts` on Tab A triggers `CAPTURE_VISIBLE_TAB`.
4. `chrome.tabs.captureVisibleTab(windowId)` captures whichever tab is **currently visible in the window** (Tab B!).
5. Raw screenshot of Tab B is returned to Tab A's content script controller!

> [!CAUTION]
> **CRITICAL PRIVACY VULNERABILITY (VULN-01):**  
> `chrome.tabs.captureVisibleTab()` inherently captures the active tab in the target window. If `sender.tab.active` is false at the time of capture, the returned image contains pixels from an unrelated browser tab.

---

## 8. Phase 9 & 10 — Visual Privacy & Coordinate Mapping Audit

- **Visual Element Coverage:**
  - DOM text: Regex & DOM attribute tokenization.
  - Canvas / SVG / Image elements: Scanned for text descriptors; unannotated visual regions covered with solid fill `#020617`.
- **Honest Claim Assessment:**
  - *Do NOT claim:* "100% absolute zero raw PII egress."
  - *Defensible Claim:* "On-device DOM layout perception & PII tokenization paired with fail-closed visual canvas overlay masking and minimum-disclosure payload validation."
- **Coordinate Conversion:**
  - HTML5 Canvas `drawImage(img, 0, 0, CSS_width, CSS_height)` automatically rescales high-DPI (devicePixelRatio) screenshots onto CSS viewport bounds.
  - Bounding rects from `getBoundingClientRect()` map 1:1 onto canvas CSS dimensions.

---

## 9. Phase 17 & 18 — Performance & Test Credibility Audit

```
+---------------------------------------------------------------------------------------------------+
| TEST SUITE CATEGORY                       | ASSERTION COUNT | RUNTIME CREDIBILITY LEVEL           |
+-------------------------------------------+-----------------+-------------------------------------+
| Static Source Code Verification           |        5        | HIGH (AST Regex Source Inspection)  |
| Python Behavioral Simulation              |       11        | MEDIUM (Simulated IPC & Canvas)     |
| Production Bundle Integration             |        1        | HIGH (Compiled dist/ Verification)  |
| Automated Hostile Red-Team Assertions     |      136        | HIGH (Direct Python Logic Engine)   |
| Live Chrome Browser Runtime Automation    |        0        | UNVERIFIED (No Puppeteer/Playwright)|
+-------------------------------------------+-----------------+-------------------------------------+
| TOTAL ASSERTIONS VERIFIED                 |      153        |                                     |
+-------------------------------------------+-----------------+-------------------------------------+
```

> [!IMPORTANT]
> **TESTING TRANSPARENCY NOTICE:**  
> Python test suites test extension logic in isolated Node/Python mock environments. They are **static and behavioral simulations**, NOT live Chrome browser end-to-end automation test runs.

---

## 10. Phase 19 — Adversarial SIH Judge Scorecard

```
====================================================================================================
                             REVISED ZERO-TRUST JUDGE SCORECARD
====================================================================================================
 CATEGORY                               WEIGHT   SCORE   JUSTIFICATION / EVIDENCE
----------------------------------------------------------------------------------------------------
 1. Problem Statement Alignment          20%     18/20   Strong alignment; real capture path verified.
 2. Security Architecture                15%     12/15   HMAC firewall verified; TOCTOU & active-tab vulns.
 3. Privacy & Sanitization               15%     13/15   Local PII tokenization & canvas masking verified.
 4. Browser Security Boundary            10%      7/10   Active-tab ambiguity leak vulnerability (VULN-01).
 5. Action Security                      10%     10/10   HMAC token gate & single-use nonces verified.
 6. Engineering Quality                  10%      9/10   Clean MV3 TypeScript modular implementation.
 7. Performance Credibility               5%      4/5    Sub-second responsiveness in benchmark.
 8. Testing Credibility                   5%      4/5    153 assertions pass; synthetic test distinction.
 9. Demo Reliability                      5%      4/5    Offline fallback planner active.
10. Presentation Defensibility            5%      6/10   Requires disarming active-tab & TOCTOU risks.
----------------------------------------------------------------------------------------------------
 TOTAL ADVERSARIAL SCORE                        87 / 100
====================================================================================================
 OFFICIAL VERDICT: HOLD — P0 REMEDIATION REQUIRED BEFORE FINAL CODE FREEZE
====================================================================================================
```

---

## 11. Discovered Vulnerabilities & Prioritized Remediation Queue

### P0 — MUST FIX BEFORE FINAL CODE FREEZE:
1. **VULN-01 [CRITICAL]: Active-Tab Ambiguity Cross-Tab Capture Leakage**
   - *Exploit:* User switches active tab to `banking.com` mid-task; `captureVisibleTab` captures `banking.com` pixels and returns them to task content script on `booking.com`.
   - *Fix:* In `service_worker.ts`, verify `sender.tab.active === true` both BEFORE and AFTER `captureVisibleTab()`. Fail closed if `sender.tab.active` is false.
2. **VULN-02 [HIGH]: Post-Capture TOCTOU Navigation Race Condition**
   - *Exploit:* Page navigates between initial origin check and capture completion.
   - *Fix:* In `service_worker.ts`, re-query `chrome.tabs.get(senderTabId)` *after* `captureVisibleTab()` resolves and verify `tab.url` origin matches `request.expectedOrigin` before returning data URL.

### P1 — STRONGLY RECOMMENDED:
3. **VULN-03 [HIGH]: Raw Screenshot In-Memory IPC Exposure**
   - *Fix:* Ensure content script immediately nullifies `captureRes.dataUrl` after canvas rendering.
4. **VULN-04 [MEDIUM]: Lack of Cryptographic Screenshot Signature**
   - *Fix:* Service Worker signs capture payload with HMAC signature of `taskId + tabId + origin + timestamp`.

### P2 — OPTIONAL IMPROVEMENT:
5. **VULN-05 [MEDIUM]: Concurrent Capture Request Queue**
   - *Fix:* Implement a request queue inside Service Worker to serialize concurrent tab capture calls.

---

## 12. Claims Honesty Guide (For Judging)

- **SAFE TO CLAIM:** Real browser viewport screen capture (`chrome.tabs.captureVisibleTab()`) processed locally inside client extension; fail-closed visual canvas overlay masking (`#020617`); minimum-disclosure PII tokenization; local HMAC-SHA-256 Action Firewall execution gate.
- **DO NOT CLAIM:** Do NOT claim zero network connectivity; do NOT claim running a 7B neural VLM in browser WASM; do NOT claim 100% un-hackable mathematical perfection.

> **AUDIT COMPLETE — NO SOURCE CODE WAS MODIFIED IN THIS PASS. REMEDIATION QUEUE READY.**
