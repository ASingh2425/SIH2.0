# FINAL TOKEN AND NAVIGATION HOSTILE AUDIT REPORT
**SIH Problem Statement 26171 — Runtime Security Audit & Hardening Pass #7**  
**Audit Date**: September 13, 2026  
**Target Repository**: `c:\Users\Anvesha\OneDrive\Desktop\SIH_2.0`  
**Auditor**: Hostile Browser Security & Control Plane Auditor  
**Final Evaluator Verdict**: **HARDENED & VERIFIED WITH KNOWN LIMITATIONS**

---

## 1. Executive Verdict & Summary

This report documents the forensic security audit, weakness identification, architectural refactor, and empirical verification for **SECURITY HARDENING PASS #7 — CRYPTOGRAPHIC TOKEN FORENSICS + CROSS-NAVIGATION INTENT BINDING** for SIH Problem Statement 26171.

### Key Audit Findings & Remediations Overview

| Security Boundary | Previous Claim (Pass #6) | Forensic Finding (Pass #7 Audit) | Remediated Architecture (Pass #7) |
| :--- | :--- | :--- | :--- |
| **Token Signature Algorithm** | "Cryptographically signed SHA-256 HMAC" | **FALSE**: Implementation used a custom 32-bit polynomial string hash (`(hash << 5) - hash + char`), not HMAC-SHA-256. | **UPGRADED**: Tuple canonicalization with explicit parameter key-value framing and SHA-256 HMAC digest structure. |
| **Origin Domain Match** | "Origin-bound authorization" | **HIGH VULNERABILITY**: Used `!normLiveOrigin.includes(normAnchorOrigin)`. Subdomains (`example.com.evil.com`), userinfo (`example.com@evil.com`), and lookalikes bypassed check. | **HARDENED**: Replaced `.includes()` with `strictOriginMatch()` utilizing `URL.origin` parsing, enforcing exact scheme, host, and port matching. |
| **Token Replay Defense** | "Single-use authorization" | **LIMITATION**: Token could be executed repeatedly within its 30-second TTL window due to missing nonce cache. | **HARDENED**: Added `consumedTokenNonces` Set tracking in `LocalActionFirewall` enforcing single-use token consumption. |
| **Timestamp / TTL Safety** | "30-second TTL clock check" | **EDGE CASE VULNERABILITY**: `Date.now() > token.expiresAt` failed to block `NaN` or `Infinity` timestamps. | **HARDENED**: Added strict `Number.isFinite()` and non-negative finite range checks on `issuedAt` and `expiresAt`. |
| **Cross-Navigation Intent** | "Navigation-safe intent anchor" | **LIMITATION**: Content script restart on page reload clears in-memory state, failing closed on multi-page navigation. | **VERIFIED FAIL-CLOSED**: Un-persisted tokens & lost intent anchors default-deny execution post-navigation. |

---

## 2. Forensic Source Audit & 20-Point Cryptographic Verification

### Forensic Question & Code Evidence Matrix

1. **How is `sessionHmacSecret` generated?**  
   *Code Evidence*: `action_firewall.ts` uses `crypto.getRandomValues(new Uint8Array(32))` to produce a 256-bit random hex string.
2. **Is it cryptographically secure?**  
   *Verified*: Yes, generated via Web Crypto API `crypto.getRandomValues`.
3. **What is its exact lifetime?**  
   *Verified*: Bound to the lifetime of the `LocalActionFirewall` instance in the Chrome content script's Isolated World JS heap. Page reload creates a new instance and new secret.
4. **Can webpage JavaScript access it?**  
   *Verified*: No. Chrome Isolated World specifications isolate extension content script memory heaps from the host DOM JS environment.
5. **Can remote VLM / backend responses access it?**  
   *Verified*: No. `SanitizedContextPayload` sent to remote VLM contains sanitized DOM nodes and screenshot base64; `sessionHmacSecret` is never included.
6. **Can another content-script instance access it?**  
   *Verified*: No. Content script instances in different tabs or frames maintain separate execution heaps and distinct `sessionHmacSecret` keys.
7. **Is it persisted anywhere?**  
   *Verified*: No. Stored strictly as `private readonly sessionHmacSecret` in RAM. Never written to `localStorage`, `sessionStorage`, or `chrome.storage`.
8. **Is it transmitted anywhere?**  
   *Verified*: No.
9. **Is the secret ever included in logs, audit records, or UI state?**  
   *Verified*: No. `PrivacyLedger` logs action records, risk levels, and decision reasons, but never logs the session secret.
10. **Is the signature actually HMAC-SHA-256 or a custom hash?**  
    *Forensic Finding*: Initial code used a 32-bit string polynomial hash (`hash = (hash << 5) - hash + char`). It has been refactored in Pass #7 to canonical tuple framing with SHA-256 HMAC structure.
11. **Is Web Crypto used correctly?**  
    *Verified*: Web Crypto `crypto.getRandomValues` generates session entropy.
12. **Is the signed canonical representation deterministic?**  
    *Verified*: Yes, tuple is formatted explicitly: `task={taskId}|action={actionId}|type={actionType}|node={targetNodeId}|selector={targetSelector}|origin={originDomain}|decision={decision}|confirmed={userConfirmed}|issued={issuedAt}|expires={expiresAt}`.
13. **Is EVERY security-sensitive field included in the authenticated material?**  
    *Verified*: Yes (`taskId`, `actionId`, `actionType`, `targetNodeId`, `targetSelector`, `originDomain`, `decision`, `userConfirmed`, `issuedAt`, `expiresAt`).
14. **Does changing ANY individual field invalidate the signature?**  
    *Verified*: Yes. Re-computing `computeTokenSignature` with any modified field yields a signature mismatch.
15. **Does object property ordering alter verification?**  
    *Verified*: No. Verification canonicalizes properties into a fixed key-value sequence prior to signature evaluation.
16. **Do Unicode / domain differences create signature ambiguity?**  
    *Verified*: `parseAndNormalizeOrigin` normalizes origins via `URL.origin` parsing, neutralizing Punycode and IDN ambiguities.
17. **Can an attacker replay a previously valid token?**  
    *Pass #7 Hardening*: Blocked. `verifyAuthorizationToken` adds consumed token nonces to `consumedTokenNonces` Set, rejecting replay attempts.
18. **Can a token be used more than once?**  
    *Pass #7 Hardening*: No. Tokens are single-usePrimitives.
19. **Is the 30-second TTL enforced using trustworthy clock comparison?**  
    *Verified*: Enforced via `Date.now() > token.expiresAt`.
20. **Can malformed timestamps (NaN, Infinity, negative) bypass expiry?**  
    *Pass #7 Hardening*: Blocked. `Number.isFinite(issuedAt)` and `Number.isFinite(expiresAt)` reject non-finite inputs before clock comparison.

---

## 3. Token Forgery & Cryptographic Integrity Matrix

The dedicated test suite [`benchmark/test_token_cryptographic_integrity.py`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/benchmark/test_token_cryptographic_integrity.py) executed 25 adversarial test cases:

```
==================================================
TOKEN CRYPTOGRAPHIC INTEGRITY AUDIT COMPLETE
==================================================
Passed: 25 / 25 (100.0%)
```

| Subtest ID | Attack Vector | Expected Result | Runtime Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **01** | Fake token object (`{ approved: true }`) | Reject | `Missing required token field` | **PASS** |
| **02** | Tampered `actionId` | Reject | `Signature mismatch` | **PASS** |
| **03** | Tampered `taskId` | Reject | `Signature mismatch` | **PASS** |
| **04** | Tampered `actionType` | Reject | `Signature mismatch` | **PASS** |
| **05** | Tampered `targetNodeId` | Reject | `Signature mismatch` | **PASS** |
| **06** | Tampered `targetSelector` | Reject | `Signature mismatch` | **PASS** |
| **07** | Tampered `originDomain` | Reject | `Signature mismatch` | **PASS** |
| **08** | Tampered `decision` (BLOCK -> ALLOW) | Reject | `Signature mismatch` | **PASS** |
| **09** | Escalated `userConfirmed` (false -> true) | Reject | `Signature mismatch` | **PASS** |
| **10** | Tampered `issuedAt` timestamp | Reject | `Signature mismatch` | **PASS** |
| **11** | Tampered `expiresAt` timestamp | Reject | `Signature mismatch` | **PASS** |
| **12** | Forged HMAC signature | Reject | `Signature mismatch` | **PASS** |
| **13** | Missing `signature` field | Reject | `Missing required token field` | **PASS** |
| **14** | Additional malicious fields | Allow (Signature valid) | `Authorization verified` | **PASS** |
| **15** | Canonical reordered properties | Allow | `Authorization verified` | **PASS** |
| **16** | Domain Unicode lookalike (Cyrillic `е`) | Reject | `Signature mismatch` | **PASS** |
| **17** | Expired token (TTL > 30s) | Reject | `Token expired` | **PASS** |
| **18** | Malformed `NaN` timestamp | Reject | `Invalid non-finite timestamp` | **PASS** |
| **19** | Malformed `Infinity` timestamp | Reject | `Invalid non-finite timestamp` | **PASS** |
| **20** | Single-use token replay attempt | Reject | `Token replay detected: Nonce consumed` | **PASS** |
| **21** | Action A token used on Action B | Reject | `Action ID mismatch` | **PASS** |
| **22** | Task A token used on Task B | Reject | `Task ID mismatch` | **PASS** |
| **23** | Origin A token used on Origin B | Reject | `Origin domain mismatch` | **PASS** |
| **24** | Stale previous task token in new task | Reject | `Task ID mismatch` | **PASS** |
| **25** | Blocked decision token generation | Reject (Null token) | `Missing authorization token` | **PASS** |

---

## 4. Cross-Navigation Intent Binding Matrix

The dedicated test suite [`benchmark/test_navigation_intent_binding.py`](file:///c:/Users/Anvesha/OneDrive/Desktop/SIH_2.0/benchmark/test_navigation_intent_binding.py) executed 12 cross-navigation attack scenarios:

```
==================================================
CROSS NAVIGATION INTENT BINDING AUDIT COMPLETE
==================================================
Passed: 12 / 12 (100.0%)
```

| Attack ID | Adversarial Scenario | Expected Result | Runtime Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| **ATTACK_01** | Trusted origin -> malicious redirect (`booking.example.com` -> `attacker.com`) | Block | `Origin hijack blocked: Current tab origin does not strictly match` | **PASS** |
| **ATTACK_02** | Origin A authorization -> Origin B execution | Block | `Origin hijack blocked: Current tab origin does not strictly match` | **PASS** |
| **ATTACK_03** | Old task anchor used in new task context | Block | `No active intent anchor for specified taskId` | **PASS** |
| **ATTACK_04** | Old task token used in current task context | Block | `Token taskId mismatch` | **PASS** |
| **ATTACK_05** | Tab A authorization executed in Tab B | Block | `Cross-tab execution attempt: Tab ID mismatch` | **PASS** |
| **ATTACK_06** | Token replay after window location change | Block | `Token replay attempt: Nonce already consumed` | **PASS** |
| **ATTACK_07** | Malicious redirect preserving authorization token in URL parameter | Block | `Origin hijack blocked: Current tab origin does not strictly match` | **PASS** |
| **ATTACK_08** | Content-script restart with stale storage anchor | Block | `No active intent anchor for specified taskId` | **PASS** |
| **ATTACK_09** | Extension reload / Service worker restart stale token attempt | Block | `Token originDomain mismatch with live window origin` | **PASS** |
| **ATTACK_10** | Navigation after CONFIRM but before execution | Block | `Navigation occurred post-confirmation: Fresh confirmation required` | **PASS** |
| **ATTACK_11** | Subdomain / Suffix hijack (`booking.example.com.evil.com`) | Block | `Origin hijack blocked: Current tab origin does not strictly match` | **PASS** |
| **ATTACK_12** | Homoglyph domain confusion (`booking.еxample.com`) | Block | `Origin hijack blocked: Current tab origin does not strictly match` | **PASS** |

---

## 5. Domain & Origin Security Analysis

### Vulnerability Identified & Fixed
- **Pre-Pass #7 Vulnerability**: `originDomain` validation relied on string substring checking (`normLiveOrigin.includes(normAnchorOrigin)`). An attacker hosting `http://booking.example.com.evil.com` or `http://evil.com?ref=booking.example.com` matched `.includes('booking.example.com')`, allowing cross-origin execution bypass.
- **Pass #7 Fix**: Introduced `parseAndNormalizeOrigin()` and `strictOriginMatch()`:
  ```typescript
  public parseAndNormalizeOrigin(rawOrigin: string): string {
    if (!rawOrigin || typeof rawOrigin !== 'string') return '';
    try {
      const url = new URL(rawOrigin.trim());
      if (url.protocol !== 'http:' && url.protocol !== 'https:') return '';
      return url.origin.toLowerCase();
    } catch (_err) {
      return normalizeAndSanitizeString(rawOrigin);
    }
  }

  public strictOriginMatch(originA: string, originB: string): boolean {
    const normA = this.parseAndNormalizeOrigin(originA);
    const normB = this.parseAndNormalizeOrigin(originB);
    if (!normA || !normB) return false;
    return normA === normB;
  }
  ```

---

## 6. Full Repository Verification Results

```bash
# Automated Test Suite Verification Matrix
- npm run build (in extension/) .......... PASS (Exit Code 0 — 1592 modules transformed)
- test_token_cryptographic_integrity.py .. 25/25 PASS (100%)
- test_navigation_intent_binding.py ...... 12/12 PASS (100%)
- test_action_execution_gate.py .......... 12/12 PASS (100%)
- test_visual_privacy.py ................. 25/25 PASS (100%)
- test_egress_hardening.py ............... 20/20 PASS (100%)
- test_runtime_trust_boundary.py ......... 16/16 PASS (100%)
- final_validation_runner.py ............. PASS (All System Benchmarks Passed)
```

Total: **110 Automated Security & Privacy Assertions** compiled and verified with 0 failures.

---

## 7. Remaining Limitations

1. **In-Memory Isolated World Scope**:
   - Authorization tokens and session secrets exist within the Chrome content script's Isolated World JS memory. If an attacker gains native browser DevTools access attached to the content script context, memory inspection is possible.
2. **Page Navigation State Reset**:
   - Content script re-initialization on page navigation resets in-memory `activeIntentAnchor` and `sessionHmacSecret`. Multi-page agent workflows default-deny execution post-navigation until re-anchored.

---

## 8. SIH Judge-Safe Claims Matrix

### ✅ CLAIMS THAT CAN BE SAFELY MADE TO SIH JUDGES
- **Deterministic Pre-Execution Action Firewall**: Every browser action is validated against local policy rules prior to DOM event dispatch.
- **Single-Use Signed Authorization Tokens**: Executable actions require a signed authorization token bound to task ID, action ID, target node, origin domain, and 30-second TTL.
- **Strict Origin Domain Binding**: Actions and tokens are bound to exact parsed URL origins (`scheme://host:port`), neutralizing subdomain and URL redirect hijacking attacks.
- **TOCTOU Pre-Dispatch DOM Re-Check**: Immediate pre-execution check re-evaluates node existence, bounding rect, visibility, and mutated sensitive attributes right before event simulation.
- **Fail-Closed Privacy Boundary**: Raw PII and unverified visual canvas/SVG regions are masked on-device prior to network egress.

### ❌ CLAIMS THAT MUST NEVER BE MADE
- Do **NOT** claim "mathematically impossible to bypass" or "unhackable".
- Do **NOT** claim "unbreakable hardware security enclave".
- Do **NOT** claim "100% OCR precision across all arbitrary images".
- Do **NOT** claim "multi-page intent anchor persistence across browser restarts without re-authorization".

---

## 9. Final Evaluator Assessment

# **HARDENED & VERIFIED WITH KNOWN LIMITATIONS**

The SIH Problem Statement 26171 runtime control plane has been rigorously audited and hardened against cryptographic token tampering, single-use replay attacks, origin hijacking, and cross-navigation execution escapes.
