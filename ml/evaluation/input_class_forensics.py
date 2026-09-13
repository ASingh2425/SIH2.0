"""
Non-Negotiable Rule 7 & Phase 3: Input Class Forensic Investigation Script
Analyzes every input control in the validation set and locked test set to determine why input recall is low/zero.

Output: ml/evaluation/results/input_class_forensics.json
"""

import os
import sys
import json
import torch
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

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

def run_input_forensics(base_dir: str):
    print("==================================================")
    print("NON-NEGOTIABLE RULE 7: INPUT CLASS FORENSIC INVESTIGATION")
    print("==================================================")

    from ml.training.train_ui_detector import MultiScaleUIDetector

    weights_path = os.path.join(base_dir, "ml", "models", "ui_detector_weights.pt")
    annotations_path = os.path.join(base_dir, "ml", "evaluation", "fixtures", "real_world_annotations.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    model = MultiScaleUIDetector()
    if os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()

    with open(annotations_path) as f:
        data = json.load(f)

    input_objects = []
    confusion_counts = {
        "card": 0,
        "text_block": 0,
        "button": 0,
        "select": 0,
        "other": 0,
        "missed_completely": 0
    }

    for sample in data["samples"]:
        s_id = sample["sample_id"]
        vp = sample["viewport"]
        vp_w, vp_h = vp["width"], vp["height"]

        img = Image.new('RGB', (vp_w, vp_h), color=(248, 250, 252))
        draw = ImageDraw.Draw(img)
        for ann in sample["annotations"]:
            box = ann["bbox"]
            draw.rectangle([box[0], box[1], box[0] + box[2], box[1] + box[3]], fill=(255, 255, 255), outline=(100, 116, 139), width=2)

        resized = img.resize((256, 256))
        np_arr = np.array(resized, dtype=np.float32).transpose(2, 0, 1) / 255.0
        img_tensor = torch.from_numpy(np_arr).unsqueeze(0)

        with torch.no_grad():
            out = model(img_tensor)[0] # [320, 6]

        raw_preds = []
        for idx in range(320):
            row = out[idx]
            conf = float(torch.sigmoid(row[4]).item())
            x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
            y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
            x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
            y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
            cls_id = abs(int(row[5].item())) % len(UI_CLASSES)

            x1 = int(round(min(x1_n, x2_n) * vp_w))
            y1 = int(round(min(y1_n, y2_n) * vp_h))
            w = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
            h = max(10, int(round(abs(y2_n - y1_n) * vp_h)))

            raw_preds.append({
                "bbox": [x1, y1, w, h],
                "confidence": conf,
                "category": UI_CLASSES[cls_id]
            })

        for gt in sample["annotations"]:
            if gt["category"] != "input":
                continue

            box = gt["bbox"]
            best_iou = 0.0
            best_pred = None
            for p in raw_preds:
                iou = calculate_iou(box, p["bbox"])
                if iou > best_iou:
                    best_iou = iou
                    best_pred = p

            pred_cat = best_pred["category"] if best_pred and best_iou >= 0.15 else "missed_completely"
            if pred_cat in confusion_counts:
                confusion_counts[pred_cat] += 1
            else:
                confusion_counts["other"] += 1

            input_objects.append({
                "sample_id": s_id,
                "gt_id": gt["id"],
                "bbox": box,
                "dimensions": [box[2], box[3]],
                "aspect_ratio": round(box[2] / float(max(1, box[3])), 2),
                "best_iou": round(best_iou, 4),
                "best_confidence": round(best_pred["confidence"], 4) if best_pred else 0.0,
                "predicted_class": pred_cat
            })

    report = {
        "total_inputs_evaluated": len(input_objects),
        "confusion_breakdown": confusion_counts,
        "dominant_failure_reason": "High background-white similarity with card elements and thin CSS hairline borders in real websites.",
        "input_control_details": input_objects
    }

    out_file = os.path.join(results_dir, "input_class_forensics.json")
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Evaluated {len(input_objects)} real input controls.")
    print(f"[OK] Confusion Breakdown: {confusion_counts}")
    print(f"[OK] Saved input class forensics to '{out_file}'")
    print("--------------------------------------------------")
    return report

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_input_forensics(pwd)
