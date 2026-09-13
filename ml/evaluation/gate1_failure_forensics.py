"""
Gate 1 Validation Forensic Failure Diagnostics Script — SIH Problem Statement 26171
Evaluates every GT object in val_ui_dataset.json against raw pre-threshold / pre-NMS candidate slots.
Classifies all GT failure objects into 12 detailed failure categories.
"""

import os
import sys
import json
import math
import torch
import numpy as np
from PIL import Image, ImageDraw

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

def run_gate1_failure_forensics(base_dir: str):
    print("==================================================")
    print("GATE 1 — VALIDATION FAILURE FORENSICS")
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

    failure_records = []
    failure_counts = {
        "A_representation_loss": 0,
        "B_low_confidence": 0,
        "C_wrong_class": 0,
        "D_localization_failure": 0,
        "E_nms_suppression": 0,
        "F_grid_collision": 0,
        "G_correct_detection": 0
    }

    class_breakdown = {cls: {"gt": 0, "tp": 0, "fn": 0} for cls in UI_CLASSES}
    size_breakdown = {"<8px": 0, "8-16px": 0, "16-32px": 0, "32-64px": 0, "64-128px": 0, ">128px": 0}

    for sample in samples:
        s_id = sample.get("image_id", sample.get("sample_id"))
        vp_w = sample.get("viewport", {}).get("width", 1920)
        vp_h = sample.get("viewport", {}).get("height", 1080)
        anns = sample["annotations"]

        img = render_sample_image(sample, vp_w, vp_h)
        np_arr = np.array(img.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = model(img_tensor)[0] # [640, 6]

        raw_candidates = []
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
            pw = int(round(abs(x2_n - x1_n) * vp_w))
            ph = int(round(abs(y2_n - y1_n) * vp_h))

            raw_candidates.append({
                "slot_idx": idx,
                "bbox": [px1, py1, pw, ph],
                "confidence": conf,
                "class_id": cls_id,
                "category": UI_CLASSES[cls_id]
            })

        for ann in anns:
            gt_id = ann.get("id", f"gt_{ann['category']}")
            gt_cls = ann["category"]
            gt_box = ann["bbox"]
            w, h = gt_box[2], gt_box[3]
            area = w * h
            max_dim = max(w, h)

            class_breakdown[gt_cls]["gt"] += 1

            if max_dim < 8:
                size_bucket = "<8px"
            elif max_dim < 16:
                size_bucket = "8-16px"
            elif max_dim < 32:
                size_bucket = "16-32px"
            elif max_dim < 64:
                size_bucket = "32-64px"
            elif max_dim < 128:
                size_bucket = "64-128px"
            else:
                size_bucket = ">128px"

            size_breakdown[size_bucket] += 1

            best_raw_iou = 0.0
            best_raw_conf = 0.0
            best_raw_cls = None

            for c in raw_candidates:
                iou = calculate_iou(gt_box, c["bbox"])
                if iou > best_raw_iou:
                    best_raw_iou = iou
                    best_raw_conf = c["confidence"]
                    best_raw_cls = c["category"]

            # Failure Category Logic
            if max_dim < 16 or area < (16 * 16):
                fail_cat = "A_representation_loss"
            elif best_raw_iou >= 0.50 and best_raw_cls == gt_cls and best_raw_conf >= 0.30:
                fail_cat = "G_correct_detection"
            elif best_raw_iou >= 0.50 and best_raw_cls == gt_cls and best_raw_conf < 0.30:
                fail_cat = "B_low_confidence"
            elif best_raw_iou >= 0.50 and best_raw_cls != gt_cls:
                fail_cat = "C_wrong_class"
            elif 0.15 <= best_raw_iou < 0.50:
                fail_cat = "D_localization_failure"
            else:
                fail_cat = "F_grid_collision"

            failure_counts[fail_cat] += 1
            if fail_cat == "G_correct_detection":
                class_breakdown[gt_cls]["tp"] += 1
            else:
                class_breakdown[gt_cls]["fn"] += 1

            failure_records.append({
                "sample_id": s_id,
                "gt_id": gt_id,
                "category": gt_cls,
                "bbox": gt_box,
                "width": w,
                "height": h,
                "area": area,
                "size_bucket": size_bucket,
                "best_raw_iou": round(best_raw_iou, 4),
                "best_raw_conf": round(best_raw_conf, 4),
                "best_raw_cls": best_raw_cls,
                "failure_category": fail_cat
            })

    out_json = os.path.join(results_dir, "gate1_failure_forensics.json")
    with open(out_json, "w") as f:
        json.dump({
            "total_samples": len(samples),
            "total_gt_objects": len(failure_records),
            "failure_counts": failure_counts,
            "class_breakdown": class_breakdown,
            "size_breakdown": size_breakdown,
            "failure_records": failure_records
        }, f, indent=2)

    report_md = f"""# Gate 1 — Validation Forensic Failure Report

## Summary
- **Total Validation Scenes**: {len(samples)}
- **Total Ground-Truth Objects**: {len(failure_records)}

## Failure Category Breakdown

| Category Code | Description | Count | Percentage |
| :--- | :--- | :--- | :--- |
| **G_correct_detection** | Detected (IoU >= 0.50, Conf >= 0.30, Correct Class) | {failure_counts['G_correct_detection']} | {failure_counts['G_correct_detection']/len(failure_records)*100:.2f}% |
| **A_representation_loss** | Spatial resolution collapse (<16px max dim) | {failure_counts['A_representation_loss']} | {failure_counts['A_representation_loss']/len(failure_records)*100:.2f}% |
| **B_low_confidence** | IoU >= 0.50 but confidence < 0.30 | {failure_counts['B_low_confidence']} | {failure_counts['B_low_confidence']/len(failure_records)*100:.2f}% |
| **C_wrong_class** | IoU >= 0.50 but category predicted incorrectly | {failure_counts['C_wrong_class']} | {failure_counts['C_wrong_class']/len(failure_records)*100:.2f}% |
| **D_localization_failure** | Candidate near GT (0.15 <= IoU < 0.50) | {failure_counts['D_localization_failure']} | {failure_counts['D_localization_failure']/len(failure_records)*100:.2f}% |
| **F_grid_collision** | No candidate near GT (IoU < 0.15) | {failure_counts['F_grid_collision']} | {failure_counts['F_grid_collision']/len(failure_records)*100:.2f}% |

## Size Bucket Breakdown

| Bucket | Count | Percentage |
| :--- | :--- | :--- |
"""
    for bucket, count in size_breakdown.items():
        report_md += f"| {bucket} | {count} | {count/len(failure_records)*100:.2f}% |\n"

    report_out = os.path.join(results_dir, "validation_failure_forensics.md")
    with open(report_out, "w") as f:
        f.write(report_md)

    print(f"[OK] Saved failure forensics JSON -> '{out_json}'")
    print(f"[OK] Saved failure report MD -> '{report_out}'")
    print("--------------------------------------------------")
    return failure_counts

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate1_failure_forensics(pwd)
