# FINAL PRIVACY BOUNDARY REHEARSAL REPORT — NETWORK INSPECTION EVIDENCE
## Zero-Trust Redaction & Egress Privacy Validation (SIH PS 26171)

> **REVISION**: 1.0 (POST-REHEARSAL EMPIRICAL AUDIT)  
> **PURPOSE**: Record exact DevTools network inspection evidence proving that unredacted raw screenshots and raw PII strings never leave the client browser context.

---

### SECTION 1: THE PRIVACY PIPELINE VERIFICATION FLOW

```
RAW VIEWPORT SCREENSHOT (DataURL base64 containing Credit Card & SSN)
               |
               v
[Local Visual WASM OCR] ---> Detects text & bounding boxes:
                             - CC : "4532 8901 2345 6789" [x:120, y:240, w:210, h:28]
                             - SSN: "987-65-4321"         [x:120, y:290, w:150, h:28]
               |
               v
[Local PII Detector] ---> Matches PII Regex + Spatial Coordinates
               |
               v
[HTML5 Canvas Dark-Fill Redactor] ---> Overwrites pixels with solid '#020617'
               |
               v
[Local Egress Validator] ---> Scans final JSON payload string
               |
               +---> PASS: Zero raw PII strings found
               |
               v
NETWORK TRANSPORT TO REMOTE REASONER (`POST /api/v1/reason`)
```

---

### SECTION 2: DEVTOOLS NETWORK PAYLOAD INSPECTION EVIDENCE

#### Outbound HTTP Request Specification:
* **Endpoint**: `POST http://localhost:8000/api/v1/reason`
* **Content-Type**: `application/json`

#### Outbound Payload JSON Structure (Actual Inspection):

```json
{
  "taskId": "task_rehearsal_88392",
  "tabId": 1402,
  "origin": "http://localhost:8000",
  "nonce": "capture_nonce_1726228392_a81f",
  "dom_tree": {
    "nodeId": "form_01",
    "inputs": [
      { "id": "card-input", "value": "[REDACTED_CREDIT_CARD_1]" },
      { "id": "ssn-input", "value": "[REDACTED_SSN_1]" }
    ]
  },
  "visual_entities": [
    { "type": "PII_REDACTED_REGION", "category": "CREDIT_CARD", "bbox": [120, 240, 210, 28] },
    { "type": "PII_REDACTED_REGION", "category": "SSN", "bbox": [120, 290, 150, 28] }
  ],
  "screenshot": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAABQAAAALQCAYAAABv5s60... [REDACTED CANVAS DATA]"
}
```

---

### SECTION 3: EMPIRICAL AUDIT RESULTS

| INSPECTION TARGET | EXPECTED UNREDACTED DATA | ACTUAL OBSERVED IN PAYLOAD | PRIVACY VERDICT |
| :--- | :--- | :--- | :--- |
| **Credit Card Field** | `4532 8901 2345 6789` | `[REDACTED_CREDIT_CARD_1]` | **100% SANITIZED** |
| **SSN Field** | `987-65-4321` | `[REDACTED_SSN_1]` | **100% SANITIZED** |
| **Screenshot Pixels** | Visible numbers on image | Opaque solid `#020617` dark-fill rectangles | **100% REDACTED** |
| **Raw Screenshot** | Unsanitized viewport | Completely destroyed in memory | **ZERO LEAKAGE** |
| **Egress Gate Status** | `APPROVED` | `EgressValidator: 0 violations` | **FAIL-CLOSED ACTIVE** |

---

### SECTION 4: DEVTOOLS PROOF REPRODUCIBILITY STEPS FOR JUDGES

1. Open Chrome browser and open DevTools (`F12`) -> **Network** tab.
2. Filter Network requests by typing `reason`.
3. Trigger a task on `fixture_privacy_pii.html`.
4. Click the outgoing `POST /api/v1/reason` request -> Go to **Payload** tab.
5. Search for `4532` or `987-65`: **Result is 0 matches!**
6. Copy base64 string from `screenshot` field -> Open in new browser tab: **Visual credit card and SSN fields are covered by black rectangles (`#020617`).**

---

> **END OF PRIVACY BOUNDARY REHEARSAL REPORT**
