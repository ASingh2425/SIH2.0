import json
import time
import math
from typing import Dict, List, Any, Optional

# ==============================================================================
# AUTHORITATIVE FIREWALL AUTHORIZATION TOKEN SIMULATOR
# ==============================================================================
class ActionExecutionGateSimulator:
    def __init__(self):
        # Isolated World Session Secret (Inaccessible to web page JS / Remote VLM)
        self._session_hmac_secret = "fw_isolated_session_secret_998127341"

    def compute_signature(
        self,
        task_id: str,
        action_id: str,
        action_type: str,
        target_node_id: str,
        target_selector: str,
        origin_domain: str,
        decision: str,
        user_confirmed: bool,
        issued_at: int,
        expires_at: int
    ) -> str:
        raw_tuple = f"{task_id}:{action_id}:{action_type}:{target_node_id}:{target_selector}:{origin_domain}:{decision}:{user_confirmed}:{issued_at}:{expires_at}:{self._session_hmac_secret}"
        # Simple Hash Simulator matching TypeScript string hash
        hash_val = 0
        for ch in raw_tuple:
            hash_val = ((hash_val << 5) - hash_val) + ord(ch)
            hash_val &= 0xFFFFFFFF
        return f"auth_sig_{abs(hash_val):x}_{issued_at}"

    def issue_token(
        self,
        action: Dict[str, Any],
        origin_domain: str,
        decision: str,
        user_confirmed: bool = False
    ) -> Optional[Dict[str, Any]]:
        if decision == "BLOCK":
            return None # Blocked decisions CANNOT generate authorization tokens

        issued_at = int(time.time() * 1000)
        expires_at = issued_at + 30000 # 30-second TTL
        task_id = action.get("taskId", "")
        action_id = action.get("actionId", "")
        action_type = action.get("action", "")
        target_node_id = action.get("target", {}).get("nodeId", "")
        target_selector = action.get("target", {}).get("selector", "")

        sig = self.compute_signature(
            task_id, action_id, action_type, target_node_id, target_selector,
            origin_domain, decision, user_confirmed, issued_at, expires_at
        )

        return {
            "tokenId": f"token_{issued_at}_test",
            "actionId": action_id,
            "taskId": task_id,
            "actionType": action_type,
            "targetNodeId": target_node_id,
            "targetSelector": target_selector,
            "originDomain": origin_domain,
            "decision": decision,
            "userConfirmed": user_confirmed,
            "issuedAt": issued_at,
            "expiresAt": expires_at,
            "signature": sig
        }

    def verify_token(
        self,
        token: Optional[Dict[str, Any]],
        action: Dict[str, Any],
        live_origin: str,
        now_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        if not token or not isinstance(token, dict):
            return {"valid": False, "reason": "Missing or non-dict authorization token"}

        if now_ms is None:
            now_ms = int(time.time() * 1000)

        # 1. Signature Verification
        expected_sig = self.compute_signature(
            token.get("taskId", ""),
            token.get("actionId", ""),
            token.get("actionType", ""),
            token.get("targetNodeId", ""),
            token.get("targetSelector", ""),
            token.get("originDomain", ""),
            token.get("decision", ""),
            token.get("userConfirmed", False),
            token.get("issuedAt", 0),
            token.get("expiresAt", 0)
        )

        if token.get("signature") != expected_sig:
            return {"valid": False, "reason": "Cryptographic signature mismatch or token forged"}

        # 2. TTL Verification
        if now_ms > token.get("expiresAt", 0):
            return {"valid": False, "reason": "Authorization token expired"}

        # 3. Action & Intent Tuple Binding Verification
        if token.get("taskId") != action.get("taskId"):
            return {"valid": False, "reason": "Task ID mismatch"}

        if token.get("actionId") != action.get("actionId"):
            return {"valid": False, "reason": "Action ID mismatch"}

        if token.get("actionType") != action.get("action"):
            return {"valid": False, "reason": "Action type mismatch"}

        if token.get("targetNodeId") != action.get("target", {}).get("nodeId", ""):
            return {"valid": False, "reason": "Target node ID mismatch"}

        if token.get("originDomain") != live_origin:
            return {"valid": False, "reason": "Origin domain mismatch"}

        # 4. Decision State & CONFIRM Semantics
        if token.get("decision") == "CONFIRM" and not token.get("userConfirmed", False):
            return {"valid": False, "reason": "Action requires explicit user confirmation (userConfirmed is false)"}

        return {"valid": True, "reason": "Authorization verified"}

    def execute_verified_action(
        self,
        action: Dict[str, Any],
        live_origin: str,
        token: Optional[Dict[str, Any]],
        dom_node: Optional[Dict[str, Any]] = None,
        now_ms: Optional[int] = None
    ) -> Dict[str, Any]:
        # Gate 1: Cryptographic Authorization Token Verification
        auth_res = self.verify_token(token, action, live_origin, now_ms)
        if not auth_res["valid"]:
            return {"success": False, "stage": "GATE_1_TOKEN_VERIFICATION", "message": f"Execution Security Abort: {auth_res['reason']}"}

        # Gate 2: Pre-Execution Immediate DOM TOCTOU Re-Evaluation
        if not dom_node:
            return {"success": False, "stage": "GATE_2_TOCTOU_DOM_RECHECK", "message": "Pre-Execution Security Abort: Target element missing in live DOM"}

        node_id = dom_node.get("id", "").lower()
        node_type = dom_node.get("type", "").lower()
        node_action = dom_node.get("data-action", "").lower()

        if "transfer" in node_id or "delete" in node_id or "reset" in node_id or "exfiltrate" in node_action or (node_type == "password" and action.get("action") != "TYPE"):
            return {"success": False, "stage": "GATE_2_TOCTOU_DOM_RECHECK", "message": "Pre-Execution Security Abort: Target element attributes mutated into security-sensitive target post-approval"}

        bounds = dom_node.get("bounds", {"width": 100, "height": 30})
        if bounds.get("width", 0) <= 0 or bounds.get("height", 0) <= 0:
            return {"success": False, "stage": "GATE_2_TOCTOU_DOM_RECHECK", "message": "Pre-Execution Security Abort: Target element is hidden or invisible"}

        # Gate 3: DOM Event Execution Success
        return {"success": True, "stage": "GATE_3_DOM_EXECUTION", "message": f"Action {action.get('actionId')} successfully executed on target {action.get('target', {}).get('nodeId')}"}


# ==============================================================================
# ADVERSARIAL TEST SUITE FOR PASS #6 EXECUTION GATE HARDENING
# ==============================================================================
def run_action_execution_gate_test_suite():
    gate = ActionExecutionGateSimulator()
    now = int(time.time() * 1000)

    test_action_a = {
        "taskId": "task_101",
        "actionId": "act_001",
        "action": "CLICK",
        "target": {"nodeId": "el_search_btn", "selector": "#el_search_btn"}
    }

    test_action_b = {
        "taskId": "task_101",
        "actionId": "act_002",
        "action": "TYPE",
        "target": {"nodeId": "el_input_name", "selector": "#el_input_name"},
        "value": "PERSON#A72F"
    }

    test_action_confirm = {
        "taskId": "task_101",
        "actionId": "act_003",
        "action": "CLICK",
        "target": {"nodeId": "btn_confirm_pay", "selector": "#btn_confirm_pay"}
    }

    valid_dom_node = {"id": "el_search_btn", "type": "button", "bounds": {"width": 100, "height": 30}}

    valid_token_a = gate.issue_token(test_action_a, "http://localhost:8000", "ALLOW")
    confirm_token_unconfirmed = gate.issue_token(test_action_confirm, "http://localhost:8000", "CONFIRM", user_confirmed=False)
    confirm_token_user_approved = gate.issue_token(test_action_confirm, "http://localhost:8000", "CONFIRM", user_confirmed=True)

    test_cases = [
        {
            "name": "1. Direct Execution Without Authorization Token",
            "action": test_action_a,
            "origin": "http://localhost:8000",
            "token": None,
            "dom": valid_dom_node,
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "2. Forged Authorization Token ({ approved: true })",
            "action": test_action_a,
            "origin": "http://localhost:8000",
            "token": {"approved": True, "decision": "ALLOW", "signature": "fake_sig"},
            "dom": valid_dom_node,
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "3. Token Action ID Mismatch (Token for Action A used for Action B)",
            "action": test_action_b,
            "origin": "http://localhost:8000",
            "token": valid_token_a,
            "dom": valid_dom_node,
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "4. Task ID / Intent Mismatch (Token task_101 used for task_999)",
            "action": {**test_action_a, "taskId": "task_999"},
            "origin": "http://localhost:8000",
            "token": valid_token_a,
            "dom": valid_dom_node,
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "5. Expired Authorization Token (TTL Exceeded)",
            "action": test_action_a,
            "origin": "http://localhost:8000",
            "token": valid_token_a,
            "dom": valid_dom_node,
            "now_offset_ms": 35000, # 35 seconds later
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "6. Target Node ID Mutation / Selector Alteration",
            "action": {**test_action_a, "target": {"nodeId": "el_mutated_target"}},
            "origin": "http://localhost:8000",
            "token": valid_token_a,
            "dom": valid_dom_node,
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "7. Origin Domain Hijack / Mismatch",
            "action": test_action_a,
            "origin": "http://attacker.com",
            "token": valid_token_a,
            "dom": valid_dom_node,
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "8. Blocked Firewall Decision Token Generation Failure",
            "action": test_action_a,
            "origin": "http://localhost:8000",
            "token": gate.issue_token(test_action_a, "http://localhost:8000", "BLOCK"),
            "dom": valid_dom_node,
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "9. CONFIRM Decision Without Explicit User Approval (userConfirmed: false)",
            "action": test_action_confirm,
            "origin": "http://localhost:8000",
            "token": confirm_token_unconfirmed,
            "dom": {"id": "btn_confirm_pay", "type": "button", "bounds": {"width": 100, "height": 30}},
            "expected_success": False,
            "expected_stage": "GATE_1_TOKEN_VERIFICATION"
        },
        {
            "name": "10. CONFIRM Decision WITH Explicit User Approval (userConfirmed: true)",
            "action": test_action_confirm,
            "origin": "http://localhost:8000",
            "token": confirm_token_user_approved,
            "dom": {"id": "btn_confirm_pay", "type": "button", "bounds": {"width": 100, "height": 30}},
            "expected_success": True,
            "expected_stage": "GATE_3_DOM_EXECUTION"
        },
        {
            "name": "11. TOCTOU DOM Mutation Pre-Dispatch Abort (Element Mutated Post-Approval)",
            "action": test_action_a,
            "origin": "http://localhost:8000",
            "token": valid_token_a,
            "dom": {"id": "btn_delete_account", "type": "button", "bounds": {"width": 100, "height": 30}}, # Mutated to delete_account
            "expected_success": False,
            "expected_stage": "GATE_2_TOCTOU_DOM_RECHECK"
        },
        {
            "name": "12. Legitimate Verified Action Execution",
            "action": test_action_a,
            "origin": "http://localhost:8000",
            "token": valid_token_a,
            "dom": valid_dom_node,
            "expected_success": True,
            "expected_stage": "GATE_3_DOM_EXECUTION"
        }
    ]

    results = []
    passed_count = 0

    for tc in test_cases:
        now_check = now + tc.get("now_offset_ms", 0)
        res = gate.execute_verified_action(tc["action"], tc["origin"], tc["token"], tc["dom"], now_ms=now_check)
        passed = (res["success"] == tc["expected_success"]) and (res["stage"] == tc["expected_stage"])

        if passed:
            passed_count += 1

        results.append({
            "test_name": tc["name"],
            "passed": passed,
            "result": res
        })

    total = len(test_cases)
    return {
        "suite_name": "ACTION EXECUTION GATE ADVERSARIAL HARDENING SUITE",
        "total_tests": total,
        "passed_tests": passed_count,
        "failed_tests": total - passed_count,
        "success_rate_pct": round((passed_count / total) * 100, 2),
        "results": results
    }

if __name__ == "__main__":
    suite_report = run_action_execution_gate_test_suite()
    print("==================================================")
    print("ACTION EXECUTION GATE HARDENING AUDIT COMPLETE")
    print("==================================================")
    print(json.dumps(suite_report, indent=2))
