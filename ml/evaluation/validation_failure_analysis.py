"""
Validation Set Forensic Failure Analysis Script — SIH Problem Statement 26171
Evaluates EVERY ground-truth object in val_ui_dataset.json (Validation Set).
Generates:
- ml/evaluation/results/validation_failure_matrix.json
- ml/evaluation/results/validation_failure_report.md
"""

import os
import sys
import json
import math
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    import torch
    from ml.training.train_ui_detector import MultiScaleUIDetector, render_sample_image
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

UI_CLASSES = [
    "button", "input", "checkbox", "radio", "select",
    "link", "navigation", "card", "image", "icon", "text_block"
]

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

def run_validation_failure_analysis(base_dir: str):
    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    with open(val_dataset_path) as f:
        val_data = json.load(f)

    samples = val_data["samples"]
    print(f"[INFO] Loaded {len(samples)} validation scenes from '{val_dataset_path}'")

    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        print(f"[OK] Loaded PyTorch model weights from '{weights_path}'")
    model.eval()

    failure_records = []
    class_summary = {cls: {"total": 0, "detected": 0, "correct_class": 0, "loc_passed": 0} for cls in UI_CLASSES}

    for sample in samples:
        s_id = sample.get("image_id", sample.get("sample_id"))
        vp_w = sample.get("viewport", {}).get("width", 1920)
        vp_h = sample.get("viewport", {}).get("height", 1080)
        anns = sample["annotations"]

        img = render_sample_image(sample, vp_w, vp_h)
        np_arr = np.array(img.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = model(img_tensor)[0]

        num_slots = out.shape[0]
        preds = []
        for idx in range(num_slots):
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
                pw = max(14, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(14, int(round(abs(y2_n - y1_n) * vp_h)))

                preds.append({
                    "bbox": [px1, py1, pw, ph],
                    "confidence": round(conf, 4),
                    "class_id": cls_id,
                    "category": UI_CLASSES[cls_id]
                })

        for ann in anns:
            gt_id = ann.get("id", f"gt_{ann['category']}")
            gt_cls = ann["category"]
            gt_box = ann["bbox"]
            area = gt_box[2] * gt_box[3]
            w, h = gt_box[2], gt_box[3]

            class_summary[gt_cls]["total"] += 1

            best_iou = 0.0
            best_conf = 0.0
            best_pred_cls = None

            for p in preds:
                iou = calculate_iou(gt_box, p["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_conf = p["confidence"]
                    best_pred_cls = p["category"]

            predicted = best_iou >= 0.30
            correct_class = (best_pred_cls == gt_cls) if predicted else False
            loc_passed = best_iou >= 0.50

            if predicted:
                class_summary[gt_cls]["detected"] += 1
            if correct_class:
                class_summary[gt_cls]["correct_class"] += 1
            if loc_passed:
                class_summary[gt_cls]["loc_passed"] += 1

            failure_records.append({
                "sample_id": s_id,
                "gt_id": gt_id,
                "category": gt_cls,
                "bbox": gt_box,
                "area_px2": area,
                "width": w,
                "height": h,
                "predicted": predicted,
                "correct_class": correct_class,
                "localization_passed": loc_passed,
                "highest_confidence": round(best_conf, 4),
                "best_pred_category": best_pred_cls,
                "best_iou": round(best_iou, 4),
                "is_tiny": area < (32 * 32),
                "is_input": gt_cls == "input",
                "is_button": gt_cls == "button",
                "is_dense": len(anns) > 15
            })

    matrix_out = os.path.join(results_dir, "validation_failure_matrix.json")
    with open(matrix_out, "w") as f:
        json.dump({
            "total_samples": len(samples),
            "total_objects": len(failure_records),
            "class_summary": class_summary,
            "failure_records": failure_records
        }, f, indent=2)
    print(f"[OK] Saved validation failure matrix -> '{matrix_out}'")

    report_out = os.path.join(results_dir, "validation_failure_report.md")
    report_md = f"""# Validation Set Forensic Failure Report

## Forensic Summary
- Total Validation Scenes: {len(samples)}
- Total Ground Truth Objects: {len(failure_records)}

## Per-Class Detection & Classification Breakdown

| Category | Total GT | Detected (IoU >= 0.30) | Correct Class | Localization Passed (IoU >= 0.50) | Detection Recall |
| :--- | :--- | :--- | :--- | :--- | :--- |
"""
    for cls in UI_CLASSES:
        st = class_summary[cls]
        rec = (st["detected"] / float(st["total"]) * 100.0) if st["total"] > 0 else 0.0
        report_md += f"| {cls} | {st['total']} | {st['detected']} | {st['correct_class']} | {st['loc_passed']} | {rec:.2f}% |\n"

    with open(report_out, "w") as f:
        f.write(report_md)
    print(f"[OK] Saved validation failure report -> '{report_out}'")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_validation_failure_analysis(base_dir)
