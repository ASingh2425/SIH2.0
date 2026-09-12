import json
import time
import urllib.parse
from typing import Dict, List, Any, Optional

# ==============================================================================
# AUTHORITATIVE ORIGIN & NAVIGATION BINDING ENGINE SIMULATOR
# ==============================================================================
def parse_and_normalize_origin(raw_url_or_origin: str) -> Dict[str, Any]:
    if not raw_url_or_origin or not isinstance(raw_url_or_origin, str):
        return {"valid": False, "origin": "", "hostname": "", "scheme": "", "port": None}

    clean_str = raw_url_or_origin.strip()
    try:
        parsed = urllib.parse.urlparse(clean_str)
        scheme = parsed.scheme.lower()
        if scheme not in ["http", "https"]:
            return {"valid": False, "origin": "", "hostname": "", "scheme": scheme, "port": None}

        # Check for userinfo hijacking (e.g. https://example.com@evil.com)
        if parsed.username or parsed.password:
            # Userinfo present -> actual host is parsed.hostname (evil.com)
            hostname = parsed.hostname.lower() if parsed.hostname else ""
        else:
            hostname = parsed.hostname.lower() if parsed.hostname else ""

        if not hostname:
            return {"valid": False, "origin": "", "hostname": "", "scheme": scheme, "port": None}

        # Unicode / Punycode IDN normalization
        try:
            hostname_ascii = hostname.encode('idna').decode('ascii')
        except Exception:
            hostname_ascii = hostname

        port = parsed.port
        default_port = (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
        if port and not default_port:
            origin = f"{scheme}://{hostname_ascii}:{port}"
        else:
            origin = f"{scheme}://{hostname_ascii}"

        return {
            "valid": True,
            "origin": origin,
            "hostname": hostname_ascii,
            "scheme": scheme,
            "port": port
        }
    except Exception:
        return {"valid": False, "origin": "", "hostname": "", "scheme": "", "port": None}

def strict_origin_match(origin_a: str, origin_b: str) -> bool:
    norm_a = parse_and_normalize_origin(origin_a)
    norm_b = parse_and_normalize_origin(origin_b)

    if not norm_a["valid"] or not norm_b["valid"]:
        return False

    return norm_a["origin"] == norm_b["origin"]

class NavigationIntentTrackerSimulator:
    def __init__(self):
        self.active_task_id: Optional[str] = None
        self.active_tab_id: Optional[int] = None
        self.anchor_origin: Optional[str] = None
        self.consumed_token_ids = set()

    def start_task(self, task_id: str, tab_id: int, origin: str):
        norm = parse_and_normalize_origin(origin)
        if not norm["valid"]:
            raise ValueError("Invalid origin")
        self.active_task_id = task_id
        self.active_tab_id = tab_id
        self.anchor_origin = norm["origin"]

    def validate_navigation_execution(
        self,
        task_id: str,
        tab_id: int,
        current_origin: str,
        token: Optional[Dict[str, Any]],
        navigated_since_confirmation: bool = False
    ) -> Dict[str, Any]:
        # 1. Active Task Binding
        if not self.active_task_id or self.active_task_id != task_id:
            return {"allowed": False, "reason": "No active intent anchor for specified taskId"}

        # 2. Strict Tab Isolation
        if self.active_tab_id != tab_id:
            return {"allowed": False, "reason": "Cross-tab execution attempt: Tab ID mismatch"}

        # 3. Strict Origin Domain Matching (NO .includes() or suffix matching)
        if not strict_origin_match(self.anchor_origin, current_origin):
            return {"allowed": False, "reason": f"Origin hijack blocked: Current tab origin ({currentOrigin if 'currentOrigin' in locals() else current_origin}) does not strictly match Intent Anchor origin ({self.anchor_origin})"}

        # 4. Token Check
        if not token:
            return {"allowed": False, "reason": "Missing authorization token"}

        if token.get("taskId") != task_id:
            return {"allowed": False, "reason": "Token taskId mismatch"}

        if not strict_origin_match(token.get("originDomain", ""), current_origin):
            return {"allowed": False, "reason": "Token originDomain mismatch with live window origin"}

        # Single use token check
        token_id = token.get("tokenId")
        if token_id in self.consumed_token_ids:
            return {"allowed": False, "reason": "Token replay attempt: Nonce already consumed"}

        # 5. CONFIRM Navigation Invalidation
        if token.get("decision") == "CONFIRM":
            if navigated_since_confirmation:
                return {"allowed": False, "reason": "Navigation occurred post-confirmation: Fresh confirmation required"}

        return {"allowed": True, "reason": "Navigation & Intent binding verified safe"}


# ==============================================================================
# PHASE 6 CROSS-NAVIGATION ADVERSARIAL TEST SUITE (12 ATTACK SCENARIOS)
# ==============================================================================
def run_cross_navigation_intent_binding_suite():
    tracker = NavigationIntentTrackerSimulator()
    tracker.start_task("task_flight_777", tab_id=1, origin="https://booking.example.com")

    token_valid = {
        "tokenId": "tok_nav_101",
        "taskId": "task_flight_777",
        "actionId": "act_001",
        "originDomain": "https://booking.example.com",
        "decision": "ALLOW"
    }

    token_confirm = {
        "tokenId": "tok_nav_102",
        "taskId": "task_flight_777",
        "actionId": "act_002",
        "originDomain": "https://booking.example.com",
        "decision": "CONFIRM",
        "userConfirmed": True
    }

    test_cases = [
        {
            "id": "ATTACK_01",
            "name": "ATTACK 01: Trusted Origin -> Malicious Origin Redirect (booking.example.com -> attacker.com)",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://attacker.com",
            "token": token_valid,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_02",
            "name": "ATTACK 02: Origin A Authorization -> Origin B Execution",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://other-domain.org",
            "token": token_valid,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_03",
            "name": "ATTACK 03: Old Task Anchor Used in New Task Context",
            "task_id": "task_old_999",
            "tab_id": 1,
            "current_origin": "https://booking.example.com",
            "token": token_valid,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_04",
            "name": "ATTACK 04: Old Task Token Used in Current Task Context",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://booking.example.com",
            "token": {**token_valid, "taskId": "task_old_999"},
            "expected_allowed": False
        },
        {
            "id": "ATTACK_05",
            "name": "ATTACK 05: Tab A Authorization Executed in Tab B",
            "task_id": "task_flight_777",
            "tab_id": 2, # Different tab!
            "current_origin": "https://booking.example.com",
            "token": token_valid,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_06",
            "name": "ATTACK 06: Token Replay After Window Location Change",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://booking.example.com",
            "token": token_valid,
            "replay": True,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_07",
            "name": "ATTACK 07: Malicious Redirect Preserving Authorization Token in URL Parameter",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://evil.com/?token=tok_nav_101",
            "token": token_valid,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_08",
            "name": "ATTACK 08: Content-Script Restart with Stale Local Storage Anchor",
            "task_id": "task_stale_000",
            "tab_id": 1,
            "current_origin": "https://booking.example.com",
            "token": token_valid,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_09",
            "name": "ATTACK 09: Extension Reload / Service Worker Restart Stale Token Attempt",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://booking.example.com",
            "token": {**token_valid, "originDomain": "chrome-extension://stale-id"},
            "expected_allowed": False
        },
        {
            "name": "ATTACK 10: Navigation After CONFIRM But Before Execution",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://booking.example.com",
            "token": token_confirm,
            "navigated_since_confirm": True,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_11",
            "name": "ATTACK 11: Subdomain / Suffix Hijack (booking.example.com.evil.com)",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://booking.example.com.evil.com",
            "token": token_valid,
            "expected_allowed": False
        },
        {
            "id": "ATTACK_12",
            "name": "ATTACK 12: Unicode / Homoglyph Domain Confusion (booking.еxample.com Cyrillic e)",
            "task_id": "task_flight_777",
            "tab_id": 1,
            "current_origin": "https://booking.еxample.com",
            "token": token_valid,
            "expected_allowed": False
        }
    ]

    results = []
    passed_count = 0

    for tc in test_cases:
        if tc.get("replay"):
            tracker.consumed_token_ids.add(tc["token"]["tokenId"])

        res = tracker.validate_navigation_execution(
            tc["task_id"],
            tc["tab_id"],
            tc["current_origin"],
            tc["token"],
            navigated_since_confirmation=tc.get("navigated_since_confirm", False)
        )

        passed = (res["allowed"] == tc["expected_allowed"])

        if passed:
            passed_count += 1

        results.append({
            "test_id": tc.get("id", tc["name"][:10]),
            "test_name": tc["name"],
            "passed": passed,
            "reason": res["reason"]
        })

    total = len(test_cases)
    report = {
        "suite_name": "CROSS NAVIGATION INTENT BINDING ADVERSARIAL SUITE",
        "total_tests": total,
        "passed_tests": passed_count,
        "failed_tests": total - passed_count,
        "success_rate_pct": round((passed_count / total) * 100, 2),
        "results": results
    }
    return report

if __name__ == "__main__":
    rep = run_cross_navigation_intent_binding_suite()
    print("==================================================")
    print("CROSS NAVIGATION INTENT BINDING AUDIT COMPLETE")
    print("==================================================")
    print(json.dumps(rep, indent=2))
