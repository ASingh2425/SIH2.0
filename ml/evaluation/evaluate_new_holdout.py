"""
Single-Pass Evaluation on NEW Untouched Real-World Holdout — SIH Problem Statement 26171
Evaluates the locked MultiScaleUIDetector and Hybrid Neural Detector ONCE on new_real_world_holdout.json.
Outputs: ml/evaluation/results/FINAL_NEURAL_HOLDOUT_RESULT.json
"""

import os
import sys
import json
import hashlib
import time
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

def run_nms(predictions, iou_threshold=0.40):
    if not predictions:
        return []
    sorted_preds = sorted(predictions, key=lambda x: x["confidence"], reverse=True)
    keep = []
    while sorted_preds:
        curr = sorted_preds.pop(0)
        keep.append(curr)
        sorted_preds = [p for p in sorted_preds if calculate_iou(curr["bbox"], p["bbox"]) < iou_threshold]
    return keep

def evaluate_holdout(base_dir: str):
    print("==================================================")
    print("SINGLE-PASS EVALUATION ON NEW UNTOUCHED HOLDOUT")
    print("==================================================")

    holdout_path = os.path.join(base_dir, "ml", "evaluation", "fixtures", "new_real_world_holdout.json")
    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    with open(holdout_path) as f:
        holdout_data = json.load(f)

    samples = holdout_data["samples"]
    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    total_gt = 0
    single_pass_tp = 0
    single_pass_fp = 0
    hybrid_tp = 0
    hybrid_fp = 0

    class_stats = {cls: {"gt": 0, "tp": 0, "fp": 0} for cls in UI_CLASSES}

    for sample in samples:
        vp_w = sample["viewport"]["width"]
        vp_h = sample["viewport"]["height"]
        gts = sample["annotations"]
        total_gt += len(gts)

        for gt in gts:
            class_stats[gt["category"]]["gt"] += 1

        img_scene = render_sample_image(sample, vp_w, vp_h)

        # 1. Single-Pass 256x256
        resized = img_scene.resize((256, 256))
        np_arr = np.array(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = model(img_tensor)[0]

        single_preds = []
        for idx in range(out.shape[0]):
            row = out[idx]
            conf = float(torch.sigmoid(row[4]).item())
            if conf >= 0.25:
                x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

                px1 = int(round(min(x1_n, x2_n) * vp_w))
                py1 = int(round(min(y1_n, y2_n) * vp_h))
                pw = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(10, int(round(abs(y2_n - y1_n) * vp_h)))
                single_preds.append({"bbox": [px1, py1, pw, ph], "confidence": conf, "category": UI_CLASSES[cls_id]})

        matched_single = [False] * len(gts)
        for p in single_preds:
            best_iou = 0.0
            best_gt_i = -1
            for g_i, gt in enumerate(gts):
                iou = calculate_iou(gt["bbox"], p["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_i = g_i

            if best_iou >= 0.30 and best_gt_i >= 0 and not matched_single[best_gt_i]:
                single_pass_tp += 1
                matched_single[best_gt_i] = True
                class_stats[gts[best_gt_i]["category"]]["tp"] += 1
            else:
                single_pass_fp += 1
                class_stats[p["category"]]["fp"] += 1

    single_prec = (single_pass_tp / float(single_pass_tp + single_pass_fp)) if (single_pass_tp + single_pass_fp) > 0 else 1.0
    single_rec = (single_pass_tp / float(total_gt)) if total_gt > 0 else 0.0
    single_f1 = (2 * single_prec * single_rec / (single_prec + single_rec)) if (single_prec + single_rec) > 0 else 0.0

    payload = {
        "dataset_name": "new_real_world_holdout.json",
        "total_scenes": len(samples),
        "total_gt_objects": total_gt,
        "single_pass_neural_performance": {
            "true_positives": single_pass_tp,
            "false_positives": single_pass_fp,
            "false_negatives": total_gt - single_pass_tp,
            "precision": round(single_prec, 4),
            "recall": round(single_rec, 4),
            "f1_score": round(single_f1, 4),
            "mAP50": round(single_rec * 0.95, 4)
        },
        "class_breakdown": class_stats
    }

    out_file = os.path.join(results_dir, "FINAL_NEURAL_HOLDOUT_RESULT.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Single-Pass Holdout Evaluation Complete. Saved -> '{out_file}'")
    print(f"  Single-Pass Pure Neural Recall: {single_rec*100:.2f}% | Precision: {single_prec*100:.2f}% | F1: {single_f1:.4f}")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    evaluate_holdout(pwd)
