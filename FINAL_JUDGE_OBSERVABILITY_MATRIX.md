# FINAL JUDGE OBSERVABILITY MATRIX — LIVE DEMO DEMONSTRABILITY
## Empirical Observability Assessment for SIH Judging Panel (PS 26171)

> **REVISION**: 1.0 (POST-REHEARSAL AUDITED STATE)  
> **PURPOSE**: Classify every core technical feature by its direct visual demonstrability so presenters know exactly which screen, console tab, or log window to highlight during judging.

---

### SECTION 1: CORE FEATURE OBSERVABILITY MATRIX

| FEATURE / CLAIM | OBSERVABILITY CLASSIFICATION | HOW THE JUDGE SEES IT LIVE | EXACT DEMO / INSPECTION LOCATION |
| :--- | :--- | :--- | :--- |
| **1. Real Screenshot Capture** | **VISIBLE THROUGH DEVTOOLS & LOG** | DevTools Service Worker Console logs `captureVisibleTab` with fresh SHA-256 nonce. | Service Worker DevTools Console -> `[ServiceWorker] Captured active tab` |
| **2. Local WASM OCR Execution** | **VISIBLE THROUGH DEVTOOLS** | Web Worker thread `tesseract-worker.js` visible under DevTools Application/Threads; Console logs recognizePixels. | Extension Console -> `[LocalVisualModelEngine] WASM recognizePixels` |
| **3. Pixel Dependence (Canvas Text)** | **VISIBLE DIRECTLY & LOG** | HTML DOM shows `ALICE@EXAMPLE.COM`; Canvas overlay displays `BOB@EXAMPLE.COM`. Agent extracts `BOB@EXAMPLE.COM`. | Webpage UI + SidePanel Output + Console `VISUAL_OVERRIDE` log |
| **4. Local PII Detection** | **VISIBLE DIRECTLY & DEVTOOLS** | Detected PII fields (Credit Card, SSN, Email) highlighted with category labels in SidePanel perception log. | Extension SidePanel -> Perception Entities List |
| **5. Canvas `#020617` Redaction** | **VISIBLE DIRECTLY & DEVTOOLS** | Network tab payload preview shows solid black `#020617` rectangles covering sensitive image areas. | DevTools Network Tab -> POST `/api/v1/reason` -> Image Payload Preview |
| **6. Network Sanitization** | **VISIBLE THROUGH DEVTOOLS** | Outbound JSON payload contains zero unredacted PII strings; PII replaced with `[REDACTED_*]` tokens. | DevTools Network Tab -> Request Payload JSON Inspection |
| **7. Action Firewall Gating** | **VISIBLE DIRECTLY & LOG** | Malicious / replayed action proposal triggers red UI Security Alert; Console logs `FIREWALL_HMAC_INVALID`. | Webpage UI Security Alert Banner + Console Logs |
| **8. Audit Security Ledger** | **VISIBLE DIRECTLY** | Security Ledger table in Extension SidePanel displays immutable append-only log of approved & blocked actions. | Extension SidePanel -> Security Ledger Tab |

---

### SECTION 2: OBSERVABILITY CLASSIFICATION BREAKDOWN

```
+-----------------------------------------------------------------------------------+
|                           JUDGE OBSERVABILITY SUMMARY                             |
+-----------------------------------------------------------------------------------+
| VISIBLE DIRECTLY (UI / On-Screen)        | 4 Features (Pixel OCR, PII, Firewall, Ledger)|
| VISIBLE THROUGH DEVTOOLS (Network/Console)| 4 Features (Capture, WASM, Redaction, Egress)|
| VISIBLE THROUGH LOG / LEDGER              | 8 Features (100% Audit Traceability)        |
| ONLY PROVABLE FROM SOURCE                 | 0 Features (All claims backed by runtime logs)|
| NOT CURRENTLY DEMONSTRABLE                | 0 Features (All features executable live)   |
+-----------------------------------------------------------------------------------+
```

---

### SECTION 3: PRESENTER OBSERVABILITY MAP FOR 7-MINUTE DEMO

1. **Minute 1:30 (Visual OCR)** -> Point to Extension Console: Show `[LocalVisualModelEngine] WASM recognizePixels` log + `tesseract-worker.js` thread.
2. **Minute 3:00 (Privacy Redaction)** -> Open DevTools Network Tab -> Click `Payload` -> Show `#020617` dark-fill image preview.
3. **Minute 4:45 (Action Firewall)** -> Trigger Prompt Injection -> Point to red UI Alert Banner + Console `FIREWALL_HMAC_INVALID` log.
4. **Minute 5:45 (Security Ledger)** -> Click SidePanel `Ledger` tab -> Show immutable log table.

---

> **END OF JUDGE OBSERVABILITY MATRIX**
