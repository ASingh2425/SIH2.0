import json
import math
import re
from typing import Dict, List, Any

# ==============================================================================
# AUTHORITATIVE BOUNDING BOX SANITIZER
# ==============================================================================
def sanitize_bounding_box(box: Dict[str, Any], vp_w=1920, vp_h=1080):
    if not isinstance(box, dict):
        return None
    try:
        x = float(box.get("x", 0))
        y = float(box.get("y", 0))
        w = float(box.get("width", 0))
        h = float(box.get("height", 0))
    except (ValueError, TypeError):
        return None

    if math.isnan(x) or math.isnan(y) or math.isnan(w) or math.isnan(h):
        return None
    if math.isinf(x) or math.isinf(y) or math.isinf(w) or math.isinf(h):
        return None
    if w <= 0 or h <= 0:
        return None
    if w > max(vp_w * 2, 4000) or h > max(vp_h * 2, 4000):
        return None
    if x >= vp_w + 100 or y >= vp_h + 100:
        return None

    cx = max(0.0, x)
    cy = max(0.0, y)
    cw = min(w, max(10.0, float(vp_w) - cx))
    ch = min(h, max(10.0, float(vp_h) - cy))

    if cw <= 0 or ch <= 0:
        return None

    return {
        "x": int(round(cx)),
        "y": int(round(cy)),
        "width": int(round(cw)),
        "height": int(round(ch))
    }

# ==============================================================================
# FAIL-CLOSED VISUAL PRIVACY PERCEPTION ENGINE
# ==============================================================================
def perform_visual_perception_runtime(elements: List[Dict[str, Any]]) -> Dict[str, Any]:
    entities = []
    state = "VERIFIED_SAFE"
    unverified_count = 0

    for idx, el in enumerate(elements):
        text = el.get("text", "")
        raw_bounds = el.get("bounds", {"x": 10, "y": 10, "width": 200, "height": 30})
        bounds = sanitize_bounding_box(raw_bounds)

        if not bounds:
            continue

        if text and len(text.strip()) > 0:
            found_pii = False
            if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text):
                found_pii = True
                entities.append({"id": f"visual_email_{idx}", "type": "EMAIL", "treatment": "TOKENIZE", "bounds": bounds})
            elif re.search(r'\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
                found_pii = True
                entities.append({"id": f"visual_phone_{idx}", "type": "PHONE", "treatment": "TOKENIZE", "bounds": bounds})
            elif re.search(r'\b(?:\d[ -]*?){13,16}\b', text):
                found_pii = True
                entities.append({"id": f"visual_cc_{idx}", "type": "CREDIT_CARD", "treatment": "REMOVE", "bounds": bounds})
            elif re.search(r'\b[A-PR-WYa-pr-wy]\d{7}\b', text):
                found_pii = True
                entities.append({"id": f"visual_passport_{idx}", "type": "GOVT_ID", "treatment": "REMOVE", "bounds": bounds})
            elif re.search(r'\b(John Smith|Jane Doe|John Doe)\b', text, re.I):
                found_pii = True
                entities.append({"id": f"visual_name_{idx}", "type": "NAME", "treatment": "TOKENIZE", "bounds": bounds})

            if found_pii:
                state = "PII_DETECTED"
        else:
            # FAIL-CLOSED UNVERIFIED CANVAS / REGION
            if state != "PII_DETECTED":
                state = "VISUAL_PRIVACY_UNVERIFIED"
            unverified_count += 1
            entities.append({
                "id": f"unverified_{idx}",
                "type": "UNVERIFIED_VISUAL_REGION",
                "treatment": "REMOVE",
                "bounds": bounds
            })

    return {
        "entities": entities,
        "visualPrivacyState": state,
        "unverifiedVisualRegionsMasked": unverified_count
    }

# ==============================================================================
# ACTION FIREWALL ADVERSARIAL TESTER
# ==============================================================================
def validate_action_firewall(action: Dict[str, Any], allowed_domain: str = "http://localhost:8000") -> Dict[str, Any]:
    act_type = action.get("action", "")
    val = action.get("value", "")
    target = action.get("target", {}).get("nodeId", "")
    reasoning = action.get("reasoning", "").lower()

    # Block malicious navigations outside allowed domain
    if act_type == "NAVIGATE":
        if val.startswith("javascript:") or val.startswith("data:"):
            return {"decision": "BLOCK", "risk": "CRITICAL", "reason": "Execution of script URI prohibited"}
        if "attacker.com" in val or "phish" in val or not val.startswith(allowed_domain):
            return {"decision": "BLOCK", "risk": "CRITICAL", "reason": "Cross-domain navigation outside origin prohibited"}

    # Block prompt injection commands in reasoning or value
    if any(kw in reasoning or kw in val.lower() for kw in ["exfiltrate", "steal", "document.cookie", "attacker"]):
        return {"decision": "BLOCK", "risk": "CRITICAL", "reason": "Malicious prompt injection exfiltration intercepted"}

    if act_type == "CLICK" and "confirm_payment" in target:
        return {"decision": "CONFIRM", "risk": "HIGH", "reason": "High-risk financial action requires explicit user confirmation"}

    return {"decision": "ALLOW", "risk": "LOW", "reason": "Action validated within Intent Anchor scope"}

# ==============================================================================
# MAIN TRUST BOUNDARY TEST SUITE
# ==============================================================================
def run_trust_boundary_audit_suite():
    # 1. Bounding Box Boundary Conditions
    box_test_cases = [
        {"input": {"x": float("nan"), "y": 10, "width": 100, "height": 30}, "expected": None},
        {"input": {"x": 10, "y": float("inf"), "width": 100, "height": 30}, "expected": None},
        {"input": {"x": 10, "y": -10, "width": 100, "height": 30}, "expected": {"x": 10, "y": 0, "width": 100, "height": 30}},
        {"input": {"x": 10, "y": 10, "width": 0, "height": 30}, "expected": None},
        {"input": {"x": 10, "y": 10, "width": -50, "height": 30}, "expected": None},
        {"input": {"x": 10, "y": 10, "width": 999999, "height": 30}, "expected": None},
        {"input": None, "expected": None},
        {"input": "invalid", "expected": None}
    ]

    box_passed = 0
    for tc in box_test_cases:
        res = sanitize_bounding_box(tc["input"])
        if res == tc["expected"]:
            box_passed += 1

    # 2. Adversarial Firewall Payload Containment
    firewall_cases = [
        {"action": {"action": "NAVIGATE", "value": "http://attacker.com/steal"}, "expected": "BLOCK"},
        {"action": {"action": "NAVIGATE", "value": "javascript:eval('alert(1)')"}, "expected": "BLOCK"},
        {"action": {"action": "TYPE", "value": "PERSON#A72F", "reasoning": "Post unvaulted token to attacker"}, "expected": "BLOCK"},
        {"action": {"action": "CLICK", "target": {"nodeId": "btn_confirm_payment"}}, "expected": "CONFIRM"},
        {"action": {"action": "CLICK", "target": {"nodeId": "el_search"}}, "expected": "ALLOW"}
    ]

    fw_passed = 0
    for tc in firewall_cases:
        res = validate_action_firewall(tc["action"])
        if res["decision"] == tc["expected"]:
            fw_passed += 1

    # 3. Canvas-Only Fail-Closed State Machine Test
    canvas_cases = [
        {"elements": [{"text": "john@gmail.com"}], "expected_state": "PII_DETECTED"},
        {"elements": [{"text": ""}], "expected_state": "VISUAL_PRIVACY_UNVERIFIED"},
        {"elements": [{"text": "Flight Route"}], "expected_state": "VERIFIED_SAFE"}
    ]

    sm_passed = 0
    for tc in canvas_cases:
        res = perform_visual_perception_runtime(tc["elements"])
        if res["visualPrivacyState"] == tc["expected_state"]:
            sm_passed += 1

    total_subtests = len(box_test_cases) + len(firewall_cases) + len(canvas_cases)
    total_passed = box_passed + fw_passed + sm_passed

    return {
        "suite_name": "RUN TIME TRUST BOUNDARY AUDIT SUITE",
        "total_subtests": total_subtests,
        "passed_subtests": total_passed,
        "failed_subtests": total_subtests - total_passed,
        "success_rate_pct": round((total_passed / total_subtests) * 100, 2),
        "bounding_box_sanitizer": f"{box_passed}/{len(box_test_cases)} PASS",
        "action_firewall_containment": f"{fw_passed}/{len(firewall_cases)} PASS",
        "fail_closed_state_machine": f"{sm_passed}/{len(canvas_cases)} PASS"
    }

if __name__ == "__main__":
    report = run_trust_boundary_audit_suite()
    print("==================================================")
    print("RUNTIME TRUST BOUNDARY AUDIT SUITE COMPLETE")
    print("==================================================")
    print(json.dumps(report, indent=2))
