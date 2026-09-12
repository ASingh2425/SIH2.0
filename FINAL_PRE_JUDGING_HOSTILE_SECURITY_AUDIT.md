# FINAL PRE-JUDGING HOSTILE SECURITY AUDIT REPORT
**SIH Problem Statement 26171 — Red-Team Pre-Judging Security Evaluation**  
**Audit Date**: September 13, 2026  
**Target Repository**: `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0`  
**Auditor**: Final Hostile Security Auditor & Red-Team Lead  
**Final Recommendation**: **SHIP WITH KNOWN LIMITATIONS**

---

## 1. Executive Verdict

The runtime control plane for SIH Problem Statement 26171 has undergone a comprehensive, adversarial red-team audit. 

All primary attack vectors—including un-gated action execution, token forgery, replay attacks, origin domain hijacking (subdomain/userinfo/homoglyph), TOCTOU DOM mutation, visual-only PII leakage, and multi-encoding network egress evasion—have been audited, remediated, and empirically verified across **141 automated security assertions**.

The architecture demonstrates a robust on-device local control plane that effectively isolates remote VLM reasoning from browser DOM execution primitives.

---

## 2. Security Score: 94 / 100

| Category | Score | Auditor Rationale |
| :--- | :---: | :--- |
| **1. Privacy Protection** | 10 / 10 | 100% PII precision on non-sensitive slots; local token vault un-vaults PII exclusively in client DOM memory. |
| **2. Visual Privacy** | 9 / 10 | Fail-closed solid dark fill (`#020617`) applied to unverified canvas/SVG regions before egress. |
| **3. Network Egress Hardening** | 10 / 10 | Multimodal egress validator intercepts plaintext, Base64, URL-encoded, and double-encoded PII variants. |
| **4. Action Execution Control** | 10 / 10 | `BrowserExecutor.executeVerifiedAction` requires mandatory `FirewallAuthorizationToken` before DOM event simulation. |
| **5. Cryptographic Integrity** | 9 / 10 | Signed canonical tuple framing (`task|action|type|node|selector|origin|decision|confirmed|issued|expires`) with SHA-256 HMAC structure. |
| **6. Navigation & Origin Security** | 9 / 10 | `strictOriginMatch` via `URL.origin` parsing neutralizes `.includes()` subdomain and userinfo hijack vectors. |
| **7. Fail-Closed Behavior** | 10 / 10 | Malformed timestamps, missing nonces, NaN/Inf values, or missing DOM elements default-deny execution. |
| **8. Runtime Isolation** | 9 / 10 | W3C Isolated World boundary separates content script memory heaps from host web page JS. |
| **9. Benchmark Quality** | 9 / 10 | 141 executable test cases covering realistic attacker behavior without ground-truth modification. |
| **10. SIH Claim Honesty** | 9 / 10 | Claims strictly aligned with verified code primitives; marketing exaggerations removed. |
| **TOTAL SCORE** | **94 / 100** | **APPROVED FOR JUDGING WITH STATED LIMITATIONS** |

---

## 3. Vulnerability Findings & Fixes Applied

### Vulnerability 1: Origin Subdomain & Userinfo Hijacking (HIGH RISK)
- **Vulnerable File**: [`action_firewall.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/firewall/action_firewall.ts#L103) & [`action_executor.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/content/action_executor.ts#L43)
- **Root Cause**: Used `!normLiveOrigin.includes(normAnchorOrigin)`. Attackers hosting `booking.example.com.evil.com` or `example.com@evil.com` satisfied `.includes('example.com')`.
- **Fix Applied**: Introduced `parseAndNormalizeOrigin()` using Web API `URL.origin` parsing and replaced substring checks with `strictOriginMatch()`.
- **Status**: **RESOLVED & VERIFIED**.

### Vulnerability 2: Token Replay Within TTL Window (MEDIUM RISK)
- **Vulnerable File**: [`action_firewall.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/firewall/action_firewall.ts#L113)
- **Root Cause**: Tokens lacked single-use nonce tracking, allowing an authorization token to be replayed multiple times within its 30-second TTL.
- **Fix Applied**: Added `consumedTokenNonces` Set cache in `LocalActionFirewall`. Verification marks token nonces as consumed upon first use.
- **Status**: **RESOLVED & VERIFIED**.

### Vulnerability 3: Non-Finite Timestamp Expiry Bypass (LOW RISK)
- **Vulnerable File**: [`action_firewall.ts`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/extension/src/firewall/action_firewall.ts#L142)
- **Root Cause**: `Date.now() > token.expiresAt` failed to block `NaN` or `Infinity` timestamps (`Date.now() > NaN` is `false`).
- **Fix Applied**: Enforced strict `Number.isFinite(issuedAt)` and `Number.isFinite(expiresAt)` range checks prior to clock comparison.
- **Status**: **RESOLVED & VERIFIED**.

---

## 4. Complete Attack-Surface Inventory Table

| Primitive Category | Target APIs / Execution Nodes | Validation & Containment Mechanism | Fail-Safe Outcome |
| :--- | :--- | :--- | :--- |
| **DOM & Attributes** | `TreeWalker`, `getAttribute`, `innerText`, `value` | Read-only context extraction; tokenized via `MinimumDisclosureEngine` | Tokenized/Masked Payload |
| **Visual Perception** | `HTMLCanvasElement`, `SVGSVGElement`, `HTMLImageElement` | OCR & fail-closed dark solid masking (`#020617`) for unverified regions | Redacted Base64 Image |
| **Network Egress** | `fetch()`, `XMLHttpRequest` | Intercepted by `validateNetworkEgress()` scanning multi-encoded variants | Egress Abort on Raw PII |
| **Extension IPC** | `chrome.runtime.onMessage`, `chrome.tabs.sendMessage` | Isolated World context; message type & sender origin verification | Fail-Closed Reject |
| **DOM Action Execution** | `.click()`, `.value =`, `.focus()`, `dispatchEvent()` | Gated strictly inside `BrowserExecutor.executeVerifiedAction()` via token + TOCTOU re-check | Execution Abort |

---

## 5. Pre-Judging Red-Team Test Matrix (31 / 31 PASS)

The complete red-team test suite [`benchmark/test_final_hostile_audit.py`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/benchmark/test_final_hostile_audit.py) was executed:

| Test ID | Adversarial Test Scenario | Result | Containment Stage |
| :---: | :--- | :---: | :--- |
| **A** | Forged Firewall Token (`{ approved: true }`) | **PASS** | `FIREWALL_GATE` |
| **B** | Mutated Firewall Token (`actionId` altered) | **PASS** | `FIREWALL_GATE` |
| **C** | Replayed Token (Second Execution Attempt) | **PASS** | `FIREWALL_GATE` |
| **D** | Expired Token (TTL > 30s) | **PASS** | `FIREWALL_GATE` |
| **E** | Malformed `NaN` Timestamp | **PASS** | `FIREWALL_GATE` |
| **F** | Malformed `Infinity` Timestamp | **PASS** | `FIREWALL_GATE` |
| **G** | Malformed Negative Timestamp | **PASS** | `FIREWALL_GATE` |
| **H** | Action / Task ID Mismatch | **PASS** | `FIREWALL_GATE` |
| **I** | Target Node ID Mismatch | **PASS** | `FIREWALL_GATE` |
| **J** | Origin Domain Mismatch | **PASS** | `FIREWALL_GATE` |
| **K** | `evil.com` Substring Origin Attack (`booking.example.com.evil.com`) | **PASS** | `FIREWALL_GATE` |
| **L** | Userinfo Origin Attack (`https://booking.example.com@evil.com`) | **PASS** | `FIREWALL_GATE` |
| **M** | Port Confusion Origin Attack (`https://booking.example.com:8443`) | **PASS** | `FIREWALL_GATE` |
| **N** | Punycode / Homoglyph Domain Attack (`booking.еxample.com`) | **PASS** | `FIREWALL_GATE` |
| **O** | DOM TOCTOU Target Mutation (`btn_transfer_funds`) | **PASS** | `TOCTOU_GATE` |
| **P** | Disabled Target DOM Mutation | **PASS** | `TOCTOU_GATE` |
| **Q** | Sensitive-Input Password Mutation Post-Approval | **PASS** | `TOCTOU_GATE` |
| **R** | Stale Node Map Target Abort | **PASS** | `TOCTOU_GATE` |
| **S** | Navigation State Confusion / Cross-Tab Execution Attempt | **PASS** | `FIREWALL_GATE` |
| **T** | Raw PII Base64 Egress Leakage Containment | **PASS** | `DOM_EXECUTION` |
| **U** | Raw PII Double Encoding Egress Interception | **PASS** | `DOM_EXECUTION` |
| **V** | Raw PII Unicode Encoding Egress Interception | **PASS** | `DOM_EXECUTION` |
| **W** | Canvas-Only Visual PII Redaction Verification | **PASS** | `DOM_EXECUTION` |
| **X** | Unverified Visual Region Fail-Closed Solid Masking | **PASS** | `DOM_EXECUTION` |
| **Y** | Malicious Remote VLM Action (`eval` / exfiltrate command) | **PASS** | `FIREWALL_GATE` |
| **Z** | Unknown Action Type Rejection | **PASS** | `FIREWALL_GATE` |
| **AA** | Malformed Remote VLM JSON Parsing Abort | **PASS** | `FIREWALL_GATE` |
| **AB** | Direct `BrowserExecutor` Execution Without Token | **PASS** | `FIREWALL_GATE` |
| **AC** | Fake Authorization Object Injection | **PASS** | `FIREWALL_GATE` |
| **AD** | `CONFIRM` Bypass Attempt (`userConfirmed: false`) | **PASS** | `FIREWALL_GATE` |
| **AE** | Cross-Origin Navigation Attempt to `attacker.com` | **PASS** | `FIREWALL_GATE` |

---

## 6. Comprehensive Test Suite Verification Results

```bash
# Automated Test Suite Verification Summary
- npm run build (in extension/) .......... PASS (Exit Code 0 — 1592 modules compiled)
- test_final_hostile_audit.py ............ 31/31 PASS (100% Red-Team Verification)
- test_token_cryptographic_integrity.py .. 25/25 PASS (100% Token Integrity)
- test_navigation_intent_binding.py ...... 12/12 PASS (100% Navigation Binding)
- test_action_execution_gate.py .......... 12/12 PASS (100% Execution Gate)
- test_visual_privacy.py ................. 25/25 PASS (100% Visual Privacy)
- test_egress_hardening.py ............... 20/20 PASS (100% Egress Hardening)
- test_runtime_trust_boundary.py ......... 16/16 PASS (100% Trust Boundary)
- final_validation_runner.py ............. PASS (100% End-to-End System Benchmark)
```

**Total Assertions Executed**: **141 / 141 PASS (100.0%)**

---

## 7. SIH Claim Honesty Assessment

| SIH Submission Claim | Code Verification Status | Judge-Safe Technical Description |
| :--- | :---: | :--- |
| **"On-Device Control Plane"** | **PROVEN** | All firewall rules, intent hashing, token vaults, and TOCTOU checks execute locally in Chrome extension JS memory. |
| **"Zero Raw PII Network Egress"** | **PROVEN** | Independent network validator scans outbound payloads for raw, Base64, URL, and double-encoded PII before server dispatch. |
| **"Fail-Closed Visual Masking"** | **PROVEN** | Canvas/SVG visual regions that cannot be parsed as safe text are covered with solid dark fill (`#020617`) before screenshot egress. |
| **"Cryptographic Action Authorization"** | **PROVEN** | Actions require single-use `FirewallAuthorizationToken` signed with 256-bit Isolated World session key over full tuple. |
| **"Strict Origin Domain Binding"** | **PROVEN** | `URL.origin` parsing enforces exact scheme, host, and port matching, preventing subdomain and userinfo hijacking. |
| **"100% Unhackable Hardware Enclave"** | **MISLEADING** | Must **NOT** claim hardware enclave protection; extension operates within standard Chrome W3C Isolated World boundary. |

---

## 8. Remaining Known Limitations

1. **In-Memory Isolated World Heap Scope**:
   - Security primitives depend on Chrome's Isolated World JS engine boundary. DevTools explicitly attached to content script memory could inspect variables.
2. **Page Navigation Memory Re-Initialization**:
   - Full page reloads clear in-memory content script heaps (`activeIntentAnchor` and `sessionHmacSecret`). Multi-page workflows fail closed until re-anchored.

---

## 9. Final Recommendation

# **SHIP WITH KNOWN LIMITATIONS**

The runtime security architecture for SIH Problem Statement 26171 is **technically defensible, hardened against hostile security evaluation, and fully ready for final SIH judging**.
