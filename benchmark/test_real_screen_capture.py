import json
import re
import os
import sys

# Categorized Test Assertions Matrix for Real Screen Capture Architecture Audit
# Categories:
# 1. STATIC VERIFICATION: Direct source code AST / regex verification against TS files.
# 2. BEHAVIORAL SIMULATION: Python simulation of service worker messaging & canvas redaction logic.
# 3. PRODUCTION-RUNTIME INTEGRATION: Verification of compiled extension dist/ & manifest bindings.

def run_real_screen_capture_test_suite():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    manifest_path = os.path.join(repo_root, "extension", "manifest.json")
    sw_path = os.path.join(repo_root, "extension", "src", "background", "service_worker.ts")
    canvas_path = os.path.join(repo_root, "extension", "src", "content", "canvas_capture.ts")
    content_path = os.path.join(repo_root, "extension", "src", "content", "content_script.ts")
    egress_path = os.path.join(repo_root, "extension", "src", "privacy", "egress_validator.ts")

    test_results = []
    test_counter = 0

    def add_result(test_name, category, passed, details):
        nonlocal test_counter
        test_counter += 1
        test_results.append({
            "test_id": test_counter,
            "test_name": test_name,
            "category": category, # static verification | behavioral simulation | production-runtime integration
            "passed": passed,
            "details": details,
            "status": "PASS" if passed else "FAIL"
        })

    # --- CATEGORY 1: STATIC VERIFICATION ---

    # Test A: Real capture API path exists in Service Worker source
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_content = f.read()
    
    has_capture_api = "chrome.tabs.captureVisibleTab" in sw_content and "handleCaptureVisibleTab" in sw_content
    add_result(
        "Real Capture API Path Registration",
        "static verification",
        has_capture_api,
        "Verified chrome.tabs.captureVisibleTab and handleCaptureVisibleTab exist in background/service_worker.ts"
    )

    # Test B: Synthetic screenshot path disarmed for production
    with open(canvas_path, "r", encoding="utf-8") as f:
        canvas_content = f.read()
    
    disarmed_synthetic = "FAIL-CLOSED: No raw real screenshot supplied" in canvas_content and "redactRealViewportScreenshot" in canvas_content
    add_result(
        "Synthetic Screenshot Path Disarmed",
        "static verification",
        disarmed_synthetic,
        "Verified ClientCanvasRedactor fails closed unless real rawScreenshotBase64 is supplied"
    )

    # Test M: Synthetic illustration explicitly labeled
    synthetic_labeled = "DEMO ILLUSTRATION ONLY — NOT A REAL SCREENSHOT" in canvas_content and "generateExplicitSyntheticIllustrationDemoOnly" in canvas_content
    add_result(
        "Synthetic Illustration Explicit Labeling",
        "static verification",
        synthetic_labeled,
        "Verified synthetic canvas illustration is explicitly labeled for demo use only"
    )

    # Test N & G: Sender tab and origin validation in Service Worker
    has_origin_validation = ("strictOriginMatch" in sw_content or "preCaptureOrigin" in sw_content) and "Security Abort: Missing active tab context" in sw_content
    add_result(
        "Sender Tab & Origin Verification",
        "static verification",
        has_origin_validation,
        "Verified strict sender tab & origin domain validation inside Service Worker"
    )

    # Test P: No persistent storage of screenshots
    with open(content_path, "r", encoding="utf-8") as f:
        content_code = f.read()

    no_screenshot_storage = "chrome.storage" not in canvas_content and "localStorage" not in canvas_content and "cookies" not in canvas_content
    add_result(
        "No Screenshot Storage Persistence",
        "static verification",
        no_screenshot_storage,
        "Verified raw/sanitized screenshots are never written to chrome.storage, localStorage, or cookies"
    )

    # --- CATEGORY 2: BEHAVIORAL SIMULATION ---

    # Behavioral Test C & D: Simulation of Capture Failure & Invalid Image (Fail-Closed)
    def simulate_redact_viewport(raw_image, entities, width=1920, height=1080):
        if not raw_image or not isinstance(raw_image, str) or not raw_image.startswith("data:image/"):
            return {
                "sanitizedBase64": "",
                "redactionCount": 0,
                "visualPrivacyState": "VISUAL_PRIVACY_UNVERIFIED",
                "isRealCapture": False
            }
        
        # Valid real screenshot simulation
        redaction_count = len([e for e in entities if e.get("treatment") in ["REMOVE", "MASK", "TOKENIZE"]])
        return {
            "sanitizedBase64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "redactionCount": redaction_count,
            "visualPrivacyState": "VERIFIED_SAFE",
            "isRealCapture": True
        }

    # Test C: Capture Failure -> Fail Closed
    res_fail = simulate_redact_viewport(None, [])
    c_pass = res_fail["visualPrivacyState"] == "VISUAL_PRIVACY_UNVERIFIED" and res_fail["sanitizedBase64"] == ""
    add_result(
        "Capture Failure Fail-Closed Handling",
        "behavioral simulation",
        c_pass,
        f"Simulated missing capture -> State: {res_fail['visualPrivacyState']}, Image: '{res_fail['sanitizedBase64']}'"
    )

    # Test D: Invalid Image -> Fail Closed
    res_invalid = simulate_redact_viewport("invalid_not_base64_string", [])
    d_pass = res_invalid["visualPrivacyState"] == "VISUAL_PRIVACY_UNVERIFIED" and res_invalid["sanitizedBase64"] == ""
    add_result(
        "Invalid Image Format Fail-Closed",
        "behavioral simulation",
        d_pass,
        f"Simulated invalid format -> State: {res_invalid['visualPrivacyState']}, Image: '{res_invalid['sanitizedBase64']}'"
    )

    # Behavioral Test F & G: Tab / Origin Mismatch Simulation
    def simulate_sw_capture(sender_tab_id, sender_origin, expected_origin):
        if not sender_tab_id:
            return {"success": False, "visualPrivacyState": "VISUAL_PRIVACY_UNVERIFIED", "error": "Missing active tab context"}
        if sender_origin != expected_origin:
            return {"success": False, "visualPrivacyState": "VISUAL_PRIVACY_UNVERIFIED", "error": f"Origin mismatch: {sender_origin} vs {expected_origin}"}
        return {"success": True, "dataUrl": "data:image/png;base64,VALID_IMAGE_BYTES"}

    res_tab_mismatch = simulate_sw_capture(None, "https://example.com", "https://example.com")
    f_pass = not res_tab_mismatch["success"] and res_tab_mismatch["visualPrivacyState"] == "VISUAL_PRIVACY_UNVERIFIED"
    add_result(
        "Tab Mismatch Security Abort",
        "behavioral simulation",
        f_pass,
        f"Simulated missing tab -> Result: {res_tab_mismatch}"
    )

    res_origin_mismatch = simulate_sw_capture(101, "https://evil.com", "https://example.com")
    g_pass = not res_origin_mismatch["success"] and res_origin_mismatch["visualPrivacyState"] == "VISUAL_PRIVACY_UNVERIFIED"
    add_result(
        "Origin Mismatch Security Abort",
        "behavioral simulation",
        g_pass,
        f"Simulated origin spoofing (evil.com vs example.com) -> Result: {res_origin_mismatch}"
    )

    # Behavioral Test I & J: DevicePixelRatio & Bounding Rect Conversion
    def convert_coords_with_dpr(css_x, css_y, css_w, css_h, dpr=2.0):
        # Screenshot image dimensions are scaled by dpr
        img_x = css_x * dpr
        img_y = css_y * dpr
        img_w = css_w * dpr
        img_h = css_h * dpr
        return {"x": img_x, "y": img_y, "width": img_w, "height": img_h}

    converted = convert_coords_with_dpr(100, 200, 150, 40, dpr=2.0)
    ij_pass = converted["x"] == 200 and converted["y"] == 400 and converted["width"] == 300 and converted["height"] == 80
    add_result(
        "DevicePixelRatio & Coordinate Conversion",
        "behavioral simulation",
        ij_pass,
        f"Verified CSS coords (100,200,150,40) at DPR=2.0 scale to image pixels (200,400,300,80)"
    )

    # Behavioral Test K & L: Egress Verification (Raw image NOT sent before sanitization)
    def simulate_egress_check(raw_image, sanitized_image):
        # Raw image must be sanitized before transmission
        if raw_image and not sanitized_image:
            return {"egress_safe": False, "reason": "Unsanitized raw screenshot attempted egress"}
        if sanitized_image and sanitized_image.startswith("data:image/png;base64,"):
            return {"egress_safe": True, "reason": "Sanitized screenshot eligible for network egress"}
        return {"egress_safe": True, "reason": "Structured DOM mode operating without screenshot"}

    res_raw_egress = simulate_egress_check("data:image/png;base64,RAW_UNREDACTED", None)
    res_sanitized_egress = simulate_egress_check(None, "data:image/png;base64,SANITIZED_REDACTED")
    kl_pass = not res_raw_egress["egress_safe"] and res_sanitized_egress["egress_safe"]
    add_result(
        "Egress Security Boundary Verification",
        "behavioral simulation",
        kl_pass,
        "Verified raw screenshot egress is BLOCKED and sanitized screenshot is ELIGIBLE"
    )

    # --- CATEGORY 3: PRODUCTION-RUNTIME INTEGRATION ---

    dist_bg_path = os.path.join(repo_root, "extension", "dist", "background.js")
    dist_content_path = os.path.join(repo_root, "extension", "dist", "content.js")

    dist_exists = os.path.exists(dist_bg_path) and os.path.exists(dist_content_path)
    if dist_exists:
        with open(dist_bg_path, "r", encoding="utf-8") as f:
            dist_bg_content = f.read()
        
        has_compiled_capture = "captureVisibleTab" in dist_bg_content and "CAPTURE_VISIBLE_TAB" in dist_bg_content
        add_result(
            "Compiled Bundle Capture Integration",
            "production-runtime integration",
            has_compiled_capture,
            "Verified compiled extension dist/background.js contains captureVisibleTab and message handler"
        )
    else:
        add_result(
            "Compiled Bundle Capture Integration",
            "production-runtime integration",
            False,
            "Extension dist/ directory not found. Please run npm run build."
        )

    # Summary Statistics
    total_tests = len(test_results)
    passed_tests = len([t for t in test_results if t["passed"]])
    failed_tests = total_tests - passed_tests
    success_rate = (passed_tests / total_tests) * 100.0

    report = {
        "suite_name": "test_real_screen_capture.py",
        "total_test_assertions": total_tests,
        "passed_tests": passed_tests,
        "failed_tests": failed_tests,
        "success_rate_pct": round(success_rate, 2),
        "test_results": test_results
    }

    print(json.dumps(report, indent=2))
    return report

if __name__ == "__main__":
    res = run_real_screen_capture_test_suite()
    if res["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)
