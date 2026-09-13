"""
Gate 1 — Mathematical Target Encoding & Decoding Audit Script
Validates mathematical consistency of coordinate encoding and decoding.
Traces: GT BBOX -> NORMALIZED COORDS -> GRID CELL ASSIGNMENT -> DECODER -> RECOVERED BBOX
Generates:
- ml/evaluation/results/target_encoding_audit.json
"""

import os
import sys
import json
import torch
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from ml.training.train_ui_detector import build_target_tensor, UI_CLASSES, CLASS_MAP

def run_gate1_target_encoding_audit(base_dir: str):
    print("==================================================")
    print("GATE 1 — MATHEMATICAL TARGET ENCODING AUDIT")
    print("==================================================")

    test_objects = [
        {"id": "top_left_1x1", "bbox": [0, 0, 1, 1], "category": "icon"},
        {"id": "top_left_2x2", "bbox": [0, 0, 2, 2], "category": "icon"},
        {"id": "top_left_4x4", "bbox": [0, 0, 4, 4], "category": "icon"},
        {"id": "top_left_8x8", "bbox": [0, 0, 8, 8], "category": "icon"},
        {"id": "top_left_16x16", "bbox": [0, 0, 16, 16], "category": "icon"},
        {"id": "center_control", "bbox": [944, 524, 32, 32], "category": "button"},
        {"id": "bottom_right_input", "bbox": [1600, 1020, 310, 44], "category": "input"},
        {"id": "wide_nav", "bbox": [0, 0, 1920, 64], "category": "navigation"},
        {"id": "tall_sidebar", "bbox": [0, 64, 240, 1000], "category": "card"},
        {"id": "boundary_cell_16", "bbox": [120, 120, 40, 40], "category": "select"},
        {"id": "overlapping_a", "bbox": [800, 300, 200, 100], "category": "card"},
        {"id": "overlapping_b_nested", "bbox": [820, 320, 160, 40], "category": "input"}
    ]

    sample_doc = {
        "viewport": {"width": 1920, "height": 1080},
        "annotations": test_objects
    }

    target = build_target_tensor(sample_doc, 1920, 1080)  # [640, 6]
    active_indices = torch.where(target[:, 4] > 0.5)[0].tolist()

    records = []
    max_abs_error_px = 0.0

    for gt in test_objects:
        single_doc = {
            "viewport": {"width": 1920, "height": 1080},
            "annotations": [gt]
        }

        target = build_target_tensor(single_doc, 1920, 1080)
        active_indices = torch.where(target[:, 4] > 0.5)[0].tolist()

        gt_box = gt["bbox"]
        gt_x1, gt_y1, gt_w, gt_h = gt_box
        gt_x2, gt_y2 = gt_x1 + gt_w, gt_y1 + gt_h

        matching_slot = None
        min_diff = 1e9

        for idx in active_indices:
            row = target[idx]
            tx1 = float(row[0]) * 1920.0
            ty1 = float(row[1]) * 1080.0
            tx2 = float(row[2]) * 1920.0
            ty2 = float(row[3]) * 1080.0

            diff = abs(tx1 - gt_x1) + abs(ty1 - gt_y1) + abs(tx2 - gt_x2) + abs(ty2 - gt_y2)
            if diff < min_diff:
                min_diff = diff
                matching_slot = (idx, [tx1, ty1, tx2 - tx1, ty2 - ty1])

        if matching_slot:
            rec_box = matching_slot[1]
            abs_err = float(np.max(np.abs(np.array(rec_box) - np.array(gt_box))))
            rel_err = float(abs_err / float(max(1, max(gt_w, gt_h))))

            if abs_err > max_abs_error_px:
                max_abs_error_px = abs_err

            records.append({
                "object_id": gt["id"],
                "category": gt["category"],
                "gt_box": gt_box,
                "assigned_slot": matching_slot[0],
                "decoded_box": [round(c, 2) for c in rec_box],
                "abs_error_px": round(abs_err, 4),
                "rel_error": round(rel_err, 4)
            })

    audit_report = {
        "gate": "GATE_1_TARGET_ENCODING_AUDIT",
        "num_objects_tested": len(test_objects),
        "num_slots_assigned": len(active_indices),
        "max_abs_coordinate_error_px": round(max_abs_error_px, 4),
        "mathematically_consistent": max_abs_error_px <= 0.50,
        "object_records": records
    }

    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")
    os.makedirs(results_dir, exist_ok=True)
    out_path = os.path.join(results_dir, "target_encoding_audit.json")

    with open(out_path, "w") as f:
        json.dump(audit_report, f, indent=2)

    print(f"[OK] Gate 1 Target Encoding Audit Complete: Max Abs Error = {max_abs_error_px:.4f} px")
    print(f"[OK] Target Encoding Mathematically Consistent: {max_abs_error_px <= 0.50}")
    print(f"[OK] Saved audit report -> '{out_path}'")
    print("--------------------------------------------------")

if __name__ == "__main__":
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate1_target_encoding_audit(base_dir)
