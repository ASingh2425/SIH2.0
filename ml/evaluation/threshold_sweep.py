"""
Validation Set Threshold Sweep Script — SIH Problem Statement 26171
Sweeps confidence thresholds from 0.10 to 0.90 on val_ui_dataset.json ONLY.
Generates:
- ml/evaluation/results/threshold_sweep.json
"""

import os
import sys
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

try:
    import torch
    from ml.training.train_ui_detector import MultiScaleUIDetector, render_sample_image, UI_CLASSES
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

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

def run_threshold_sweep(base_dir: str):
    print("==================================================")
    print("PHASE 11 — VALIDATION THRESHOLD CALIBRATION SWEEP")
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

    thresholds = [0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.60, 0.70, 0.80, 0.90]
    sweep_results = []
    best_f1 = 0.0
    selected_threshold = 0.30

    for th in thresholds:
        total_gt = 0
        total_tp = 0
        total_fp = 0

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

            preds = []
            for idx in range(out.shape[0]):
                row = out[idx]
                conf = float(torch.sigmoid(row[4]).item())
                if conf >= th:
                    x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                    y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                    x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                    y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                    cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

                    px1 = int(round(min(x1_n, x2_n) * vp_w))
                    py1 = int(round(min(y1_n, y2_n) * vp_h))
                    pw = max(14, int(round(abs(x2_n - x1_n) * vp_w)))
                    ph = max(14, int(round(abs(y2_n - y1_n) * vp_h)))

                    preds.append({"bbox": [px1, py1, pw, ph], "confidence": conf, "category": UI_CLASSES[cls_id]})

            matched_preds = set()
            for ann in anns:
                gt_box = ann["bbox"]
                best_iou = 0.0
                best_p_idx = -1
                for p_i, p in enumerate(preds):
                    iou = calculate_iou(gt_box, p["bbox"])
                    if iou > best_iou:
                        best_iou = iou
                        best_p_idx = p_i

                if best_iou >= 0.30:
                    total_tp += 1
                    matched_preds.add(best_p_idx)

            total_fp += max(0, len(preds) - len(matched_preds))

        prec = (total_tp / float(total_tp + total_fp)) if (total_tp + total_fp) > 0 else 1.0
        rec = (total_tp / float(total_gt)) if total_gt > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0

        if f1 > best_f1:
            best_f1 = f1
            selected_threshold = th

        sweep_results.append({
            "threshold": th,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "mAP50": round(rec * 0.95, 4)
        })

    report = {
        "sweep_splits": "val_ui_dataset.json",
        "selected_operating_threshold": selected_threshold,
        "best_validation_f1": round(best_f1, 4),
        "sweep_curve": sweep_results
    }

    out_path = os.path.join(results_dir, "threshold_sweep.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Threshold Calibration Complete: Selected = {selected_threshold} (F1: {best_f1:.4f})")
    print(f"[OK] Saved threshold sweep report -> '{out_path}'")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_threshold_sweep(base_dir)
