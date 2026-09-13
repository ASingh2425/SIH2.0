"""
Gated Evaluation Runner & Metric Gatekeeper
SIH Problem Statement 26171 — Objective 10

Refuses to label model 'production-ready' or 'generalizes' unless all required unseen-test
experiments execute successfully and pass strict quantitative gating thresholds.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from ml.evaluation.verify_data_leakage import verify_dataset_provenance
from ml.evaluation.evaluate_onnx_provenance import run_onnx_provenance_eval
from ml.evaluation.evaluate_ablation_study import run_3way_ablation_study
from ml.evaluation.evaluate_privacy_utility import run_privacy_utility_evaluation
from ml.evaluation.evaluate_e2e_traces import run_e2e_traces_evaluation

def run_gated_evaluation_pipeline(base_dir: str):
    print("==================================================")
    print("SIH26171 GATED EVALUATION PIPELINE RUNNER")
    print("==================================================")

    # 1. Dataset Leakage Verification
    if not verify_dataset_provenance(base_dir):
        print("[FAIL] GATED PIPELINE ABORTED: Dataset data leakage check failed!")
        return False

    # 2. ONNX Model Provenance & Per-Class Evaluation
    if not run_onnx_provenance_eval(base_dir):
        print("[FAIL] GATED PIPELINE ABORTED: ONNX provenance evaluation failed!")
        return False

    # 3. 3-Way Baseline Ablation Study
    if not run_3way_ablation_study(base_dir):
        print("[FAIL] GATED PIPELINE ABORTED: 3-way ablation study failed!")
        return False

    # 4. Privacy-Utility Trade-Off Evaluation
    if not run_privacy_utility_evaluation(base_dir):
        print("[FAIL] GATED PIPELINE ABORTED: Privacy-utility evaluation failed!")
        return False

    # 5. End-to-End Visual Agent Traces
    if not run_e2e_traces_evaluation(base_dir):
        print("[FAIL] GATED PIPELINE ABORTED: E2E agent trace execution failed!")
        return False

    # Check Gating Thresholds from machine-readable JSON artifacts
    eval_dir = os.path.join(base_dir, "ml", "evaluation")
    with open(os.path.join(eval_dir, "metrics.json")) as f: metrics = json.load(f)
    with open(os.path.join(eval_dir, "privacy_utility_results.json")) as f: priv_res = json.load(f)
    with open(os.path.join(eval_dir, "e2e_traces.json")) as f: trace_res = json.load(f)

    print("==================================================")
    print("QUANTITATIVE GATING CRITERIA CHECK")
    print("==================================================")
    
    gate_checks = [
        ("Unseen Challenge mAP@0.50 >= 0.85", metrics["mAP_50"] >= 0.85, metrics["mAP_50"]),
        ("Unseen Challenge Mean IoU >= 0.85", metrics["mean_bounding_box_iou"] >= 0.85, metrics["mean_bounding_box_iou"]),
        ("PII Recall == 100.0%", priv_res["pii_detection_metrics"]["recall_pct"] == 100.0, priv_res["pii_detection_metrics"]["recall_pct"]),
        ("Benign Destruction Rate <= 1.0%", priv_res["pixel_utility_metrics"]["benign_pixel_destruction_rate_pct"] <= 1.0, priv_res["pixel_utility_metrics"]["benign_pixel_destruction_rate_pct"]),
        ("E2E Scenarios Pass Rate == 100.0%", trace_res["scenarios_passed"] == trace_res["total_scenarios"], f"{trace_res['scenarios_passed']}/{trace_res['total_scenarios']}")
    ]

    all_passed = True
    for name, condition, value in gate_checks:
        status = "[PASS]" if condition else "[FAIL]"
        print(f"{status} {name} (Value: {value})")
        if not condition:
            all_passed = False

    print("--------------------------------------------------")
    if all_passed:
        print("[SUCCESS] EVALUATION_GATE_PASSED: Model is empirically verified on unseen challenge dataset.")
    else:
        print("[FAIL] EVALUATION_GATE_FAILED: Gating criteria not satisfied.")

    return all_passed

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    success = run_gated_evaluation_pipeline(pwd)
    if not success:
        sys.exit(1)
