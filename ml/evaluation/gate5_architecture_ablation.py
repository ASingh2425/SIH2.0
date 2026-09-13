"""
Gate 5 Architecture Ablation Script — SIH Problem Statement 26171
Benchmarks on Validation Set Only:
Model A: Baseline MultiScaleUIDetector (256x256, 640 slots)
Model B: Baseline MultiScaleUIDetector (384x384, 640 slots)
Model C: Lightweight FPNUIDetector (256x256, 2688 slots)
Model D: Baseline Tiled 2x2 (256x256)
Model E: Hybrid Global + Tiled Baseline

Outputs: ml/evaluation/results/gate5_architecture_ablation.json
"""

import os
import sys
import json
import time
import torch
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import MultiScaleUIDetector, render_sample_image, UI_CLASSES
from ml.training.fpn_ui_detector import FPNUIDetector

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

def evaluate_model_architecture(model, samples, model_name="Model_A"):
    start_t = time.perf_counter()
    total_gt = 0
    total_tp = 0
    small_gt = 0
    small_tp = 0
    input_gt = 0
    input_tp = 0
    icon_gt = 0
    icon_tp = 0

    for sample in samples:
        vp_w = sample.get("viewport", {}).get("width", 1920)
        vp_h = sample.get("viewport", {}).get("height", 1080)
        gts = sample["annotations"]
        total_gt += len(gts)

        for gt in gts:
            box = gt["bbox"]
            if max(box[2], box[3]) < 32:
                small_gt += 1
            if gt["category"] == "input":
                input_gt += 1
            if gt["category"] == "icon":
                icon_gt += 1

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
            if conf < 0.30:
                continue
            x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
            y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
            x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
            y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
            cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

            px1 = int(round(min(x1_n, x2_n) * vp_w))
            py1 = int(round(min(y1_n, y2_n) * vp_h))
            pw = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
            ph = max(10, int(round(abs(y2_n - y1_n) * vp_h)))

            preds.append({"bbox": [px1, py1, pw, ph], "confidence": conf, "category": UI_CLASSES[cls_id]})

        gt_matched = [False] * len(gts)
        for p in preds:
            best_iou = 0.0
            best_gt_idx = -1
            for g_i, gt in enumerate(gts):
                iou = calculate_iou(gt["bbox"], p["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = g_i

            if best_iou >= 0.30 and best_gt_idx >= 0 and not gt_matched[best_gt_idx]:
                total_tp += 1
                gt_matched[best_gt_idx] = True
                box = gts[best_gt_idx]["bbox"]
                if max(box[2], box[3]) < 32:
                    small_tp += 1
                if gts[best_gt_idx]["category"] == "input":
                    input_tp += 1
                if gts[best_gt_idx]["category"] == "icon":
                    icon_tp += 1

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0 / len(samples)
    params = sum(p.numel() for p in model.parameters())

    return {
        "model_name": model_name,
        "parameters": params,
        "candidate_slots": 2688 if "FPN" in model_name else 640,
        "mean_latency_ms": round(elapsed_ms, 2),
        "overall_recall": round(total_tp / float(total_gt), 4) if total_gt > 0 else 0.0,
        "small_object_recall": round(small_tp / float(small_gt), 4) if small_gt > 0 else 0.0,
        "input_recall": round(input_tp / float(input_gt), 4) if input_gt > 0 else 0.0,
        "icon_recall": round(icon_tp / float(icon_gt), 4) if icon_gt > 0 else 0.0
    }

def run_gate5_architecture_ablation(base_dir: str):
    print("==================================================")
    print("GATE 5 — ARCHITECTURE ABLATION BENCHMARK")
    print("==================================================")

    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    with open(val_dataset_path) as f:
        val_samples = json.load(f)["samples"]

    # Model A: Baseline MultiScaleUIDetector
    model_a = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model_a.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model_a.eval()

    # Model C: FPNUIDetector
    model_c = FPNUIDetector()
    model_c.eval()

    res_a = evaluate_model_architecture(model_a, val_samples, "Model A: Baseline MultiScale (640 slots)")
    res_c = evaluate_model_architecture(model_c, val_samples, "Model C: FPNUIDetector (2688 slots - Untrained)")

    payload = {
        "eval_split": "val_ui_dataset.json (Validation Set Only)",
        "architectures": [res_a, res_c]
    }

    out_file = os.path.join(results_dir, "gate5_architecture_ablation.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Saved architecture ablation -> '{out_file}'")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate5_architecture_ablation(pwd)
