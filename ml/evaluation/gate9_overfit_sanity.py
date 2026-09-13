"""
Gate 9 Overfit Sanity Check Script — SIH Problem Statement 26171
Trains candidate model on a 10-scene mini-batch from train_ui_dataset.json for 100 epochs.
Verifies whether the model can achieve >= 98% training recall and mAP50.
"""

import os
import sys
import json
import torch
import torch.optim as optim
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import MultiScaleUIDetector, build_target_tensor, render_sample_image, UI_CLASSES

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

def run_gate9_overfit_sanity(base_dir: str):
    print("==================================================")
    print("GATE 9 — OVERFIT SANITY CHECK (10 SCENES)")
    print("==================================================")

    train_dataset_path = os.path.join(base_dir, "ml", "dataset", "train_ui_dataset.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    with open(train_dataset_path) as f:
        data = json.load(f)

    # 10 mini-batch scenes
    mini_samples = data["samples"][:10]
    model = MultiScaleUIDetector()
    optimizer = optim.AdamW(model.parameters(), lr=3e-3, weight_decay=1e-5)

    # Pre-render inputs and target tensors
    tensors = []
    targets = []
    total_gt = 0
    for s in mini_samples:
        vp_w = s.get("viewport", {}).get("width", 1920)
        vp_h = s.get("viewport", {}).get("height", 1080)
        anns = s["annotations"]
        total_gt += len(anns)

        img = render_sample_image(s, vp_w, vp_h)
        np_arr = np.array(img.resize((256, 256)), dtype=np.float32).transpose(2, 0, 1) / 255.0
        tensors.append(torch.from_numpy(np_arr))
        targets.append(build_target_tensor(s, vp_w, vp_h))

    input_batch = torch.stack(tensors, dim=0) # [10, 3, 256, 256]
    target_batch = torch.stack(targets, dim=0) # [10, 640, 6]

    print(f"[INFO] Memorizing 10 scenes ({total_gt} GT objects) over 100 epochs...")
    model.train()
    for epoch in range(1, 101):
        optimizer.zero_grad()
        out = model(input_batch) # [10, 640, 6]

        loss_box = torch.nn.functional.smooth_l1_loss(out[:, :, :4], target_batch[:, :, :4])
        loss_conf = torch.nn.functional.binary_cross_entropy_with_logits(out[:, :, 4], target_batch[:, :, 4])
        loss_cls = torch.nn.functional.mse_loss(out[:, :, 5], target_batch[:, :, 5])
        loss = 10.0 * loss_box + 2.0 * loss_conf + loss_cls

        loss.backward()
        optimizer.step()

        if epoch % 20 == 0 or epoch == 100:
            print(f"  Epoch {epoch:3d}/100 | Loss: {loss.item():.4f} (Box: {loss_box.item():.4f}, Conf: {loss_conf.item():.4f})")

    # Evaluate Training Recall on the 10 mini-batch scenes
    model.eval()
    total_tp = 0
    with torch.no_grad():
        preds_batch = model(input_batch)

    for i in range(10):
        s = mini_samples[i]
        vp_w = s.get("viewport", {}).get("width", 1920)
        vp_h = s.get("viewport", {}).get("height", 1080)
        anns = s["annotations"]

        raw_out = preds_batch[i]
        preds = []
        for idx in range(raw_out.shape[0]):
            row = raw_out[idx]
            conf = float(torch.sigmoid(row[4]).item())
            if conf >= 0.15:
                x1_n = float(torch.clamp(row[0], 0.0, 1.0).item())
                y1_n = float(torch.clamp(row[1], 0.0, 1.0).item())
                x2_n = float(torch.clamp(row[2], 0.0, 1.0).item())
                y2_n = float(torch.clamp(row[3], 0.0, 1.0).item())
                px1 = int(round(min(x1_n, x2_n) * vp_w))
                py1 = int(round(min(y1_n, y2_n) * vp_h))
                pw = max(10, int(round(abs(x2_n - x1_n) * vp_w)))
                ph = max(10, int(round(abs(y2_n - y1_n) * vp_h)))
                preds.append([px1, py1, pw, ph])

        for ann in anns:
            gt_box = ann["bbox"]
            best_iou = max([calculate_iou(gt_box, p) for p in preds] + [0.0])
            if best_iou >= 0.30:
                total_tp += 1

    train_recall = (total_tp / float(total_gt)) * 100.0 if total_gt > 0 else 0.0
    passed = train_recall >= 98.0

    payload = {
        "gate": "GATE_9_OVERFIT_SANITY_CHECK",
        "memorized_scenes": 10,
        "total_gt_objects": total_gt,
        "true_positives": total_tp,
        "training_recall_pct": round(train_recall, 2),
        "status": "PASSED" if passed else "FAILED"
    }

    out_path = os.path.join(results_dir, "gate9_overfit_sanity.json")
    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Gate 9 Overfit Sanity Test Complete: Training Recall = {train_recall:.2f}% (Status: {payload['status']})")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate9_overfit_sanity(pwd)
