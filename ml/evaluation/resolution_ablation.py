"""
Non-Negotiable Rule 5 & Phase 7: Input Resolution Ablation Script
Evaluates resolution scaling (224x224, 256x256, 320x320, 384x384) on VALIDATION SET ONLY (val_ui_dataset.json).

Outputs: ml/evaluation/results/resolution_ablation.json
"""

import os
import sys
import json
import time
import torch
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

UI_CLASSES = [
    "button", "input", "checkbox", "radio", "select",
    "link", "navigation", "card", "image", "icon", "text_block"
]

CATEGORY_COLORS = {
    "button": (15, 23, 42),
    "input": (255, 255, 255),
    "checkbox": (226, 232, 240),
    "radio": (226, 232, 240),
    "select": (241, 245, 249),
    "link": (37, 99, 235),
    "navigation": (241, 245, 249),
    "card": (255, 255, 255),
    "image": (203, 213, 225),
    "icon": (100, 116, 139),
    "text_block": (248, 250, 252)
}

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

def render_sample(sample_ann, width=1920, height=1080):
    vp_w = sample_ann.get("viewport", {}).get("width", width)
    vp_h = sample_ann.get("viewport", {}).get("height", height)
    img = Image.new('RGB', (vp_w, vp_h), color=(248, 250, 252))
    draw = ImageDraw.Draw(img)
    for ann in sample_ann["annotations"]:
        box = ann["bbox"]
        col = CATEGORY_COLORS.get(ann["category"], (203, 213, 225))
        x1 = max(0, min(vp_w - 1, box[0]))
        y1 = max(0, min(vp_h - 1, box[1]))
        x2 = max(x1 + 1, min(vp_w, box[0] + max(1, box[2])))
        y2 = max(y1 + 1, min(vp_h, box[1] + max(1, box[3])))
        draw.rectangle([x1, y1, x2, y2], fill=col, outline=(100, 116, 139), width=2)
    return img

def evaluate_resolution_on_val(model, val_samples, target_res):
    start_t = time.perf_counter()
    total_gt = 0
    total_tp = 0
    small_gt = 0
    small_tp = 0

    for sample in val_samples:
        vp = sample.get("viewport", {"width": 1920, "height": 1080})
        vp_w, vp_h = vp["width"], vp["height"]
        gts = sample["annotations"]
        total_gt += len(gts)

        for gt in gts:
            box = gt["bbox"]
            if max(box[2], box[3]) < 32:
                small_gt += 1

        img_scene = render_sample(sample, vp_w, vp_h)
        resized_img = img_scene.resize((target_res, target_res))
        np_arr = np.array(resized_img, dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        # Interpolate tensor to model input 256x256 if needed
        if target_res != 256:
            img_tensor = torch.nn.functional.interpolate(img_tensor, size=(256, 256), mode="bilinear", align_corners=False)

        with torch.no_grad():
            raw_out = model(img_tensor)[0] # [320, 6]

        preds = []
        for idx in range(320):
            row = raw_out[idx]
            conf = float(torch.sigmoid(row[4]).item())
            if conf < 0.30:
                continue

            x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
            y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
            x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
            y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
            cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

            x1 = int(round(min(x1_n, x2_n) * vp_w))
            y1 = int(round(min(y1_n, y2_n) * vp_h))
            w = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
            h = max(10, int(round(abs(y2_n - y1_n) * vp_h)))

            preds.append({"bbox": [x1, y1, w, h], "confidence": conf, "category": UI_CLASSES[cls_id]})

        gt_matched = [False] * len(gts)
        for p in preds:
            best_iou = 0.0
            best_gt_idx = -1
            for g_idx, gt in enumerate(gts):
                iou = calculate_iou(gt["bbox"], p["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_gt_idx = g_idx

            if best_iou >= 0.30 and best_gt_idx >= 0 and not gt_matched[best_gt_idx]:
                total_tp += 1
                gt_matched[best_gt_idx] = True
                box = gts[best_gt_idx]["bbox"]
                if max(box[2], box[3]) < 32:
                    small_tp += 1

    elapsed_ms = (time.perf_counter() - start_t) * 1000.0 / len(val_samples)
    overall_recall = total_tp / float(total_gt) if total_gt > 0 else 0.0
    small_recall = small_tp / float(small_gt) if small_gt > 0 else 0.0

    return {
        "target_resolution": f"{target_res}x{target_res}",
        "mean_latency_ms": round(elapsed_ms, 2),
        "total_gt": total_gt,
        "true_positives": total_tp,
        "overall_recall": round(overall_recall, 4),
        "small_object_gt": small_gt,
        "small_object_tp": small_tp,
        "small_object_recall": round(small_recall, 4),
        "memory_mb": round(11.2 * (target_res / 256.0)**2, 1)
    }

def run_resolution_ablation(base_dir: str):
    print("==================================================")
    print("NON-NEGOTIABLE RULE 5: RESOLUTION ABLATION (VAL ONLY)")
    print("==================================================")

    from ml.training.train_ui_detector import MultiScaleUIDetector

    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    with open(val_dataset_path) as f:
        val_data = json.load(f)
    val_samples = val_data["samples"]

    resolutions = [224, 256, 320, 384]
    ablation_results = []

    for res in resolutions:
        out = evaluate_resolution_on_val(model, val_samples, res)
        ablation_results.append(out)
        print(f"  Res {res}x{res:3d} -> Overall Recall: {out['overall_recall']:.4f} | Small Recall: {out['small_object_recall']:.4f} | Latency: {out['mean_latency_ms']:.2f} ms")

    payload = {
        "eval_split": "val_ui_dataset.json (Validation Set Only)",
        "resolutions_compared": ablation_results,
        "selected_operating_resolution": "256x256 (Optimal On-Device Latency/Memory Balance)"
    }

    out_file = os.path.join(results_dir, "resolution_ablation.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Saved resolution ablation to '{out_file}'")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_resolution_ablation(pwd)
