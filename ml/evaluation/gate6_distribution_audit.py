"""
Gate 6 Training vs Validation Domain Gap Audit Script — SIH Problem Statement 26171
Quantifies distribution statistics between train_ui_dataset.json and val_ui_dataset.json:
- Object size distribution (width, height, area)
- Class distribution
- Aspect ratio distribution
- Scene object density distribution
Outputs: ml/evaluation/results/gate6_distribution_audit.json
"""

import os
import sys
import json
import numpy as np

def analyze_dataset(data_path: str):
    with open(data_path) as f:
        data = json.load(f)

    samples = data["samples"]
    class_counts = {}
    areas = []
    aspect_ratios = []
    densities = []
    widths = []
    heights = []

    for s in samples:
        anns = s["annotations"]
        densities.append(len(anns))
        for ann in anns:
            cls = ann["category"]
            class_counts[cls] = class_counts.get(cls, 0) + 1
            w, h = ann["bbox"][2], ann["bbox"][3]
            widths.append(w)
            heights.append(h)
            areas.append(w * h)
            aspect_ratios.append(round(w / float(max(1, h)), 2))

    return {
        "num_scenes": len(samples),
        "total_objects": len(areas),
        "class_distribution": class_counts,
        "mean_object_density": round(float(np.mean(densities)), 2),
        "median_area": round(float(np.median(areas)), 1),
        "mean_area": round(float(np.mean(areas)), 1),
        "small_objects_pct": round(float(np.sum(np.array(areas) < (32*32)) / len(areas) * 100.0), 2),
        "mean_aspect_ratio": round(float(np.mean(aspect_ratios)), 2)
    }

def run_gate6_distribution_audit(base_dir: str):
    print("==================================================")
    print("GATE 6 — TRAINING VS VALIDATION DOMAIN GAP AUDIT")
    print("==================================================")

    train_path = os.path.join(base_dir, "ml", "dataset", "train_ui_dataset.json")
    val_path = os.path.join(base_dir, "ml", "dataset", "val_ui_dataset.json")
    results_dir = os.path.join(base_dir, "ml", "evaluation", "results")

    train_stats = analyze_dataset(train_path)
    val_stats = analyze_dataset(val_path)

    audit_payload = {
        "train_distribution": train_stats,
        "validation_distribution": val_stats,
        "domain_gaps": {
            "density_gap": round(val_stats["mean_object_density"] - train_stats["mean_object_density"], 2),
            "small_object_gap_pct": round(val_stats["small_objects_pct"] - train_stats["small_objects_pct"], 2),
            "aspect_ratio_gap": round(val_stats["mean_aspect_ratio"] - train_stats["mean_aspect_ratio"], 2)
        }
    }

    out_file = os.path.join(results_dir, "gate6_distribution_audit.json")
    with open(out_file, "w") as f:
        json.dump(audit_payload, f, indent=2)

    print(f"[OK] Distribution Audit Complete. Saved -> '{out_file}'")
    print(f"  Train Density: {train_stats['mean_object_density']} vs Val Density: {val_stats['mean_object_density']}")
    print(f"  Train Small Objects %: {train_stats['small_objects_pct']}% vs Val Small Objects %: {val_stats['small_objects_pct']}%")
    print("--------------------------------------------------")
    return audit_payload

if __name__ == "__main__":
    pwd = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_gate6_distribution_audit(pwd)
