"""
Phase 0: Freeze Evaluation Contract & Immutable Test Set Verification
Computes and locks SHA-256 hashes of real-world test fixtures and evaluator code.
"""

import os
import json
import hashlib

def hash_file(filepath):
    if not os.path.exists(filepath):
        return "MISSING"
    with open(filepath, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def freeze_contract(base_dir):
    fixtures_dir = os.path.join(base_dir, "ml", "evaluation", "fixtures")
    eval_script = os.path.join(base_dir, "ml", "evaluation", "evaluate_real_world_generalization.py")
    manifest_path = os.path.join(fixtures_dir, "real_world_manifest.json")
    annotations_path = os.path.join(fixtures_dir, "real_world_annotations.json")

    contract = {
        "frozen_at": "2026-09-13T21:07:00Z",
        "hashes": {
            "evaluate_real_world_generalization.py": hash_file(eval_script),
            "real_world_manifest.json": hash_file(manifest_path),
            "real_world_annotations.json": hash_file(annotations_path)
        },
        "locked_test_set": {
            "total_samples": 25,
            "total_ground_truth_objects": 137,
            "immutable": True
        }
    }

    out_path = os.path.join(fixtures_dir, "frozen_eval_contract.json")
    with open(out_path, "w") as f:
        json.dump(contract, f, indent=2)

    print("==================================================")
    print("PHASE 0: FROZEN EVALUATION CONTRACT")
    print("==================================================")
    for k, v in contract["hashes"].items():
        print(f"  {k:40s} : {v}")
    print(f"[OK] Saved frozen contract to '{out_path}'")
    print("--------------------------------------------------")

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    freeze_contract(pwd)
