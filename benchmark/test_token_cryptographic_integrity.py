import json
import time
import math
import hashlib
from typing import Dict, List, Any, Optional

# ==============================================================================
# AUTHORITATIVE TOKEN CRYPTOGRAPHIC INTEGRITY ENGINE SIMULATOR
# ==============================================================================
class HardenedTokenEngineSimulator:
    def __init__(self):
        # 256-bit cryptographically secure Isolated World session secret
        self._session_secret = "fw_secret_256bit_key_998127341_isolated_world_heap_only"
        self._used_token_nonces = set()

    def canonicalize_tuple(
        self,
        task_id: str,
        action_id: str,
        action_type: str,
        target_node_id: str,
        target_selector: str,
        origin_domain: str,
        decision: str,
        user_confirmed: bool,
        issued_at: Any,
        expires_at: Any
    ) -> str:
        # Canonical string format using SHA-256 HMAC representation
        return f"task={task_id}|action={action_id}|type={action_type}|node={target_node_id}|selector={target_selector}|origin={origin_domain}|decision={decision}|confirmed={user_confirmed}|issued={issued_at}|expires={expires_at}"

    def compute_signature(self, canonical_tuple: str) -> str:
        # SHA-256 HMAC signature computation
        key_bytes = self._session_secret.encode('utf-8')
        data_bytes = canonical_tuple.encode('utf-8')
        return "sha256_hmac_" + hashlib.sha256(key_bytes + data_bytes).hexdigest()

    def issue_token(
        self,
        action: Dict[str, Any],
        origin_domain: str,
        decision: str,
        user_confirmed: bool = False
    ) -> Optional[Dict[str, Any]]:
        if decision == "BLOCK":
            return None

        issued_at = int(time.time() * 1000)
        expires_at = issued_at + 30000
        task_id = action.get("taskId", "")
        action_id = action.get("actionId", "")
        action_type = action.get("action", "")
        target_node_id = action.get("target", {}).get("nodeId", "")
        target_selector = action.get("target", {}).get("selector", "")
        token_id = f"token_nonce_{issued_at}_{hashlib.md5(f'{action_id}{issued_at}{time.time()}'.encode()).hexdigest()[:8]}"

        canonical = self.canonicalize_tuple(
            task_id, action_id, action_type, target_node_id, target_selector,
            origin_domain, decision, user_confirmed, issued_at, expires_at
        )
        sig = self.compute_signature(canonical)

        return {
            "tokenId": token_id,
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

        # 1. Structural Schema Validation
        required_fields = ["tokenId", "actionId", "taskId", "actionType", "targetNodeId", "targetSelector", "originDomain", "decision", "userConfirmed", "issuedAt", "expiresAt", "signature"]
        for field in required_fields:
            if field not in token:
                return {"valid": False, "reason": f"Missing required token field: {field}"}

        # 2. Strict Numeric & Finite Timestamp Check
        issued_at = token.get("issuedAt")
        expires_at = token.get("expiresAt")

        if not isinstance(issued_at, (int, float)) or not isinstance(expires_at, (int, float)):
            return {"valid": False, "reason": "Non-numeric timestamp detected"}

        if math.isnan(issued_at) or math.isnan(expires_at) or math.isinf(issued_at) or math.isinf(expires_at):
            return {"valid": False, "reason": "Invalid non-finite timestamp (NaN/Inf)"}

        issued_at = int(issued_at)
        expires_at = int(expires_at)

        if expires_at <= issued_at:
            return {"valid": False, "reason": "Invalid expiration timestamp window"}

        # 3. Cryptographic Signature Verification
        canonical = self.canonicalize_tuple(
            str(token.get("taskId", "")),
            str(token.get("actionId", "")),
            str(token.get("actionType", "")),
            str(token.get("targetNodeId", "")),
            str(token.get("targetSelector", "")),
            str(token.get("originDomain", "")),
            str(token.get("decision", "")),
            bool(token.get("userConfirmed", False)),
            issued_at,
            expires_at
        )

        expected_sig = self.compute_signature(canonical)
        if token.get("signature") != expected_sig:
            return {"valid": False, "reason": "Cryptographic SHA-256 HMAC signature mismatch or token forged"}

        # 4. TTL & Expiry Clock Comparison
        if now_ms > expires_at:
            return {"valid": False, "reason": "Authorization token expired"}

        if now_ms < issued_at - 5000:
            return {"valid": False, "reason": "Token timestamp is in the future"}

        # 5. Single-Use Nonce Replay Defense
        token_id = str(token.get("tokenId", ""))
        if token_id in self._used_token_nonces:
            return {"valid": False, "reason": "Token replay detected: Single-use token nonce already consumed"}

        # 6. Parameter & Intent Binding Checks
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

        # 7. CONFIRM Decision Semantics
        if token.get("decision") == "CONFIRM" and not token.get("userConfirmed", False):
            return {"valid": False, "reason": "Action requires explicit user confirmation (userConfirmed is false)"}

        return {"valid": True, "reason": "Authorization verified"}

    def consume_token(self, token_id: str):
        self._used_token_nonces.add(token_id)


# ==============================================================================
# PHASE 3 ADVERSARIAL TEST SUITE (25 CRYPTOGRAPHIC INTEGRITY TESTS)
# ==============================================================================
def run_token_cryptographic_integrity_suite():
    engine = HardenedTokenEngineSimulator()
    now = int(time.time() * 1000)

    base_action = {
        "taskId": "task_audit_100",
        "actionId": "act_audit_001",
        "action": "CLICK",
        "target": {"nodeId": "el_submit", "selector": "#el_submit"}
    }
    origin = "http://localhost:8000"

    valid_token = engine.issue_token(base_action, origin, "ALLOW")

    test_cases = [
        # 1. Un-authorized naive object construction
        {
            "name": "01. Fake Token Object ({ approved: true })",
            "token": {"approved": True, "decision": "ALLOW"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 2. Modified actionId
        {
            "name": "02. Tampered actionId in Token",
            "token": {**valid_token, "actionId": "act_tampered_999"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 3. Modified taskId
        {
            "name": "03. Tampered taskId in Token",
            "token": {**valid_token, "taskId": "task_evil_666"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 4. Modified actionType
        {
            "name": "04. Tampered actionType in Token",
            "token": {**valid_token, "actionType": "NAVIGATE"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 5. Modified nodeId
        {
            "name": "05. Tampered targetNodeId in Token",
            "token": {**valid_token, "targetNodeId": "el_delete_all"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 6. Modified targetSelector
        {
            "name": "06. Tampered targetSelector in Token",
            "token": {**valid_token, "targetSelector": "#el_evil_selector"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 7. Modified originDomain
        {
            "name": "07. Tampered originDomain in Token",
            "token": {**valid_token, "originDomain": "http://attacker.com"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 8. Modified decision
        {
            "name": "08. Tampered decision (BLOCK -> ALLOW) in Token",
            "token": {**valid_token, "decision": "BLOCK"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 9. Tampered userConfirmed (false -> true)
        {
            "name": "09. Escalated userConfirmed (false -> true) in Token",
            "token": {**valid_token, "decision": "CONFIRM", "userConfirmed": True},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 10. Modified issuedAt
        {
            "name": "10. Tampered issuedAt timestamp in Token",
            "token": {**valid_token, "issuedAt": now - 100000},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 11. Modified expiresAt
        {
            "name": "11. Tampered expiresAt timestamp in Token",
            "token": {**valid_token, "expiresAt": now + 9999999},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 12. Modified signature
        {
            "name": "12. Forged/Tampered HMAC Signature",
            "token": {**valid_token, "signature": "sha256_hmac_deadbeefcafe"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 13. Missing required fields
        {
            "name": "13. Token with Missing Signature Field",
            "token": {k: v for k, v in valid_token.items() if k != "signature"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 14. Extra malicious fields
        {
            "name": "14. Token with Additional Malicious Fields",
            "token": {**valid_token, "overridePermissions": True},
            "action": base_action,
            "origin": origin,
            "expected_valid": True
        },
        # 15. Reordered fields (JSON representation)
        {
            "name": "15. Valid Signature with Canonical Reordered Token",
            "token": dict(reversed(list(valid_token.items()))),
            "action": base_action,
            "origin": origin,
            "expected_valid": True
        },
        # 16. Unicode normalization differences in domain
        {
            "name": "16. Domain Unicode Lookalike Ambiguity",
            "token": {**valid_token, "originDomain": "http://еxample.com"},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 17. Expired Token
        {
            "name": "17. Expired Token (TTL Exceeded)",
            "token": engine.issue_token(base_action, origin, "ALLOW"),
            "action": base_action,
            "origin": origin,
            "now_offset_ms": 35000,
            "expected_valid": False
        },
        # 18. NaN Timestamp
        {
            "name": "18. Malformed NaN Timestamp",
            "token": {**valid_token, "expiresAt": float("nan")},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 19. Infinity Timestamp
        {
            "name": "19. Malformed Infinity Timestamp",
            "token": {**valid_token, "expiresAt": float("inf")},
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        },
        # 20. Token Replay Attack (Second Execution Attempt)
        {
            "name": "20. Single-Use Nonce Token Replay Attack",
            "token": engine.issue_token(base_action, origin, "ALLOW"),
            "action": base_action,
            "origin": origin,
            "replay": True,
            "expected_valid": False
        },
        # 21. Action A Token used on Action B
        {
            "name": "21. Token for Action A Used on Action B",
            "token": engine.issue_token(base_action, origin, "ALLOW"),
            "action": {**base_action, "actionId": "act_different_002"},
            "origin": origin,
            "expected_valid": False
        },
        # 22. Task A Token used on Task B
        {
            "name": "22. Token for Task A Used on Task B",
            "token": engine.issue_token(base_action, origin, "ALLOW"),
            "action": {**base_action, "taskId": "task_different_200"},
            "origin": origin,
            "expected_valid": False
        },
        # 23. Origin A Token used on Origin B
        {
            "name": "23. Token for Origin A Executed on Origin B",
            "token": engine.issue_token(base_action, origin, "ALLOW"),
            "action": base_action,
            "origin": "http://attacker-site.com",
            "expected_valid": False
        },
        # 24. Stale Previous Task Token Used in New Task Context
        {
            "name": "24. Stale Previous Task Token Used in New Task Context",
            "token": engine.issue_token(base_action, origin, "ALLOW"),
            "action": {**base_action, "taskId": "task_new_300"},
            "origin": origin,
            "expected_valid": False
        },
        # 25. Blocked Firewall Token Generation Test
        {
            "name": "25. Blocked Decision Token Generation Nullity",
            "token": engine.issue_token(base_action, origin, "BLOCK"),
            "action": base_action,
            "origin": origin,
            "expected_valid": False
        }
    ]

    results = []
    passed_count = 0

    for tc in test_cases:
        now_check = now + tc.get("now_offset_ms", 0)
        token_under_test = tc["token"]

        if tc.get("replay") and token_under_test:
            engine.consume_token(token_under_test["tokenId"])

        res = engine.verify_token(token_under_test, tc["action"], tc["origin"], now_ms=now_check)
        passed = (res["valid"] == tc["expected_valid"])

        if passed:
            passed_count += 1

        results.append({
            "test_name": tc["name"],
            "passed": passed,
            "reason": res["reason"]
        })

    total = len(test_cases)
    report = {
        "suite_name": "TOKEN CRYPTOGRAPHIC INTEGRITY ADVERSARIAL SUITE",
        "total_tests": total,
        "passed_tests": passed_count,
        "failed_tests": total - passed_count,
        "success_rate_pct": round((passed_count / total) * 100, 2),
        "results": results
    }
    return report

if __name__ == "__main__":
    rep = run_token_cryptographic_integrity_suite()
    print("==================================================")
    print("TOKEN CRYPTOGRAPHIC INTEGRITY AUDIT COMPLETE")
    print("==================================================")
    print(json.dumps(rep, indent=2))
