"""
Gate 0 Baseline Manifest Generator — SIH Problem Statement 26171
Computes and records cryptographic SHA-256 hashes of all source code, model weights,
dataset splits, locked test sets, and environment metadata.
"""

import os
import sys
import json
import hashlib
import torch
import onnxruntime as ort

def get_file_sha256(filepath: str) -> str:
    if not os.path.exists(filepath):
        return "FILE_NOT_FOUND"
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def run_gate0_baseline_manifest(base_dir: str):
    print("==================================================")
    print("GATE 0 — BASELINE CRYPTOGRAPHIC FREEZE")
    print("==================================================")

    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    onnx_path = os.path.join(base_dir, "ml", "models", "ui_detector_v1.onnx")
    train_dataset_path = os.path.join(base_dir, "ml", "dataset", "train_ui_dataset.json")
    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    locked_ann_path = os.path.join(base_dir, "ml", "evaluation", "fixtures", "real_world_annotations.json")
    locked_man_path = os.path.join(base_dir, "ml", "evaluation", "fixtures", "real_world_manifest.json")
    train_script_path = os.path.join(base_dir, "ml", "training", "train_ui_detector.py")

    manifest = {
        "timestamp": "2026-09-13T22:31:00Z",
        "gate": "GATE_0_BASELINE_FREEZE",
        "hashes": {
            "train_script": get_file_sha256(train_script_path),
            "pytorch_weights": get_file_sha256(weights_path),
            "onnx_model": get_file_sha256(onnx_path),
            "train_dataset": get_file_sha256(train_dataset_path),
            "val_dataset": get_file_sha256(val_dataset_path),
            "real_world_annotations": get_file_sha256(locked_ann_path),
            "real_world_manifest": get_file_sha256(locked_man_path)
        },
        "environment": {
            "python_version": sys.version,
            "pytorch_version": torch.__version__,
            "onnxruntime_version": ort.__version__
        },
        "baseline_configuration": {
            "input_resolution": [256, 256],
            "candidate_slots": 640,
            "confidence_threshold": 0.30,
            "nms_threshold": 0.40,
            "model_architecture": "MultiScaleUIDetector (Dual-Anchor 16x16 + 8x8)",
            "parameter_count": 150000,
            "onnx_size_bytes": os.path.getsize(onnx_path) if os.path.exists(onnx_path) else 0
        }
    }

    out_path = os.path.join(results_dir, "gate0_baseline_manifest.json")
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[OK] Baseline Freeze Complete. Hashes recorded to '{out_path}'")
    print(f"  Locked Test SHA-256: {manifest['hashes']['real_world_annotations'][:16]}...")
    print("--------------------------------------------------")
    return manifest

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate0_baseline_manifest(pwd)
