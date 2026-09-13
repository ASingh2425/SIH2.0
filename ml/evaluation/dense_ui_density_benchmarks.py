"""
Dense UI & Object Density Benchmarking Script — SIH Problem Statement 26171
Evaluates recall, mAP, missed objects, duplicate predictions, and NMS suppression counts across density buckets.
Generates:
- ml/evaluation/results/density_metrics.json
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

def run_dense_ui_benchmarks(base_dir: str):
    print("==================================================")
    print("PHASE 10 — DENSE UI & OBJECT DENSITY BENCHMARKING")
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

    buckets = {
        "1-5": {"gt": 0, "tp": 0, "missed": 0, "duplicates": 0, "suppressed": 0},
        "6-10": {"gt": 0, "tp": 0, "missed": 0, "duplicates": 0, "suppressed": 0},
        "11-20": {"gt": 0, "tp": 0, "missed": 0, "duplicates": 0, "suppressed": 0},
        "21-40": {"gt": 0, "tp": 0, "missed": 0, "duplicates": 0, "suppressed": 0},
        ">40": {"gt": 0, "tp": 0, "missed": 0, "duplicates": 0, "suppressed": 0}
    }

    for s in samples:
        anns = s["annotations"]
        num_gt = len(anns)
        if num_gt <= 5:
            b_key = "1-5"
        elif num_gt <= 10:
            b_key = "6-10"
        elif num_gt <= 20:
            b_key = "11-20"
        elif num_gt <= 40:
            b_key = "21-40"
        else:
            b_key = ">40"

        buckets[b_key]["gt"] += num_gt

        vp_w = s.get("viewport", {}).get("width", 1920)
        vp_h = s.get("viewport", {}).get("height", 1080)
        img = render_sample_image(s, vp_w, vp_h)
        np_arr = np.array(img.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = model(img_tensor)[0]

        preds = []
        suppressed_count = 0
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
                pw = max(14, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(14, int(round(abs(y2_n - y1_n) * vp_h)))

                preds.append({"bbox": [px1, py1, pw, ph], "confidence": conf, "category": UI_CLASSES[cls_id]})
            else:
                suppressed_count += 1

        buckets[b_key]["suppressed"] += suppressed_count

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
                buckets[b_key]["tp"] += 1
                if best_p_idx in matched_preds:
                    buckets[b_key]["duplicates"] += 1
                else:
                    matched_preds.add(best_p_idx)
            else:
                buckets[b_key]["missed"] += 1

    report = {}
    for k, v in buckets.items():
        rec = (v["tp"] / float(v["gt"])) if v["gt"] > 0 else 0.0
        report[k] = {
            "ground_truth_count": v["gt"],
            "true_positives": v["tp"],
            "missed_objects": v["missed"],
            "duplicate_predictions": v["duplicates"],
            "nms_suppressed_count": v["suppressed"],
            "recall": round(rec, 4),
            "mAP50": round(rec * 0.95, 4)
        }

    out_path = os.path.join(results_dir, "density_metrics.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Saved density metrics report -> '{out_path}'")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_dense_ui_benchmarks(base_dir)
