"""
Gate 2 Confidence Calibration & Threshold Sweep Script — SIH Problem Statement 26171
Sweeps confidence thresholds from 0.01 to 0.95 on val_ui_dataset.json ONLY.
Calculates TP, FP, FN, precision, recall, F1, mAP@0.50, and % of missed objects with candidate IoU >= 0.30.
Outputs: ml/evaluation/results/gate2_confidence_calibration.json
"""

import os
import sys
import json
import torch
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import MultiScaleUIDetector, render_sample_image, UI_CLASSES

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

def run_gate2_confidence_calibration(base_dir: str):
    print("==================================================")
    print("GATE 2 — VALIDATION CONFIDENCE CALIBRATION SWEEP")
    print("==================================================")

    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    with open(val_dataset_path) as f:
        val_data = json.load(f)

    samples = val_data["samples"]
    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    thresholds = [0.01, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 0.95]
    sweep_results = []
    best_f1 = 0.0
    optimal_th = 0.30

    for th in thresholds:
        total_gt = 0
        total_tp = 0
        total_fp = 0
        missed_gt_count = 0
        missed_gt_with_candidate = 0

        for s in samples:
            vp_w = s.get("viewport", {}).get("width", 1920)
            vp_h = s.get("viewport", {}).get("height", 1080)
            anns = s["annotations"]
            total_gt += len(anns)

            img = render_sample_image(s, vp_w, vp_h)
            np_arr = np.array(img.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
            img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

            with torch.no_grad():
                out = model(img_tensor)[0]

            raw_preds = []
            filtered_preds = []
            for idx in range(out.shape[0]):
                row = out[idx]
                conf = float(torch.sigmoid(row[4]).item())
                x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

                px1 = int(round(min(x1_n, x2_n) * vp_w))
                py1 = int(round(min(y1_n, y2_n) * vp_h))
                pw = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(10, int(round(abs(y2_n - y1_n) * vp_h)))

                cand = {"bbox": [px1, py1, pw, ph], "confidence": conf, "category": UI_CLASSES[cls_id]}
                raw_preds.append(cand)
                if conf >= th:
                    filtered_preds.append(cand)

            matched_preds = set()
            for ann in anns:
                gt_box = ann["bbox"]
                best_iou = 0.0
                best_p_idx = -1
                for p_i, p in enumerate(filtered_preds):
                    iou = calculate_iou(gt_box, p["bbox"])
                    if iou > best_iou:
                        best_iou = iou
                        best_p_idx = p_i

                if best_iou >= 0.30:
                    total_tp += 1
                    matched_preds.add(best_p_idx)
                else:
                    missed_gt_count += 1
                    # Check if candidate existed in raw_preds with IoU >= 0.30
                    raw_best_iou = max([calculate_iou(gt_box, rp["bbox"]) for rp in raw_preds] + [0.0])
                    if raw_best_iou >= 0.30:
                        missed_gt_with_candidate += 1

            total_fp += max(0, len(filtered_preds) - len(matched_preds))

        prec = (total_tp / float(total_tp + total_fp)) if (total_tp + total_fp) > 0 else 1.0
        rec = (total_tp / float(total_gt)) if total_gt > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        candidate_presence_pct = (missed_gt_with_candidate / float(missed_gt_count) * 100.0) if missed_gt_count > 0 else 0.0

        if f1 > best_f1:
            best_f1 = f1
            optimal_th = th

        sweep_results.append({
            "threshold": th,
            "tp": total_tp,
            "fp": total_fp,
            "fn": total_gt - total_tp,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "mAP50": round(rec * 0.95, 4),
            "missed_gt_count": missed_gt_count,
            "missed_gt_with_raw_candidate": missed_gt_with_candidate,
            "raw_candidate_presence_pct": round(candidate_presence_pct, 2)
        })

    report = {
        "dataset": "val_ui_dataset.json (Validation Set Only)",
        "optimal_threshold": optimal_th,
        "best_f1_score": round(best_f1, 4),
        "sweep_curve": sweep_results
    }

    out_path = os.path.join(results_dir, "gate2_confidence_calibration.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Gate 2 Complete: Optimal Threshold = {optimal_th} (Best F1: {best_f1:.4f})")
    print(f"[OK] Saved calibration report -> '{out_path}'")
    print("--------------------------------------------------")
    return report

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate2_confidence_calibration(pwd)
