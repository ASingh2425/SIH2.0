"""
Phase 1 Representation Collision Audit Script — SIH Problem Statement 26171
Calculates exact spatial grid slot collisions for ground-truth objects in val_ui_dataset.json.
Determines how many GT objects map to identical grid cells (16x16 vs 32x32) and anchor slots.
Outputs: ml/evaluation/results/representation_collision_audit.json
"""

import os
import sys
import json
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import UI_CLASSES

def audit_grid_collisions(samples, grid_size=16):
    total_gt = 0
    unique_slots = 0
    shared_slots = 0
    collision_map = defaultdict(list)
    objects_per_slot_dist = defaultdict(int)

    for sample in samples:
        s_id = sample.get("image_id", sample.get("sample_id"))
        vp_w = sample.get("viewport", {}).get("width", 1920)
        vp_h = sample.get("viewport", {}).get("height", 1080)
        anns = sample["annotations"]
        total_gt += len(anns)

        scene_slots = defaultdict(list)
        for ann in anns:
            box = ann["bbox"]
            cls_name = ann["category"]
            cx = (box[0] + box[2] / 2.0) / vp_w
            cy = (box[1] + box[3] / 2.0) / vp_h
            gx = max(0, min(grid_size - 1, int(cx * grid_size)))
            gy = max(0, min(grid_size - 1, int(cy * grid_size)))

            w_n = box[2] / vp_w
            h_n = box[3] / vp_h
            # Anchor 1: Wide (w > h), Anchor 2: Small/Square (w <= h)
            anchor_idx = 0 if w_n > h_n else 1
            slot_key = (s_id, gy, gx, anchor_idx)
            scene_slots[slot_key].append(ann)

        for slot_key, items in scene_slots.items():
            count = len(items)
            objects_per_slot_dist[count] += 1
            if count == 1:
                unique_slots += 1
            else:
                shared_slots += count
                collision_map[slot_key] = items

    pct_unique = (unique_slots / float(total_gt) * 100.0) if total_gt > 0 else 0.0
    pct_collided = (shared_slots / float(total_gt) * 100.0) if total_gt > 0 else 0.0

    return {
        "grid_size": f"{grid_size}x{grid_size}",
        "total_gt_objects": total_gt,
        "unique_slot_assigned_objects": unique_slots,
        "collided_objects": shared_slots,
        "pct_unique_slots": round(pct_unique, 2),
        "pct_collided_slots": round(pct_collided, 2),
        "objects_per_slot_distribution": {str(k): v for k, v in objects_per_slot_dist.items()}
    }

def run_phase1_collision_audit(base_dir: str):
    print("==================================================")
    print("PHASE 1 — REPRESENTATION COLLISION AUDIT")
    print("==================================================")

    val_dataset_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    with open(val_dataset_path) as f:
        val_samples = json.load(f)["samples"]

    grid_16_audit = audit_grid_collisions(val_samples, grid_size=16)
    grid_32_audit = audit_grid_collisions(val_samples, grid_size=32)

    payload = {
        "dataset": "val_ui_dataset.json (Validation Set Only)",
        "grid_16x16_baseline_640_slots": grid_16_audit,
        "grid_32x32_fpn_2048_slots": grid_32_audit,
        "conclusion": f"Baseline 16x16 grid incurs {grid_16_audit['pct_collided_slots']}% spatial collisions, whereas 32x32 FPN grid reduces collisions to {grid_32_audit['pct_collided_slots']}%."
    }

    out_file = os.path.join(results_dir, "representation_collision_audit.json")
    with open(out_file, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[OK] Collision Audit Complete. Saved -> '{out_file}'")
    print(f"  Baseline 16x16 Collisions: {grid_16_audit['pct_collided_slots']}%")
    print(f"  FPN 32x32 Collisions: {grid_32_audit['pct_collided_slots']}%")
    print("--------------------------------------------------")
    return payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_phase1_collision_audit(pwd)
