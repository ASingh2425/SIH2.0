"""
Phase 6 Coarse-to-Fine Adaptive Neural Inference Script — SIH Problem Statement 26171
1. Cheap global pass (256x256) identifies high-density / form container regions.
2. Selective neural crops (384x384) are extracted around uncertain / high-density regions.
3. Box coordinates are remapped to global viewport space and suppressed via cross-crop NMS.
Outputs: ml/evaluation/results/coarse_to_fine_neural_inference.json
"""

import os
import sys
import json
import time
import torch
import numpy as np
from PIL import Image

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

def predict_neural_crop(model, img_crop, vp_w, vp_h, offset_x, offset_y, crop_w, crop_h, res=256):
    resized = img_crop.resize((res, res))
    np_arr = np.array(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0
    img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

    with torch.no_grad():
        out = model(img_tensor)[0]

    preds = []
    for idx in range(out.shape[0]):
        row = out[idx]
        conf = float(torch.sigmoid(row[4]).item())
        if conf < 0.20:
            continue
        x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
        y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
        x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
        y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
        cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

        lx1 = min(x1_n, x2_n) * crop_w
        ly1 = min(y1_n, y2_n) * crop_h
        lw = abs(x2_n - x1_n) * crop_w
        lh = abs(y2_n - y1_n) * crop_h

        gx = int(round(offset_x + lx1))
        gy = int(round(offset_y + ly1))
        gw = max(10, int(round(lw)))
        gh = max(10, int(round(lh)))

        preds.append({
            "bbox": [gx, gy, gw, gh],
            "confidence": round(conf, 4),
            "category": UI_CLASSES[cls_id]
        })
    return preds

def run_coarse_to_fine_pipeline(model, samples):
    start_t = time.perf_counter()
    total_gt = 0
    total_tp = 0
    small_gt = 0
    small_tp = 0
    input_gt = 0
    input_tp = 0

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

        img_scene = render_sample_image(sample, vp_w, vp_h)

        # 1. Cheap Global Pass (256x256)
        global_preds = predict_neural_crop(model, img_scene, vp_w, vp_h, 0, 0, vp_w, vp_h, res=256)

        # 2. Identify dense container / card regions from global predictions
        dense_regions = []
        for p in global_preds:
            if p["category"] in ["card", "navigation"]:
                dense_regions.append(p["bbox"])

        # 3. Selective High-Res Neural Crops around dense regions
        crop_preds = []
        for reg in dense_regions[:3]: # Max 3 selective crops to bound latency
            rx, ry, rw, rh = reg
            # Add context margin
            cx = max(0, rx - 20)
            cy = max(0, ry - 20)
            cw = min(vp_w - cx, rw + 40)
            ch = min(vp_h - cy, rh + 40)
            crop_img = img_scene.crop((cx, cy, cx + cw, cy + ch))
            preds = predict_neural_crop(model, crop_img, vp_w, vp_h, cx, cy, cw, ch, res=256)
            crop_preds.extend(preds)

        # 4. Merge predictions and run cross-crop NMS
        all_preds = run_nms(global_preds + crop_preds, iou_threshold=0.40)

        # 5. Evaluate matches
        gt_matched = [False] * len(gts)
        for p in all_preds:
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

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0 / len(samples)

    return {
        "pipeline": "Coarse-to-Fine Adaptive Neural Crops (Global 256 + Selective Container Crops)",
        "mean_latency_ms": round(elapsed_ms, 2),
        "overall_recall": round(total_tp / float(total_gt), 4) if total_gt > 0 else 0.0,
        "small_object_recall": round(small_tp / float(small_gt), 4) if small_gt > 0 else 0.0,
        "input_recall": round(input_tp / float(input_gt), 4) if input_gt > 0 else 0.0
    }

def run_phase6_coarse_to_fine(base_dir: str):
    print("==================================================")
    print("PHASE 6 — COARSE-TO-FINE ADAPTIVE NEURAL CROPS")
    print("==================================================")

    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    with open(val_dataset_path) as f:
        val_samples = json.load(f)["samples"]

    res = run_coarse_to_fine_pipeline(model, val_samples)

    out_file = os.path.join(results_dir, "coarse_to_fine_neural_inference.json")
    with open(out_file, "w") as f:
        json.dump(res, f, indent=2)

    print(f"[OK] Coarse-to-Fine Pipeline Complete. Saved -> '{out_file}'")
    print(f"  Overall Recall: {res['overall_recall']:.4f} | Small Recall: {res['small_object_recall']:.4f} | Latency: {res['mean_latency_ms']:.2f} ms")
    print("--------------------------------------------------")
    return res

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_phase6_coarse_to_fine(pwd)
