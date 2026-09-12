import json
import base64
import urllib.parse
import re

# Mirror implementation of extractAllStringVariants for Python test harness verification
def extract_all_string_variants(data, depth=0, max_depth=8, visited=None):
    if visited is None:
        visited = set()

    if depth > max_depth or data is None:
        return []

    if isinstance(data, (dict, list)):
        obj_id = id(data)
        if obj_id in visited:
            return []
        visited.add(obj_id)

    results = []

    if isinstance(data, str):
        results.append(data)

        current = data
        for layer in range(2):
            decoded = current
            changed = False

            # 1. URL / Percent Decoding
            if '%' in decoded:
                try:
                    u_dec = urllib.parse.unquote(decoded)
                    if u_dec != decoded and len(u_dec) > 0:
                        decoded = u_dec
                        changed = True
                        results.append(decoded)
                except Exception:
                    pass

            # 2. Unicode Escape Decoding
            if '\\u' in decoded:
                try:
                    u_unesc = decoded.encode().decode('unicode-escape')
                    if u_unesc != decoded and len(u_unesc) > 0:
                        decoded = u_unesc
                        changed = True
                        results.append(decoded)
                except Exception:
                    pass

            # 3. Base64 Decoding
            clean_b64 = decoded.strip().replace(' ', '')
            if 4 <= len(clean_b64) <= 8192 and re.match(r'^[A-Za-z0-9+/=_-]+$', clean_b64) and not clean_b64.startswith('data:image/'):
                try:
                    b64_std = clean_b64.replace('-', '+').replace('_', '/')
                    while len(b64_std) % 4 != 0:
                        b64_std += '='
                    raw_bytes = base64.b64decode(b64_std, validate=True)
                    b64_dec = raw_bytes.decode('utf-8', errors='ignore')
                    if re.search(r'[\x20-\x7E]{3,}', b64_dec) and b64_dec != decoded:
                        decoded = b64_dec
                        changed = True
                        results.append(decoded)
                except Exception:
                    pass

            if not changed:
                break
            current = decoded

    elif isinstance(data, list):
        for item in data[:500]:
            results.extend(extract_all_string_variants(item, depth + 1, max_depth, visited))

    elif isinstance(data, dict):
        for k, v in list(data.items())[:200]:
            results.append(str(k))
            results.extend(extract_all_string_variants(v, depth + 1, max_depth, visited))

    return results

EGRESS_EMAIL_REGEX = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
EGRESS_CREDIT_CARD_REGEX = re.compile(r'\b(?:\d[ -]*?){13,16}\b')
EGRESS_PASSPORT_REGEX = re.compile(r'\b[A-PR-WYa-pr-wy]\d{7}\b')

def validate_network_egress_test(raw_entities, sanitized_nodes):
    variants = extract_all_string_variants(sanitized_nodes)
    zero_raw_pii_verified = True
    details = []

    sensitive_targets = set()
    for ent in raw_entities:
        if ent.get("treatment") != "KEEP" and ent.get("rawValue") and len(ent["rawValue"].strip()) >= 3:
            val = ent["rawValue"].strip().lower()
            sensitive_targets.add(val)
            try:
                b64_val = base64.b64encode(ent["rawValue"].strip().encode()).decode().lower()
                sensitive_targets.add(b64_val)
            except Exception:
                pass
            try:
                url_val = urllib.parse.quote(ent["rawValue"].strip()).lower()
                sensitive_targets.add(url_val)
            except Exception:
                pass

    for variant in variants:
        var_lower = variant.lower()
        for target in sensitive_targets:
            if target in var_lower:
                is_legit_token = bool(re.match(r'^[A-Z_]+#[A-F0-9]+$', variant, re.IGNORECASE)) or '[REDACTED]' in variant or '••••' in variant
                if not is_legit_token:
                    zero_raw_pii_verified = False
                    details.append(f"DETECTED_TARGET:{target}")

        for match in EGRESS_EMAIL_REGEX.findall(variant):
            for ent in raw_entities:
                if ent.get("treatment") != "KEEP" and ent.get("rawValue") and match.lower() == ent["rawValue"].lower():
                    zero_raw_pii_verified = False
                    details.append(f"DETECTED_EMAIL:{match}")

        for match in EGRESS_CREDIT_CARD_REGEX.findall(variant):
            clean_cc = re.sub(r'\D', '', match)
            if 13 <= len(clean_cc) <= 19:
                for ent in raw_entities:
                    if ent.get("rawValue") and clean_cc == re.sub(r'\D', '', ent["rawValue"]):
                        zero_raw_pii_verified = False
                        details.append(f"DETECTED_CC:{clean_cc}")

    return {
        "zeroRawPIIVerified": zero_raw_pii_verified,
        "details": details
    }

def run_20_adversarial_egress_test_suite():
    raw_entities = [
        {"id": "e1", "type": "NAME", "rawValue": "John Smith", "treatment": "TOKENIZE", "assignedToken": "PERSON#A72F"},
        {"id": "e2", "type": "EMAIL", "rawValue": "john@gmail.com", "treatment": "TOKENIZE", "assignedToken": "EMAIL#B91C"},
        {"id": "e3", "type": "PHONE", "rawValue": "+1-555-0199", "treatment": "TOKENIZE", "assignedToken": "PHONE#C123"},
        {"id": "e4", "type": "CREDIT_CARD", "rawValue": "4111-2222-3333-4444", "treatment": "REMOVE"},
        {"id": "e5", "type": "PASSWORD", "rawValue": "Pass123!", "treatment": "REMOVE"}
    ]

    test_cases = [
        {"id": 1, "name": "Raw Plaintext PII", "payload": [{"text": "John Smith"}], "expected_pass": False},
        {"id": 2, "name": "Raw Email", "payload": [{"text": "john@gmail.com"}], "expected_pass": False},
        {"id": 3, "name": "Raw Phone", "payload": [{"text": "+1-555-0199"}], "expected_pass": False},
        {"id": 4, "name": "Raw Credit Card", "payload": [{"text": "4111-2222-3333-4444"}], "expected_pass": False},
        {"id": 5, "name": "Raw Password Secret", "payload": [{"text": "Pass123!"}], "expected_pass": False},
        {"id": 6, "name": "Base64 Encoded Person Name", "payload": [{"text": "Sm9obiBTbWl0aA=="}], "expected_pass": False},
        {"id": 7, "name": "Base64 Encoded Email", "payload": [{"text": "am9obkBnbWFpbC5jb20="}], "expected_pass": False},
        {"id": 8, "name": "URL Encoded PII", "payload": [{"text": "john%40gmail.com"}], "expected_pass": False},
        {"id": 9, "name": "Unicode Escaped PII", "payload": [{"text": "\\u004a\\u006f\\u0068\\u006e\\u0020\\u0053\\u006d\\u0069\\u0074\\u0068"}], "expected_pass": False},
        {"id": 10, "name": "Double Encoded PII", "payload": [{"text": "%53%6d%39%6f%62%69%42%54%62%57%6c%30%61%41%3d%3d"}], "expected_pass": False},
        {"id": 11, "name": "PII Nested Inside JSON", "payload": [{"text": "{\"user\":\"john@gmail.com\"}"}], "expected_pass": False},
        {"id": 12, "name": "PII Nested Inside Arrays", "payload": [["safe_item", "john@gmail.com"]], "expected_pass": False},
        {"id": 13, "name": "PII Hidden in Object Property", "payload": [{"meta": {"user": "John Smith"}}], "expected_pass": False},
        {"id": 14, "name": "Tokenized PERSON# Token", "payload": [{"text": "PERSON#A72F"}], "expected_pass": True},
        {"id": 15, "name": "REDACTED Placeholder Value", "payload": [{"text": "[REDACTED]"}], "expected_pass": True},
        {"id": 16, "name": "Benign Random Base64", "payload": [{"text": "SGVsbG8gV29ybGQ="}], "expected_pass": True},
        {"id": 17, "name": "Benign Encoded URL", "payload": [{"text": "https%3A%2F%2Fexample.com"}], "expected_pass": True},
        {"id": 18, "name": "Large Payload (1000 items)", "payload": [{"text": f"item_{i}"} for i in range(1000)], "expected_pass": True},
        {"id": 19, "name": "Malformed Nested Payload", "payload": [{"text": None, "val": [1, 2, "safe"]}], "expected_pass": True},
        {"id": 20, "name": "Adversarial Deep Nested Payload", "payload": {"a": {"b": {"c": {"d": {"e": {"f": "john@gmail.com"}}}}}}, "expected_pass": False}
    ]

    results = []
    passed_cases = 0

    for tc in test_cases:
        res = validate_network_egress_test(raw_entities, tc["payload"])
        is_pass = (res["zeroRawPIIVerified"] == tc["expected_pass"])
        if is_pass:
            passed_cases += 1
        results.append({
            "test_id": tc["id"],
            "test_name": tc["name"],
            "expected_zero_raw_pii": tc["expected_pass"],
            "actual_zero_raw_pii": res["zeroRawPIIVerified"],
            "result": "PASS" if is_pass else "FAIL",
            "details": res["details"]
        })

    return {
        "total_tests": len(test_cases),
        "passed_tests": passed_cases,
        "failed_tests": len(test_cases) - passed_cases,
        "success_rate_pct": round((passed_cases / len(test_cases)) * 100, 2),
        "test_matrix": results
    }

if __name__ == "__main__":
    report = run_20_adversarial_egress_test_suite()
    print("==================================================")
    print("ADVERSARIAL NETWORK EGRESS SECURITY TEST SUITE")
    print("==================================================")
    print(json.dumps(report, indent=2))
