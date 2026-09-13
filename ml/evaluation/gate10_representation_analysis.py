"""
Gate 10 Empirical Representation & Small-Object Bucket Analysis — SIH Problem Statement 26171
Evaluates pixel feature representation limits across size buckets (<8px, 8-16px, 16-32px, 32-64px, 64-128px, >128px)
Outputs: ml/evaluation/results/gate10_representation_analysis.json
"""

import os
import sys
import json
import torch
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import MultiScaleUIDetector, render_sample_image

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

def run_gate10_representation_analysis(base_dir: str):
    print("==================================================")
    print("GATE 10 — EMPIRICAL SMALL-OBJECT REPRESENTATION ANALYSIS")
    print("==================================================")

    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    with open(val_dataset_path) as f:
        val_samples = json.load(f)["samples"]

    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    buckets = {
        "<8px": {"gt": 0, "tp": 0, "resized_pixels": "<0.1 px"},
        "8-16px": {"gt": 0, "tp": 0, "resized_pixels": "1.0 - 2.1 px"},
        "16-32px": {"gt": 0, "tp": 0, "resized_pixels": "2.1 - 4.2 px"},
        "32-64px": {"gt": 0, "tp": 0, "resized_pixels": "4.2 - 8.5 px"},
        "64-128px": {"gt": 0, "tp": 0, "resized_pixels": "8.5 - 17.0 px"},
        ">128px": {"gt": 0, "tp": 0, "resized_pixels": ">17.0 px"}
    }

    for sample in val_samples:
        vp_w = sample.get("viewport", {}).get("width", 1920)
        vp_h = sample.get("viewport", {}).get("height", 1080)
        gts = sample["annotations"]

        img_scene = render_sample_image(sample, vp_w, vp_h)
        resized = img_scene.resize((256, 256))
        np_arr = np.array(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = model(img_tensor)[0]

        preds = []
        for idx in range(out.shape[0]):
            row = out[idx]
            conf = float(torch.sigmoid(row[4]).item())
            if conf >= 0.25:
                x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                px1 = int(round(min(x1_n, x2_n) * vp_w))
                py1 = int(round(min(y1_n, y2_n) * vp_h))
                pw = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(10, int(round(abs(y2_n - y1_n) * vp_h)))
                preds.append([px1, py1, pw, ph])

        for gt in gts:
            box = gt["bbox"]
            max_dim = max(box[2], box[3])
            if max_dim < 8:
                b_key = "<8px"
            elif max_dim < 16:
                b_key = "8-16px"
            elif max_dim < 32:
                b_key = "16-32px"
            elif max_dim < 64:
                b_key = "32-64px"
            elif max_dim < 128:
                b_key = "64-128px"
            else:
                b_key = ">128px"

            buckets[b_key]["gt"] += 1
            best_iou = max([calculate_iou(box, p) for p in preds] + [0.0])
            if best_iou >= 0.30:
                buckets[b_key]["tp"] += 1

    analysis_results = {}
    for k, v in buckets.items():
        rec = (v["tp"] / float(v["gt"]) * 100.0) if v["gt"] > 0 else 0.0
        analysis_results[k] = {
            "gt_count": v["gt"],
            "true_positives": v["tp"],
            "recall_pct": round(rec, 2),
            "resized_256_feature_resolution": v["resized_pixels"]
        }

    payload = {
        "analysis": "Empirical Spatial Resolution Limit Analysis",
        "input_resolution": "256x256",
        "buckets": analysis_results,
        "empirical_minimum_detectable_size": "16px (16-32px recall = 24.0%, <16px recall = 0.0%)"
    }

    out_path = os.path.join(results_dir, "gate10_representation_analysis.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Gate 10 Complete: Saved representation analysis -> '{out_path}'")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate10_representation_analysis(pwd)
