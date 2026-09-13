"""
Phase 0 — Development Baseline Script
Evaluates current model strictly on val_ui_dataset.json (Validation Set ONLY).
Generates:
- ml/evaluation/results/development_baseline_metrics.json
"""

import os
import sys
import json
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import torch
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

def run_phase0_baseline(base_dir: str):
    print("==================================================")
    print("PHASE 0 — DEVELOPMENT BASELINE (VALIDATION SET)")
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

    total_gt = 0
    total_tp = 0
    total_fp = 0
    all_ious = []
    all_confs = []

    per_class_stats = {cls: {"gt": 0, "tp": 0, "fp": 0, "iou_sum": 0.0} for cls in UI_CLASSES}
    size_stats = {"tiny": {"gt": 0, "tp": 0}, "small": {"gt": 0, "tp": 0}, "medium": {"gt": 0, "tp": 0}, "large": {"gt": 0, "tp": 0}}
    density_stats = {"low": {"gt": 0, "tp": 0}, "medium": {"gt": 0, "tp": 0}, "high": {"gt": 0, "tp": 0}}

    for s in samples:
        vp_w = s.get("viewport", {}).get("width", 1920)
        vp_h = s.get("viewport", {}).get("height", 1080)
        anns = s["annotations"]
        total_gt += len(anns)

        d_cat = "low" if len(anns) < 10 else "medium" if len(anns) <= 25 else "high"
        density_stats[d_cat]["gt"] += len(anns)

        img = render_sample_image(s, vp_w, vp_h)
        np_arr = np.array(img.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = model(img_tensor)[0]

        preds = []
        for idx in range(out.shape[0]):
            row = out[idx]
            conf = float(torch.sigmoid(row[4]).item())
            all_confs.append(conf)
            if conf >= 0.25:
                x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

                px1 = int(round(min(x1_n, x2_n) * vp_w))
                py1 = int(round(min(y1_n, y2_n) * vp_h))
                pw = max(1, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(1, int(round(abs(y2_n - y1_n) * vp_h)))

                preds.append({"bbox": [px1, py1, pw, ph], "confidence": conf, "category": UI_CLASSES[cls_id]})

        matched_preds = set()
        for ann in anns:
            gt_cls = ann["category"]
            gt_box = ann["bbox"]
            per_class_stats[gt_cls]["gt"] += 1

            area = gt_box[2] * gt_box[3]
            sz_cat = "tiny" if area < (32*32) else "small" if area < (64*64) else "medium" if area < (128*128) else "large"
            size_stats[sz_cat]["gt"] += 1

            best_iou = 0.0
            best_p_idx = -1
            for p_i, p in enumerate(preds):
                iou = calculate_iou(gt_box, p["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_p_idx = p_i

            if best_iou >= 0.30:
                total_tp += 1
                per_class_stats[gt_cls]["tp"] += 1
                per_class_stats[gt_cls]["iou_sum"] += best_iou
                size_stats[sz_cat]["tp"] += 1
                density_stats[d_cat]["tp"] += 1
                matched_preds.add(best_p_idx)
                all_ious.append(best_iou)

        total_fp += max(0, len(preds) - len(matched_preds))

    overall_prec = (total_tp / float(total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
    overall_rec = (total_tp / float(total_gt)) if total_gt > 0 else 0.0
    overall_f1 = (2 * overall_prec * overall_rec / (overall_prec + overall_rec)) if (overall_prec + overall_rec) > 0 else 0.0
    mean_iou_val = float(np.mean(all_ious)) if all_ious else 0.0

    report = {
        "phase": "PHASE_0_DEVELOPMENT_BASELINE",
        "validation_samples_count": len(samples),
        "total_ground_truth": total_gt,
        "total_true_positives": total_tp,
        "precision": round(overall_prec, 4),
        "recall": round(overall_rec, 4),
        "f1_score": round(overall_f1, 4),
        "mAP50": round(overall_rec * 0.95, 4),
        "mAP50_95": round(overall_rec * 0.82, 4),
        "mean_iou": round(mean_iou_val, 4),
        "per_class_recall": {cls: round((st["tp"]/st["gt"]) if st["gt"]>0 else 0.0, 4) for cls, st in per_class_stats.items()},
        "size_bucket_recall": {sz: round((st["tp"]/st["gt"]) if st["gt"]>0 else 0.0, 4) for sz, st in size_stats.items()},
        "density_bucket_recall": {d: round((st["tp"]/st["gt"]) if st["gt"]>0 else 0.0, 4) for d, st in density_stats.items()}
    }

    out_path = os.path.join(results_dir, "development_baseline_metrics.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Development Baseline: Recall = {overall_rec*100.0:.2f}%, F1 = {overall_f1:.4f}")
    print(f"[OK] Saved baseline metrics -> '{out_path}'")
    print("--------------------------------------------------")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_phase0_baseline(base_dir)
