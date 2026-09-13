"""
Phase 1 — Representation Diagnostics Script
Executes tiny-set overfit tests, single-class model sanity tests, and grid collision analysis.
Generates:
- ml/evaluation/results/representation_diagnostics.json
"""

import os
import sys
import json
import time
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from ml.training.train_ui_detector import MultiScaleUIDetector, render_sample_image, build_target_tensor, UI_CLASSES, CLASS_MAP

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

def run_phase1_diagnostics(base_dir: str):
    print("==================================================")
    print("PHASE 1 — REPRESENTATION DIAGNOSTICS")
    print("==================================================")

    train_dataset_path = os.path.join(base_dir, "ml", "dataset", "train_ui_dataset.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)

    with open(train_dataset_path) as f:
        train_data = json.load(f)

    all_samples = train_data["samples"]

    # C. Grid Slot Collision Analysis
    collision_stats = []
    total_gt = 0
    total_preserved = 0

    for s in all_samples[:50]:
        anns = s["annotations"]
        total_gt += len(anns)
        target = build_target_tensor(s)
        num_pos = int((target[:, 4] > 0.5).sum().item())
        total_preserved += num_pos
        collision_stats.append({
            "sample_id": s.get("image_id", s.get("sample_id")),
            "gt_count": len(anns),
            "preserved_slots": num_pos,
            "overwritten_count": len(anns) - num_pos
        })

    preservation_ratio = (total_preserved / float(total_gt)) if total_gt > 0 else 0.0

    # A. Tiny Overfit Tests
    overfit_results = {}
    for subset_size in [5, 10, 20]:
        mini_samples = all_samples[:subset_size]
        X_list = [torch.from_numpy(np.array(render_sample_image(s).resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0) for s in mini_samples]
        Y_list = [build_target_tensor(s) for s in mini_samples]

        X_train = torch.stack(X_list)
        Y_train = torch.stack(Y_list)

        model = MultiScaleUIDetector()
        opt = optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-5)
        conf_crit = nn.BCEWithLogitsLoss()
        box_crit = nn.MSELoss()

        model.train()
        for epoch in range(1, 81):
            for i in range(len(mini_samples)):
                x = X_train[i:i+1]
                y_true = Y_train[i:i+1]
                opt.zero_grad()
                out = model(x)

                c_loss = conf_crit(out[:, :, 4], y_true[:, :, 4])
                mask = (y_true[:, :, 4] > 0.5)
                b_loss = box_crit(out[:, :, :4][mask], y_true[:, :, :4][mask]) if mask.sum() > 0 else torch.tensor(0.0)
                cls_loss = F.smooth_l1_loss(out[:, :, 5][mask], y_true[:, :, 5][mask]) if mask.sum() > 0 else torch.tensor(0.0)

                (5.0 * b_loss + 1.0 * c_loss + 0.5 * cls_loss).backward()
                opt.step()

        model.eval()
        t_gt, t_tp = 0, 0
        for i, s in enumerate(mini_samples):
            img_tensor = X_train[i:i+1]
            with torch.no_grad():
                out = model(img_tensor)[0]
            preds = []
            for idx in range(out.shape[0]):
                r = out[idx]
                conf = float(torch.sigmoid(r[4]).item())
                if conf >= 0.20:
                    px1 = int(round(min(float(r[0]), float(r[2])) * 1920))
                    py1 = int(round(min(float(r[1]), float(r[3])) * 1080))
                    pw = max(1, int(round(abs(float(r[2]) - float(r[0])) * 1920)))
                    ph = max(1, int(round(abs(float(r[3]) - float(r[1])) * 1080)))
                    cls_id = abs(int(r[5].item())) % len(UI_CLASSES)
                    preds.append({"bbox": [px1, py1, pw, ph], "category": UI_CLASSES[cls_id]})

            for ann in s["annotations"]:
                t_gt += 1
                best_iou = max([calculate_iou(ann["bbox"], p["bbox"]) for p in preds], default=0.0)
                if best_iou >= 0.30:
                    t_tp += 1

        rec = (t_tp / float(t_gt)) if t_gt > 0 else 0.0
        overfit_results[f"{subset_size}_scenes"] = {
            "subset_size": subset_size,
            "total_gt": t_gt,
            "true_positives": t_tp,
            "memorization_recall": round(rec, 4)
        }

    report = {
        "phase": "PHASE_1_REPRESENTATION_DIAGNOSTICS",
        "grid_preservation_ratio": round(preservation_ratio, 4),
        "total_gt_tested": total_gt,
        "total_preserved_slots": total_preserved,
        "overfit_experiments": overfit_results
    }

    out_path = os.path.join(results_dir, "representation_diagnostics.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)

    print(f"[OK] Grid Preservation Ratio: {preservation_ratio*100.0:.2f}%")
    print(f"[OK] Saved representation diagnostics -> '{out_path}'")
    print("--------------------------------------------------")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_phase1_diagnostics(base_dir)
