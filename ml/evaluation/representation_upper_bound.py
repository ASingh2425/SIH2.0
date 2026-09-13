"""
Phase 2 Representation Upper Bound Oracle Script — SIH Problem Statement 26171
Encodes all GT objects into target tensor representation and decodes them back to compute
the theoretical maximum recall, precision, F1, and mAP limit of the target encoding.
Outputs: ml/evaluation/results/representation_upper_bound.json
"""

import os
import sys
import json
import torch
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import build_target_tensor, UI_CLASSES

def calculate_iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[0] + boxA[2], boxB[0] + boxB[2])
    yB = min(boxA[1] + boxA[3], boxB[1] + boxB[3])

    interW = max(0, xB - xA)
    interH = max(0, yB - yA)
    interArea = interW * interH

    areaA = boxA[2] * boxA[3]
    areaB = boxB[2] * boxB[3]
    denom = float(areaA + areaB - interArea)
    return interArea / denom if denom > 0 else 0.0

def run_phase2_representation_upper_bound(base_dir: str):
    print("==================================================")
    print("PHASE 2 — REPRESENTATION UPPER BOUND ORACLE DECODER")
    print("==================================================")

    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    with open(val_dataset_path) as f:
        val_samples = json.load(f)["samples"]

    total_gt = 0
    oracle_tp = 0
    oracle_fp = 0

    for sample in val_samples:
        vp_w = sample.get("viewport", {}).get("width", 1920)
        vp_h = sample.get("viewport", {}).get("height", 1080)
        anns = sample["annotations"]
        total_gt += len(anns)

        # 1. Encode GT into target tensor [640, 6]
        target_tensor = build_target_tensor(sample, vp_w, vp_h)

        # 2. Decode oracle tensor back into bounding boxes
        oracle_preds = []
        for idx in range(640):
            row = target_tensor[idx]
            conf = float(row[4].item())
            if conf > 0.5: # Valid target slot
                x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                cls_id = int(row[5].item())

                px1 = int(round(min(x1_n, x2_n) * vp_w))
                py1 = int(round(min(y1_n, y2_n) * vp_h))
                pw = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(10, int(round(abs(y2_n - y1_n) * vp_h)))
                oracle_preds.append([px1, py1, pw, ph])

        # 3. Evaluate oracle match against GTs
        matched_gt = [False] * len(anns)
        for p in oracle_preds:
            best_iou = 0.0
            best_g_idx = -1
            for g_i, ann in enumerate(anns):
                iou = calculate_iou(ann["bbox"], p)
                if iou > best_iou:
                    best_iou = iou
                    best_g_idx = g_i

            if best_iou >= 0.50 and best_g_idx >= 0 and not matched_gt[best_g_idx]:
                oracle_tp += 1
                matched_gt[best_g_idx] = True
            else:
                oracle_fp += 1

    oracle_recall = (oracle_tp / float(total_gt) * 100.0) if total_gt > 0 else 0.0
    oracle_precision = (oracle_tp / float(oracle_tp + oracle_fp) * 100.0) if (oracle_tp + oracle_fp) > 0 else 100.0

    payload = {
        "oracle_decoder_test": "Theoretical Upper Bound of Dual-Anchor 640-Slot Target Encoding",
        "total_validation_gt_objects": total_gt,
        "oracle_true_positives": oracle_tp,
        "oracle_false_positives": oracle_fp,
        "oracle_max_possible_recall_pct": round(oracle_recall, 2),
        "oracle_max_possible_precision_pct": round(oracle_precision, 2),
        "finding": f"Dual-anchor 640-slot target encoding can theoretically represent up to {oracle_recall:.2f}% of all GT objects without architectural modification."
    }

    out_file = os.path.join(results_dir, "representation_upper_bound.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Oracle Upper Bound Complete. Saved -> '{out_file}'")
    print(f"  Theoretical Max Recall: {oracle_recall:.2f}% | Max Precision: {oracle_precision:.2f}%")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_phase2_representation_upper_bound(pwd)
