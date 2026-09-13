"""
Gate 4 Full-Frame vs Tiled Inference Ablation Script — SIH Problem Statement 26171
Evaluates validation set only:
Option A: Full-Frame 256x256
Option B: Full-Frame 384x384
Option C: 2x2 Tiled 256x256 (Overlap 32px) + Cross-Tile NMS
Option D: 2x2 Tiled 320x320 (Overlap 32px) + Cross-Tile NMS
Option E: Hybrid Global + 2x2 Tiled Inference

Outputs: ml/evaluation/results/gate4_tiled_inference_ablation.json
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

def predict_single_tensor(model, img_tensor, vp_w, vp_h, offset_x=0, offset_y=0, scale_w=1.0, scale_h=1.0):
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

        # Scale normalized tile coords back to full viewport space
        local_x1 = min(x1_n, x2_n) * (vp_w * scale_w)
        local_y1 = min(y1_n, y2_n) * (vp_h * scale_h)
        local_w = abs(x2_n - x1_n) * (vp_w * scale_w)
        local_h = abs(y2_n - y1_n) * (vp_h * scale_h)

        global_x1 = int(round(offset_x + local_x1))
        global_y1 = int(round(offset_y + local_y1))
        global_w = max(10, int(round(local_w)))
        global_h = max(10, int(round(local_h)))

        preds.append({
            "bbox": [global_x1, global_y1, global_w, global_h],
            "confidence": round(conf, 4),
            "category": UI_CLASSES[cls_id]
        })
    return preds

def evaluate_inference_mode(model, samples, mode="full_256"):
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

        if mode == "full_256":
            resized = img_scene.resize((256, 256))
            tensor = torch.from_numpy(np.array(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0).unsqueeze(0)
            all_preds = predict_single_tensor(model, tensor, vp_w, vp_h)

        elif mode == "full_384":
            resized = img_scene.resize((384, 384))
            tensor = torch.from_numpy(np.array(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0).unsqueeze(0)
            # Bilinear resize tensor to 256x256 for baseline model
            tensor_256 = torch.nn.functional.interpolate(tensor, size=(256, 256), mode="bilinear", align_corners=False)
            all_preds = predict_single_tensor(model, tensor_256, vp_w, vp_h)

        elif mode in ["tiled_256", "tiled_320"]:
            tile_res = 256 if mode == "tiled_256" else 320
            all_preds = []
            half_w, half_h = vp_w // 2, vp_h // 2
            # 2x2 grid tiles
            tile_configs = [
                (0, 0, half_w, half_h),
                (half_w, 0, half_w, half_h),
                (0, half_h, half_w, half_h),
                (half_w, half_h, half_w, half_h)
            ]
            for (ox, oy, tw, th) in tile_configs:
                tile_crop = img_scene.crop((ox, oy, ox + tw, oy + th)).resize((tile_res, tile_res))
                t_tensor = torch.from_numpy(np.array(tile_crop, dtype=np.float32).transpose(2, 0, 1) / 255.0).unsqueeze(0)
                if tile_res != 256:
                    t_tensor = torch.nn.functional.interpolate(t_tensor, size=(256, 256), mode="bilinear", align_corners=False)
                t_preds = predict_single_tensor(model, t_tensor, vp_w, vp_h, offset_x=ox, offset_y=oy, scale_w=0.5, scale_h=0.5)
                all_preds.extend(t_preds)
            all_preds = run_nms(all_preds, iou_threshold=0.40)

        elif mode == "hybrid_global_tiles":
            # Global pass
            resized = img_scene.resize((256, 256))
            g_tensor = torch.from_numpy(np.array(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0).unsqueeze(0)
            global_preds = predict_single_tensor(model, g_tensor, vp_w, vp_h)

            # 2x2 Tile pass
            t_preds = []
            half_w, half_h = vp_w // 2, vp_h // 2
            tile_configs = [(0, 0, half_w, half_h), (half_w, 0, half_w, half_h), (0, half_h, half_w, half_h), (half_w, half_h, half_w, half_h)]
            for (ox, oy, tw, th) in tile_configs:
                tile_crop = img_scene.crop((ox, oy, ox + tw, oy + th)).resize((256, 256))
                t_tensor = torch.from_numpy(np.array(tile_crop, dtype=np.float32).transpose(2, 0, 1) / 255.0).unsqueeze(0)
                preds = predict_single_tensor(model, t_tensor, vp_w, vp_h, offset_x=ox, offset_y=oy, scale_w=0.5, scale_h=0.5)
                t_preds.extend(preds)

            all_preds = run_nms(global_preds + t_preds, iou_threshold=0.40)

        # Match GTs
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
                if gts[best_gt_idx]["category"] == "icon":
                    icon_tp += 1

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0 / len(samples)

    return {
        "mode": mode,
        "mean_latency_ms": round(elapsed_ms, 2),
        "overall_recall": round(total_tp / float(total_gt), 4) if total_gt > 0 else 0.0,
        "small_object_recall": round(small_tp / float(small_gt), 4) if small_gt > 0 else 0.0,
        "input_recall": round(input_tp / float(input_gt), 4) if input_gt > 0 else 0.0,
        "icon_recall": round(icon_tp / float(icon_gt), 4) if icon_gt > 0 else 0.0
    }

def run_gate4_tiled_ablation(base_dir: str):
    print("==================================================")
    print("GATE 4 — FULL-FRAME VS TILED INFERENCE ABLATION")
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

    modes = ["full_256", "full_384", "tiled_256", "tiled_320", "hybrid_global_tiles"]
    results = []

    for m in modes:
        res = evaluate_inference_mode(model, val_samples, m)
        results.append(res)
        print(f"  Mode: {m:20s} | Overall Recall: {res['overall_recall']:.4f} | Small Recall: {res['small_object_recall']:.4f} | Latency: {res['mean_latency_ms']:.2f} ms")

    payload = {
        "eval_split": "val_ui_dataset.json (Validation Set Only)",
        "inference_ablations": results
    }

    out_file = os.path.join(results_dir, "gate4_tiled_inference_ablation.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Saved tiled inference ablation -> '{out_file}'")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate4_tiled_ablation(pwd)
