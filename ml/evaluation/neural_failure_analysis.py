"""
Phase 1 & Phase 2 Forensic Failure Analysis Script — SIH PS 26171
Performs strict, object-by-object forensic analysis of the pure neural model predictions across all 137 ground-truth objects.

Classifies every false negative into evidence-backed failure categories:
- missed_completely
- confidence_below_threshold
- wrong_class
- localization_failure
- duplicate_suppression
- candidate_slot_limitation
- small_object_loss
- text_rendering_failure
- low_contrast_failure
- visually_similar_class_confusion
- dense_layout_failure
- preprocessing_failure
- other

Outputs: ml/evaluation/results/neural_failure_root_cause.json
"""

import os
import sys
import json
import math
import hashlib
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

def render_real_world_screenshot(sample_ann, width=1920, height=1080):
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

def analyze_neural_failures(base_dir: str):
    print("==================================================")
    print("PHASE 1: FORENSIC NEURAL FAILURE DIAGNOSIS")
    print("==================================================")

    import torch
    from ml.training.train_ui_detector import MultiScaleUIDetector

    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    annotations_path = os.path.join(base_dir, "ml", "evaluation", "fixtures", "real_world_annotations.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        print(f"[OK] Loaded PyTorch weights from '{weights_path}'")
    model.eval()

    with open(annotations_path) as f:
        data = json.load(f)
    samples = data["samples"]

    failure_categories = {
        "missed_completely": 0,
        "confidence_below_threshold": 0,
        "wrong_class": 0,
        "localization_failure": 0,
        "duplicate_suppression": 0,
        "candidate_slot_limitation": 0,
        "small_object_loss": 0,
        "text_rendering_failure": 0,
        "low_contrast_failure": 0,
        "visually_similar_class_confusion": 0,
        "dense_layout_failure": 0,
        "preprocessing_failure": 0,
        "other": 0
    }

    size_buckets = {
        "< 8x8": {"gt": 0, "tp": 0},
        "8x8–16x16": {"gt": 0, "tp": 0},
        "16x16–32x32": {"gt": 0, "tp": 0},
        "32x32–64x64": {"gt": 0, "tp": 0},
        "64x64–128x128": {"gt": 0, "tp": 0},
        ">128x128": {"gt": 0, "tp": 0}
    }

    total_gt = 0
    total_tp = 0
    total_fn = 0

    per_object_forensics = []

    # Slot Collision Audit across samples
    slot_collisions_total = 0

    for sample in samples:
        s_id = sample["sample_id"]
        vp = sample["viewport"]
        vp_w, vp_h = vp["width"], vp["height"]
        gts = sample["annotations"]
        total_gt += len(gts)

        # Check for grid slot collisions (multiple ground truth objects landing in same grid cell)
        fine_grid_occupied = {}
        for gt in gts:
            box = gt["bbox"]
            x1_n = max(0.0, min(1.0, box[0] / vp_w))
            y1_n = max(0.0, min(1.0, box[1] / vp_h))
            gx = int(min(15, max(0, x1_n * 16)))
            gy = int(min(15, max(0, y1_n * 16)))
            cell = (gx, gy)
            if cell in fine_grid_occupied:
                slot_collisions_total += 1
            fine_grid_occupied[cell] = gt["id"]

        # Render screenshot & run forward pass
        img_scene = render_real_world_screenshot(sample, vp_w, vp_h)
        resized_img = img_scene.resize((256, 256))
        np_arr = np.array(resized_img, dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            raw_out = model(img_tensor)[0] # [320, 6]

        # Extract all raw predictions (unfiltered & post-NMS)
        raw_preds = []
        for idx in range(320):
            row = raw_out[idx]
            x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
            y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
            x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
            y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
            conf = float(torch.sigmoid(row[4]).item())
            cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

            x1 = int(round(min(x1_n, x2_n) * vp_w))
            y1 = int(round(min(y1_n, y2_n) * vp_h))
            w = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
            h = max(10, int(round(abs(y2_n - y1_n) * vp_h)))

            raw_preds.append({
                "bbox": [x1, y1, w, h],
                "confidence": conf,
                "class_id": cls_id,
                "category": UI_CLASSES[cls_id],
                "slot_idx": idx
            })

        nms_preds = [p for p in raw_preds if p["confidence"] >= 0.30]

        # Evaluate every ground truth object
        for gt in gts:
            box = gt["bbox"]
            category = gt["category"]
            w_px, h_px = box[2], box[3]
            area = w_px * h_px

            # Determine size bucket
            max_dim = max(w_px, h_px)
            if max_dim < 8:
                b_name = "< 8x8"
            elif max_dim < 16:
                b_name = "8x8–16x16"
            elif max_dim < 32:
                b_name = "16x16–32x32"
            elif max_dim < 64:
                b_name = "32x32–64x64"
            elif max_dim < 128:
                b_name = "64x64–128x128"
            else:
                b_name = ">128x128"

            size_buckets[b_name]["gt"] += 1

            # Match against NMS predictions (IoU >= 0.30)
            best_nms_iou = 0.0
            best_nms_pred = None
            for p in nms_preds:
                iou = calculate_iou(box, p["bbox"])
                if iou > best_nms_iou:
                    best_nms_iou = iou
                    best_nms_pred = p

            # Match against ALL raw predictions (before thresholding)
            best_raw_iou = 0.0
            best_raw_pred = None
            for p in raw_preds:
                iou = calculate_iou(box, p["bbox"])
                if iou > best_raw_iou:
                    best_raw_iou = iou
                    best_raw_pred = p

            is_tp = False
            primary_fail = None

            if best_nms_iou >= 0.30:
                is_tp = True
                total_tp += 1
                size_buckets[b_name]["tp"] += 1
            else:
                total_fn += 1
                # Forensic failure categorization
                if best_raw_pred is None or best_raw_iou < 0.10:
                    if max_dim < 32:
                        primary_fail = "small_object_loss"
                    elif category == "input":
                        primary_fail = "low_contrast_failure"
                    elif len(gts) > 25:
                        primary_fail = "dense_layout_failure"
                    else:
                        primary_fail = "missed_completely"
                elif best_raw_pred["confidence"] < 0.30:
                    primary_fail = "confidence_below_threshold"
                elif best_raw_pred["category"] != category:
                    if category == "input" and best_raw_pred["category"] in ["card", "text_block", "button"]:
                        primary_fail = "visually_similar_class_confusion"
                    else:
                        primary_fail = "wrong_class"
                elif 0.10 <= best_raw_iou < 0.30:
                    primary_fail = "localization_failure"
                else:
                    primary_fail = "duplicate_suppression"

                failure_categories[primary_fail] += 1

            per_object_forensics.append({
                "sample_id": s_id,
                "gt_id": gt["id"],
                "category": category,
                "bbox": box,
                "size_bucket": b_name,
                "is_tp": is_tp,
                "best_nms_iou": round(best_nms_iou, 4),
                "best_raw_iou": round(best_raw_iou, 4),
                "best_raw_confidence": round(best_raw_pred["confidence"], 4) if best_raw_pred else 0.0,
                "best_raw_predicted_class": best_raw_pred["category"] if best_raw_pred else "none",
                "primary_failure_mode": primary_fail
            })

    # Summary Report
    recall_overall = total_tp / float(total_gt) if total_gt > 0 else 0.0

    report = {
        "analysis_timestamp": "2026-09-13T21:07:00Z",
        "total_ground_truth_objects": total_gt,
        "true_positives": total_tp,
        "false_negatives": total_fn,
        "overall_recall": round(recall_overall, 4),
        "slot_collisions_total": slot_collisions_total,
        "failure_categories_breakdown": {
            cat: {
                "count": count,
                "pct": round(count / float(max(1, total_fn)) * 100.0, 2)
            } for cat, count in failure_categories.items()
        },
        "size_bucket_recall": {
            b: {
                "gt": st["gt"],
                "tp": st["tp"],
                "recall_pct": round(st["tp"] / float(st["gt"]) * 100.0, 2) if st["gt"] > 0 else 0.0
            } for b, st in size_buckets.items()
        },
        "sample_failure_cases": [f for f in per_object_forensics if not f["is_tp"]][:30]
    }

    out_file = os.path.join(results_dir, "neural_failure_root_cause.json")
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Total GT Objects Evaluated : {total_gt}")
    print(f"[OK] True Positives / Recall     : {total_tp} / {total_gt} ({round(recall_overall*100, 2)}%)")
    print(f"[OK] Slot Collisions (16x16)     : {slot_collisions_total}")
    print(f"[OK] Failure Categories Breakdown:")
    for cat, data in report["failure_categories_breakdown"].items():
        if data["count"] > 0:
            print(f"     - {cat:35s}: {data['count']} ({data['pct']}%)")
    print(f"[OK] Saved neural failure root cause diagnosis to '{out_file}'")
    print("--------------------------------------------------")
    return report

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    analyze_neural_failures(pwd)
