# FINAL PRIVACY PROOF DEMO GUIDE — ZERO-TRUST REDACTION & EGRESS CONTROL
## On-Device PII Masking & Solid `#020617` Canvas Redaction (SIH PS 26171)

> **REVISION**: 1.0 (CODE-FROZEN VERIFIED STATE)  
> **PURPOSE**: Comprehensive demonstration guide to prove client-side visual privacy redaction, solid dark-fill canvas rendering, and fail-closed egress validation to SIH technical judges.

---

### PRIVACY ARCHITECTURE OVERVIEW

Before any multimodal screenshot or page context is transmitted off-device to an external reasoner, the browser extension executes an automated 3-stage privacy workflow:

```
[RAW VIEWPORT SCREENSHOT] + [RAW DOM TEXT]
           |
           v
1. LOCAL PII DETECTION (Regex + Local OCR Spatial Bounding Boxes)
   - Credit Card Pattern: `\b(?:\d[ -]*?){13,16}\b` (Luhn Verified)
   - SSN Pattern:         `\b\d{3}-\d{2}-\d{4}\b`
   - Email Pattern:       `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
           |
           v
2. SOLID DARK-FILL CANVAS REDACTION (`#020617`)
   - Creates in-memory HTML5 `<canvas>` matching viewport dimensions
   - Draws original image onto canvas
   - Sets `ctx.fillStyle = '#020617'` (Solid Opaque Midnight Slate)
   - Fills exact bounding box rectangles over detected PII coordinates
   - Re-encodes canvas to base64 DataURL (Original image destroyed)
           |
           v
3. FAIL-CLOSED EGRESS VALIDATION (`EgressValidator`)
   - Scans final JSON outbound payload string for unredacted PII patterns
   - If ANY unredacted PII matches: ABORT REQUEST IMMEDIATELY
```

---

### LIVE JUDGE DEMONSTRATION STEP-BY-STEP

#### STEP 1: LOAD PRIVACY TEST FIXTURE
1. Open Chrome browser and navigate to local test page `fixture_privacy_pii.html`.
2. Point out the sensitive fields visible on screen:
   - **Credit Card Number**: `4532 8901 2345 6789`
   - **Social Security Number**: `987-65-4321`
   - **User Email**: `john.doe.private@company.org`

#### STEP 2: OPEN NETWORK TAB & PREPARE MONITORS
1. Open Chrome DevTools (`F12`) -> **Network** tab.
2. Filter Network requests by typing: `reason`.
3. Select **Console** tab side-by-side.

#### STEP 3: TRIGGER AGENT TASK WITH PRIVACY REDACTION
1. In the Extension SidePanel, click **"Analyze & Prepare Task Egress"**.
2. Observe Console output:
   ```
   [LocalPIIDetector] Scanning DOM text + OCR bounding boxes...
   [LocalPIIDetector] Detected 3 PII entities:
     - CREDIT_CARD at BBox [x:120, y:240, w:210, h:28]
     - SSN at BBox [x:120, y:290, w:150, h:28]
     - EMAIL at BBox [x:120, y:340, w:180, h:28]
   [LocalPIIDetector] Canvas redaction pass completed using fillStyle='#020617'.
   [EgressValidator] Payload scan complete. 0 PII leaks detected. Egress APPROVED.
   ```

#### STEP 4: INSPECT REDACTED SCREENSHOT IN NETWORK PAYLOAD
1. In the Network tab, click the outbound POST request to `/api/v1/reason`.
2. Go to the **Payload** tab.
3. Locate the `screenshot` base64 field -> Right click -> **Open image in new tab** (or render preview).
4. **Show the Judge**:
   - The credit card, SSN, and email text areas are **100% covered by solid black/dark-slate rectangles (`#020617`)**.
   - No gradient, blur, or transparent overlay is used. The pixels under the rectangle are completely overwritten with constant hex color `#020617`.

#### STEP 5: PROVE FAIL-CLOSED EGRESS PROTECTION (ATTACK SIMULATION)
1. To prove the egress gate is not just decorative, open Console and simulate a leaked PII string in the outbound payload by calling:
   ```javascript
   EgressValidator.validatePayload({
     task: "test",
     user_input: "My secret card is 4532-8901-2345-6789"
   });
   ```
2. Observe immediate exception thrown:
   ```
   [EgressValidator] CRITICAL SECURITY ALERT: Raw PII string detected in egress payload!
   Pattern Matched: CREDIT_CARD
   Action: ABORTED payload transmission. Status: EGRESS_VIOLATION_BLOCKED
   ```
3. Show the judge: *"Even if the local OCR engine were to miss a visual entity, if any unredacted PII makes it into the final network JSON payload, our fail-closed EgressValidator kills the network request on the spot."*

---

### AUTOMATED BENCHMARK VERIFICATION

To verify privacy redaction programmatically across all test cases, run:

```bash
python -m unittest benchmark/test_visual_privacy_hardening.py
```

#### EXPECTED TEST OUTPUT:
```
test_canvas_dark_fill_redaction (benchmark.test_visual_privacy_hardening.TestVisualPrivacy) ... OK
test_egress_validator_fail_closed (benchmark.test_visual_privacy_hardening.TestVisualPrivacy) ... OK
test_pii_bbox_extraction (benchmark.test_visual_privacy_hardening.TestVisualPrivacy) ... OK
----------------------------------------------------------------------
Ran 3 tests in 0.185s
OK
```

---

### KEY DEFENSE POINTS FOR SIH JUDGES

1. **Why `#020617` Dark Fill?**: Blur/pixelation filters can be inverted or reconstructed using AI deconvolution models. Solid pixel replacement with `#020617` is mathematically non-recoverable.
2. **Dual Protection Layer**: Visual redaction on screenshot pixels + tokenization (`[REDACTED_SSN_1]`) on text strings.
3. **Fail-Closed Egress**: Network request cannot fire unless `EgressValidator` returns zero unredacted PII matches.

---

> **END OF PRIVACY PROOF DEMO GUIDE**
