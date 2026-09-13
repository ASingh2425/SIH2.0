"""
Gate 3 — PyTorch vs ONNX Runtime Equivalence Audit Script
Evaluates 20 different images simultaneously through PyTorch model and ONNX Runtime.
Measures max absolute error, mean absolute error, cosine similarity, and detection match rate.
Generates:
- ml/evaluation/results/onnx_equivalence_report.json
"""

import os
import sys
import json
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import torch
import onnxruntime as ort
from ml.training.train_ui_detector import MultiScaleUIDetector, render_sample_image

def cosine_similarity(a, b):
    dot = np.dot(a.flatten(), b.flatten())
    norm_a = np.linalg.norm(a.flatten())
    norm_b = np.linalg.norm(b.flatten())
    return float(dot / (norm_a * norm_b)) if (norm_a * norm_b) > 0 else 1.0

def run_gate3_onnx_equivalence(base_dir: str):
    print("==================================================")
    print("GATE 3 — PYTORCH / ONNX EQUIVALENCE AUDIT")
    print("==================================================")

    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    onnx_path = os.path.join(base_dir, "extension", "public", "models", "ui_detector_v1.onnx")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    with open(val_dataset_path) as f:
        val_data = json.load(f)

    test_samples = val_data["samples"][:20]

    # Load PyTorch model
    pt_model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        pt_model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    pt_model.eval()

    # Load ONNX session
    ort_session = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    input_name = ort_session.get_inputs()[0].name

    max_abs_diffs = []
    mean_abs_diffs = []
    cos_sims = []
    match_count = 0

    for idx, sample in enumerate(test_samples):
        img = render_sample_image(sample)
        np_arr = np.array(img.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
        input_tensor = np.expand_dims(np_arr, axis=0)  # [1, 3, 256, 256]

        # PyTorch forward
        with torch.no_grad():
            pt_out = pt_model(torch.from_numpy(input_tensor)).numpy()  # [1, 640, 6]

        # ONNX Runtime forward
        ort_out = ort_session.run(None, {input_name: input_tensor})[0]  # [1, 640, 6]

        max_diff = float(np.max(np.abs(pt_out - ort_out)))
        mean_diff = float(np.mean(np.abs(pt_out - ort_out)))
        cos_sim = cosine_similarity(pt_out, ort_out)

        max_abs_diffs.append(max_diff)
        mean_abs_diffs.append(mean_diff)
        cos_sims.append(cos_sim)

        if max_diff < 1e-3 and cos_sim > 0.999:
            match_count += 1

    overall_max_diff = float(np.max(max_abs_diffs))
    overall_mean_diff = float(np.mean(mean_abs_diffs))
    overall_cos_sim = float(np.mean(cos_sims))
    match_rate = float(match_count / len(test_samples))

    equivalence_passed = (overall_max_diff < 1e-3) and (overall_cos_sim >= 0.999) and (match_rate >= 0.95)

    report = {
        "gate": "GATE_3_PYTORCH_ONNX_EQUIVALENCE",
        "num_test_images": len(test_samples),
        "overall_max_abs_diff": round(overall_max_diff, 6),
        "overall_mean_abs_diff": round(overall_mean_diff, 6),
        "mean_cosine_similarity": round(overall_cos_sim, 6),
        "detection_match_rate": round(match_rate, 4),
        "onnx_equivalence_verified": equivalence_passed
    }

    out_path = os.path.join(results_dir, "onnx_equivalence_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] ONNX Equivalence Test Complete: Max Diff = {overall_max_diff:.6f}, CosSim = {overall_cos_sim:.6f}")
    print(f"[OK] ONNX Equivalence Verified: {equivalence_passed}")
    print(f"[OK] Saved ONNX equivalence report -> '{out_path}'")
    print("--------------------------------------------------")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate3_onnx_equivalence(base_dir)
